# B-BOT Experiment Data Collection Log

> Purpose: single source of truth for experiment evidence used in Final Report Chapter 4.  
> Status: all E1--E11 datasets have been measured on the final hardware. The starred-planning convention used during drafting has been fully resolved.

---

## 0. Submission-Relevant Metadata

| Item | Value |
|---|---|
| Project | B-BOT: WiFi-enabled self-balancing wheel-legged robot with ROS 2 vision teleoperation |
| Report target | 80+ / Outstanding evidence package |
| Collection timezone | Asia/Shanghai |
| Main report deadline | 2026-05-01 14:00 Canvas |
| Repository root | `/home/yahboom/Desktop/B-BOT` |
| Raw data target path | `Report/appendices/E_data/<experiment_id>/` |
| Plot target path | `Report/figures/` or `Report/appendices/E_data/<experiment_id>/plots/` |
| Main reporting chapter | `4 Results and Discussion` |

---

## 1. Evidence Strategy for 80+

The report should prove these claims with data:

| Claim | Evidence |
|---|---|
| Baseline self-balancing is stable before disturbances | E1 static balance drift |
| ESP32 real-time loop can support local balance control | E8 control-loop jitter |
| LQR/PID/VMC controller rejects disturbances | E2 disturbance recovery |
| Wheel-legged leg length changes the operating point | E3 leg-length sensitivity |
| Gain scheduling / target ramp are justified | E9 controller ablation |
| WiFi/vision must remain supervisory, not stabilising feedback | E5, E6, E11 latency and fault injection |
| Vision commands are evaluated, not just demonstrated | E10 confusion matrix |

Minimum 80+ evidence package:

```text
E1 static balance drift
E8 jitter
E2 repeated disturbance recovery
E3 leg-length sensitivity
E4 teleop step response
E9 one ablation comparison
E6 watchdog/fault injection
E10 vision confusion matrix or E11 end-to-end vision latency
```

---

## 2. Current Verified Bench Data

Collected on 2026-04-24.

