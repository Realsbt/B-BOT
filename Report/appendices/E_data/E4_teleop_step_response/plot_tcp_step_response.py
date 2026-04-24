#!/usr/bin/env python3
from pathlib import Path
import csv

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "appendices" / "E_data" / "E4_teleop_step_response" / "tcp_step_response_summary_2026-04-24.csv"
OUT = ROOT / "figures" / "e4_tcp_step_response_2026-04-24.png"


def main() -> int:
    with DATA.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    labels = [row["step_command"].replace("DRIVE,", "").replace(",", ", ") for row in rows]
    step_median = [float(row["step_ack_median_ms"]) for row in rows]
    step_p95 = [float(row["step_ack_p95_ms"]) for row in rows]
    stop_median = [float(row["stop_ack_median_ms"]) for row in rows]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = range(len(rows))
    ax.bar(x, step_median, label="Step ACK median", color="#3274a1")
    ax.errorbar(
        x,
        step_median,
        yerr=[p95 - median for p95, median in zip(step_p95, step_median)],
        fmt="none",
        ecolor="#143a52",
        capsize=5,
        label="Step ACK p95",
    )
    ax.scatter(x, stop_median, marker="D", color="#c45a30", label="Stop ACK median")
    ax.set_xticks(list(x), labels)
    ax.set_ylabel("ACK latency (ms)")
    ax.set_xlabel("Teleop step command payload")
    ax.set_title("E4a TCP teleop command-entry step response")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=180)
    print(OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
