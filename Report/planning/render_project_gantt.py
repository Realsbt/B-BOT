#!/usr/bin/env python3
"""Render the reconstructed B-BOT project Gantt chart."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


matplotlib.use("Agg")

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures"


def date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


TASKS = [
    ("Planning", "Project scoping, objectives and feasibility", "2025-10-06", "2025-10-20"),
    ("Planning", "Proposal, initial Gantt and H&S/risk assessment", "2025-10-06", "2025-10-18"),
    ("Planning", "Architecture refinement and evidence planning", "2025-10-20", "2025-11-09"),
    ("Planning", "Final report structure and appendix integration", "2026-04-20", "2026-04-30"),
    ("Mechanical/Electrical", "Chassis inspection and measurement", "2025-10-13", "2025-10-27"),
    ("Mechanical/Electrical", "3D modelling of mounts/brackets", "2025-10-20", "2025-11-17"),
    ("Mechanical/Electrical", "3D print iteration and mechanical modification", "2025-11-03", "2025-12-15"),
    ("Mechanical/Electrical", "PCB schematic/layout and wiring plan", "2025-10-20", "2025-12-01"),
    ("Mechanical/Electrical", "PCB soldering and bring-up", "2025-11-24", "2025-12-22"),
    ("Mechanical/Electrical", "Wiring harness and motor lead soldering", "2025-11-24", "2026-01-12"),
    ("Mechanical/Electrical", "Mechanical/electrical reliability cleanup", "2026-02-18", "2026-03-25"),
    ("Embedded Firmware/Control", "ESP32/PlatformIO setup, CAN, motors and IMU", "2025-11-01", "2025-11-15"),
    ("Embedded Firmware/Control", "PID loops, yaw/roll/leg regulation", "2025-11-08", "2025-11-22"),
    ("Embedded Firmware/Control", "Ground detection, protection and stand-up states", "2025-11-16", "2025-12-01"),
    ("Embedded Firmware/Control", "Jump behaviour and BLE controller", "2025-12-01", "2025-12-15"),
    ("Embedded Firmware/Control", "Calibration, persistence and voltage monitoring", "2025-12-15", "2025-12-22"),
    ("Embedded Firmware/Control", "UART2 command queue and scripted actions", "2025-12-23", "2026-01-01"),
    ("Embedded Firmware/Control", "Cross-step, input arbitration and trigger redesign", "2026-02-01", "2026-02-17"),
    ("Embedded Firmware/Control", "MATLAB kinematics, VMC and LQR code generation", "2026-02-02", "2026-02-11"),
    ("Embedded Firmware/Control", "Debugging, tuning and hardware diagnosis", "2026-02-15", "2026-03-08"),
    ("Host Software/ROS 2/Vision", "ToF/OpenMV/host architecture research", "2026-02-18", "2026-03-04"),
    ("Host Software/ROS 2/Vision", "Host-command protocol and supervisory-control plan", "2026-02-18", "2026-03-11"),
    ("Host Software/ROS 2/Vision", "ROS 2 camera/micro-ROS bring-up", "2026-04-20", "2026-04-25"),
    ("Host Software/ROS 2/Vision", "MediaPipe vision bridge and TCP command safety", "2026-04-23", "2026-04-26"),
    ("Testing/Data/Report", "Early test matrix and report outline", "2026-03-09", "2026-03-23"),
    ("Testing/Data/Report", "Data-template and evidence planning", "2026-03-16", "2026-03-30"),
    ("Testing/Data/Report", "Easter report catch-up and appendix planning", "2026-03-30", "2026-04-19"),
    ("Testing/Data/Report", "Final experiment design and 80+ evidence planning", "2026-04-20", "2026-04-25"),
    ("Testing/Data/Report", "E4/E5/E6/E8/E10/E11 data collection", "2026-04-23", "2026-04-25"),
    ("Testing/Data/Report", "E1/E2/E3/E4b/E9 physical data collection", "2026-04-24", "2026-04-26"),
    ("Testing/Data/Report", "Chapter 2/3/4/5 report drafting", "2026-04-24", "2026-04-27"),
    ("Testing/Data/Report", "Measured-data integration and consistency checks", "2026-04-26", "2026-04-28"),
    ("Testing/Data/Report", "LaTeX formatting and final upload preparation", "2026-04-28", "2026-05-02"),
]

CONSTRAINTS = [
    ("Christmas vacation", "2025-12-15", "2026-01-05"),
    ("Exam period", "2026-01-05", "2026-01-27"),
    ("Easter vacation", "2026-03-30", "2026-04-18"),
]

COLORS = {
    "Planning": "#4c78a8",
    "Mechanical/Electrical": "#f58518",
    "Embedded Firmware/Control": "#54a24b",
    "Host Software/ROS 2/Vision": "#b279a2",
    "Testing/Data/Report": "#e45756",
}


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    last_group = None
    for group, task, start, end in TASKS:
        if group != last_group:
            rows.append(("header", group, "", "", ""))
            last_group = group
        rows.append(("task", group, task, start, end))

    fig_height = 0.34 * len(rows) + 2.2
    fig, ax = plt.subplots(figsize=(17, fig_height))
    fig.subplots_adjust(left=0.31, right=0.98, top=0.88, bottom=0.08)

    fig.suptitle(
        "B-BOT Reconstructed Project Gantt Chart (Oct 2025 - Apr 2026)",
        fontsize=15,
        fontweight="bold",
        y=0.985,
    )

    for label, start, end in CONSTRAINTS:
        start_dt = date(start)
        end_dt = date(end)
        ax.axvspan(
            start_dt,
            end_dt,
            facecolor="#bdbdbd",
            alpha=0.18,
            hatch="///",
            edgecolor="#777777",
            linewidth=0.0,
            zorder=0,
        )
        ax.text(
            start_dt + (end_dt - start_dt) / 2,
            -0.62,
            label.replace(" ", "\n"),
            ha="center",
            va="center",
            fontsize=9,
            color="#555555",
        )

    y_positions = list(range(len(rows)))
    labels = []

    for y, row in zip(y_positions, rows):
        row_type, group, task, start, end = row
        if row_type == "header":
            labels.append("")
            ax.axhline(y + 0.52, color="#d9d9d9", linewidth=0.8, zorder=1)
            ax.text(
                date("2025-10-01"),
                y,
                group,
                ha="left",
                va="center",
                fontsize=9.5,
                fontweight="bold",
                color=COLORS[group],
            )
            continue

        start_dt = date(start)
        end_dt = date(end)
        labels.append(task)
        ax.barh(
            y,
            (end_dt - start_dt).days,
            left=start_dt,
            height=0.64,
            color=COLORS[group],
            edgecolor="white",
            linewidth=0.8,
            zorder=2,
        )

    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_ylim(len(rows) - 0.25, -1.15)

    ax.set_xlim(date("2025-10-01"), date("2026-05-05"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
    ax.grid(axis="x", which="major", color="#cfcfcf", linewidth=0.8)
    ax.grid(axis="x", which="minor", color="#eeeeee", linewidth=0.5)
    ax.set_axisbelow(True)

    ax.set_xlabel("Calendar date", fontsize=10)

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="y", length=0)

    legend_items = [Patch(facecolor=color, label=group) for group, color in COLORS.items()]
    legend_items.append(
        Patch(facecolor="#bdbdbd", edgecolor="#777777", alpha=0.25, hatch="///", label="Reduced-development period")
    )
    ax.legend(
        handles=legend_items,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.075),
        ncol=3,
        frameon=False,
        fontsize=9,
    )

    png_path = FIG_DIR / "project_management_gantt.png"
    pdf_path = FIG_DIR / "project_management_gantt.pdf"
    fig.savefig(png_path, dpi=220, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    print(png_path)
    print(pdf_path)


if __name__ == "__main__":
    main()
