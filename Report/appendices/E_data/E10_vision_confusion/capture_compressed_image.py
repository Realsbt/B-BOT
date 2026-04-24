#!/usr/bin/env python3
import pathlib
import sys
import time

import rclpy
from sensor_msgs.msg import CompressedImage


def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "/espRos/esp32camera"
    out_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("frame.jpg")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rclpy.init()
    node = rclpy.create_node("capture_compressed_image_once")
    saved = {"done": False}

    def callback(msg):
        out_path.write_bytes(bytes(msg.data))
        print(f"saved={out_path} format={msg.format} bytes={len(msg.data)}")
        saved["done"] = True

    node.create_subscription(CompressedImage, topic, callback, 1)
    deadline = time.monotonic() + 10.0
    while rclpy.ok() and not saved["done"] and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)

    node.destroy_node()
    rclpy.shutdown()
    if not saved["done"]:
        print(f"timeout waiting for {topic}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
