#!/usr/bin/env python3
"""Generate clearly marked synthetic placeholder datasets for unmeasured tests.

These files are intentionally not measured data. They exist so report tables,
plots, and analysis text can be developed before the final hardware campaign.
Every generated CSV row contains:

- provisional=true
- source=synthetic_planning_placeholder_not_measured
"""

from __future__ import annotations

import csv
import math
import random
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


SEED = 42024
random.seed(SEED)

REPORT = Path(__file__).resolve().parents[2]
DATA = REPORT / "appendices" / "E_data"
FIGS = REPORT / "figures" / "provisional"
SOURCE = "synthetic_planning_placeholder_not_measured"


def ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    ensure(path.parent)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def rms(values: list[float]) -> float:
    return math.sqrt(sum(v * v for v in values) / len(values))


def lin_slope(xs: list[float], ys: list[float]) -> float:
    xbar = sum(xs) / len(xs)
    ybar = sum(ys) / len(ys)
    num = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    den = sum((x - xbar) ** 2 for x in xs)
    return num / den if den else 0.0


def fmt(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}"


def e1_static_balance() -> None:
    out = ensure(DATA / "E1_static_balance_drift")
    rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    specs = [
        ("e1_synth_01", 0.012, 0.010, 0.33, 0.27),
        ("e1_synth_02", 0.016, 0.012, 0.36, 0.31),
        ("e1_synth_03", 0.014, 0.011, 0.34, 0.29),
    ]
    dt = 0.1
    n = int(60 / dt) + 1
    for trial_id, pitch_drift, roll_drift, pitch_amp, roll_amp in specs:
        pitch_values: list[float] = []
        roll_values: list[float] = []
        ts: list[float] = []
        for i in range(n):
            t = i * dt
            pitch = (
                pitch_drift * (t - 30.0)
                + pitch_amp * 0.62 * math.sin(2 * math.pi * 0.72 * t)
                + pitch_amp * 0.22 * math.sin(2 * math.pi * 1.35 * t + 0.4)
                + random.gauss(0.0, pitch_amp * 0.12)
            )
            roll = (
                roll_drift * (t - 30.0)
                + roll_amp * 0.60 * math.sin(2 * math.pi * 0.61 * t + 0.7)
                + roll_amp * 0.18 * math.sin(2 * math.pi * 1.2 * t)
                + random.gauss(0.0, roll_amp * 0.12)
            )
            pitch_values.append(pitch)
            roll_values.append(roll)
            ts.append(t)
            rows.append({
                "trial_id": trial_id,
                "t_s": fmt(t, 3),
                "pitch_deg": fmt(pitch, 5),
                "roll_deg": fmt(roll, 5),
                "balance_enabled": 1,
                "protection_state": 0,
                "provisional": True,
                "source": SOURCE,
            })
        summaries.append({
            "trial_id": trial_id,
            "duration_s": 60,
            "pitch_rms_deg": fmt(rms(pitch_values), 4),
            "roll_rms_deg": fmt(rms(roll_values), 4),
            "pitch_peak_abs_deg": fmt(max(abs(v) for v in pitch_values), 4),
            "roll_peak_abs_deg": fmt(max(abs(v) for v in roll_values), 4),
            "pitch_peak_to_peak_deg": fmt(max(pitch_values) - min(pitch_values), 4),
            "roll_peak_to_peak_deg": fmt(max(roll_values) - min(roll_values), 4),
            "pitch_drift_deg_s": fmt(lin_slope(ts, pitch_values), 5),
            "roll_drift_deg_s": fmt(lin_slope(ts, roll_values), 5),
            "protection_triggered": 0,
            "provisional": True,
            "source": SOURCE,
        })
    write_csv(out / "synthetic_static_timeseries_2026-04-24.csv", rows)
    write_csv(out / "synthetic_static_summary_2026-04-24.csv", summaries)

    trial1 = [r for r in rows if r["trial_id"] == "e1_synth_01"]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.plot([float(r["t_s"]) for r in trial1], [float(r["pitch_deg"]) for r in trial1], label="pitch")
    ax.plot([float(r["t_s"]) for r in trial1], [float(r["roll_deg"]) for r in trial1], label="roll")
    ax.set_title("E1 static balance drift (PROVISIONAL synthetic)")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Angle (deg)")
    ax.grid(alpha=0.25)
    ax.legend()
    save(fig, "e1_static_balance_drift_provisional.png")


def recovery_curve(t: float, sign: float, peak: float, settle: float) -> float:
    if t < 0:
        return random.gauss(0.0, 0.12)
    decay = math.exp(-t / max(0.25, settle * 0.55))
    return sign * peak * decay * math.cos(2.8 * t) + random.gauss(0.0, 0.12)