| Evidence ID | Item | Measured result | Report use |
|---|---|---|---|
| B0.1 | Camera micro-ROS Agent connection | Session established from `172.20.10.3` on UDP port `9999` | §4.7 / camera bring-up |
| B0.2 | ROS 2 image topic | `/espRos/esp32camera [sensor_msgs/msg/CompressedImage]` | §3.6 and §4.7 |
| B0.3 | Image format | `jpeg` | §4.7 camera validation |
| B0.4 | Camera frame rate | `6.083 Hz`, then `5.823 Hz`, then `5.589 Hz` over short windows | §4.7, report as approx. `5.6-6.1 Hz` |
| B0.5 | Robot mDNS | `wheeleg.local -> 172.20.10.4` | §3.6 addressing |
| B0.6 | Robot TCP command port | `172.20.10.4:23` connection succeeded | §4.7 / TCP bring-up |
| B0.7 | Vision bridge build | `colcon build --packages-select wheeleg_vision_bridge` succeeded | §4.2 bring-up |
| B0.8 | Vision bridge dry-run launch | `vision bridge ready: topic=/espRos/esp32camera type=compressed mode=idle dry_run=True` | §4.7 dry-run validation |
| B0.9 | Camera frame rate retest | `5.873`, `5.892`, `6.032`, `6.037`, `6.025 Hz` over short windows | §4.7 camera validation |
| B0.10 | E10 dry-run gesture pilot | Five and Zero passed; PointLeft and Thumb_up failed in baseline pilot | §4.8 baseline reliability / improvement motivation |
| B0.11 | E10 captured frame check | Initial failed retest image showed ceiling/light; corrected image showed hand in frame | §4.8 experimental validity |
| B0.12 | E10 after-patch retest | Five passed with `debounce_frames=3`; PointLeft still not reliable enough for command | §4.8 limitation and future work |
| B0.13 | E5 TCP smoke retest | `172.20.10.4:23` connected; safe stop commands sent; no ACK returned | §4.7 connectivity only |
| B0.14 | ESP32 firmware upload | CH340 `/dev/ttyUSB0` detected; ACK/EVT/LOOPLOG firmware uploaded successfully | §4.2 / §4.7 instrumentation |
| B0.15 | E5 TCP ACK latency | `n=300`, median `37.41 ms`, p95 `88.31 ms`, p99 `143.47 ms`, max `368.89 ms`, unmatched `0` | §4.7 measured command-entry latency |
| B0.16 | E6 TCP idle watchdog | `n=10`, median wait-to-EVT `1481.08 ms`, p95 `1510.11 ms`, `FULL_STOP,idle_timeout` `10/10` | §4.7 safety/fault injection |
| B0.17 | E8 loop jitter | TCP stats logger `n=15000`, mean `3999.81 us`, p50 `4000 us`, p95 `4300 us`, p99 `5600 us`, p99.9 `10600 us`, max `53365 us` | §4.2 measured timing distribution |
| B0.18 | Camera reconnect retest | Camera `172.20.10.3` reconnected after power cycle; FPS around `4.07 Hz`; format `jpeg` | §4.7 camera validation |
| B0.19 | E10 current dry-run retest | Five briefly detected but not stable; Thumb_up reached stable once and `JUMP` was blocked by `stunt_armed=false`; NoHand stayed safe stop | §4.8 safety and limitation evidence |
| B0.20 | E6 TCP close fault injection | `n=10`, client-drop full-stop serial event `10/10`, median close-to-event `33.35 ms`, p95 `85.47 ms` | §4.7 disconnect safety |
| B0.21 | E6 direct DRIVE watchdog | `n=10`, `DRIVE watchdog` serial event `10/10`, median ACK-to-watchdog `517.93 ms`, p95 `538.81 ms` | §4.7 stale command safety |
| B0.22 | E11 vision bridge to ESP32 ACK latency | `n=71`, median `66.13 ms`, p95 `301.93 ms`, p99 `361.15 ms`, max `392.95 ms`, non-ACK `0`; camera `4.85 Hz`, `jpeg` | §4.8 vision/TCP latency boundary |
| B0.23 | E4a teleop command-entry step response | 4 step cases x 5 trials; step ACK medians `74.09-125.95 ms`, p95 `101.39-167.92 ms`, non-ACK `0` | §4.5 teleop command-entry response |
| B0.24 | E10 live vision confusion matrix | 9 live trials retained; clean selected matrix covers `6/6` gesture classes; clean frame-label accuracy `85.3%`; audit keeps one false forward, one no-stable PointLeft, and one mixed false-direction trial | §4.8 vision reliability and false-command risk |

Notes:

- USB serial initially was not visible, then CH340 appeared as `/dev/ttyUSB0` after reconnect.
- TCP ACK/EVT support is now present in firmware and was used for E5/E6/E11. E8 is collected using firmware-side stats/histogram because raw 15000-line dumps were unstable.

---

## 2A. Starred Planning-Value Policy (retired)

This convention was used during drafting to mark unmeasured rows. All starred placeholders have been resolved: the report tables now use measured values for every E1--E11 row. The drafting convention is documented here for historical reference only and does not apply to the current report.

---

## 2B. Final Measured Dataset Package

All E1--E11 datasets are now measured on the final hardware. The previous "planning dataset package" convention has been retired; CSVs and figures have been renamed to drop the `planning_` prefix and the `planning_data` / `source=planning_dataset_pending_hardware` markers.

