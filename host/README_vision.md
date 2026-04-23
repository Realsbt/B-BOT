# Wheeleg Host Tools

Two host-side tools share the same `PC → WiFi TCP:23 → Robot ESP32` path:

1. `wheeleg_vision_bridge` — ROS 2 package, camera + MediaPipe → commands
2. `tools/keyboard_drive.py` — standalone WASD teleop over TCP

Both talk the same line protocol (`DRIVE`, `YAWRATE`, `BLE_DISABLE`, `JUMP`, ...).

---

## Addressing

The robot ESP32 advertises mDNS as `wheeleg.local` (port 23) once it joins WiFi.
All tools default to that hostname; fall back to the DHCP IP printed on the USB
serial monitor if mDNS is unavailable on your network.

---

## `tools/keyboard_drive.py` — WASD over WiFi

```bash
python3 /home/yahboom/Desktop/esp32-wheeleg-A-main/host/tools/keyboard_drive.py
# or, with an explicit host
python3 keyboard_drive.py --host 192.168.1.23 --rate 20
```

Keys:

| key | effect |
|-----|--------|
| `W` / `S` | toggle forward / backward |
| `A` / `D` | toggle left / right yaw |
| `1` / `2` / `3` | speed preset 150 / 250 / 350 mm/s |
| `space` | hard stop (`DRIVE,0,0` + `QUEUE_STOP`) |
| `H` | reprint help |
| `Q` | quit cleanly (re-enables Xbox BLE) |

On start the script sends `BLE_DISABLE` then `DRIVE,0,0`; on any exit path
(`atexit`, `SIGTERM`, `SIGHUP`, `Ctrl+C`) it sends `DRIVE,0,0` → `YAWRATE,0` →
`BLE_ENABLE`.

> `DRIVE` only moves the robot after balance is enabled. Trigger standup via the
> Xbox `A` button (or send `BALANCE_ON` on the USB serial console) **before**
> driving.

---

## Command protocol (shared)

Direct-teleop commands bypass the queue and need periodic re-sending:

```
DRIVE,<speed_mm_s>,<yaw_mrad_s>     direct teleop, 500 ms watchdog on robot
YAWRATE,<mrad_s>                    yaw-only direct, 500 ms watchdog
```

Queue commands run to completion:

```
FORWARD,<pct>,<sec>
BACKWARD,<pct>,<sec>
LEFT,<deg>,<sec>
RIGHT,<deg>,<sec>
JUMP
INCREASELEGLENGTH,<units>
DECREASELEGLENGTH,<units>
CROSSLEG,0,<sec>
QUEUE_STATUS / QUEUE_STOP / QUEUE_PAUSE / QUEUE_RESUME
```

Arbitration / safety:

```
BLE_DISABLE / BLE_ENABLE            enable/disable Xbox controller input
VISION_DISABLE / VISION_ENABLE      enable/disable all WiFi-side input
BALANCE_ON / BALANCE_OFF            caution: BALANCE_ON auto-triggers standup
```

Robot-side watchdogs:

- `DRIVE` target is zeroed if no new `DRIVE` for 500 ms
- `YAWRATE` target is zeroed if no new `YAWRATE` for 500 ms
- TCP client is force-closed if no line arrives for 1500 ms; on disconnect the
  robot injects `DRIVE,0,0 + YAWRATE,0 + QUEUE_STOP`

---

## `wheeleg_vision_bridge` — ROS 2 vision node

### Build

```bash
source /opt/ros/humble/setup.bash
cd /home/yahboom/Desktop/esp32-wheeleg-A-main/host/ros2_ws
colcon build --packages-select wheeleg_vision_bridge
source install/setup.bash
```

### Camera

Start the micro-ROS agent in a dedicated terminal:

```bash
/home/yahboom/Desktop/esp32-wheeleg-A-main/host/scripts/camera_quickstart.sh
```

Default image topic: `/espRos/esp32camera` (`sensor_msgs/CompressedImage`).

### Run

```bash
ros2 launch wheeleg_vision_bridge bridge.launch.py
```

The bridge starts in `idle` mode with `dry_run: true` — no commands are
transmitted. `transport: tcp` and `tcp_host: wheeleg.local` are the current
defaults (see `config/config.yaml`).

### Mode switching

```bash
ros2 param set /wheeleg_vision_bridge mode gesture
ros2 param set /wheeleg_vision_bridge mode stunt
ros2 param set /wheeleg_vision_bridge mode face
ros2 param set /wheeleg_vision_bridge mode idle
```

### Gesture mapping (DRIVE-based, continuous)

| gesture | command |
|---------|---------|
| fist (Zero) | `DRIVE,0,0` |
| open palm (Five) | `DRIVE,250,0` |
| point left | `DRIVE,0,600` |
| point right | `DRIVE,0,-600` |
| thumb up | `JUMP` (impulse, gated by `stunt_armed`? No — gesture sends JUMP directly) |

Gesture DRIVE commands are re-sent at `command_rate_hz` (default 10 Hz) so the
robot-side 500 ms watchdog is fed; losing the hand drops the target to
`DRIVE,0,0` immediately.

### Stunt safety gate

Stunt mode's `JUMP` and `CROSSLEG,0,5` are **blocked by default** to avoid
someone in the camera frame accidentally triggering acrobatics:

```bash
ros2 param set /wheeleg_vision_bridge stunt_armed true    # arm
ros2 param set /wheeleg_vision_bridge stunt_armed false   # disarm
```

### Going live

Disable dry-run only after bench validation:

```bash
ros2 param set /wheeleg_vision_bridge dry_run false
```

---

## Safety reminders

- Keep physical power accessible during bench tests
- Use `dry_run: true` until every mode has been individually verified
- `BALANCE_ON` triggers a standup action — never send it to an unsecured robot
- The robot's watchdog stops motion on disconnect, but a held physical stop is
  still the most reliable last line of defense