def e2_disturbance() -> None:
    out = ensure(DATA / "E2_disturbance_recovery")
    timeseries: list[dict[str, object]] = []
    summary: list[dict[str, object]] = []
    dt = 0.02
    times = [round(-0.2 + i * dt, 3) for i in range(int(3.2 / dt) + 1)]
    specs = []
    for direction, sign, base_settle, base_peak, failures in [
        ("forward", 1.0, 0.86, 8.4, {10}),
        ("backward", -1.0, 0.79, 7.6, set()),
    ]:
        for idx in range(1, 11):
            fail = idx in failures
            settle = base_settle + random.gauss(0, 0.07) + (0.45 if fail else 0.0)
            peak = base_peak + random.gauss(0, 0.7) + (3.2 if fail else 0.0)
            specs.append((f"e2_{direction}_{idx:02d}", direction, sign, max(settle, 0.45), max(peak, 4.0), fail))

    for trial_id, direction, sign, settle, peak, fail in specs:
        max_wheel = 10.0 + peak * 1.02 + random.gauss(0, 0.7)
        for t in times:
            pitch = recovery_curve(t, sign, peak, settle)
            wheel = sign * max_wheel * math.exp(-max(t, 0) / 0.75) * (1 if t >= 0 else 0)
            timeseries.append({
                "trial_id": trial_id,
                "direction": direction,
                "t_s": fmt(t, 3),
                "pitch_deg": fmt(pitch, 5),
                "pitch_rate_deg_s": fmt(-pitch / max(settle, 0.2) + random.gauss(0, 0.6), 4),
                "wheel_speed_rad_s": fmt(wheel, 4),
                "balance_enabled": 1,
                "protection_triggered": int(fail),
                "provisional": True,
                "source": SOURCE,
            })
        summary.append({
            "trial_id": trial_id,
            "direction": direction,
            "success": int(not fail),
            "settling_time_s": "NA" if fail else fmt(settle, 3),
            "peak_pitch_deg": fmt(peak, 3),
            "max_wheel_speed_rad_s": fmt(max_wheel, 3),
            "protection_triggered": int(fail),
            "provisional": True,
            "source": SOURCE,
        })
    write_csv(out / "synthetic_recovery_timeseries_2026-04-24.csv", timeseries)
    write_csv(out / "synthetic_recovery_summary_2026-04-24.csv", summary)

    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    for direction, color in [("forward", "#4C78A8"), ("backward", "#F58518")]:
        trial_ids = sorted({r["trial_id"] for r in timeseries if r["direction"] == direction})[:5]
        for trial_id in trial_ids:
            rows = [r for r in timeseries if r["trial_id"] == trial_id]
            ax.plot([float(r["t_s"]) for r in rows], [float(r["pitch_deg"]) for r in rows], color=color, alpha=0.28)
    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    ax.set_title("E2 disturbance recovery curves (PROVISIONAL synthetic)")
    ax.set_xlabel("Time from impulse (s)")
    ax.set_ylabel("Pitch (deg)")
    ax.grid(alpha=0.25)
    save(fig, "e2_recovery_curves_synthetic_provisional.png")


def e3_leg_length() -> None:
    out = ensure(DATA / "E3_leg_length_sensitivity")
    rows: list[dict[str, object]] = []
    summary: list[dict[str, object]] = []
    specs = [
        ("short", 0.055, 0.68, 6.3, set()),
        ("nominal", 0.070, 0.82, 7.8, set()),
        ("tall", 0.085, 1.10, 10.5, {5}),
    ]
    dt = 0.02
    times = [round(-0.2 + i * dt, 3) for i in range(int(3.2 / dt) + 1)]
    for leg_setting, leg_length, base_settle, base_peak, failures in specs:
        for idx in range(1, 6):
            fail = idx in failures
            settle = base_settle + random.gauss(0, 0.05) + (0.40 if fail else 0.0)
            peak = base_peak + random.gauss(0, 0.45) + (2.0 if fail else 0.0)
            trial_id = f"e3_{leg_setting}_{idx:02d}"
            for t in times:
                pitch = recovery_curve(t, 1.0, peak, settle)
                rows.append({
                    "trial_id": trial_id,
                    "leg_setting": leg_setting,
                    "leg_length_m": fmt(leg_length, 3),
                    "t_s": fmt(t, 3),
                    "pitch_deg": fmt(pitch, 5),
                    "target_leg_m": fmt(leg_length, 3),
                    "balance_enabled": 1,
                    "protection_triggered": int(fail),
                    "provisional": True,
                    "source": SOURCE,
                })
            summary.append({
                "trial_id": trial_id,
                "leg_setting": leg_setting,
                "leg_length_m": fmt(leg_length, 3),
                "success": int(not fail),
                "settling_time_s": "NA" if fail else fmt(settle, 3),
                "peak_pitch_deg": fmt(peak, 3),
                "protection_triggered": int(fail),
                "provisional": True,
                "source": SOURCE,
            })
    write_csv(out / "synthetic_leg_length_timeseries_2026-04-24.csv", rows)
    write_csv(out / "synthetic_leg_length_summary_2026-04-24.csv", summary)

    agg = {}
    for leg_setting, leg_length, _, _, _ in specs:
        vals = [float(r["settling_time_s"]) for r in summary if r["leg_setting"] == leg_setting and r["settling_time_s"] != "NA"]
        peaks = [float(r["peak_pitch_deg"]) for r in summary if r["leg_setting"] == leg_setting]
        agg[leg_setting] = (leg_length, sum(vals) / len(vals), sum(peaks) / len(peaks))
    labels = ["short", "nominal", "tall"]
    fig, ax1 = plt.subplots(figsize=(6.2, 3.6))
    x = [agg[label][0] for label in labels]
    ax1.plot(x, [agg[label][1] for label in labels], marker="o", label="settling time")
    ax1.set_xlabel("Leg length (m)")
    ax1.set_ylabel("Settling time (s)")
    ax2 = ax1.twinx()
    ax2.plot(x, [agg[label][2] for label in labels], marker="s", color="#E45756", label="peak pitch")
    ax2.set_ylabel("Peak pitch (deg)")
    ax1.set_title("E3 leg-length sensitivity (PROVISIONAL synthetic)")
    save(fig, "e3_leg_length_synthetic_provisional.png")