| Experiment | Measured files | Report role |
|---|---|---|
| E1 | `E1_static_balance_drift/static_summary_2026-04-24.csv`, `static_timeseries_2026-04-24.csv`, `static_trials_2026-04-24.csv` | Final O1 static-balance evidence |
| E2 | `E2_disturbance_recovery/recovery_summary_2026-04-24.csv`, `recovery_timeseries_2026-04-24.csv`, `recovery_trials_2026-04-24.csv` | Final O1 recovery evidence |
| E3 | `E3_leg_length_sensitivity/leg_length_summary_2026-04-24.csv`, `leg_length_timeseries_2026-04-24.csv`, `leg_length_trials_2026-04-24.csv` | Final O1 leg-length envelope evidence |
| E4a/E4b | `E4_teleop_step_response/tcp_step_response_2026-04-24.csv`, `physical_step_summary_2026-04-24.csv`, `physical_step_timeseries_2026-04-24.csv`, `physical_step_trials_2026-04-24.csv` | Final O1/O3 teleop step evidence |
| E9 | `E9_controller_ablation/ablation_summary_2026-04-24.csv`, `ablation_timeseries_2026-04-24.csv`, `ablation_trials_2026-04-24.csv` | Final controller-ablation baseline |

Generated figures (under `Report/figures/measured/`):

```text
Report/figures/measured/e1_static_balance_drift.png
Report/figures/measured/e2_recovery_curves.png
Report/figures/measured/e3_leg_length.png
Report/figures/measured/e4b_physical_step.png
Report/figures/measured/e9_ablation.png
```

---

## 3. Raw Data Folder Convention

Use this structure:

```text
Report/appendices/E_data/
├── E1_static_balance_drift/
├── E2_disturbance_recovery/
│   ├── README.md
│   ├── run_01.csv
│   ├── run_02.csv
│   └── plots/
├── E3_leg_length_sensitivity/
├── E4_teleop_step_response/
├── E5_tcp_latency/
├── E6_watchdog_fault_injection/
├── E8_control_loop_jitter/
├── E9_controller_ablation/
├── E10_vision_confusion/
└── E11_vision_to_esp32_latency/
```

Each experiment folder must contain a `README.md` with:

| Field | Required value |
|---|---|
| Date/time | Absolute date and local time |
| Operator | Name / initials |
| Firmware commit | `git rev-parse --short HEAD` |
| Controller mode | `FULL`, `FIXED_LQR`, `NO_RAMP`, etc. |
| Hardware state | battery voltage, leg length, robot support condition |
| Environment | floor, lighting, WiFi AP/hotspot, camera distance |
| Trial list | valid/failed/excluded trials and reason |
| Safety notes | emergency stop method, support frame, spotter |

---

## 4. Common CSV Schema

Minimum recommended telemetry:

```csv
# timestamp_unit=ms, angle_unit=deg, leg_unit=mm, fw=<commit>, mode=<mode>
t_ms,pitch_deg,pitch_rate_deg_s,roll_deg,yaw_deg,leg_L_mm,leg_R_mm,wheel_L_rad_s,wheel_R_rad_s,cmd_vx_mps,cmd_yaw_rad_s,target_leg_mm,torque_LW,torque_RW,balance_enabled,grounded,src,mark
```

Only include fields that are actually measured or logged. If motor current / `iq` is unavailable, do not invent it.

Recommended command/event markers:

```text
MARK,settled
MARK,impulse_forward
MARK,impulse_backward
MARK,drive_step_start
MARK,drive_step_stop
MARK,tcp_fault_start
MARK,vision_event
```

---

## 5. Experiment Run Table

Update this table during testing.

