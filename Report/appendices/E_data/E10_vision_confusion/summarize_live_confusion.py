#!/usr/bin/env python3
"""Summarise E10 live gesture confusion data.

The live CSV intentionally keeps failed and operator-error trials. This script
audits each trial, selects the latest clean pass per gesture for the clean
confusion matrix, and keeps a separate audit table for the report discussion.
"""

from __future__ import annotations

import ast
import csv
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = ROOT / "Report" / "appendices" / "E_data" / "E10_vision_confusion"
FIG_DIR = ROOT / "Report" / "figures"

TRIALS_CSV = DATA_DIR / "confusion_trials_live_2026-04-24.csv"
FRAMES_CSV = DATA_DIR / "confusion_frames_live_2026-04-24.csv"

AUDIT_CSV = DATA_DIR / "confusion_trials_live_audit_2026-04-24.csv"
COMMAND_MATRIX_CSV = DATA_DIR / "confusion_command_matrix_live_clean_2026-04-24.csv"
FRAME_MATRIX_CSV = DATA_DIR / "confusion_frame_label_matrix_live_clean_2026-04-24.csv"
SUMMARY_MD = DATA_DIR / "confusion_live_summary_2026-04-24.md"
FIG_PATH = FIG_DIR / "e10_vision_confusion_live_2026-04-24.png"

GESTURES = ["NoHand", "Zero", "Five", "PointLeft", "PointRight", "Thumb_up"]
LABELS = ["None", "Zero", "Five", "PointLeft", "PointRight", "Thumb_up", "One", "Other"]
COMMAND_COLS = ["STOP_OR_NONE", "FORWARD", "LEFT", "RIGHT", "JUMP", "OTHER_FALSE"]


def parse_dict(text: str) -> dict[str, int]:
    if not text:
        return {}
    try:
        value = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return {}
    if not isinstance(value, dict):
        return {}
    return {str(k): int(v) for k, v in value.items()}


def command_bucket(command: str, actual: str) -> str:
    if actual == "NoHand" and command == "":
        return "STOP_OR_NONE"
    mapping = {
        "": "STOP_OR_NONE",
        "DRIVE,0,0": "STOP_OR_NONE",
        "DRIVE,250,0": "FORWARD",
        "DRIVE,0,600": "LEFT",
        "DRIVE,0,-600": "RIGHT",
        "JUMP": "JUMP",
    }
    return mapping.get(command, "OTHER_FALSE")


