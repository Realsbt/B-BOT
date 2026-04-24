# Appendix G: Experiment Data, Logs and Extra Evidence

This appendix contains the raw and supporting data used by the Results chapter.

The key rule is that measured results and provisional placeholders must remain clearly separated. Files marked with `provisional=True`, `source=synthetic_planning_placeholder_not_measured`, or `[PROVISIONAL]` must not be treated as measured evidence in the final report.

## Evidence Status by Experiment

| Experiment | Purpose | Evidence status | Main folder / files | Report use |
| --- | --- | --- | --- | --- |
| E1 static balance drift | Static balance stability over repeated 60 s trials | **Provisional/synthetic only** | `E1_static_balance_drift/` | Replace before final O1 performance claim |
| E2 disturbance recovery | Recovery from repeatable forward/backward disturbance | **Provisional/synthetic only** | `E2_disturbance_recovery/` | Replace before final O1 performance claim |
| E3 leg-length sensitivity | Effect of leg length on recovery and stability | **Provisional/synthetic only** | `E3_leg_length_sensitivity/` | Replace before final O1 performance claim |
| E4 teleoperation step response | WiFi command-entry and physical response to step commands | **Mixed**: TCP command-entry measured; physical robot response provisional/synthetic | `E4_teleop_step_response/` | Use TCP part as measured; replace physical response before final O1/O3 claim |
| E5 TCP latency | PC-to-ESP32 command-entry ACK latency | **Measured** | `E5_tcp_latency/tcp_ack_latency_2026-04-24.csv`, summary CSV | Final O2/O3 communication evidence |
| E6 watchdog fault injection | Direct-command expiry, TCP close and idle timeout behaviour | **Measured** | `E6_watchdog_fault_injection/` | Final safety/fault-response evidence |
| E7 camera topic bring-up | ROS 2 WiFi camera module topic visibility, format and frame rate | **Measured bring-up evidence** | `E7_camera_topic_bringup/`, E10/E11 supporting files | Camera path validation, not a standalone control result |
| E8 control-loop jitter | Embedded control-loop timing distribution | **Measured** | `E8_control_loop_jitter/looplog_stats_15000_summary_2026-04-24.csv` and related CSVs | Final embedded timing evidence |
| E9 controller ablation | Full controller vs reduced variants | **Provisional/synthetic only** | `E9_controller_ablation/` | Replace before final controller-design claim |
| E10 vision confusion matrix | Live gesture recognition and command mapping reliability | **Measured** | `E10_vision_confusion/` | Final vision reliability evidence |
| E11 vision-to-ESP32 latency | Vision bridge to ESP32 ACK latency | **Measured** | `E11_vision_to_esp32_latency/vision_bridge_ack_latency_2026-04-24.csv`, summary CSV | Final supervisory-vision latency evidence |

## Generated Figures

Current measured figures in `Report/figures/`:

- `e4_tcp_step_response_2026-04-24.png`
- `e8_loop_jitter_15000_2026-04-24.png`
- `e10_vision_confusion_live_2026-04-24.png`
- `e11_vision_bridge_ack_latency_2026-04-24.png`

Project-management figure:

- `project_management_gantt.png`
- `project_management_gantt.pdf`

## Provisional Data Policy

The provisional-data rules are stored in:

- `PROVISIONAL_DATA_POLICY.md`
- `SYNTHETIC_DATASET_INDEX_2026-04-24.md`

Before final submission, run:

```bash
rg "provisional=true|provisional=True|synthetic_planning_placeholder_not_measured|PROVISIONAL" Report
```

Any remaining match must either be replaced with measured data or explicitly discussed as provisional and excluded from final performance claims.

## Minimum Final Replacement List

The following must be prioritised once the final robot hardware is ready:

- E1 measured static balance drift trials.
- E2 measured disturbance recovery trials.
- E3 measured leg-length sensitivity trials.
- E4 measured physical teleoperation response.
- E9 measured controller ablation or a clear explanation if ablation cannot be run safely.

Measured E5, E6, E8, E10 and E11 can already support the communication, watchdog, timing and vision parts of the report.
