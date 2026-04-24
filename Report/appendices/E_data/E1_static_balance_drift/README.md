# E1 Static Balance Drift

Date/time: 2026-04-24 CST
Operator: user + Codex
Firmware commit: pending real collection
Controller mode: FULL balance controller
Hardware state: full robot required; current values are placeholders only
Environment: flat indoor floor, stationary robot, no intentional disturbance
Trial list: see `provisional_trials_2026-04-24.csv`, `synthetic_static_timeseries_2026-04-24.csv`, and `synthetic_static_summary_2026-04-24.csv`
Safety notes: real collection should use a support frame or spotter during bring-up.

Status: PROVISIONAL_READY

Purpose:

- Establish a baseline before disturbance and teleoperation tests.
- Report pitch/roll RMS, peak drift, and drift slope over 60 s static balance windows.

Files:

- `provisional_trials_2026-04-24.csv` - early table placeholder
- `synthetic_static_timeseries_2026-04-24.csv` - fictional 60 s x 3 trial time series
- `synthetic_static_summary_2026-04-24.csv` - fictional RMS, peak, and drift metrics
- `Report/figures/provisional/e1_static_balance_drift_provisional.png`

Important:

- The synthetic CSV files in this folder are planning data only.
- Rows marked `provisional=true` or `provisional=True` must be replaced before final report submission.
- Rows with `source=synthetic_planning_placeholder_not_measured` are fictional, not experimental measurements.
