import time

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
        self.declare_parameter("debug_events", False)
        self.declare_parameter("debug_event_rate_hz", 2.0)
        self.declare_parameter("stunt_armed", False)

        self.mode = self.get_parameter("mode").value
        self.image_type = self.get_parameter("image_type").value
        self.frame_skip = max(1, int(self.get_parameter("frame_skip").value))
        self.debug_window = bool(self.get_parameter("debug_window").value)
        self.debug_events = bool(self.get_parameter("debug_events").value)
        self.debug_event_period = 1.0 / max(0.1, float(self.get_parameter("debug_event_rate_hz").value))
        self.dry_run = bool(self.get_parameter("dry_run").value)
        self.stunt_armed = bool(self.get_parameter("stunt_armed").value)
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
        self._last_face_command = "YAWRATE,0"
        self._current_gesture_drive = "DRIVE,0,0"
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
            return

        frame = self._decode_frame(msg)
        event = self.runner.process(frame, self.mode)

        if self.mode == "gesture":
            label = event.get("label") if event else None
            stable = self.debouncer.update(label)
            self._debug_event(f"gesture label={label} stable={stable}")
            command = self.encoder.encode_gesture(stable) if stable else None
            if label is None:
                # hand lost this frame → stop continuous teleop immediately
                self._current_gesture_drive = "DRIVE,0,0"
            elif command and command.startswith("DRIVE,"):
                self._current_gesture_drive = command
            elif command:
                # impulse command (e.g. JUMP): send once on the stabilising edge
                self._send(command, force=True)
        elif self.mode == "stunt":
            self._debug_event(f"stunt event={event}")
            command = self.encoder.encode_stunt(event)
            if command:
                if command in ("JUMP", "CROSSLEG,0,5") and not self.stunt_armed:
                    self._debug_event(f"stunt {command} blocked: stunt_armed=False")
                else:
                    self._send(command)
        elif self.mode == "face":
            self._last_face_command = self.encoder.encode_face(event)
            self._debug_event(f"face event={event} command={self._last_face_command}")

        if self.debug_window:
            cv.imshow("wheeleg_vision_bridge", frame)
            cv.waitKey(1)

    def _decode_frame(self, msg):
        if self.image_type == "compressed":
            return self.bridge.compressed_imgmsg_to_cv2(msg)
        return self.bridge.imgmsg_to_cv2(msg, "bgr8")

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
            self.transport.write_line(command)
            self.get_logger().info(f"sent: {command}")
        except (OSError, TransportError) as exc:
            self.get_logger().warning(f"transport write failed: {exc}")

    def _debug_event(self, text):
        if not self.debug_events:
            return
        now = time.monotonic()
        if now - self._last_debug_event_time < self.debug_event_period:
            return
        self._last_debug_event_time = now
        self.get_logger().info(f"debug event: {text}")


def main():
    rclpy.init()
    node = VisionBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.transport.close()
        node.destroy_node()
        rclpy.shutdown()
