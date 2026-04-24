#!/usr/bin/env python3
import argparse
import csv
import os
import time
from collections import Counter
from datetime import datetime, timezone

import cv2 as cv
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage

from wheeleg_vision_bridge.command_encoder import CommandEncoder
from wheeleg_vision_bridge.debouncer import Debouncer
from wheeleg_vision_bridge.mediapipe_runner import MediaPipeRunner


EXPECTED_COMMANDS = {
    "NoHand": "DRIVE,0,0",
    "Zero": "DRIVE,0,0",
    "Five": "DRIVE,250,0",
    "PointLeft": "DRIVE,0,600",
    "PointRight": "DRIVE,0,-600",
    "Thumb_up": "JUMP",
}


class GestureTrialCollector(Node):
    def __init__(self, args):
        super().__init__("e10_gesture_trial_collector")
        self.args = args
        self.runner = MediaPipeRunner(args.mediapipe_confidence)
        self.debouncer = Debouncer(args.debounce_frames)
        self.encoder = CommandEncoder(face_gain_mrad=1500, face_deadband=0.1)
        self.frames = []
        self.stable_events = []
        self.first_matching_label_s = None
        self.first_stable_label_s = None
        self.start_monotonic = None
        self.stop_requested = False
        self.sample_saved = False
        self.preview_frame_count = 0
        self.preview_fps_start = time.monotonic()
        self.preview_fps = 0.0

        self.create_subscription(CompressedImage, args.image_topic, self._image_cb, 1)
        self.timer = self.create_timer(0.1, self._timer_cb)

    def _decode_compressed(self, msg):
        data = np.frombuffer(msg.data, dtype=np.uint8)
        return cv.imdecode(data, cv.IMREAD_COLOR)

    def _image_cb(self, msg):
        now = time.monotonic()
        if self.start_monotonic is None:
            return
        elapsed = now - self.start_monotonic
        if elapsed < 0 or elapsed > self.args.duration:
            return

        frame = self._decode_compressed(msg)
        if frame is None:
            return

        event = self.runner.process(frame, "gesture")
        label = event.get("label") if event else None
        stable = self.debouncer.update(label)
        command = self.encoder.encode_gesture(stable) if stable else ""

        label_text = label if label is not None else "None"
        stable_text = stable if stable is not None else ""
        if self._label_matches(label_text) and self.first_matching_label_s is None:
            self.first_matching_label_s = elapsed
        if stable:
            self.stable_events.append((elapsed, stable, command))
            if self.first_stable_label_s is None:
                self.first_stable_label_s = elapsed

        self.frames.append({
            "trial_id": self.args.trial_id,
            "actual_gesture": self.args.actual_gesture,
            "t_rel_s": f"{elapsed:.6f}",
            "label": label_text,
            "stable_label": stable_text,
            "command": command,
        })

        if self.args.save_sample and not self.sample_saved and elapsed >= self.args.duration * 0.5:
            os.makedirs(self.args.output_dir, exist_ok=True)
            sample_path = os.path.join(
                self.args.output_dir,
                f"{self.args.trial_id}_{self.args.actual_gesture}_sample.jpg",
            )
            cv.imwrite(sample_path, frame)
            self.sample_saved = True
        if self.args.preview:
            self._show_preview(frame, elapsed, label_text, stable_text, command)

    def _show_preview(self, frame, elapsed, label_text, stable_text, command):
        self.preview_frame_count += 1
        now = time.monotonic()
        fps_elapsed = now - self.preview_fps_start
        if fps_elapsed >= 1.0:
            self.preview_fps = self.preview_frame_count / fps_elapsed
            self.preview_frame_count = 0
            self.preview_fps_start = now

        display = frame.copy()
        if self.args.preview_scale != 1.0:
            display = cv.resize(
                display,
                None,
                fx=self.args.preview_scale,
                fy=self.args.preview_scale,
                interpolation=cv.INTER_LINEAR,
            )
        h, w = display.shape[:2]
        cv.line(display, (w // 2, 0), (w // 2, h), (0, 255, 255), 1)
        cv.line(display, (0, h // 2), (w, h // 2), (0, 255, 255), 1)
        margin_x = int(w * 0.18)
        margin_y = int(h * 0.14)
        cv.rectangle(display, (margin_x, margin_y), (w - margin_x, h - margin_y), (0, 255, 0), 1)
        lines = [
            f"trial: {self.args.trial_id}  actual: {self.args.actual_gesture}",
            f"elapsed: {elapsed:.1f}/{self.args.duration:.1f}s  fps: {self.preview_fps:.2f}",
            f"label: {label_text}  stable: {stable_text}",
            f"command: {command}",
            "q/esc: stop trial",
        ]
        y = 22
        for line in lines:
            cv.putText(display, line, (10, y), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv.LINE_AA)
            cv.putText(display, line, (10, y), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
            y += 20
        cv.imshow(self.args.window_name, display)
        key = cv.waitKey(1) & 0xFF
        if key in (27, ord("q")):
            self.stop_requested = True

    def _label_matches(self, label_text):
        if self.args.actual_gesture == "NoHand":
            return label_text == "None"
        return label_text == self.args.actual_gesture

    def _timer_cb(self):
        if self.start_monotonic is None:
            self.start_monotonic = time.monotonic() + self.args.warmup
            self.get_logger().info(
                f"trial={self.args.trial_id} actual={self.args.actual_gesture} "
                f"warmup={self.args.warmup:.1f}s duration={self.args.duration:.1f}s"
            )
            return
        if time.monotonic() - self.start_monotonic > self.args.duration + 0.2:
            self.stop_requested = True

    def build_summary(self):
        labels = [row["label"] for row in self.frames]
        stable_labels = [label for _, label, _ in self.stable_events]
        commands = [command for _, _, command in self.stable_events if command]
        label_counts = Counter(labels)
        stable_counts = Counter(stable_labels)
        command_counts = Counter(commands)
        frame_count = len(self.frames)
        expected_label = "None" if self.args.actual_gesture == "NoHand" else self.args.actual_gesture
        expected_command = EXPECTED_COMMANDS[self.args.actual_gesture]
        correct_frames = sum(1 for label in labels if label == expected_label)
        correct_ratio = correct_frames / frame_count if frame_count else 0.0
        mode_label, mode_count = ("None", 0)
        if label_counts:
            mode_label, mode_count = label_counts.most_common(1)[0]
        mode_ratio = mode_count / frame_count if frame_count else 0.0
        first_stable_label = stable_labels[0] if stable_labels else ""
        first_command = commands[0] if commands else ""

        wrong_commands = [command for command in commands if command != expected_command]
        if self.args.actual_gesture == "NoHand":
            result = "pass_safety" if not wrong_commands and correct_ratio >= 0.8 else "fail_false_positive"
        elif expected_label in stable_counts and not wrong_commands:
            result = "pass"
        elif expected_label in stable_counts and wrong_commands:
            result = "mixed_false_command"
        elif correct_ratio >= 0.4:
            result = "partial_fail"
        else:
            result = "fail"

        return {
            "trial_id": self.args.trial_id,
            "actual_gesture": self.args.actual_gesture,
            "expected_label": expected_label,
            "expected_command": expected_command,
            "start_utc": datetime.now(timezone.utc).isoformat(),
            "duration_s": f"{self.args.duration:.3f}",
            "frames": frame_count,
            "mode_label": mode_label,
            "mode_label_ratio": f"{mode_ratio:.6f}",
            "correct_label_frames": correct_frames,
            "correct_label_ratio": f"{correct_ratio:.6f}",
            "stable_label_counts": dict(stable_counts),
            "command_counts": dict(command_counts),
            "first_matching_label_s": _fmt_time(self.first_matching_label_s),
            "first_stable_label_s": _fmt_time(self.first_stable_label_s),
            "observed_stable_label": first_stable_label,
            "observed_command": first_command,
            "result": result,
            "notes": self.args.notes,
        }


def _fmt_time(value):
    return "NA" if value is None else f"{value:.6f}"


def _append_csv(path, row, fieldnames):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_header = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def _append_frame_csv(path, rows):
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_header = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def parse_args():
    parser = argparse.ArgumentParser(description="Collect one E10 gesture confusion trial.")
    parser.add_argument("--actual-gesture", required=True, choices=sorted(EXPECTED_COMMANDS))
    parser.add_argument("--trial-id", required=True)
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--warmup", type=float, default=5.0)
    parser.add_argument("--image-topic", default="/espRos/esp32camera")
    parser.add_argument("--debounce-frames", type=int, default=3)
    parser.add_argument("--mediapipe-confidence", type=float, default=0.6)
    parser.add_argument("--output-dir", default="Report/appendices/E_data/E10_vision_confusion")
    parser.add_argument("--summary-csv", default="confusion_trials_live_2026-04-24.csv")
    parser.add_argument("--frames-csv", default="confusion_frames_live_2026-04-24.csv")
    parser.add_argument("--notes", default="")
    parser.add_argument("--save-sample", action="store_true")
    parser.add_argument("--preview", action="store_true", help="Show a live monitor window during the trial.")
    parser.add_argument("--preview-scale", type=float, default=2.0)
    parser.add_argument("--window-name", default="E10 gesture collection")
    return parser.parse_args()


def main():
    args = parse_args()
    rclpy.init()
    node = GestureTrialCollector(args)
    try:
        while rclpy.ok() and not node.stop_requested:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        summary = node.build_summary()
        summary_path = os.path.join(args.output_dir, args.summary_csv)
        frames_path = os.path.join(args.output_dir, args.frames_csv)
        _append_csv(summary_path, summary, list(summary.keys()))
        _append_frame_csv(frames_path, node.frames)
        node.get_logger().info(f"summary={summary}")
        node.get_logger().info(f"wrote {summary_path}")
        node.get_logger().info(f"wrote {frames_path}")
        if args.preview:
            cv.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
