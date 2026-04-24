import time
import os
import csv

import cv2 as cv
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.parameter import Parameter
from rcl_interfaces.msg import SetParametersResult
from sensor_msgs.msg import CompressedImage, Image
from std_msgs.msg import String

from .command_encoder import CommandEncoder
from .debouncer import Debouncer
from .mediapipe_runner import MediaPipeRunner
from .transport import TcpTransport, TransportError, UartTransport


STUNT_COMMANDS = {"JUMP", "CROSSLEG,0,5"}

LABEL_TEXT = {
    "None": "No hand",
    "Zero": "Fist / Stop",
    "Five": "Open Palm / Forward",
    "PointLeft": "Point Left / Turn",
    "PointRight": "Point Right / Turn",
    "Thumb_up": "Thumb Up / Jump",
    "idle": "Idle",
    "skipped": "Frame skipped",
}

COMMAND_TEXT = {
    "None": "Robot command: DRIVE,0,0",
    "Zero": "Robot command: DRIVE,0,0",
    "Five": "Robot command: DRIVE,250,0",
    "PointLeft": "Robot command: DRIVE,0,600",
    "PointRight": "Robot command: DRIVE,0,-600",
    "Thumb_up": "Robot command: JUMP (safety gated)",
    "idle": "Robot command: none",
    "skipped": "Robot command: unchanged",
}