def e4b_physical_response() -> None:
    out = ensure(DATA / "E4_teleop_step_response")
    rows: list[dict[str, object]] = []
    summary: list[dict[str, object]] = []
    specs = [
        ("speed_030", "speed_step", 0.30, 0.0, 0.31, 0.03, 2.4, True),
        ("speed_060", "speed_step", 0.60, 0.0, 0.42, 0.06, 4.1, True),
        ("speed_100", "speed_step", 1.00, 0.0, 0.58, 0.11, 6.8, False),
        ("yaw_left", "yaw_step", 0.0, 1.0, 0.36, 0.0, 3.2, True),
        ("yaw_right", "yaw_step", 0.0, -1.0, 0.38, 0.0, 3.4, True),
    ]
    dt = 0.02
    times = [round(-0.5 + i * dt, 3) for i in range(int(4.5 / dt) + 1)]
    for trial_id, command_type, target_speed, target_yaw, rise, steady_error, pitch_peak, settled in specs:
        for t in times:
            active_t = max(t, 0.0)
            if command_type == "speed_step":
                cmd_speed = target_speed if 0 <= t <= 3.0 else 0.0
                measured_speed = max(0.0, target_speed - steady_error) * (1 - math.exp(-active_t / max(rise / 2.2, 0.08))) if t >= 0 else 0.0
                if t > 3.0:
                    measured_speed *= math.exp(-(t - 3.0) / 0.22)
                measured_yaw = 0.0
            else:
                cmd_speed = 0.0
                measured_speed = 0.0
                measured_yaw = target_yaw * (1 - math.exp(-active_t / max(rise / 2.2, 0.08))) if t >= 0 else 0.0
                if t > 3.0:
                    measured_yaw *= math.exp(-(t - 3.0) / 0.22)
            pitch = pitch_peak * math.exp(-active_t / 0.55) * math.sin(5.0 * active_t) if t >= 0 else random.gauss(0, 0.08)
            rows.append({
                "trial_id": trial_id,
                "command_type": command_type,
                "t_s": fmt(t, 3),
                "cmd_speed_m_s": fmt(cmd_speed, 4),
                "cmd_yaw_rad_s": fmt(target_yaw if 0 <= t <= 3.0 else 0.0, 4),
                "measured_speed_m_s": fmt(measured_speed + random.gauss(0, 0.01), 4),
                "measured_yaw_rad_s": fmt(measured_yaw + random.gauss(0, 0.015), 4),
                "pitch_deg": fmt(pitch + random.gauss(0, 0.10), 4),
                "protection_triggered": int(not settled),
                "provisional": True,
                "source": SOURCE,
            })
        summary.append({
            "trial_id": trial_id,
            "command_type": command_type,
            "target_speed_m_s": fmt(target_speed, 2),
            "target_yaw_rad_s": fmt(target_yaw, 2),
            "rise_time_s": fmt(rise, 3),
            "steady_state_error_m_s": fmt(steady_error, 3),
            "pitch_peak_abs_deg": fmt(pitch_peak, 3),
            "settled_without_fault": int(settled),
            "provisional": True,
            "source": SOURCE,
        })
    write_csv(out / "synthetic_physical_step_timeseries_2026-04-24.csv", rows)
    write_csv(out / "synthetic_physical_step_summary_2026-04-24.csv", summary)

    fig, ax1 = plt.subplots(figsize=(7.2, 3.8))
    trial = [r for r in rows if r["trial_id"] == "speed_060"]
    ax1.plot([float(r["t_s"]) for r in trial], [float(r["cmd_speed_m_s"]) for r in trial], label="cmd speed", color="#777777")
    ax1.plot([float(r["t_s"]) for r in trial], [float(r["measured_speed_m_s"]) for r in trial], label="measured speed", color="#4C78A8")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Speed (m/s)")
    ax2 = ax1.twinx()
    ax2.plot([float(r["t_s"]) for r in trial], [float(r["pitch_deg"]) for r in trial], label="pitch", color="#E45756", alpha=0.8)
    ax2.set_ylabel("Pitch (deg)")
    ax1.set_title("E4b physical teleop step response (PROVISIONAL synthetic)")
    ax1.grid(alpha=0.25)
    save(fig, "e4b_physical_step_synthetic_provisional.png")


