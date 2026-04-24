#!/usr/bin/env python3
import argparse
import os
import time
from datetime import datetime

import cv2 as cv
import numpy as np
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage

try:
    from wheeleg_vision_bridge.mediapipe_runner import MediaPipeRunner
except ImportError:
    MediaPipeRunner = None


LABEL_TEXT = {
    "None": "No hand",
    "Zero": "Fist / Stop",
    "Five": "Open Palm / Forward",
    "PointLeft": "Point Left / Turn",
    "PointRight": "Point Right / Turn",
    "Thumb_up": "Thumb Up / Jump",
}

COMMAND_TEXT = {
    "None": "Robot command: DRIVE,0,0",
    "Zero": "Robot command: DRIVE,0,0",
    "Five": "Robot command: DRIVE,250,0",
    "PointLeft": "Robot command: DRIVE,0,600",
    "PointRight": "Robot command: DRIVE,0,-600",
    "Thumb_up": "Robot command: JUMP (safety gated)",
}


class CameraPreview(Node):
    def __init__(self, args):
        super().__init__("wheeleg_camera_preview")
        self.args = args
        if self.args.presentation:
            self.args.labels = True
        self.runner = MediaPipeRunner(args.mediapipe_confidence) if args.labels and MediaPipeRunner else None
        self.last_frame = None
        self.last_label = "None" if self.runner else "disabled"
        self.last_msg_time = None
        self.frame_count = 0
        self.fps_start = time.monotonic()
        self.fps = 0.0
        self.window_name = args.window_name
        self._window_configured = False
        self.create_subscription(CompressedImage, args.topic, self._image_cb, 1)
        self.create_timer(0.03, self._display_cb)

    def _image_cb(self, msg):
        data = np.frombuffer(msg.data, dtype=np.uint8)
        frame = cv.imdecode(data, cv.IMREAD_COLOR)
        if frame is None:
            return
        self.last_msg_time = time.monotonic()
        self.frame_count += 1
        elapsed = self.last_msg_time - self.fps_start
        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.fps_start = self.last_msg_time
        if self.runner:
            event = self.runner.process(frame, "gesture")
            label = event.get("label") if event else None
            self.last_label = label if label else "None"
        self.last_frame = frame

    def _display_cb(self):
        if self.last_frame is None:
            return
        frame = self.last_frame.copy()
        if self.args.mirror:
            frame = cv.flip(frame, 1)
        if self.args.scale != 1.0:
            frame = cv.resize(frame, None, fx=self.args.scale, fy=self.args.scale, interpolation=cv.INTER_LINEAR)
        if self.args.presentation:
            self._draw_presentation_overlay(frame)
        else:
            self._draw_overlay(frame)
        self._configure_window()
        cv.imshow(self.window_name, frame)
        key = cv.waitKey(1) & 0xFF
        if key in (27, ord("q")):
            raise KeyboardInterrupt
        if key == ord("s"):
            self._save_frame(frame)

    def _draw_overlay(self, frame):
        h, w = frame.shape[:2]
        if not self.args.hide_guides:
            cv.line(frame, (w // 2, 0), (w // 2, h), (0, 255, 255), 1)
            cv.line(frame, (0, h // 2), (w, h // 2), (0, 255, 255), 1)
            margin_x = int(w * 0.18)
            margin_y = int(h * 0.14)
            cv.rectangle(frame, (margin_x, margin_y), (w - margin_x, h - margin_y), (0, 255, 0), 1)
        age = "no frames"
        if self.last_msg_time is not None:
            age = f"age: {time.monotonic() - self.last_msg_time:.2f}s"
        lines = [
            f"topic: {self.args.topic}",
            f"fps: {self.fps:.2f}  {age}",
            f"label: {self.last_label}",
            "q/esc: quit   s: save frame",
        ]
        y = 22
        for line in lines:
            cv.putText(frame, line, (10, y), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv.LINE_AA)
            cv.putText(frame, line, (10, y), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
            y += 20

    def _draw_presentation_overlay(self, frame):
        h, w = frame.shape[:2]
        label = self.last_label if self.last_label != "disabled" else "None"
        label_text = LABEL_TEXT.get(label, label)
        command_text = COMMAND_TEXT.get(label, "Robot command: waiting for gesture")

        if not self.args.hide_guides:
            margin_x = int(w * 0.16)
            margin_y = int(h * 0.12)
            cv.rectangle(frame, (margin_x, margin_y), (w - margin_x, h - margin_y), (0, 220, 0), 2)

        self._draw_panel(frame, 0, 0, w, 86, alpha=0.58)
        self._draw_panel(frame, 0, h - 136, w, 136, alpha=0.62)
        cv.putText(frame, self.args.title, (28, 54), cv.FONT_HERSHEY_SIMPLEX, 1.35, (0, 0, 0), 5, cv.LINE_AA)
        cv.putText(frame, self.args.title, (28, 54), cv.FONT_HERSHEY_SIMPLEX, 1.35, (255, 255, 255), 2, cv.LINE_AA)
        cv.putText(frame, label_text, (28, h - 78), cv.FONT_HERSHEY_SIMPLEX, 1.45, (0, 0, 0), 5, cv.LINE_AA)
        cv.putText(frame, label_text, (28, h - 78), cv.FONT_HERSHEY_SIMPLEX, 1.45, (255, 255, 255), 2, cv.LINE_AA)
        cv.putText(frame, command_text, (30, h - 30), cv.FONT_HERSHEY_SIMPLEX, 0.78, (0, 0, 0), 4, cv.LINE_AA)
        cv.putText(frame, command_text, (30, h - 30), cv.FONT_HERSHEY_SIMPLEX, 0.78, (235, 255, 235), 2, cv.LINE_AA)
        cv.putText(frame, f"{self.fps:.1f} FPS", (w - 130, 34), cv.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 3, cv.LINE_AA)
        cv.putText(frame, f"{self.fps:.1f} FPS", (w - 130, 34), cv.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 1, cv.LINE_AA)

    def _draw_panel(self, frame, x, y, w, h, alpha):
        overlay = frame.copy()
        cv.rectangle(overlay, (x, y), (x + w, y + h), (20, 24, 28), -1)
        cv.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)

    def _configure_window(self):
        if self._window_configured:
            return
        cv.namedWindow(self.window_name, cv.WINDOW_NORMAL)
        if self.args.fullscreen:
            cv.setWindowProperty(self.window_name, cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
        self._window_configured = True

    def _save_frame(self, frame):
        os.makedirs(self.args.save_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.args.save_dir, f"preview_{stamp}.jpg")
        cv.imwrite(path, frame)
        self.get_logger().info(f"saved {path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Preview the ESP32 camera ROS2 compressed image topic.")
    parser.add_argument("--topic", default="/espRos/esp32camera")
    parser.add_argument("--window-name", default="B-BOT camera preview")
    parser.add_argument("--scale", type=float, default=2.0)
    parser.add_argument("--labels", action="store_true", help="Overlay MediaPipe gesture labels.")
    parser.add_argument("--presentation", action="store_true", help="Use large, presentation-friendly overlay.")
    parser.add_argument("--fullscreen", action="store_true")
    parser.add_argument("--mirror", action="store_true", help="Mirror preview like a selfie camera.")
    parser.add_argument("--hide-guides", action="store_true")
    parser.add_argument("--title", default="B-BOT Vision Teleoperation")
    parser.add_argument("--mediapipe-confidence", type=float, default=0.6)
    parser.add_argument("--save-dir", default="Report/appendices/E_data/E10_vision_confusion/preview_frames")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.presentation:
        args.window_name = "B-BOT presentation monitor"
    if args.labels and MediaPipeRunner is None:
        raise RuntimeError("wheeleg_vision_bridge is not on PYTHONPATH; source host/ros2_ws/install/setup.bash")
    rclpy.init()
    node = CameraPreview(args)
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.05)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        cv.destroyAllWindows()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
