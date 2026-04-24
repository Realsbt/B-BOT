#!/usr/bin/env python3
import argparse
import pathlib
import sys
import time

import cv2 as cv
import numpy as np
import rclpy
from sensor_msgs.msg import CompressedImage


def parse_args():
    parser = argparse.ArgumentParser(description="Capture one frame from a ROS2 CompressedImage topic.")
    parser.add_argument("topic", nargs="?", default="/espRos/esp32camera")
    parser.add_argument("out_path", nargs="?", default="frame.jpg")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--preview", action="store_true", help="Show frames and save when 's' is pressed.")
    parser.add_argument("--scale", type=float, default=2.0)
    return parser.parse_args()


def draw_overlay(frame, topic):
    h, w = frame.shape[:2]
    cv.line(frame, (w // 2, 0), (w // 2, h), (0, 255, 255), 1)
    cv.line(frame, (0, h // 2), (w, h // 2), (0, 255, 255), 1)
    cv.rectangle(frame, (int(w * 0.18), int(h * 0.14)), (int(w * 0.82), int(h * 0.86)), (0, 255, 0), 1)
    lines = [f"topic: {topic}", "s: save frame   q/esc: quit"]
    y = 22
    for line in lines:
        cv.putText(frame, line, (10, y), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv.LINE_AA)
        cv.putText(frame, line, (10, y), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv.LINE_AA)
        y += 20


def main():
    args = parse_args()
    topic = args.topic
    out_path = pathlib.Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rclpy.init()
    node = rclpy.create_node("capture_compressed_image_once")
    state = {"done": False, "last_msg": None, "last_frame": None}

    def callback(msg):
        if not args.preview:
            out_path.write_bytes(bytes(msg.data))
            print(f"saved={out_path} format={msg.format} bytes={len(msg.data)}")
            state["done"] = True
            return
        data = np.frombuffer(msg.data, dtype=np.uint8)
        frame = cv.imdecode(data, cv.IMREAD_COLOR)
        if frame is not None:
            state["last_msg"] = msg
            state["last_frame"] = frame

    node.create_subscription(CompressedImage, topic, callback, 1)
    deadline = time.monotonic() + args.timeout
    while rclpy.ok() and not state["done"] and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        if args.preview and state["last_frame"] is not None:
            frame = state["last_frame"].copy()
            if args.scale != 1.0:
                frame = cv.resize(frame, None, fx=args.scale, fy=args.scale, interpolation=cv.INTER_LINEAR)
            draw_overlay(frame, topic)
            cv.imshow("B-BOT frame capture", frame)
            key = cv.waitKey(1) & 0xFF
            if key == ord("s") and state["last_msg"] is not None:
                msg = state["last_msg"]
                out_path.write_bytes(bytes(msg.data))
                print(f"saved={out_path} format={msg.format} bytes={len(msg.data)}")
                state["done"] = True
            elif key in (27, ord("q")):
                break

    cv.destroyAllWindows()
    node.destroy_node()
    rclpy.shutdown()
    if not state["done"]:
        print(f"timeout waiting for {topic}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
