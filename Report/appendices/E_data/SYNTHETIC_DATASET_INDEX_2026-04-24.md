# Synthetic Placeholder Dataset Index

Date: 2026-04-24 CST

These datasets are intentionally fictional planning placeholders. They are reasonable engineering values for drafting tables, figures, analysis scripts, and report structure before the full robot hardware campaign is complete.

They are not measured data.

Every generated CSV row includes:

- `provisional=True`
- `source=synthetic_planning_placeholder_not_measured`

Before final report submission, replace these rows with measured rows, remove the provisional/source markers, and update each experiment README with the real hardware state, trial notes, and exclusions.

| Experiment | Placeholder dataset | Provisional figure | Intended replacement |
|---|---|---|---|
| E1 static balance drift | `E1_static_balance_drift/synthetic_static_timeseries_2026-04-24.csv`, `E1_static_balance_drift/synthetic_static_summary_2026-04-24.csv` | `Report/figures/provisional/e1_static_balance_drift_provisional.png` | 60 s static balance logs, 3 or more trials |
| E2 disturbance recovery | `E2_disturbance_recovery/synthetic_recovery_timeseries_2026-04-24.csv`, `E2_disturbance_recovery/synthetic_recovery_summary_2026-04-24.csv` | `Report/figures/provisional/e2_recovery_curves_synthetic_provisional.png` | Forward/backward impulse recovery trials, failed trials retained |
| E3 leg-length sensitivity | `E3_leg_length_sensitivity/synthetic_leg_length_timeseries_2026-04-24.csv`, `E3_leg_length_sensitivity/synthetic_leg_length_summary_2026-04-24.csv` | `Report/figures/provisional/e3_leg_length_synthetic_provisional.png` | Short/nominal/tall leg-length recovery trials |
| E4b physical teleoperation response | `E4_teleop_step_response/synthetic_physical_step_timeseries_2026-04-24.csv`, `E4_teleop_step_response/synthetic_physical_step_summary_2026-04-24.csv` | `Report/figures/provisional/e4b_physical_step_synthetic_provisional.png` | Physical wheel/body response to speed and yaw command steps |
| E9 controller ablation | `E9_controller_ablation/synthetic_ablation_timeseries_2026-04-24.csv`, `E9_controller_ablation/synthetic_ablation_summary_2026-04-24.csv` | `Report/figures/provisional/e9_ablation_synthetic_provisional.png` | FULL vs FIXED_LQR and NO_RAMP comparison runs |

Generator:

```bash
MPLCONFIGDIR=/tmp/matplotlib python3 Report/appendices/E_data/generate_synthetic_unmeasured_datasets.py
```

Final check:

```bash
rg "synthetic_planning_placeholder_not_measured|provisional=True|\\* \\[PROVISIONAL\\]" Report
```
