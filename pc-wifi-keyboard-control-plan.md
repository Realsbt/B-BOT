# PC WiFi Keyboard Control Plan

> Created: 2026-04-23 08:49:43 CST +0800

## 1. Decision

Keep the Xbox BLE controller as the primary manual control and backup control path.

Add PC WASD control over WiFi TCP as an intermediate test layer between:

```text
manual Xbox BLE control
```

and:

```text
camera / MediaPipe vision control
```

The PC WiFi control path is useful because it verifies:

- Robot ESP32 can receive commands over WiFi
- Host-side control software can drive the robot without UART
- The same TCP transport can later be reused by `wheeleg_vision_bridge`
- Keyboard teleop is easier to debug than camera-based gesture/face control

It should not replace the physical power cutoff or the Xbox controller as the safest manual fallback.

---

## 2. Bluetooth vs PC WiFi

### Xbox BLE Controller

Advantages:

- Already implemented and tested in the firmware
- Direct manual control, no PC needed
- Lower setup complexity
- Good for normal driving and recovery
- Good fallback if ROS / WiFi / PC software fails

Disadvantages:

- Not integrated with ROS
- Cannot easily be scripted or logged on the PC
- Not useful for validating the planned WiFi command path
- Does not prepare the robot for vision control

Best use:

- Manual driving
- Bench recovery
- Fallback control
- Keeping a human in direct control during risky tests

### PC WASD over WiFi TCP

Advantages:

- Uses the same network direction needed by future vision control:
  - `PC -> WiFi TCP -> Robot ESP32`
- Easier to test than MediaPipe because input is deterministic
- Can log every command sent by the PC
- Can add watchdog behavior on both PC and robot
- Can later share the same transport code as `wheeleg_vision_bridge`

Disadvantages:

- Requires robot ESP32 WiFi to be configured and enabled
- More failure points than BLE:
  - WiFi signal
  - IP address
  - TCP connection
  - PC process
  - router / hotspot
- WiFi and BLE share 2.4 GHz and may affect each other
- Not suitable as an emergency stop by itself

Best use:

- Testing PC-to-robot command path
- Testing future `transport: tcp`
- Keyboard teleop from ROS host
- Controlled bench tests before vision control

---

## 3. Target Architecture

```text
Xbox Controller --BLE--> Robot ESP32
                          |
                          | existing manual control
                          v
                    target speed / yaw / leg


PC keyboard --WiFi TCP--> Robot ESP32 TCP server
                          |
                          | new PC control path
                          v
                    Serial_HandleCommandLine()
                          |
                          v
                    target speed / yaw / queue
```

The camera remains separate:

```text
Camera ESP32 --WiFi/micro-ROS--> PC ROS2
```

Future vision path:

```text
Camera ESP32 -> PC ROS2 / MediaPipe -> WiFi TCP -> Robot ESP32
```

---

## 4. Control Mode Policy

Default mode:

```text
BLE controller enabled
PC control idle
Vision bridge dry_run=true
```

When PC keyboard control starts:

```text
BLE_DISABLE
DRIVE,0,0
```

When PC keyboard control exits:

```text
DRIVE,0,0
BLE_ENABLE
```

Emergency stop options, in reliability order:

1. Physical power cutoff
2. PC sends `DRIVE,0,0` + `QUEUE_STOP`
3. USB serial sends `QUEUE_STOP` / `BALANCE_OFF`
4. Xbox controller only when command queue is not busy

The PC keyboard script must always send stop commands on exit.

---

## 5. Proposed Command Protocol

Existing queue commands are not ideal for keyboard teleop:

```text
FORWARD,25,1
LEFT,20,1
```

They execute fixed-duration queue actions. Keyboard control should be real-time:

```text
press key -> update speed immediately
release key -> stop or update immediately
```

Add a new direct command:

```text
DRIVE,<speed_milli>,<yaw_mrad>
```

Examples:

```text
DRIVE,300,0      # forward 0.300 m/s
DRIVE,-300,0     # backward 0.300 m/s
DRIVE,0,800      # turn left 0.800 rad/s
DRIVE,0,-800     # turn right 0.800 rad/s
DRIVE,300,800    # forward + left
DRIVE,0,0        # stop
```

Firmware behavior:

- Does not enter the command queue
- Only applies when the queue is not `EXEC_RUNNING` or `EXEC_PAUSED`
- Writes directly:
  - `target.speedCmd`
  - `target.yawSpeedCmd`
- Clamps speed to safe limits
- Updates a `sLastDriveMs` timestamp
- If no `DRIVE` command arrives for 500 ms:
  - set `target.speedCmd = 0`
  - set `target.yawSpeedCmd = 0`

This is similar to the existing `YAWRATE` direct command, but controls both linear speed and yaw.

---

## 6. PC Keyboard Mapping

Recommended keys:

```text
W      forward
S      backward
A      turn left
D      turn right
Space  stop: DRIVE,0,0 + QUEUE_STOP
Q      quit: DRIVE,0,0 + BLE_ENABLE
1      slow speed
2      medium speed
3      high speed for bench only
```

Initial conservative values:

```text
slow speed:   150 mm/s
medium speed: 250 mm/s
high speed:   350 mm/s
yaw:          600 mrad/s
send rate:    10 Hz
watchdog:     500 ms
```

Do not start with full `MAX_SPEED` or full `MAX_YAWSPEED`.

---

## 7. Implementation Steps

### Phase A: Enable WiFi TCP on Robot ESP32

1. Fill local WiFi credentials:

```c
#define WIFI_SSID "your-wifi-name"
#define WIFI_PASS "your-wifi-password"
```

2. Enable firmware flag in `platformio.ini`:

```ini
build_flags = -DENABLE_WIFI_CMD
```

3. Build firmware:

```bash
/home/yahboom/.platformio/penv/bin/pio run
```

4. Flash robot ESP32.

5. Watch USB serial log for:

```text
WiFi command ready: <robot-ip>:23
```

### Phase B: Manual TCP Smoke Test

From PC:

```bash
nc <robot-ip> 23
```

Send safe commands first:

```text
QUEUE_STATUS
BLE_STATUS
YAWRATE,0
QUEUE_STOP
```

Then test mode arbitration:

```text
BLE_DISABLE
BLE_ENABLE
```

Do not send movement commands until the robot is physically secured.

### Phase C: Add `DRIVE` Firmware Command

Add:

```text
DRIVE,<speed_milli>,<yaw_mrad>
```

Add:

- speed clamp
- yaw clamp
- 500 ms watchdog
- queue-busy guard
- serial log output

Build and test again.

### Phase D: Add PC Keyboard Script

Create:

```text
host/tools/keyboard_drive.py
```

Script responsibilities:

- Connect to `<robot-ip>:23`
- Send `BLE_DISABLE` on start
- Read WASD key states
- Send `DRIVE,...` at 10 Hz
- Send `DRIVE,0,0` when no movement key is active
- Space sends `DRIVE,0,0` + `QUEUE_STOP`
- On quit / Ctrl+C:
  - send `DRIVE,0,0`
  - send `BLE_ENABLE`
  - close socket

### Phase E: Bench Test

Robot must be physically secured.

Pre-flight:

0. Confirm `wheeleg.local` resolves from the host:

```bash
ping -c 2 wheeleg.local
avahi-resolve -n wheeleg.local         # optional, needs avahi-utils
```

   If resolution fails, fall back to the DHCP IP printed on the USB serial
   monitor (`WiFi command ready: <ip>:23`) and pass it as `--host <ip>`.

Test sequence:

1. `Q` exits safely and restores BLE
2. Space sends stop
3. W lightly spins wheels / requests forward
4. S lightly requests backward
5. A / D request yaw
6. Release keys and confirm robot stops within 500 ms
7. Kill the keyboard script and confirm watchdog stops motion

### Phase F: Reuse for Vision

After keyboard WiFi control is stable:

