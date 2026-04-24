# E7 Camera Topic Bring-Up Evidence

This folder records the camera-topic bring-up evidence used by the report's camera and vision section.

The ROS 2 WiFi camera module publishes compressed images to the host ROS 2 graph. The expected topic is:

```text
/espRos/esp32camera  sensor_msgs/msg/CompressedImage
```

Measured bring-up notes are currently recorded in `Report/planning/Experiment_Data_Collection.md` and in the later E10/E11 datasets:

| Evidence | Status | Location |
| --- | --- | --- |
| Camera micro-ROS agent connection | measured | `Report/planning/Experiment_Data_Collection.md`, B0.1 |
| Camera topic format | measured as JPEG compressed image | `Report/workspace/report_draft.md`, Table 4.10; E11 notes |
| Camera topic rate during initial tests | measured around 5.6-6.1 Hz over short windows | `Report/planning/Experiment_Data_Collection.md`, B0.4/B0.9 |
| Camera reconnect retest | measured around 4.07 Hz after reconnect | `Report/planning/Experiment_Data_Collection.md`, B0.18 |
| Camera rate during E11 vision-to-ESP32 test | measured around 4.85 Hz | `Report/appendices/E_data/E11_vision_to_esp32_latency/README.md` |
| Camera smoke CSV | measured | `Report/appendices/E_data/E10_vision_confusion/camera_smoke_2026-04-24.csv` |

E7 is treated as bring-up and path validation evidence rather than a separate performance claim. The stronger quantitative vision evidence is stored under E10 and E11.