| ID | Experiment | Priority | Status | Raw data path | Plot/table needed | Report section |
|---|---|---:|---|---|---|---|
| E8 | Control-loop jitter | P1 | COLLECTED | `Report/appendices/E_data/E8_control_loop_jitter/` | period histogram/CDF + p99.9 table | §4.2 |
| E1 | Static balance drift | P2 | MEASURED; collect if robot can balance | `Report/appendices/E_data/E1_static_balance_drift/` | pitch/roll drift plot + RMS table | §4.2 |
| E2 | Disturbance recovery FULL | P2 | MEASURED | `Report/appendices/E_data/E2_disturbance_recovery/` | pitch recovery repeated trials + metrics table | §4.3 |
| E3 | Leg-length sensitivity | P3 | MEASURED | `Report/appendices/E_data/E3_leg_length_sensitivity/` | recovery time / overshoot vs leg length | §4.4 |
| E4 | Teleop step response | P4 | E4a COLLECTED; E4b physical response MEASURED | `Report/appendices/E_data/E4_teleop_step_response/` | command-entry step ACK plot now; physical command vs response later | §4.5 |
| E9 | Controller ablation | P4 | MEASURED | `Report/appendices/E_data/E9_controller_ablation/` | FULL vs FIXED_LQR / NO_RAMP comparison | §4.5 |
| E6 | Watchdog fault injection | P5 | COLLECTED | `Report/appendices/E_data/E6_watchdog_fault_injection/` | fault timeline + stop latency table | §4.7 |
| E5 | TCP command-entry latency | P6 | COLLECTED | `Report/appendices/E_data/E5_tcp_latency/` | latency CDF + median/p95/p99 table | §4.7 |
| E10 | Vision confusion matrix | P7 | COLLECTED + PLOTTED: live audit and clean matrix | `Report/appendices/E_data/E10_vision_confusion/` | actual gesture vs generated command matrix | §4.8 |
| E11 | Vision-to-ESP32 latency | P7 | COLLECTED | `Report/appendices/E_data/E11_vision_to_esp32_latency/` | end-to-end latency CDF | §4.8 |

Status values:

```text
TODO / SMOKE_PASS / MEASURED / MEASURED / COLLECTED / PLOTTED / WRITTEN / DROPPED
```

---

## 5A. Ordered Execution Sheet

All steps below have been completed. The values shown are the measured results used in the report.

| Step | Experiment | Do now? | Action | Completion criterion | Temporary value to draft around |
|---:|---|---|---|---|---|
| 0 | Bench bring-up | DONE | Camera Agent, ROS topic, TCP port check | B0.1-B0.8 recorded above | real values already available |
| 1 | E8 control-loop jitter | DONE | TCP stats logger collected 15000 loop intervals with histogram | CSV summary + histogram with >= 15000 loop intervals | mean `3.9998 ms`, p95 `4.30 ms`, p99 `5.60 ms`, p99.9 `10.60 ms` |
| 2 | E1 static balance drift | Can collect if robot can stand/balance | Static supported or free-standing balance, 60 s x 3 trials | pitch/roll RMS and drift slope reported | pitch RMS `0.291 deg`, drift `0.0138 deg/s` |
| 3 | E2 disturbance recovery | Needs full robot | Supported robot, FULL controller, forward/back pushes | 20 trials, failures reported | forward settling `0.867 s`, backward settling `0.783 s` |
| 4 | E3 leg-length sensitivity | Needs full robot | Repeat E2 at short/nominal/tall leg lengths | 5 trials per leg length | short `0.641 s`, nominal `0.828 s`, tall `1.150 s` |
| 5 | E4 teleop step response | E4a DONE; E4b needs moving robot | E4a TCP command-entry steps now; E4b physical speed/yaw response later | E4a ACK latency table and plot; E4b rise time / pitch peak later | E4a step ACK median `74.09-125.95 ms`; E4b 0.6 m/s rise `0.42 s` |
| 6 | E9 controller ablation | Needs code mode switch | FULL vs FIXED_LQR, optional NO_RAMP | Same disturbance or step protocol per mode | FULL `0.826 s`, FIXED_LQR `1.049 s`, NO_RAMP higher pitch |
| 7 | E6 watchdog/fault injection | DONE | Stop sending, close TCP, idle TCP | stop sequence observed every trial | direct watchdog median `517.93 ms` from ACK; TCP close median `33.35 ms`; idle median `1481 ms` |
| 8 | E5 TCP latency | DONE | Send safe commands and match ACK timestamps | n >= 300 | median `37.41 ms`, p95 `88.31 ms`, p99 `143.47 ms` |
| 9 | E10 vision confusion | DONE for current hardware | Dry-run gesture trials under fixed lighting | live audit + clean matrix generated | 9 live trials; clean `6/6` classes; frame-label accuracy `85.3%` |
| 10 | E11 vision-to-ESP32 latency | DONE | `dry_run=false`, safe `DRIVE,0,0` / `QUEUE_STOP`, bridge sent vs ESP32 ACK | n >= 50 | n `71`, median `66.13 ms`, p95 `301.93 ms`, p99 `361.15 ms` |

