# Appendix F: Software Repository Evidence

**Project:** B-BOT: A WiFi-enabled self-balancing wheel-legged robot with ROS 2 vision teleoperation  
**Repository:** https://github.com/Realsbt/B-BOT.git  
**Branch used during report preparation:** `main`  
**Audited local base commit at time of this report build:** `68e40b4`  
**Submission version policy:** the submitted repository should be frozen at the final report commit or tagged release that contains the final PDF and evidence folders.  

This appendix identifies the version-controlled software evidence for the project. It should be read with the repository `README.md`, `host/README_vision.md`, and the third-party attribution table in this appendix.

## Software Components

| Component | Repository path | Purpose |
| --- | --- | --- |
| ESP32 firmware | `src/`, `include/`, `platformio.ini` | Embedded controller, FreeRTOS tasks, motor/IMU/CAN handling, balance control, command parsing and WiFi TCP command server |
| Generated control/kinematics support | `src/matlab_code/`, `include/matlab_code/` | MATLAB-generated leg kinematics, VMC conversion and LQR support functions used by the firmware |
| Host ROS 2 vision bridge | `host/ros2_ws/src/wheeleg_vision_bridge/` | ROS 2 Python package subscribing to the ROS 2 WiFi camera module image topic, running MediaPipe perception and encoding robot commands |
| Host utility tools | `host/tools/`, `host/scripts/` | WiFi keyboard control, camera preview/presentation monitor and camera micro-ROS agent quickstart script |
| Experiment and report evidence | `Report/appendices/E_data/`, `Report/figures/`, `Report/planning/` | Raw CSV logs, provisional data policy, generated plots, Gantt evidence and experiment plans |
| Progress log | `Progress.md` | Chronological development notes, test records and decision log |

## Minimal Firmware Build

The firmware is a PlatformIO project targeting an ESP32 development board:

```bash
pio run
```

Upload and monitor are normally run as:

```bash
pio run -t upload
pio device monitor
```

The PlatformIO configuration is `platformio.ini`. The selected environment is `esp32doit-devkit-v1` using the Arduino framework and `ENABLE_WIFI_CMD`.

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

The repository should be frozen at submission using either a final commit hash or a release tag. At the time this appendix was prepared, the audited local base commit was:

`68e40b4`

The final submitted repository state will be the commit or release that contains the completed report PDF, appendix evidence and final data updates. Recording the final state prevents the marker from inspecting a moving branch tip.

## Submission Checks

Before the repository is made public or submitted, perform this checklist:

- Confirm the final commit or release tag is recorded here and in the report appendix.
- Confirm `README.md` explains the project, hardware, software, installation and run steps.
- Confirm `host/README_vision.md` explains the ROS 2 vision and camera preview workflow.
- Confirm third-party code and libraries are listed in `Third Party Code and Software Attribution - B-BOT.md`.
- Confirm no private WiFi passwords or local-only secrets are exposed in tracked files. At the time of this appendix draft, `include/wifi_config.h` is a tracked placeholder-style config and `include/wifi_config.local.h` is local-only, but this must be rechecked before the repository is made public.
- Confirm generated build folders such as `.pio/`, `host/ros2_ws/build/`, `host/ros2_ws/install/` and `host/ros2_ws/log/` are not submitted as evidence.
