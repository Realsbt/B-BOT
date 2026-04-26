# O3 Arbitration Supplement

This folder contains the controller-board evidence collection script for the
remaining O3 multi-source arbitration checks.

## Scope

The script checks two firmware-level behaviours:

- **O3-A BLE/PC gate:** `BLE_DISABLE` prevents BLE input from being accepted while
  TCP/PC commands remain accepted; `BLE_ENABLE` restores BLE input.
- **O3-B queue/direct command arbitration:** while a queued command is active, a
  direct `DRIVE` command is ignored by the firmware and reported on serial as
  `DRIVE ignored: command queue busy`.

This is a controller-board bench test. It supports O3 by showing that competing
command sources are gated in firmware, but it is not a full robot motion-safety
test.

## Hardware

- ESP32 controller board flashed with the current firmware.
- PC connected to the ESP32 USB serial port.
- PC on the same WiFi network as the ESP32 TCP command server.
- Xbox/BLE controller paired if the BLE gate check is being interpreted as
  controller-input evidence.

If motors are connected, support the robot or remove drivetrain power before
running the script.

## Run

Find the serial port first:

```bash
ls -l /dev/ttyUSB* /dev/ttyACM*
```

Run all O3 supplementary checks:

```bash
python3 collect_o3_arbitration.py \
  --host 172.20.10.4 \
  --serial-port /dev/ttyUSB0 \
  --confirm-board-only
```

Use `--host wheeleg.local` if mDNS resolves correctly on the test network.

The script writes timestamped CSV files and a Markdown summary in this folder:

- `o3_ble_pc_arbitration_<timestamp>.csv`
- `o3_queue_drive_arbitration_<timestamp>.csv`
- `o3_serial_events_<timestamp>.csv`
- `o3_arbitration_summary_<timestamp>.md`

## Report Use

The final report uses `o3_arbitration_summary_2026-04-26.md` as the consolidated
summary. The valid BLE/PC gate run is
`o3_ble_pc_arbitration_2026-04-26_103947.csv`, where all five trials recorded
`BLE connected: yes`. The queue/direct-command run is
`o3_queue_drive_arbitration_2026-04-26_103606.csv`.

The key acceptance signal for O3-B is the serial log line
`DRIVE ignored: command queue busy`; the TCP response alone is not enough because
transport-level ACKs are still returned for ignored direct commands.