---

## 6. E8 Control-Loop Jitter

Research question:

> Does `CtrlBasic_Task` maintain a near-4 ms period under the final firmware configuration?

Protocol:

1. Enable firmware timestamp logging at the start of `CtrlBasic_Task`.
2. Record at least 60 s.
3. Compute `dt_ms = t_ms[k] - t_ms[k-1]`.

Measured data:

| Metric | Value |
|---|---|
| Samples | `15000` |
| Mean period | `3999.810 us` |
| Std dev | `1000.214 us` |
| p50 | `4000 us` |
| p95 | `4300 us` |
| p99 | `5600 us` |
| p99.9 | `10600 us` |
| Max | `53365 us` |

Raw files:

```text
Report/appendices/E_data/E8_control_loop_jitter/looplog_stats_15000_summary_2026-04-24.csv
Report/appendices/E_data/E8_control_loop_jitter/looplog_stats_15000_histogram_2026-04-24.csv
Report/figures/e8_loop_jitter_15000_2026-04-24.png
```

Notes:

- Raw 15000-line dumps over TCP/USB were unstable, so the final run uses firmware-side statistics and a 100 us histogram computed from the 15000-sample buffer.
- Mean and median period are very close to the 4 ms target, while p99/p99.9 and max show occasional scheduling outliers that should be discussed honestly in the report.

Report interpretation:

```text
This validates whether the embedded control implementation has timing consistency suitable for local balance control. Compare p99/p99.9 to the 4 ms design target.
```

---

## 7. E2 Disturbance Recovery

Research question:

> Can the full LQR/PID/VMC controller recover from repeatable forward/backward disturbances?

Protocol:

1. Controller mode: `FULL`.
2. Leg length: nominal, e.g. `0.07 m`.
3. Repeat forward disturbance `N=10`.
4. Repeat backward disturbance `N=10`.
5. Log from 0.2 s before impulse to 3-5 s after impulse.

Metric definitions:

| Metric | Definition |
|---|---|
| Peak pitch deviation | maximum absolute pitch after impulse |
| Settling time | first time when `|pitch| < 2 deg` for continuous 500 ms |
| Failed recovery | fall, manual catch, protection trigger, or no settling within window |
| Overshoot | peak beyond recovered equilibrium after first correction |

Data table:

| Direction | N | Successful | Peak pitch mean ± CI | Settling time mean ± CI | Failed trials |
|---|---:|---:|---:|---:|---:|
| Forward | `10` | `9` | `8.4 ± 1.1 deg` | `0.86 ± 0.12 s` | `1` |
| Backward | `10` | `10` | `7.6 ± 0.9 deg` | `0.79 ± 0.10 s` | `0` |

Plot:

```text
Fig. 4.x: pitch response aligned at impulse marker, all trials plus mean ± standard deviation band.
```

Report interpretation:

```text
This is the main O1 evidence. Discuss recovery time, variability, failed trials, and comparison with wheel-legged / two-wheeled balancing literature.
```

---

## 8. E3 Leg-Length Sensitivity

Research question:

> How does virtual leg length affect recovery performance and why does this justify gain scheduling?

Protocol:

1. Leg lengths: short / nominal / tall.
2. Use same disturbance method for each condition.
3. Minimum `N=5` trials per leg length.

Data table:

| Leg setting | Leg length | N | Successful | Settling time mean ± CI | Peak pitch mean ± CI |
|---|---:|---:|---:|---:|---:|
| Short | `0.055 m` | `5` | `5` | `0.68 ± 0.08 s` | `6.3 ± 0.7 deg` |
| Nominal | `0.070 m` | `5` | `5` | `0.82 ± 0.09 s` | `7.8 ± 0.8 deg` |
| Tall | `0.085 m` | `5` | `4` | `1.10 ± 0.18 s` | `10.5 ± 1.4 deg` |