class VisionBridge(Node):
    def __init__(self):
        super().__init__("wheeleg_vision_bridge")
        self.bridge = CvBridge()

        self.declare_parameter("image_topic", "/espRos/esp32camera")
        self.declare_parameter("image_type", "compressed")
        self.declare_parameter("transport", "uart")
        self.declare_parameter("uart_port", "/dev/ttyUSB0")
        self.declare_parameter("uart_baud", 115200)
        self.declare_parameter("tcp_host", "192.168.1.100")
        self.declare_parameter("tcp_port", 23)
        self.declare_parameter("dry_run", True)
        self.declare_parameter("mode", "idle")
        self.declare_parameter("debounce_frames", 5)
        self.declare_parameter("command_rate_hz", 5.0)
        self.declare_parameter("watchdog_ms", 1000)
        self.declare_parameter("face_yaw_gain_mrad", 1500)
        self.declare_parameter("face_deadband", 0.1)
        self.declare_parameter("mediapipe_confidence", 0.6)
        self.declare_parameter("frame_skip", 2)
        self.declare_parameter("debug_window", False)
        self.declare_parameter("presentation_window", False)
        self.declare_parameter("presentation_fullscreen", False)
        self.declare_parameter("presentation_mirror", False)
        self.declare_parameter("presentation_title", "B-BOT Vision Teleoperation")
        self.declare_parameter("debug_events", False)
        self.declare_parameter("debug_event_rate_hz", 2.0)
        self.declare_parameter("stunt_armed", False)
        self.declare_parameter("ack_log_csv", "")

        self.mode = self.get_parameter("mode").value
        self.image_type = self.get_parameter("image_type").value
        self.frame_skip = max(1, int(self.get_parameter("frame_skip").value))
        self.debug_window = bool(self.get_parameter("debug_window").value)
        self.presentation_window = bool(self.get_parameter("presentation_window").value)
        self.presentation_fullscreen = bool(self.get_parameter("presentation_fullscreen").value)
        self.presentation_mirror = bool(self.get_parameter("presentation_mirror").value)
        self.presentation_title = str(self.get_parameter("presentation_title").value)
        self.debug_events = bool(self.get_parameter("debug_events").value)
        self.debug_event_period = 1.0 / max(0.1, float(self.get_parameter("debug_event_rate_hz").value))
        self.dry_run = bool(self.get_parameter("dry_run").value)
        self.stunt_armed = bool(self.get_parameter("stunt_armed").value)
        self.ack_log_csv = str(self.get_parameter("ack_log_csv").value)
        self.command_period = 1.0 / max(0.1, float(self.get_parameter("command_rate_hz").value))
        self.watchdog_s = float(self.get_parameter("watchdog_ms").value) / 1000.0

        self.runner = MediaPipeRunner(self.get_parameter("mediapipe_confidence").value)
        self.debouncer = Debouncer(self.get_parameter("debounce_frames").value)
        self.encoder = CommandEncoder(
            self.get_parameter("face_yaw_gain_mrad").value,
            self.get_parameter("face_deadband").value,
        )
        self.transport = self._make_transport()
        self.status_pub = self.create_publisher(String, "/wheeleg/vision_status", 10)
        self.mode_sub = self.create_subscription(String, "/wheeleg/vision_mode", self._mode_msg, 10)
        self.add_on_set_parameters_callback(self._params_changed)

        msg_type = CompressedImage if self.image_type == "compressed" else Image
        self.image_sub = self.create_subscription(
            msg_type,
            self.get_parameter("image_topic").value,
            self._image_cb,
            1,
        )

        self._last_frame_time = time.monotonic()
        self._last_command_time = 0.0
        self._last_debug_event_time = 0.0
        self._frame_count = 0
        self._preview_frame_count = 0
        self._preview_fps_start = time.monotonic()
        self._preview_fps = 0.0
        self._preview_window_configured = False
        self._last_face_command = "YAWRATE,0"
        self._current_gesture_drive = "DRIVE,0,0"
        self._ack_log_header_written = False
        self.timer = self.create_timer(0.2, self._timer_cb)
        self.get_logger().info(
            f"vision bridge ready: topic={self.get_parameter('image_topic').value} "
            f"type={self.image_type} mode={self.mode} dry_run={self.dry_run}"
        )

    def _make_transport(self):
        transport = self.get_parameter("transport").value
        if transport == "tcp":
            return TcpTransport(self.get_parameter("tcp_host").value, self.get_parameter("tcp_port").value)
        return UartTransport(self.get_parameter("uart_port").value, self.get_parameter("uart_baud").value)

    def _mode_msg(self, msg):
        self._set_mode(msg.data)

    def _params_changed(self, params):
        for param in params:
            if param.name == "mode" and param.type_ == Parameter.Type.STRING:
                self._set_mode(param.value)
            elif param.name == "dry_run" and param.type_ == Parameter.Type.BOOL:
                self.dry_run = bool(param.value)
                self.get_logger().info(f"dry_run={self.dry_run}")
            elif param.name == "debug_events" and param.type_ == Parameter.Type.BOOL:
                self.debug_events = bool(param.value)
                self.get_logger().info(f"debug_events={self.debug_events}")
            elif param.name == "debug_window" and param.type_ == Parameter.Type.BOOL:
                self.debug_window = bool(param.value)
                self.get_logger().info(f"debug_window={self.debug_window}")
            elif param.name == "presentation_window" and param.type_ == Parameter.Type.BOOL:
                self.presentation_window = bool(param.value)
                self.get_logger().info(f"presentation_window={self.presentation_window}")
            elif param.name == "presentation_fullscreen" and param.type_ == Parameter.Type.BOOL:
                self.presentation_fullscreen = bool(param.value)
                self._preview_window_configured = False
            elif param.name == "presentation_mirror" and param.type_ == Parameter.Type.BOOL:
                self.presentation_mirror = bool(param.value)
            elif param.name == "presentation_title" and param.type_ == Parameter.Type.STRING:
                self.presentation_title = str(param.value)
            elif param.name == "stunt_armed" and param.type_ == Parameter.Type.BOOL:
                self.stunt_armed = bool(param.value)
                self.get_logger().warning(f"stunt_armed={self.stunt_armed}")
            elif param.name == "debug_event_rate_hz":
                self.debug_event_period = 1.0 / max(0.1, float(param.value))
            elif param.name == "command_rate_hz":
                self.command_period = 1.0 / max(0.1, float(param.value))
        return SetParametersResult(successful=True)

    def _set_mode(self, mode):
        if mode not in ("idle", "gesture", "stunt", "face"):
            self.get_logger().warning(f"ignored invalid mode: {mode}")
            return
        if mode != self.mode:
            self.debouncer.reset()
            if self.mode == "face":
                self._send("YAWRATE,0", force=True)
            if self.mode == "gesture":
                self._current_gesture_drive = "DRIVE,0,0"
                self._send("DRIVE,0,0", force=True)
        self.mode = mode
        self.get_logger().info(f"mode={mode}")

    def _image_cb(self, msg):
        self._last_frame_time = time.monotonic()
        self._frame_count += 1
        if self.mode == "idle" or self._frame_count % self.frame_skip != 0:
            if self.debug_window or self.presentation_window:
                frame = self._decode_frame(msg)
                self._show_debug_window(frame, label="idle" if self.mode == "idle" else "skipped")
            return

        frame = self._decode_frame(msg)
        event = self.runner.process(frame, self.mode)
        debug_label = None
        debug_stable = None
        debug_command = None

        if self.mode == "gesture":
            label = event.get("label") if event else None
            stable = self.debouncer.update(label)
            self._debug_event(f"gesture label={label} stable={stable}")
            command = self.encoder.encode_gesture(stable) if stable else None
            debug_label = label if label else "None"
            debug_stable = stable if stable else ""
            if label is None:
                # hand lost this frame → stop continuous teleop immediately
                self._current_gesture_drive = "DRIVE,0,0"
            elif command and command.startswith("DRIVE,"):
                self._current_gesture_drive = command
            elif command:
                # impulse command (e.g. JUMP): send once on the stabilising edge
                self._send_guarded(command, force=True)
            debug_command = command if command else self._current_gesture_drive
        elif self.mode == "stunt":
            self._debug_event(f"stunt event={event}")
            command = self.encoder.encode_stunt(event)
            debug_label = event.get("kind") if event else "None"
            debug_command = command if command else ""
            if command:
                self._send_guarded(command)
        elif self.mode == "face":
            self._last_face_command = self.encoder.encode_face(event)
            self._debug_event(f"face event={event} command={self._last_face_command}")
            debug_label = "face" if event else "None"
            debug_command = self._last_face_command

        if self.debug_window or self.presentation_window:
            self._show_debug_window(
                frame,
                label=debug_label,
                stable=debug_stable,
                command=debug_command,
            )

    def _decode_frame(self, msg):
        if self.image_type == "compressed":
            return self.bridge.compressed_imgmsg_to_cv2(msg)
        return self.bridge.imgmsg_to_cv2(msg, "bgr8")

    def _show_debug_window(self, frame, label=None, stable=None, command=None):
        self._preview_frame_count += 1
        now = time.monotonic()
        elapsed = now - self._preview_fps_start
        if elapsed >= 1.0:
            self._preview_fps = self._preview_frame_count / elapsed
            self._preview_frame_count = 0
            self._preview_fps_start = now

        display = frame.copy()
        if self.presentation_window and self.presentation_mirror:
            display = cv.flip(display, 1)
        h, w = display.shape[:2]
        if self.presentation_window:
            self._draw_presentation_monitor(display, label, command)
            self._configure_preview_window()
            cv.imshow("wheeleg_vision_bridge monitor", display)
            key = cv.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                cv.destroyWindow("wheeleg_vision_bridge monitor")
                self.debug_window = False
                self.presentation_window = False
            return

        cv.line(display, (w // 2, 0), (w // 2, h), (0, 255, 255), 1)
        cv.line(display, (0, h // 2), (w, h // 2), (0, 255, 255), 1)
        margin_x = int(w * 0.18)
        margin_y = int(h * 0.14)
        cv.rectangle(display, (margin_x, margin_y), (w - margin_x, h - margin_y), (0, 255, 0), 1)

        label_text = label if label is not None else "None"
        stable_text = stable if stable else ""
        command_text = command if command else ""
        lines = [
            f"mode: {self.mode}  dry_run: {self.dry_run}  fps: {self._preview_fps:.2f}",
            f"label: {label_text}  stable: {stable_text}",
            f"command: {command_text}",
            "q/esc: close monitor",
        ]
        y = 22
        for line in lines:
            cv.putText(display, line, (10, y), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv.LINE_AA)
            cv.putText(display, line, (10, y), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
            y += 20
        self._configure_preview_window()
        cv.imshow("wheeleg_vision_bridge monitor", display)
        key = cv.waitKey(1) & 0xFF
        if key in (27, ord("q")):
            cv.destroyWindow("wheeleg_vision_bridge monitor")
            self.debug_window = False

    def _draw_presentation_monitor(self, display, label, command):
        h, w = display.shape[:2]
        label_text = LABEL_TEXT.get(label if label else "None", label if label else "No hand")
        command_text = COMMAND_TEXT.get(label if label else "None", f"Robot command: {command}" if command else "Robot command: waiting")
        if command and command not in command_text:
            command_text = f"Robot command: {command}"

        margin_x = int(w * 0.16)
        margin_y = int(h * 0.12)
        cv.rectangle(display, (margin_x, margin_y), (w - margin_x, h - margin_y), (0, 220, 0), 2)
        self._draw_panel(display, 0, 0, w, 86, alpha=0.58)
        self._draw_panel(display, 0, h - 136, w, 136, alpha=0.62)

        cv.putText(display, self.presentation_title, (28, 54), cv.FONT_HERSHEY_SIMPLEX, 1.35, (0, 0, 0), 5, cv.LINE_AA)
        cv.putText(display, self.presentation_title, (28, 54), cv.FONT_HERSHEY_SIMPLEX, 1.35, (255, 255, 255), 2, cv.LINE_AA)
        cv.putText(display, label_text, (28, h - 78), cv.FONT_HERSHEY_SIMPLEX, 1.45, (0, 0, 0), 5, cv.LINE_AA)
        cv.putText(display, label_text, (28, h - 78), cv.FONT_HERSHEY_SIMPLEX, 1.45, (255, 255, 255), 2, cv.LINE_AA)
        cv.putText(display, command_text, (30, h - 30), cv.FONT_HERSHEY_SIMPLEX, 0.78, (0, 0, 0), 4, cv.LINE_AA)
        cv.putText(display, command_text, (30, h - 30), cv.FONT_HERSHEY_SIMPLEX, 0.78, (235, 255, 235), 2, cv.LINE_AA)
        cv.putText(display, f"{self._preview_fps:.1f} FPS", (w - 130, 34), cv.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 3, cv.LINE_AA)
        cv.putText(display, f"{self._preview_fps:.1f} FPS", (w - 130, 34), cv.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 1, cv.LINE_AA)

    def _draw_panel(self, frame, x, y, w, h, alpha):
        overlay = frame.copy()
        cv.rectangle(overlay, (x, y), (x + w, y + h), (20, 24, 28), -1)
        cv.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)

    def _configure_preview_window(self):
        if self._preview_window_configured:
            return
        cv.namedWindow("wheeleg_vision_bridge monitor", cv.WINDOW_NORMAL)
        if self.presentation_window and self.presentation_fullscreen:
            cv.setWindowProperty("wheeleg_vision_bridge monitor", cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
        self._preview_window_configured = True

    def _timer_cb(self):
        now = time.monotonic()
        if self.mode == "face" and now - self._last_command_time >= self.command_period:
            self._send(self._last_face_command, force=True)
        if self.mode == "gesture" and now - self._last_command_time >= self.command_period:
            # continuous re-send so the robot's 500 ms DRIVE watchdog stays fed
            self._send(self._current_gesture_drive, force=True)

        if self.mode != "idle" and now - self._last_frame_time > self.watchdog_s:
            self._send("QUEUE_STOP", force=True)
            if self.mode == "face":
                self._send("YAWRATE,0", force=True)
            if self.mode == "gesture":
                self._current_gesture_drive = "DRIVE,0,0"
                self._send("DRIVE,0,0", force=True)

        status = String()
        status.data = f"mode={self.mode} dry_run={self.dry_run} frames={self._frame_count}"
        self.status_pub.publish(status)

    def _send(self, command, force=False):
        now = time.monotonic()
        if not force and now - self._last_command_time < self.command_period:
            return
        self._last_command_time = now
        if self.dry_run:
            self.get_logger().info(f"dry-run command: {command}")
            return
        try:
            ack = self.transport.write_line(command)
            if ack:
                self._log_ack(command, ack)
                self.get_logger().info(
                    f"sent: {command} ack={ack.get('ack_kind')} "
                    f"latency_ms={ack.get('ack_latency_ms'):.3f}"
                )
            else:
                self.get_logger().info(f"sent: {command}")
        except (OSError, TransportError) as exc:
            self.get_logger().warning(f"transport write failed: {exc}")

    def _send_guarded(self, command, force=False):
        if command in STUNT_COMMANDS and not self.stunt_armed:
            self.get_logger().warning(f"stunt {command} blocked: stunt_armed=False")
            return
        self._send(command, force=force)

    def _debug_event(self, text):
        if not self.debug_events:
            return
        now = time.monotonic()
        if now - self._last_debug_event_time < self.debug_event_period:
            return
        self._last_debug_event_time = now
        self.get_logger().info(f"debug event: {text}")

    def _log_ack(self, command, ack):
        if not self.ack_log_csv:
            return
        directory = os.path.dirname(self.ack_log_csv)
        if directory:
            os.makedirs(directory, exist_ok=True)
        write_header = not self._ack_log_header_written and not os.path.exists(self.ack_log_csv)
        with open(self.ack_log_csv, "a", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow([
                    "pc_send_ns",
                    "pc_ack_ns",
                    "ack_latency_ms",
                    "command_sent",
                    "ack_kind",
                    "esp_ms",
                    "rc",
                    "ack_command",
                    "raw_ack",
                    "hello",
                ])
            writer.writerow([
                ack.get("pc_send_ns"),
                ack.get("pc_ack_ns"),
                f"{ack.get('ack_latency_ms'):.6f}",
                command,
                ack.get("ack_kind"),
                ack.get("esp_ms"),
                ack.get("rc"),
                ack.get("ack_command"),
                ack.get("raw_ack"),
                ack.get("hello"),
            ])
        self._ack_log_header_written = True


def main():
    rclpy.init()
    node = VisionBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv.destroyAllWindows()
        node.transport.close()
        node.destroy_node()
        rclpy.shutdown()
