#!/usr/bin/env python3
"""Plot E11 vision bridge to ESP32 ACK latency CDF."""

from __future__ import annotations

import argparse
import csv
import os

import matplotlib.pyplot as plt


def read_latencies(path: str, command_filter: str | None = None) -> list[float]:
    values: list[float] = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if command_filter and row["command_sent"] != command_filter:
                continue
            values.append(float(row["ack_latency_ms"]))
    return sorted(values)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="Report/appendices/E_data/E11_vision_to_esp32_latency/vision_bridge_ack_latency_2026-04-24.csv")
    parser.add_argument("--output", default="Report/figures/e11_vision_bridge_ack_latency_2026-04-24.png")
    args = parser.parse_args()

    all_lat = read_latencies(args.input)
    drive_lat = read_latencies(args.input, "DRIVE,0,0")

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    for label, values, color in [
        ("all bridge commands", all_lat, "#4b7bec"),
        ("DRIVE,0,0 only", drive_lat, "#20bf6b"),
    ]:
        if not values:
            continue
        y = [(i + 1) / len(values) for i in range(len(values))]
        ax.step(values, y, where="post", label=f"{label} (n={len(values)})", color=color, linewidth=1.7)

    ax.axvline(4.0, color="#eb3b5a", linestyle="--", linewidth=1.0, label="4 ms control period")
    ax.set_xlabel("Bridge send to ESP32 ACK latency (ms)")
    ax.set_ylabel("CDF")
    ax.set_ylim(0.0, 1.02)
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(loc="lower right", frameon=False)
    ax.set_title("E11 Vision Bridge to ESP32 ACK Latency")
    fig.tight_layout()
    fig.savefig(args.output, dpi=180)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
