#!/usr/bin/env python3
"""Plot E8 loop timing histogram and cumulative distribution."""

from __future__ import annotations

import argparse
import csv
import os

import matplotlib.pyplot as plt


def read_summary(path: str) -> dict[str, float]:
    values: dict[str, float] = {}
    with open(path, newline="") as f:
        rows = (line for line in f if not line.startswith("#"))
        for row in csv.DictReader(rows):
            values[row["metric"]] = float(row["value"])
    return values


def read_histogram(path: str) -> tuple[list[float], list[int]]:
    starts: list[float] = []
    counts: list[int] = []
    with open(path, newline="") as f:
        rows = (line for line in f if not line.startswith("#"))
        for row in csv.DictReader(rows):
            starts.append(float(row["bin_start_us"]))
            counts.append(int(row["count"]))
    return starts, counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default="Report/appendices/E_data/E8_control_loop_jitter/looplog_stats_15000_summary_2026-04-24.csv")
    parser.add_argument("--histogram", default="Report/appendices/E_data/E8_control_loop_jitter/looplog_stats_15000_histogram_2026-04-24.csv")
    parser.add_argument("--output", default="Report/figures/e8_loop_jitter_15000_2026-04-24.png")
    args = parser.parse_args()

    summary = read_summary(args.summary)
    starts_us, counts = read_histogram(args.histogram)
    total = sum(counts)
    cumulative: list[float] = []
    running = 0
    for count in counts:
        running += count
        cumulative.append(running / total if total else 0.0)

    starts_ms = [value / 1000.0 for value in starts_us]
    width_ms = ((starts_us[1] - starts_us[0]) / 1000.0) if len(starts_us) > 1 else 0.1

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    fig, (ax_hist, ax_cdf) = plt.subplots(2, 1, figsize=(8.0, 6.0), sharex=True)
    ax_hist.bar(starts_ms, counts, width=width_ms, align="edge", color="#4b7bec", edgecolor="#1f3f99", linewidth=0.4)
    ax_hist.axvline(4.0, color="#2f3542", linestyle="--", linewidth=1.0, label="4 ms target")
    ax_hist.set_ylabel("Count")
    ax_hist.legend(loc="upper right", frameon=False)
    ax_hist.set_title("E8 CtrlBasic_Task Loop Period Distribution (n=15000)")

    ax_cdf.step(starts_ms, cumulative, where="post", color="#20bf6b", linewidth=1.6)
    ax_cdf.axvline(4.0, color="#2f3542", linestyle="--", linewidth=1.0)
    ax_cdf.set_xlabel("Loop period (ms)")
    ax_cdf.set_ylabel("CDF")
    ax_cdf.set_ylim(0.0, 1.02)
    ax_cdf.grid(True, axis="y", alpha=0.25)

    text = (
        f"mean={summary['mean_us'] / 1000:.3f} ms\n"
        f"p95={summary['p95_us'] / 1000:.2f} ms\n"
        f"p99={summary['p99_us'] / 1000:.2f} ms\n"
        f"p99.9={summary['p99_9_us'] / 1000:.2f} ms\n"
        f"max={summary['max_us'] / 1000:.2f} ms"
    )
    ax_cdf.text(0.98, 0.05, text, transform=ax_cdf.transAxes, ha="right", va="bottom",
                bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#d1d8e0"})

    fig.tight_layout()
    fig.savefig(args.output, dpi=180)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
