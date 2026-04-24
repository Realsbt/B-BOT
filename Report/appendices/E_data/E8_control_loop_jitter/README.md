# E8 Control-Loop Jitter

Date/time: measured on 2026-04-24, Asia/Shanghai
Operator: user + Codex
Firmware commit: local patch with `LOOPLOG_START`, chunked dump, and `LOOPLOG_STATS_TCP`
Controller mode: balance disabled during bench test; `CtrlBasic_Task` still executed the 4 ms loop path
Hardware state: ESP32 main board connected over CH340 `/dev/ttyUSB0`; robot TCP server reachable at `172.20.10.4:23`
Environment: local phone hotspot `BT26`
Trial list: measured 15000-sample looplog stats plus earlier pilot/chunked attempts
Safety notes: no robot actuation performed; all TCP tests used safe stop commands or timing logger commands

Files:

- `provisional_loop_jitter_metrics_2026-04-24.csv`
- `collect_looplog_tcp_serial.py`
- `collect_looplog_tcp.py`
- `collect_looplog_stats_tcp.py`
- `plot_looplog_stats.py`
- `looplog_tcp_100_2026-04-24.csv`
- `looplog_tcp_100_summary_2026-04-24.csv`
- `looplog_chunked_1000_2026-04-24.csv`
- `looplog_chunked_1000_summary_2026-04-24.csv`
- `looplog_chunked_15000_2026-04-24.csv` failed raw-dump attempt; do not use for final metrics
- `looplog_chunked_15000_summary_2026-04-24.csv` failed raw-dump attempt; do not use for final metrics
- `looplog_stats_15000_summary_2026-04-24.csv`
- `looplog_stats_15000_histogram_2026-04-24.csv`
- `Report/figures/e8_loop_jitter_15000_2026-04-24.png`

Measured summary:

- Samples: `15000`
- Mean: `3999.810 us`
- Std dev: `1000.214 us`
- p50: `4000 us`
- p95: `4300 us`
- p99: `5600 us`
- p99.9: `10600 us`
- Max: `53365 us`

Notes:

- Raw 15000-line TCP/USB dump attempts were unstable and caused ESP32 resets during the dump phase.
- The final measured result uses firmware-side statistics and a 100 us histogram computed from the 15000-sample buffer.
- Use the `looplog_stats_15000_*` files for the report, not the provisional CSV.