```yaml
transport: tcp
tcp_host: <robot-ip>
tcp_port: 23
dry_run: true
```

Then test:

- `gesture` dry-run
- `face` dry-run
- `transport: tcp` with conservative commands

---

## 8. Safety Rules

- Keep `dry_run=true` for vision tests until keyboard WiFi control is stable
- Keep robot physically secured for first WiFi movement tests
- Keep physical power cutoff reachable
- Do not use `BALANCE_ON` repeatedly during bridge/keyboard testing
- Prefer testing `DRIVE,0,0`, `QUEUE_STOP`, `YAWRATE,0` before any movement
- Keep Xbox BLE as fallback, but remember BLE is ignored while queue commands are running

---

## 9. Hidden Issues Found in Existing Code

Audit of the current firmware (`src/wifi_cmd.cpp`, `src/serial.cpp`, `include/wifi_config.h`, `src/ble.cpp`) turned up the following pitfalls. They must be addressed alongside the Phase C `DRIVE` implementation.

### 9.1 Blocking WiFi connect with no timeout

`src/wifi_cmd.cpp:20` uses:

```c
while (WiFi.status() != WL_CONNECTED) { delay(500); ... }
```

If the SSID is wrong, the router is off, or signal is weak, `WiFiCmdTask` stalls silently forever. Add a retry-with-timeout loop that logs failure and re-attempts periodically, instead of an infinite block.

### 9.2 Disconnect watchdog does not stop `DRIVE`

`src/wifi_cmd.cpp:56-60` currently only injects `QUEUE_STOP` on client disconnect. Because `DRIVE` bypasses the queue and writes `target.speedCmd` / `target.yawSpeedCmd` directly, `QUEUE_STOP` will not stop a moving robot after a PC script crash.

On disconnect, also inject `DRIVE,0,0` and `YAWRATE,0` (or zero the direct targets), not just `QUEUE_STOP`.

### 9.3 Watchdog thresholds inconsistent with plan

`include/wifi_config.h:7` is `WIFI_WATCHDOG_MS 1500`, but Sections 5 and 6 above assume a 500 ms watchdog. Use a two-layer scheme:

- `DRIVE`-level watchdog: 500 ms (zero `target.speedCmd` / `yawSpeedCmd`)
- TCP-level watchdog: 1500 ms (disconnect + full stop)

Raise the PC send rate from 10 Hz to 20 Hz to avoid false trips from TCP jitter / OS scheduling.

### 9.4 Stale TCP client after PC-side crash

`WiFiServer` is single-client, no keepalive is set. After `kill -9` of the keyboard script, `sClient.connected()` can stay `true` for tens of seconds or more, rejecting new connections.

Set `sClient.setTimeout()` and either enable TCP keepalive on the underlying socket or add an "idle > N seconds → force close" path in `WiFiCmdTask`.

### 9.5 Open TCP:23 has no authentication

Anyone on the same LAN can send arbitrary commands including `BALANCE_ON`, `BLE_DISABLE`, jump queue sequences, etc. Acceptable on a trusted home router, unsafe on a shared/hotspot network.

At minimum add an IP allowlist, or a simple shared-secret handshake as the first line of each TCP session.

### 9.6 Concurrency between UART2, WiFi, and BLE writers

`Serial_HandleCommandLine` is called from both `UART2_CommandTask` (`src/serial.cpp:639`) and `WiFiCmdTask`. The queue itself has `queueMutex`, but direct writes to `target.speedCmd` / `target.yawSpeedCmd` (from `YAWRATE`, future `DRIVE`, and `ble.cpp`) are not mutex-protected.

Arbitration today relies on:

- BLE only writes when `sBleInputEnabled && !Serial_IsQueueBusy()`
- `DRIVE` / `YAWRATE` only write when queue is idle

This leaves a race between WiFi `DRIVE` and BLE. Enforce ordering in the PC script:

1. send `BLE_DISABLE` first
2. then `DRIVE,0,0`
3. only after both acknowledged, start streaming `DRIVE`

