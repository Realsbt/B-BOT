# Appendix F: Software Repository Evidence

**Project:** B-BOT: A WiFi-enabled self-balancing wheel-legged robot with ROS 2 vision teleoperation  
**Repository:** https://github.com/Realsbt/B-BOT.git  
**Submission branch:** public `main` branch  
**Submitted commit:** `0e2114cfccb35874be668d403cf52bcf92e890e1` (`0e2114c`, V1)  
**Snapshot link:** https://github.com/Realsbt/B-BOT/tree/0e2114cfccb35874be668d403cf52bcf92e890e1  
**Submission version policy:** this commit is treated as the repository snapshot submitted for marking under the current assumption that the previous commit is the final submitted commit.

This appendix identifies the version-controlled software evidence for the project. It should be read with the repository `README.md`, `host/README_vision.md`, and the third-party attribution table in this appendix.

## Software Components

| Component | Repository path | Purpose |
| --- | --- | --- |
| ESP32 firmware | `src/`, `include/`, `platformio.ini` | Firmware for the self-designed ESP32 controller PCB, including FreeRTOS tasks, motor/IMU/CAN handling, balance control, command parsing and WiFi TCP command server |
| Generated control/kinematics support | `src/matlab_code/`, `include/matlab_code/` | MATLAB-generated leg kinematics, VMC conversion and LQR support functions used by the firmware |
| Host ROS 2 vision bridge | `host/ros2_ws/src/wheeleg_vision_bridge/` | ROS 2 Python package subscribing to the ROS 2 WiFi camera module image topic, running MediaPipe perception and encoding robot commands |
| Host utility tools | `host/tools/`, `host/scripts/` | WiFi keyboard control, camera preview/presentation monitor and camera micro-ROS agent quickstart script |
| Experiment and report evidence | `Report/appendices/E_data/`, `Report/figures/`, `Report/planning/` | Raw CSV logs, final measured data index, generated plots, Gantt evidence and experiment-planning records |
| Progress log | `Progress.md` | Chronological development notes, test records and decision log |

## Minimal Firmware Build

The firmware is a PlatformIO project for the self-designed ESP32 controller PCB:

```bash
pio run
```

Upload and monitor are normally run as:

```bash
pio run -t upload
pio device monitor
```

The PlatformIO configuration is `platformio.ini`. The selected environment is `esp32doit-devkit-v1` using the Arduino framework and `ENABLE_WIFI_CMD`. This environment is used as a compatible ESP32 Arduino build target for the custom PCB, not as evidence that a commercial ESP32 development board is the robot controller.

## Minimal Host-Side Build

The ROS 2 vision bridge is built inside the host workspace:

```bash
source /opt/ros/humble/setup.bash
cd host/ros2_ws
colcon build --packages-select wheeleg_vision_bridge
source install/setup.bash
```

The ROS 2 WiFi camera module image path expects:

```text
/espRos/esp32camera  sensor_msgs/msg/CompressedImage
```

The host-side bridge can be started in dry-run mode:

```bash
ros2 launch wheeleg_vision_bridge bridge.launch.py mode:=gesture dry_run:=true debug_window:=true
```

Live robot command transmission should only be enabled after bench validation:

```bash
ros2 param set /wheeleg_vision_bridge dry_run false
```

## Command and Safety Behaviour

The ESP32 command path accepts line-based WiFi TCP commands on port 23. The same parser is used by keyboard control, scripted tools and vision-generated commands.

Key safety mechanisms implemented in software:

- `DRIVE` and `YAWRATE` direct-command watchdogs.
- TCP idle timeout and full-stop injection on disconnect.
- `BLE_DISABLE` / `BLE_ENABLE` arbitration for Xbox controller input.
- Vision bridge `dry_run` default.
- `stunt_armed` gate for high-risk vision-triggered actions.

## Reproducibility Notes

The marked version is identified by the submitted commit hash above. This prevents the marker from relying only on a moving branch tip.

## Submission Checks

Before submission, the repository checks are:

- The public repository state submitted for marking is `main` at commit `0e2114cfccb35874be668d403cf52bcf92e890e1`.
- `README.md` explains the project, hardware, software, installation and run steps.
- `host/README_vision.md` explains the ROS 2 vision and camera preview workflow.
- Third-party code and libraries are listed in `Third Party Code and Software Attribution - B-BOT.md`.
- No private WiFi passwords or local-only secrets are exposed in tracked files. The tracked `include/wifi_config.h` contains `CHANGE_ME` placeholders, while `include/wifi_config.local.h` is ignored for local credentials.
- Generated build folders such as `.pio/`, `host/ros2_ws/build/`, `host/ros2_ws/install/` and `host/ros2_ws/log/` are excluded from the submitted evidence.
