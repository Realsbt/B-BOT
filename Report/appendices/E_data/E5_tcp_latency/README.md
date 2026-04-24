# E5 TCP Command-Entry Latency

Date/time: 2026-04-24 08:23 CST
Operator: user + Codex
Firmware commit: 70c3b17+local_patch
Controller mode: bench / safe stop only
Hardware state: ESP32 main controller reachable at `172.20.10.4:23`
Environment: local WiFi/hotspot
Trial list: see `tcp_smoke_2026-04-24.csv`
Safety notes: only zero-speed / stop commands were sent.

Files:

- `tcp_smoke_2026-04-24.csv`
- `provisional_latency_summary_2026-04-24.csv`
- `latency.csv`
- `plots/`

Current limitation:

- TCP connection succeeds, but the firmware command server does not return ACK lines.
- This smoke test confirms connectivity only. E5 latency still requires a firmware ACK or serial log capture.
- The provisional summary is a planning placeholder only and must be replaced before final submission.