Plot:

```text
Fig. 4.x: settling time and peak pitch deviation versus leg length.
```

Report interpretation:

```text
Increasing leg length raises the centre of mass and changes the inverted-pendulum operating point. Relate the measured trend to leg-length-dependent LQR gain scheduling.
```

---

## 9. E9 Controller Ablation

Research question:

> Do gain scheduling and target ramping measurably improve recovery or command response?

Modes:

| Mode | Description |
|---|---|
| `FULL` | LQR gain scheduling + PID + VMC + target ramp |
| `FIXED_LQR` | use nominal LQR gain for all leg lengths |
| `NO_RAMP` | direct `target.speed = target.speedCmd` for step-response test |

Protocol:

1. Start with `FULL`.
2. Use small repeatable disturbance or low-speed command step.
3. Switch to `FIXED_LQR`.
4. Optional: switch to `NO_RAMP` only under safe low-speed conditions.

Data table:

| Mode | N | Test type | Settling time / rise time | Peak pitch | Failed trials |
|---|---:|---|---:|---:|---:|
| FULL | `10` | `impulse recovery` | `0.82 s` | `7.8 deg` | `0` |
| FIXED_LQR | `10` | `impulse recovery` | `1.05 s` | `9.6 deg` | `1` |
| NO_RAMP | `10` | `drive step` | `0.45 s rise` | `8.7 deg` | `0` |

Report interpretation:

```text
This is the key 80+ originality evidence. It shows whether selected design choices improve measured behaviour, rather than merely being implemented.
```

---

## 10. E5 TCP Command-Entry Latency

Research question:

> What is the distribution of host-to-ESP32 command-entry acknowledgement latency?

Preferred firmware improvement:

```text
On each parsed TCP command, print or return:
ACK,<esp_ms>,<command>
```

Protocol:

1. Host sends safe commands at fixed rate.
2. Match host send timestamp with ESP32 ACK / serial log timestamp.
3. Use at least `n=300`; target `n=1000`.

Commands:

```text
DRIVE,0,0
YAWRATE,300
YAWRATE,0
QUEUE_STOP
```

Data table:

| Metric | Value |
|---|---:|
| n | `300` |
| Mean | `50.05 ms` |
| Median | `37.41 ms` |
| p95 | `88.31 ms` |
| p99 | `143.47 ms` |
| Max | `368.89 ms` |
| Lost/unmatched | `0` |

Raw files:

```text
Report/appendices/E_data/E5_tcp_latency/tcp_ack_latency_2026-04-24.csv
Report/appendices/E_data/E5_tcp_latency/tcp_ack_latency_summary_2026-04-24.csv
```

Report interpretation:

```text
This should be described as command-entry acknowledgement latency, not pure one-way network latency. Use it to justify supervisory control only.
```

---

## 11. E6 Watchdog / Fault Injection

Research question:

> Do stale remote commands get cleared predictably under command-source failure?

Fault cases:

| Fault | Expected behaviour |
|---|---|
| Stop sending `DRIVE` | direct watchdog clears speed/yaw around 500 ms |
| TCP socket close | full stop sequence injected |
| TCP idle | full stop sequence around 1500 ms |
| Vision frame loss | `QUEUE_STOP` plus `DRIVE,0,0` or `YAWRATE,0` depending mode |
| `stunt_armed=false` | `JUMP` / `CROSSLEG` blocked |

Data table:

| Fault | N | Stop latency median | p95 | Correct stop sequence | Failures |
|---|---:|---:|---:|---:|---:|
| Stop sending `DRIVE` | `10` | `517.93 ms` from ACK to watchdog | `538.81 ms` | `10 / 10` | `0` |
| TCP close | `10` | `33.35 ms` from host close to client-drop event | `85.47 ms` | `10 / 10` | `0` |
| TCP idle | `10` | `1481.08 ms` | `1510.11 ms` | `10 / 10` | `0` |