def e9_ablation() -> None:
    out = ensure(DATA / "E9_controller_ablation")
    rows: list[dict[str, object]] = []
    summary: list[dict[str, object]] = []
    modes = [
        ("FULL", 0.82, 7.8, set()),
        ("FIXED_LQR", 1.05, 9.6, {10}),
        ("NO_RAMP", 0.45, 8.7, set()),
    ]
    dt = 0.02
    times = [round(-0.2 + i * dt, 3) for i in range(int(3.2 / dt) + 1)]
    for mode, base_response, base_peak, failures in modes:
        for idx in range(1, 11):
            fail = idx in failures
            trial_id = f"e9_{mode.lower()}_{idx:02d}"
            response = base_response + random.gauss(0, 0.07) + (0.35 if fail else 0.0)
            peak = base_peak + random.gauss(0, 0.6) + (2.5 if fail else 0.0)
            for t in times:
                if mode == "NO_RAMP":
                    pitch = peak * math.exp(-max(t, 0) / 0.65) * math.sin(6.3 * max(t, 0)) if t >= 0 else random.gauss(0, 0.1)
                    command = 0.6 if t >= 0 else 0.0
                else:
                    sign = 1.0
                    pitch = recovery_curve(t, sign, peak, response)
                    command = 0.0
                rows.append({
                    "trial_id": trial_id,
                    "mode": mode,
                    "t_s": fmt(t, 3),
                    "pitch_deg": fmt(pitch, 5),
                    "command_speed_m_s": fmt(command, 3),
                    "protection_triggered": int(fail),
                    "provisional": True,
                    "source": SOURCE,
                })
            summary.append({
                "trial_id": trial_id,
                "mode": mode,
                "test_type": "drive_step" if mode == "NO_RAMP" else "impulse_recovery",
                "success": int(not fail),
                "response_time_s": "NA" if fail else fmt(response, 3),
                "peak_pitch_deg": fmt(peak, 3),
                "protection_triggered": int(fail),
                "provisional": True,
                "source": SOURCE,
            })
    write_csv(out / "synthetic_ablation_timeseries_2026-04-24.csv", rows)
    write_csv(out / "synthetic_ablation_summary_2026-04-24.csv", summary)

    labels = ["FULL", "FIXED_LQR", "NO_RAMP"]
    values = []
    peaks = []
    for label in labels:
        vals = [float(r["response_time_s"]) for r in summary if r["mode"] == label and r["response_time_s"] != "NA"]
        pks = [float(r["peak_pitch_deg"]) for r in summary if r["mode"] == label]
        values.append(sum(vals) / len(vals))
        peaks.append(sum(pks) / len(pks))
    fig, ax1 = plt.subplots(figsize=(6.4, 3.6))
    ax1.bar(labels, values, color=["#54A24B", "#B279A2", "#F58518"])
    ax1.set_ylabel("Response time (s)")
    ax2 = ax1.twinx()
    ax2.plot(labels, peaks, color="#E45756", marker="o")
    ax2.set_ylabel("Peak pitch (deg)")
    ax1.set_title("E9 controller ablation (PROVISIONAL synthetic)")
    save(fig, "e9_ablation_synthetic_provisional.png")


def save(fig, name: str) -> None:
    ensure(FIGS)
    fig.tight_layout()
    fig.savefig(FIGS / name, dpi=180)
    plt.close(fig)


def main() -> int:
    e1_static_balance()
    e2_disturbance()
    e3_leg_length()
    e4b_physical_response()
    e9_ablation()
    print(f"synthetic placeholder datasets written under {DATA}")
    print(f"synthetic provisional figures written under {FIGS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