def audit_trial(row: dict[str, str]) -> dict[str, object]:
    command_counts = parse_dict(row.get("command_counts", ""))
    expected = row["expected_command"]
    actual = row["actual_gesture"]
    expected_count = command_counts.get(expected, 0)
    wrong_count = sum(count for command, count in command_counts.items() if command != expected)
    primary = row.get("observed_command", "")

    if actual == "NoHand":
        clean = wrong_count == 0 and float(row["correct_label_ratio"]) >= 0.8
        status = "pass_clean" if clean else "fail_false_positive"
        primary = ""
    elif expected_count > 0 and wrong_count == 0:
        clean = True
        status = "pass_clean"
    elif expected_count > 0 and wrong_count > 0:
        clean = False
        status = "mixed_false_command"
    elif wrong_count > 0:
        clean = False
        status = "fail_false_command"
    else:
        clean = False
        status = "fail_no_stable_expected"

    return {
        "trial_id": row["trial_id"],
        "actual_gesture": actual,
        "expected_command": expected,
        "frames": row["frames"],
        "mode_label": row["mode_label"],
        "correct_label_ratio": row["correct_label_ratio"],
        "expected_command_count": expected_count,
        "wrong_command_count": wrong_count,
        "primary_command": primary,
        "audit_status": status,
        "selected_for_clean_matrix": False,
        "notes": row.get("notes", ""),
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    trials = read_csv(TRIALS_CSV)
    frames = read_csv(FRAMES_CSV)

    audit_rows = [audit_trial(row) for row in trials]
    latest_clean: dict[str, dict[str, object]] = {}
    for audit in audit_rows:
        if audit["audit_status"] == "pass_clean":
            latest_clean[str(audit["actual_gesture"])] = audit
    selected_ids = {str(row["trial_id"]) for row in latest_clean.values()}
    for audit in audit_rows:
        audit["selected_for_clean_matrix"] = str(audit["trial_id"]) in selected_ids

    write_csv(AUDIT_CSV, audit_rows, list(audit_rows[0].keys()))

    command_matrix = {gesture: Counter({col: 0 for col in COMMAND_COLS}) for gesture in GESTURES}
    for gesture in GESTURES:
        row = latest_clean.get(gesture)
        if row is None:
            continue
        bucket = command_bucket(str(row["primary_command"]), gesture)
        command_matrix[gesture][bucket] += 1
    command_rows = []
    for gesture in GESTURES:
        row = {"actual_gesture": gesture}
        row.update({col: command_matrix[gesture][col] for col in COMMAND_COLS})
        command_rows.append(row)
    write_csv(COMMAND_MATRIX_CSV, command_rows, ["actual_gesture", *COMMAND_COLS])

    frame_counts = {gesture: Counter({label: 0 for label in LABELS}) for gesture in GESTURES}
    selected_frames = [row for row in frames if row["trial_id"] in selected_ids]
    for frame in selected_frames:
        label = frame["label"]
        if label not in LABELS:
            label = "Other"
        frame_counts[frame["actual_gesture"]][label] += 1
    frame_rows = []
    for gesture in GESTURES:
        row = {"actual_gesture": gesture}
        row.update({label: frame_counts[gesture][label] for label in LABELS})
        frame_rows.append(row)
    write_csv(FRAME_MATRIX_CSV, frame_rows, ["actual_gesture", *LABELS])

    total_selected_frames = len(selected_frames)
    correct_selected_frames = 0
    per_gesture_accuracy = {}
    for gesture in GESTURES:
        expected_label = "None" if gesture == "NoHand" else gesture
        total = sum(frame_counts[gesture].values())
        correct = frame_counts[gesture][expected_label]
        correct_selected_frames += correct
        per_gesture_accuracy[gesture] = correct / total if total else 0.0
    overall_frame_accuracy = correct_selected_frames / total_selected_frames if total_selected_frames else 0.0

    write_summary(
        trials=trials,
        audit_rows=audit_rows,
        latest_clean=latest_clean,
        selected_frames=selected_frames,
        overall_frame_accuracy=overall_frame_accuracy,
        per_gesture_accuracy=per_gesture_accuracy,
    )
    plot_summary(command_rows, per_gesture_accuracy)


def write_summary(
    trials: list[dict[str, str]],
    audit_rows: list[dict[str, object]],
    latest_clean: dict[str, dict[str, object]],
    selected_frames: list[dict[str, str]],
    overall_frame_accuracy: float,
    per_gesture_accuracy: dict[str, float],
) -> None:
    status_counts = Counter(str(row["audit_status"]) for row in audit_rows)
    lines = [
        "# E10 Live Gesture Confusion Summary",
        "",
        "Date: 2026-04-24 UK test session; filename/date stamp generated by the local VM/computer",
        "",
        "This summary keeps all live trials in the audit table, then selects the latest clean pass for each gesture for the clean confusion matrix.",
        "",
        "## Key Results",
        "",
        f"- Live trials recorded: {len(trials)}",
        f"- Clean gestures available: {len(latest_clean)} / {len(GESTURES)}",
        f"- Clean selected frames: {len(selected_frames)}",
        f"- Overall clean frame-label accuracy: {overall_frame_accuracy:.3f}",
        "",
        "## Audit Status Counts",
        "",
    ]
    for status, count in sorted(status_counts.items()):
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Selected Clean Trials", ""])
    for gesture in GESTURES:
        row = latest_clean.get(gesture)
        if row is None:
            lines.append(f"- {gesture}: missing clean pass")
        else:
            lines.append(
                f"- {gesture}: `{row['trial_id']}`, frame accuracy {per_gesture_accuracy[gesture]:.3f}, "
                f"primary command `{row['primary_command'] or 'None/stop'}`"
            )
    lines.extend([
        "",
        "## Generated Files",
        "",
        f"- `{AUDIT_CSV.relative_to(ROOT)}`",
        f"- `{COMMAND_MATRIX_CSV.relative_to(ROOT)}`",
        f"- `{FRAME_MATRIX_CSV.relative_to(ROOT)}`",
        f"- `{FIG_PATH.relative_to(ROOT)}`",
        "",
        "Notes:",
        "",
        "- `live_02_zero` is retained as a false forward-command risk caused by poor closed-fist pose/lighting.",
        "- `live_05_pointleft` is retained as a failed pointing-label trial before the rule relaxation.",
        "- `live_06_pointleft` is retained as an operator pose error / mixed false-direction command trial; its sample image points image-right.",
        "- `Thumb_up` maps to `JUMP` in the encoder, but the live robot bridge blocks stunt commands unless `stunt_armed=true`.",
    ])
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot_summary(command_rows: list[dict[str, object]], per_gesture_accuracy: dict[str, float]) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    matrix = np.array([[int(row[col]) for col in COMMAND_COLS] for row in command_rows])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

    ax = axes[0]
    im = ax.imshow(matrix, cmap="Blues", vmin=0, vmax=max(1, matrix.max()))
    ax.set_title("E10 clean trial command matrix")
    ax.set_xticks(range(len(COMMAND_COLS)), COMMAND_COLS, rotation=35, ha="right")
    ax.set_yticks(range(len(GESTURES)), GESTURES)
    for y in range(matrix.shape[0]):
        for x in range(matrix.shape[1]):
            ax.text(x, y, str(matrix[y, x]), ha="center", va="center", color="black")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    ax = axes[1]
    acc = [per_gesture_accuracy[g] for g in GESTURES]
    ax.bar(GESTURES, acc, color="#4C78A8")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Frame-label accuracy")
    ax.set_title("Selected clean trial frame accuracy")
    ax.tick_params(axis="x", rotation=35)
    for idx, value in enumerate(acc):
        ax.text(idx, value + 0.025, f"{value:.2f}", ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    fig.savefig(FIG_PATH, dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
