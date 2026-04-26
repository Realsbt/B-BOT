# O3 Arbitration Supplement Summary

- Date: 2026-04-26
- TCP target: 172.20.10.4:23
- Serial port: /dev/ttyUSB0 at 115200 baud
- Test mode: controller-board bench test with robot supported / drivetrain not used

## Results

| Case | Evidence file | Trials | Result | Key acceptance evidence |
| --- | --- | ---: | --- | --- |
| O3-A BLE/PC gate | `o3_ble_pc_arbitration_2026-04-26_103947.csv` | 5 | 5/5 pass | `BLE connected: yes`, `BLE_DISABLE`, `input enabled: no`, neutral `DRIVE` accepted, `BLE_ENABLE`, `input enabled: yes` |
| O3-B queue/direct command arbitration | `o3_queue_drive_arbitration_2026-04-26_103606.csv` | 5 | 5/5 pass | Direct `DRIVE,250,0` produced `DRIVE ignored: command queue busy` while a queued command was active |

## Interpretation

The BLE/PC test confirms that the Xbox BLE controller was connected during the
test and that the firmware-level BLE input gate could disable and re-enable BLE
input while TCP/PC neutral drive commands remained accepted.

The queue/direct arbitration test confirms that direct `DRIVE` commands are
suppressed while a queued command is active. The key evidence is the serial log
line `DRIVE ignored: command queue busy`; TCP ACKs alone are not sufficient
because ignored direct commands still return transport-level ACKs.

This evidence supports O3 at controller-board arbitration level. It does not
claim full robot motion-safety validation under simultaneous human operation.
