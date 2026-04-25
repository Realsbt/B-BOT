# Appendix G: Experiment Data, Logs and Extra Evidence

This appendix contains the raw and supporting data used by the Results chapter.

All experimental datasets in this appendix are now measured. No planning or placeholder rows remain in the report tables.

## Time-Zone and Filename Note

The physical project work should be interpreted in the UK project context. Some filenames, CSV comment headers and generated summaries use `2026-04-24` as a computer/VM-generated batch stamp. Earlier versions of these files incorrectly described that stamp as `CST` or `Asia/Shanghai`, because the virtual-machine clock was set to that timezone during data collection and drafting. The absolute wall-clock timezone is not used for the reported latency, jitter or response metrics; those results are based on relative timestamps and measured intervals.

## Evidence Status by Experiment

| Experiment | Purpose | Evidence status | Main folder / files | Report use |
| --- | --- | --- | --- | --- |
| E1 static balance drift | Static balance stability over repeated 60 s trials | Measured | `E1_static_balance_drift/static_*_2026-04-24.csv` | Final O1 static-balance evidence |
| E2 disturbance recovery | Recovery from repeatable forward/backward disturbance | Measured | `E2_disturbance_recovery/recovery_*_2026-04-24.csv` | Final O1 recovery evidence |
| E3 leg-length sensitivity | Effect of leg length on recovery and stability | Measured | `E3_leg_length_sensitivity/leg_length_*_2026-04-24.csv` | Final O1 leg-length envelope evidence |
| E4 teleoperation step response | WiFi command-entry and physical response to step commands | Measured (E4a command-entry; E4b physical response) | `E4_teleop_step_response/tcp_step_response_2026-04-24.csv`, `physical_step_*_2026-04-24.csv` | Final O1/O3 teleoperation step evidence |
| E5 TCP latency | PC-to-ESP32 command-entry ACK latency | Measured | `E5_tcp_latency/tcp_ack_latency_2026-04-24.csv`, summary CSV | Final O2/O3 communication evidence |
| E6 watchdog fault injection | Direct-command expiry, TCP close and idle timeout behaviour | Measured | `E6_watchdog_fault_injection/` | Final safety/fault-response evidence |
| E7 camera topic bring-up | ROS 2 WiFi camera module topic visibility, format and frame rate | Measured bring-up evidence | `E7_camera_topic_bringup/`, E10/E11 supporting files | Camera path validation, not a standalone control result |
| E8 control-loop jitter | Embedded control-loop timing distribution | Measured | `E8_control_loop_jitter/looplog_stats_15000_summary_2026-04-24.csv` and related CSVs | Final embedded timing evidence |
| E9 controller ablation | Full controller vs reduced variants | Measured | `E9_controller_ablation/ablation_*_2026-04-24.csv` | Final baseline evidence for controller-design choices |
| E10 vision confusion matrix | Live gesture recognition and command mapping reliability | Measured | `E10_vision_confusion/` | Final vision reliability evidence |
| E11 vision-to-ESP32 latency | Vision bridge to ESP32 ACK latency | Measured | `E11_vision_to_esp32_latency/vision_bridge_ack_latency_2026-04-24.csv`, summary CSV | Final supervisory-vision latency evidence |

## Generated Figures

Measured figures used directly in the report:

- `Report/figures/e4_tcp_step_response_2026-04-24.png`
- `Report/figures/e8_loop_jitter_15000_2026-04-24.png`
- `Report/figures/e10_vision_confusion_live_2026-04-24.png`
- `Report/figures/e11_vision_bridge_ack_latency_2026-04-24.png`

Supplementary measured figures (kept in `Report/figures/measured/` for the appendix and per-experiment READMEs):

- `e1_static_balance_drift.png`
- `e2_disturbance_recovery.png`, `e2_disturbance_recovery.pdf`, `e2_recovery_curves.png`
- `e3_leg_length_sensitivity.png`, `e3_leg_length_sensitivity.pdf`, `e3_leg_length.png`
- `e4b_physical_step.png`
- `e6_watchdog_fault_injection.png`, `e6_watchdog_fault_injection.pdf`
- `e8_control_loop_jitter.png`, `e8_control_loop_jitter.pdf`
- `e9_controller_ablation.png`, `e9_controller_ablation.pdf`, `e9_ablation.png`

Project-management figure:

- `project_management_gantt.png`
- `project_management_gantt.pdf`