And on exit, reverse the order: `DRIVE,0,0` → `BLE_ENABLE`.

### 9.7 `DRIVE` without `BALANCE_ON` silently does nothing

`target.speedCmd` is only consumed by the balance controller when `balanceEnabled == true` and the robot has finished standup. Users following this plan can send `DRIVE` and see no motion, then reflexively `BALANCE_ON` and trigger an unexpected standup/jump.

Plan requirements:

- Bench test must explicitly `BALANCE_ON` (or trigger standup via Xbox A) **before** any `DRIVE`
- The keyboard script should print a warning if `BLE_STATUS` / `QUEUE_STATUS` responses suggest balance is off
- Never combine first-time `BALANCE_ON` with `DRIVE` streaming in the same session

### 9.8 2.4 GHz BLE + WiFi coexistence

ESP32 shares a single radio between BLE (Xbox) and WiFi (TCP). Heavy WiFi traffic degrades Xbox controller responsiveness and can cause BLE disconnects, which defeats the purpose of keeping BLE as a fallback.

Mitigations:

- Keep WiFi keyboard stream ≤ 20 Hz with short lines (`DRIVE,300,0\n` is ~13 bytes)
- Do not run the camera/MediaPipe bridge on the same robot ESP32 WiFi path at full rate during BLE-critical tests
- Prefer 5 GHz router band for the PC side to reduce channel contention (robot still uses 2.4 GHz)

### 9.9 IP discovery is serial-only

Robot IP is printed only on USB serial (`src/wifi_cmd.cpp:24`). After a reboot or DHCP lease change, the user must reopen the serial monitor.

Add mDNS (`ESPmDNS.h`) so the PC can reach `wheeleg.local:23` without knowing the address.

### 9.10 WiFi credentials in source

`include/wifi_config.h` holds plaintext SSID/password. Today it still contains `"CHANGE_ME"`. Before filling real credentials:

- Ensure `include/wifi_config.h` is in `.gitignore` (keep `wifi_config.example.h` tracked)
- Never commit a real credential file
- Consider loading from NVS or a build-time env var if this repo is shared

---

## 10. Minimum Fix Checklist (bundle with Phase C)

Firmware:

- [ ] `wifi_cmd.cpp`: non-blocking WiFi connect with retry/timeout
- [ ] `wifi_cmd.cpp`: on client disconnect, inject `DRIVE,0,0` + `YAWRATE,0` in addition to `QUEUE_STOP`
- [ ] `wifi_cmd.cpp`: stale-client idle-timeout close + `sClient.setTimeout()`
- [ ] `serial.cpp`: implement `DRIVE,<speed_milli>,<yaw_mrad>` with clamp + 500 ms watchdog (mirror `sLastYawRateMs` pattern at `src/serial.cpp:674-680`)
- [ ] `wifi_config.h`: keep TCP watchdog 1500 ms; document the two-layer scheme
- [ ] Optional: `ESPmDNS` advertise `wheeleg.local`
- [ ] `.gitignore`: exclude `include/wifi_config.h`

PC script (`host/tools/keyboard_drive.py`):

- [ ] 20 Hz send rate
- [ ] `atexit` + `SIGTERM` + `SIGINT` all send `DRIVE,0,0` → `YAWRATE,0` → `BLE_ENABLE`
- [ ] On start: `BLE_DISABLE` → wait → `DRIVE,0,0` → then stream
- [ ] Warn if the user forgot `BALANCE_ON`

Operational:

- [ ] Trusted LAN only, or add IP allowlist / shared secret
- [ ] BALANCE_ON done manually before first `DRIVE`
- [ ] Physical power cutoff within reach

---

## 11. Recommendation

Use both:

- Xbox BLE remains the normal human manual controller
- PC WiFi WASD is added as a test/control layer for ROS and future vision

Do not replace Bluetooth with WiFi immediately. Use WiFi to validate the PC-to-robot path, then reuse that path for camera/MediaPipe control.