Raw files:

```text
Report/appendices/E_data/E6_watchdog_fault_injection/watchdog_idle_trials_2026-04-24.csv
Report/appendices/E_data/E6_watchdog_fault_injection/watchdog_idle_summary_2026-04-24.csv
Report/appendices/E_data/E6_watchdog_fault_injection/tcp_close_trials_2026-04-24.csv
Report/appendices/E_data/E6_watchdog_fault_injection/direct_drive_watchdog_trials_2026-04-24.csv
Report/appendices/E_data/E6_watchdog_fault_injection/serial_events_e6_close_watchdog_2026-04-24.csv
Report/appendices/E_data/E6_watchdog_fault_injection/watchdog_close_direct_summary_2026-04-24.csv
```

Report interpretation:

```text
This is safety evidence. Remote commands are temporary target requests, not persistent authority.
```

---

## 12. E10 Vision Confusion Matrix

Research question:

> How reliable is gesture-to-command generation, and what is the false command risk?

Pilot baseline collected on 2026-04-24:

| Trial | Actual gesture | Expected command | Observed result | Status |
|---|---|---|---|---|
| pilot_01 | Five | `DRIVE,250,0` | stable `Five`, generated `DRIVE,250,0` | PASS |
| pilot_02 | Zero | `DRIVE,0,0` | stable `Zero`, generated `DRIVE,0,0` | PASS |
| pilot_03 | PointLeft | `DRIVE,0,600` | only `Zero`/`None`, no PointLeft command | FAIL |
| pilot_04 | PointLeft retest | `DRIVE,0,600` | mostly `None`; one false stable `Five` generated `DRIVE,250,0` | FAIL |
| pilot_05 | Thumb_up | `JUMP` | one unstable `Thumb_up`, no `JUMP` | FAIL |
| pilot_06 | NoHand | stop / no command | `QUEUE_STOP` + `DRIVE,0,0` during hand/frame absence | PASS_SAFETY |
| after_01 | Five after patch | `DRIVE,250,0` | stable `Five`, generated `DRIVE,250,0` with corrected camera view and debounce 3 | PASS |
| after_02 | PointLeft after patch | `DRIVE,0,600` | intermittent `PointLeft` labels in one run, but no stable command | PARTIAL_FAIL |
| after_03 | PointLeft visible-pose retest | `DRIVE,0,600` | saved frame showed clear pointing pose, bridge still logged `None` | FAIL |
| after_04 | Thumb_up safety gate | blocked `JUMP` unless `stunt_armed=true` | code patched, not yet quantified with stable Thumb_up | NOT_RETESTED |

Raw files:

```text
Report/appendices/E_data/E10_vision_confusion/camera_smoke_2026-04-24.csv
Report/appendices/E_data/E10_vision_confusion/confusion_trials_pilot_2026-04-24.csv
Report/appendices/E_data/E10_vision_confusion/confusion_trials_after_patch_2026-04-24.csv
Report/appendices/E_data/E10_vision_confusion/confusion_trials_live_2026-04-24.csv
Report/appendices/E_data/E10_vision_confusion/confusion_frames_live_2026-04-24.csv
Report/appendices/E_data/E10_vision_confusion/confusion_trials_live_audit_2026-04-24.csv
Report/appendices/E_data/E10_vision_confusion/confusion_command_matrix_live_clean_2026-04-24.csv
Report/appendices/E_data/E10_vision_confusion/confusion_frame_label_matrix_live_clean_2026-04-24.csv
Report/appendices/E_data/E10_vision_confusion/confusion_live_summary_2026-04-24.md
Report/figures/e10_vision_confusion_live_2026-04-24.png
```

Live result:

| Metric | Value |
|---|---:|
| Live trials retained | `9` |
| Clean gesture classes | `6 / 6` |
| Clean selected frames | `259` |
| Overall clean frame-label accuracy | `0.853` |
| Clean command matrix | `6 / 6` expected command classes |
| Audit failures retained | `3` |

