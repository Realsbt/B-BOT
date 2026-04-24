#!/usr/bin/env python3
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "appendices" / "E_data"
FIGS = ROOT / "figures" / "provisional"
FIGS.mkdir(parents=True, exist_ok=True)


def rows(path):
    with path.open(newline="") as handle:
        filtered = (line for line in handle if not line.startswith("#"))
        return list(csv.DictReader(filtered))


def mean(values):
    values = [float(v) for v in values if v not in ("", "NA")]
    return sum(values) / len(values)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIGS / name, dpi=180)
    plt.close(fig)


def plot_e2():
    data = rows(DATA / "E2_disturbance_recovery" / "provisional_trials_2026-04-24.csv")
    groups = defaultdict(list)
    for row in data:
        if row["success"] == "1":
            groups[row["direction"]].append(row["settling_time_s"])

    labels = ["forward", "backward"]
    values = [mean(groups[label]) for label in labels]
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    ax.bar(labels, values, color=["#4C78A8", "#F58518"])
    ax.set_ylabel("Settling time (s)")
    ax.set_title("E2 disturbance recovery (PROVISIONAL)")
    ax.set_ylim(0, 1.2)
    save(fig, "e2_disturbance_recovery_provisional.png")


def plot_e3():
    data = rows(DATA / "E3_leg_length_sensitivity" / "provisional_trials_2026-04-24.csv")
    groups = defaultdict(list)
    peaks = defaultdict(list)
    lengths = {}
    for row in data:
        if row["success"] == "1":
            groups[row["leg_setting"]].append(row["settling_time_s"])
            peaks[row["leg_setting"]].append(row["peak_pitch_deg"])
        lengths[row["leg_setting"]] = float(row["leg_length_m"])

    labels = ["short", "nominal", "tall"]
    x = [lengths[label] for label in labels]
    settle = [mean(groups[label]) for label in labels]
    peak = [mean(peaks[label]) for label in labels]
    fig, ax1 = plt.subplots(figsize=(5.8, 3.4))
    ax1.plot(x, settle, marker="o", color="#4C78A8", label="Settling time")
    ax1.set_xlabel("Leg length (m)")
    ax1.set_ylabel("Settling time (s)", color="#4C78A8")
    ax2 = ax1.twinx()
    ax2.plot(x, peak, marker="s", color="#E45756", label="Peak pitch")
    ax2.set_ylabel("Peak pitch (deg)", color="#E45756")
    ax1.set_title("E3 leg-length sensitivity (PROVISIONAL)")
    save(fig, "e3_leg_length_sensitivity_provisional.png")


def plot_e9():
    data = rows(DATA / "E9_controller_ablation" / "provisional_trials_2026-04-24.csv")
    groups = defaultdict(list)
    for row in data:
        if row["success"] == "1" and row["response_time_s"] != "NA":
            groups[row["mode"]].append(row["response_time_s"])

    labels = ["FULL", "FIXED_LQR", "NO_RAMP"]
    values = [mean(groups[label]) for label in labels]
    fig, ax = plt.subplots(figsize=(5.8, 3.2))
    ax.bar(labels, values, color=["#54A24B", "#B279A2", "#F58518"])
    ax.set_ylabel("Response time (s)")
    ax.set_title("E9 controller ablation (PROVISIONAL)")
    save(fig, "e9_controller_ablation_provisional.png")


def plot_e6():
    data = rows(DATA / "E6_watchdog_fault_injection" / "provisional_trials_2026-04-24.csv")
    groups = defaultdict(list)
    for row in data:
        groups[row["fault_case"]].append(row["stop_latency_ms"])

    labels = ["stop_sending", "tcp_close", "tcp_idle"]
    values = [mean(groups[label]) for label in labels]
    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    ax.bar(labels, values, color=["#4C78A8", "#72B7B2", "#E45756"])
    ax.set_ylabel("Stop latency (ms)")
    ax.set_title("E6 watchdog / fault injection (PROVISIONAL)")
    save(fig, "e6_watchdog_fault_injection_provisional.png")


def plot_e8():
    data = rows(DATA / "E8_control_loop_jitter" / "provisional_loop_jitter_metrics_2026-04-24.csv")
    metrics = {row["metric"]: float(row["value"]) for row in data if row["unit"] == "ms"}
    labels = ["mean_period", "p95", "p99", "p99_9", "max"]
    values = [metrics[label] for label in labels]
    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    ax.plot(labels, values, marker="o", color="#4C78A8")
    ax.axhline(4.0, color="#54A24B", linestyle="--", linewidth=1.0, label="4 ms target")
    ax.set_ylabel("Loop period (ms)")
    ax.set_title("E8 control-loop timing (PROVISIONAL)")
    ax.legend()
    save(fig, "e8_control_loop_jitter_provisional.png")


def main():
    plot_e2()
    plot_e3()
    plot_e6()
    plot_e8()
    plot_e9()
    print(f"wrote provisional plots to {FIGS}")


if __name__ == "__main__":
    main()
