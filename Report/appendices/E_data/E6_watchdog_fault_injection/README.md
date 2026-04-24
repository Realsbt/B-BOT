# E6 Watchdog and Fault Injection

Date/time: measured on 2026-04-24, Asia/Shanghai
Operator: user + Codex
Firmware commit: local patch with TCP `ACK` / `EVT` and serial watchdog logs
Controller mode: balance disabled during bench test
Hardware state: ESP32 main board connected over CH340 `/dev/ttyUSB0`; robot TCP server reachable at `172.20.10.4:23`
Environment: local phone hotspot `BT26`
Trial list: measured TCP idle, TCP close, and direct DRIVE watchdog trials
Safety notes: tests used command watchdog paths only; every trial ended with `DRIVE,0,0`, `YAWRATE,0`, `QUEUE_STOP`

Files:

- `provisional_trials_2026-04-24.csv`
- `watchdog_idle_trials_2026-04-24.csv`
- `watchdog_idle_summary_2026-04-24.csv`
- `tcp_close_trials_2026-04-24.csv`
- `direct_drive_watchdog_trials_2026-04-24.csv`
- `serial_events_e6_close_watchdog_2026-04-24.csv`
- `watchdog_close_direct_summary_2026-04-24.csv`
- `collect_tcp_close_direct_watchdog.py`

Measured summary:

- TCP idle: `10/10`, median `1481.08 ms`, p95 `1510.11 ms`.
- TCP close: `10/10`, median host-close to `client_drop` serial event `33.35 ms`, p95 `85.47 ms`.
- Direct DRIVE watchdog: `10/10`, median ACK-to-watchdog `517.93 ms`, p95 `538.81 ms`.

Replacement note:

- The old provisional values should not be used for E6. Use the measured CSV files above.