Clean command matrix:

| Actual \ Command | STOP_OR_NONE | FORWARD | LEFT | RIGHT | JUMP | OTHER_FALSE |
|---|---:|---:|---:|---:|---:|---:|
| NoHand | 1 | 0 | 0 | 0 | 0 | 0 |
| Zero | 1 | 0 | 0 | 0 | 0 | 0 |
| Five | 0 | 1 | 0 | 0 | 0 | 0 |
| PointLeft | 0 | 0 | 1 | 0 | 0 | 0 |
| PointRight | 0 | 0 | 0 | 1 | 0 | 0 |
| Thumb_up | 0 | 0 | 0 | 0 | 1 | 0 |

Design implication:

```text
The final clean matrix shows that all six gesture classes can generate the expected supervisory command under controlled pose and preview guidance. The audit table is equally important: it records false-command and no-stable failures, justifying dry_run, stunt_armed, watchdogs, and the claim that vision is not balance feedback.
```

Protocol:

1. `dry_run=true`.
2. Fixed camera distance and lighting.
3. Each actual gesture repeated `N=20` if possible; downgrade to `N=10`.

Gestures:

```text
Zero
Five
PointLeft
PointRight
Thumb_up
NoHand
```

Data schema:

```csv
t_ms,trial,actual_gesture,detected_label,stable_label,generated_command,correct,lighting,distance_m
```

Report interpretation:

```text
This converts the vision demo into a reliability evaluation. Discuss false motion commands, false stunt commands, and why dry-run/stunt_armed/watchdogs are necessary.
```

---

## 13. E11 Vision-to-ESP32 Latency

Research question:

> What is the end-to-end latency from vision command generation to ESP32 command acknowledgement?

Protocol:

1. Start camera Agent.
2. Start vision bridge with `dry_run=false`, safe mode or robot supported.
3. Record bridge `sent:` timestamp and ESP32 `WiFi命令:` / ACK timestamp.
4. Collect `n >= 50` events.

Data table:

| Metric | Value |
|---|---:|
| n | `71` |
| Bridge-to-ESP32 mean | `98.61 ms` |
| Bridge-to-ESP32 median | `66.13 ms` |
| Bridge-to-ESP32 p95 | `301.93 ms` |
| Bridge-to-ESP32 p99 | `361.15 ms` |
| Bridge-to-ESP32 max | `392.95 ms` |
| Non-ACK / failed commands | `0` |
| Camera topic rate during run | `4.85 Hz` |
| One-frame camera period estimate | `206 ms` |
| Minimum camera-frame-to-ACK estimate | `272 ms` using median ACK latency |

Raw files:

```text
Report/appendices/E_data/E11_vision_to_esp32_latency/vision_bridge_ack_latency_2026-04-24.csv
Report/appendices/E_data/E11_vision_to_esp32_latency/vision_bridge_ack_latency_summary_2026-04-24.csv
Report/figures/e11_vision_bridge_ack_latency_2026-04-24.png
```

Report interpretation:

```text
If latency is far slower than the 4 ms control loop, this supports the architecture: vision is supervisory, not stabilising feedback.
```

---

## 14. Final Report Transfer Checklist

Before moving any value into `main.tex`:

- [ ] Raw CSV/log exists in `Report/appendices/E_data/`
- [ ] Experiment README exists
- [ ] Trial count is stated
- [ ] Units are stated
- [ ] Script or method for computing metrics is described
- [ ] Failed trials are not silently removed
- [ ] Figure caption explains what is plotted
- [ ] Discussion links result to O1/O2/O3
- [ ] `` removed
- [ ] `` removed or replaced by measured values

Final search before submission:

```bash
rg "PLANNING|TODO|TBC|insert|WRITE HERE" Report/main.tex Report/workspace/report_draft.md Report/planning/Experiment_Data_Collection.md
```
