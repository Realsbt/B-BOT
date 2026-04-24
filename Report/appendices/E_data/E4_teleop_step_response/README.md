# E4 Teleop Step Response

Date/time: 2026-04-24 CST
Operator: user + Codex
Firmware commit: 035ebe4+local monitor/E4a changes
Controller mode: ESP32 TCP command parser, direct teleoperation commands
Hardware state: ESP32 controller board reachable over WiFi; physical speed/pitch response not measured
Environment: local hotspot, host PC to ESP32 TCP port `23`
Trial list: see `tcp_step_response_2026-04-24.csv`, `provisional_trials_2026-04-24.csv`, `synthetic_physical_step_timeseries_2026-04-24.csv`, and `synthetic_physical_step_summary_2026-04-24.csv`
Safety notes: every step trial ends with `DRIVE,0,0`, `YAWRATE,0`, and `QUEUE_STOP`.

Status: E4a COLLECTED; E4b physical robot response still PROVISIONAL_READY

Purpose:

- Quantify how quickly the robot responds to teleoperation step commands.
- Report speed/yaw rise time, steady-state error, and pitch disturbance during commanded motion.
- E4a measures command-entry step response only: host command to ESP32 ACK.
- E4b will measure physical wheel/body response after the full robot is available.

Measured E4a summary:

| Case | Command | n | Step ACK median | Step ACK p95 | Stop ACK median | Non-ACK |
|---|---|---:|---:|---:|---:|---:|
| speed_150 | `DRIVE,150,0` | 5 | 74.09 ms | 127.57 ms | 110.06 ms | 0 |
| speed_250 | `DRIVE,250,0` | 5 | 96.64 ms | 167.92 ms | 124.31 ms | 0 |
| yaw_left_600 | `DRIVE,0,600` | 5 | 125.95 ms | 132.27 ms | 115.93 ms | 0 |
| yaw_right_600 | `DRIVE,0,-600` | 5 | 82.59 ms | 101.39 ms | 123.87 ms | 0 |

Figure:

- `Report/figures/e4_tcp_step_response_2026-04-24.png`
- `Report/figures/provisional/e4b_physical_step_synthetic_provisional.png`

Important:

- `tcp_step_response_2026-04-24.csv` is measured E4a command-entry data.
- `provisional_trials_2026-04-24.csv` is early planning data for E4b physical response only.
- `synthetic_physical_step_timeseries_2026-04-24.csv` and `synthetic_physical_step_summary_2026-04-24.csv` are fictional E4b planning datasets.
- Rows marked `provisional=true` or `provisional=True` must be replaced before final report submission.
- Rows with `source=synthetic_planning_placeholder_not_measured` are fictional, not experimental measurements.
