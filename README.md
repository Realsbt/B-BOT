<a id="top"></a>

# B-BOT

<p align="center">
  <a href="#中文说明">
    <img src="https://img.shields.io/badge/中文-查看中文说明-blue?style=for-the-badge" alt="中文说明">
  </a>
  <a href="#english-readme">
    <img src="https://img.shields.io/badge/English-Read%20English%20README-green?style=for-the-badge" alt="English README">
  </a>
</p>

<a id="中文说明"></a>

## 中文说明

### 项目概述

B-BOT 是一个自研轮腿自平衡机器人控制项目。机器人机械平台和 ESP32 控制 PCB 为本项目自行设计；Yahboom 只作为 ROS 2 WiFi 摄像头模块来源。当前仓库包含 ESP32 固件、Xbox 蓝牙手柄控制、串口/队列命令系统、WiFi TCP 控制入口、PC 端 ROS 2 + MediaPipe 视觉桥，以及独立的 WASD WiFi 键盘控制工具。

这个项目当前推荐的视觉控制链路是：

```text
ROS 2 WiFi 摄像头模块
  -> WiFi + micro-ROS
  -> 电脑 ROS 2 图像话题 /espRos/esp32camera
  -> MediaPipe 视觉识别
  -> WiFi TCP :23
  -> ESP32 小车固件
```

摄像头只负责把图像发给电脑，真实控制指令由电脑直接通过 WiFi 发给小车，不依赖摄像头模块再转 UART。

### 当前控制架构

```text
Xbox 手柄
  -> BLE 蓝牙
  -> ESP32 小车固件

ROS 2 WiFi 摄像头模块
  -> WiFi + micro-ROS
  -> 电脑 ROS 2 / MediaPipe
  -> WiFi TCP :23
  -> ESP32 小车固件

电脑键盘
  -> host/tools/keyboard_drive.py
  -> WiFi TCP :23
  -> ESP32 小车固件

可选 UART 外设
  -> ESP32 UART2 RX/TX
  -> 同一个串口命令解析器
```

### 主要功能

- ESP32 + Arduino + PlatformIO 固件工程，当前默认启用 `ENABLE_WIFI_CMD`。
- FreeRTOS 多任务结构，包含 CAN 接收、电机下发、IMU 更新、控制主环、腿部位置更新、蓝牙输入、串口命令、WiFi TCP 命令等任务。
- 控制核心包含 LQR 平衡、PID 腿长/横滚/偏航控制、VMC 虚拟模型控制、触地检测、跳跃、起立、交叉腿动作。
- Xbox 蓝牙手柄仍然是主要人工控制方式，PC WiFi 控制和视觉控制作为扩展输入。
- WiFi TCP 指令服务默认使用 `wheeleg.local:23`，也可以使用机器人串口打印出的 DHCP IP。
- ROS 2 视觉桥支持 `idle`、`gesture`、`face`、`stunt` 模式，默认 `dry_run: true`，测试时只打印命令，不真实控制机器人。

### 程序结构

```text
.
├── platformio.ini
│   └── ESP32 PlatformIO 构建配置
├── src/
│   ├── main.cpp
│   │   └── 固件启动入口：Serial、WiFi、CAN、IMU、电机、腿部、控制、BLE
│   ├── ctrl.cpp
│   │   └── 平衡控制、LQR/PID/VMC、起立、跳跃、交叉腿动作
│   ├── serial.cpp
│   │   └── UART2 命令解析、队列命令、DRIVE/YAWRATE 实时控制
│   ├── wifi_cmd.cpp
│   │   └── WiFi TCP 服务、mDNS、掉线看门狗、命令注入
│   ├── ble.cpp
│   │   └── Xbox 手柄输入和输入仲裁
│   ├── can.cpp / motor.cpp / imu.cpp / legs.cpp / adc.cpp / pid.cpp
│   │   └── 硬件驱动和控制支撑代码
│   └── matlab_code/
│       └── MATLAB 生成的腿部运动学和 LQR 辅助代码
├── include/
│   ├── wifi_config.example.h
│   │   └── 本地 WiFi 配置模板
│   ├── wifi_cmd.h / serial.h / ctrl.h / ble.h / ...
│   │   └── 固件头文件
│   └── matlab_code/
│       └── MATLAB 生成代码的头文件
├── host/
│   ├── tools/keyboard_drive.py
│   │   └── PC 端 WASD WiFi 键盘控制工具
│   ├── scripts/camera_quickstart.sh
│   │   └── 启动本地或 Docker micro-ROS Agent
│   ├── README_vision.md
│   │   └── 电脑端视觉桥和键盘控制详细说明
│   └── ros2_ws/src/wheeleg_vision_bridge/
│       ├── wheeleg_vision_bridge/bridge_node.py
│       │   └── ROS 2 节点：摄像头图像 -> MediaPipe -> 小车命令
│       ├── wheeleg_vision_bridge/mediapipe_runner.py
│       │   └── 手势、人体姿态、人脸检测
│       ├── wheeleg_vision_bridge/command_encoder.py
│       │   └── 视觉事件到小车命令的映射
│       ├── wheeleg_vision_bridge/transport.py
│       │   └── UART 和 TCP 命令传输
│       ├── config/config.yaml
│       │   └── 视觉桥默认参数
│       └── launch/bridge.launch.py
│           └── ROS 2 launch 入口
├── lib/NimBLE-Arduino/
│   └── Xbox 蓝牙手柄使用的第三方 BLE 库
├── Progress.md
│   └── 开发进度、测试记录、当前任务记录
├── introduction.md
│   └── 面向导师/答辩的中文项目介绍
├── yahboom-camera-ros2-guide.md
├── yahboom-wifi-mediapipe-plan.md
└── pc-wifi-keyboard-control-plan.md
```

`include/wifi_config.h` 是本地 WiFi 密码配置文件，已经被 `.gitignore` 排除，不应该提交到 GitHub。

### 硬件组成

- 自研 ESP32 控制 PCB；PlatformIO 使用 `esp32doit-devkit-v1` 作为兼容 ESP32 Arduino 构建目标。
- MPU6050 IMU，用于姿态角和角速度。
- 6 个电机接口：4 个腿部关节电机 + 2 个轮电机，通过 CAN 总线通信。
- ADS1115/ADC 电压检测，用于电池电压监测和输出补偿。
- 额外拓展接口和电源管理电路位于自研控制 PCB 上。
- Xbox 蓝牙手柄，用作主要人工遥控器。
- Yahboom ROS 2 WiFi 摄像头模块，用于把图像通过 micro-ROS 发布到电脑。

### 软件环境

固件端：

- PlatformIO
- ESP32 Arduino framework
- `platformio.ini` 中的依赖：
  - `electroniccats/MPU6050`
  - `adafruit/Adafruit ADS1X15`
  - `SPI`
  - `lib/NimBLE-Arduino`

电脑端：

- Ubuntu / ROS 2 Humble
- `micro_ros_agent`
- Python 3
- ROS 2 包：`rclpy`、`sensor_msgs`、`std_msgs`、`cv_bridge`、`launch`、`launch_ros`
- Python 视觉包：OpenCV、MediaPipe、NumPy
- 可选 Docker：`host/scripts/camera_quickstart.sh` 在找不到本地 `micro_ros_agent` 时会尝试使用 Docker

### 固件配置与编译

1. 配置本地 WiFi：

```bash
cp include/wifi_config.example.h include/wifi_config.h
```

编辑 `include/wifi_config.h`：

```c
#define WIFI_SSID "your-wifi-ssid"
#define WIFI_PASS "your-wifi-password"
#define WIFI_TCP_PORT 23
#define WIFI_WATCHDOG_MS 1500
```

2. 编译固件：

```bash
pio run
```

3. 烧录固件：

```bash
pio run -t upload
```

4. 打开串口监视器：

```bash
pio device monitor
```

机器人连上 WiFi 后会打印 IP，并尝试注册 `wheeleg.local:23`。如果电脑不能解析 mDNS，就使用串口打印出的 IP。

### 电脑端快速启动

启动摄像头 micro-ROS Agent：

```bash
host/scripts/camera_quickstart.sh
```

期望摄像头话题：

```bash
/espRos/esp32camera  sensor_msgs/msg/CompressedImage
```

本地实测记录：

- 摄像头发布 JPEG 压缩图像。
- 测试帧为 `320x240`。
- 图像频率约 `5.6 Hz`。

编译 ROS 2 视觉桥：

```bash
source /opt/ros/humble/setup.bash
cd host/ros2_ws
colcon build --packages-select wheeleg_vision_bridge
source install/setup.bash
```

以 dry-run 模式运行视觉桥：

```bash
ros2 launch wheeleg_vision_bridge bridge.launch.py
```

默认参数在 `host/ros2_ws/src/wheeleg_vision_bridge/config/config.yaml`。当前默认值是 `mode: idle`、`dry_run: true`、`transport: tcp`、`tcp_host: wheeleg.local`。dry-run 只打印命令，不向机器人发送真实控制。

切换模式：

```bash
ros2 param set /wheeleg_vision_bridge mode gesture
ros2 param set /wheeleg_vision_bridge mode face
ros2 param set /wheeleg_vision_bridge mode stunt
ros2 param set /wheeleg_vision_bridge mode idle
```

台架验证通过后再关闭 dry-run：

```bash
ros2 param set /wheeleg_vision_bridge dry_run false
```

### 视觉模式

| 模式 | 输入 | 输出 |
|---|---|---|
| `idle` | 不处理图像 | 只发布状态 |
| `gesture` | MediaPipe Hands 手势识别 | 连续 `DRIVE` 命令 + 可选 `JUMP` |
| `face` | MediaPipe Face Detection 人脸检测 | `YAWRATE,<mrad_s>` 跟随转向命令 |
| `stunt` | MediaPipe Pose 人体姿态识别 | `JUMP`、`CROSSLEG`、腿长变化等队列动作 |

手势映射：

| 手势 | 标签 | 命令 |
|---|---|---|
| 握拳 | `Zero` | `DRIVE,0,0` |
| 张掌 | `Five` | `DRIVE,250,0` |
| 向左指 | `PointLeft` | `DRIVE,0,600` |
| 向右指 | `PointRight` | `DRIVE,0,-600` |
| 点赞 | `Thumb_up` | `JUMP` |

`gesture` 模式会周期性重发 `DRIVE`，喂机器人端 500 ms 看门狗；手从画面中消失时会立即改为 `DRIVE,0,0`。

`stunt` 模式默认不允许 `JUMP` 和 `CROSSLEG,0,5` 真实发送，必须手动设置 `stunt_armed=true`：

```bash
ros2 param set /wheeleg_vision_bridge stunt_armed true
ros2 param set /wheeleg_vision_bridge stunt_armed false
```

### WiFi 键盘控制

使用 mDNS：

```bash
python3 host/tools/keyboard_drive.py
```

使用机器人 IP：

```bash
python3 host/tools/keyboard_drive.py --host 192.168.1.23 --rate 20
```

按键：

| 按键 | 动作 |
|---|---|
| `W` / `S` | 前进 / 后退 |
| `A` / `D` | 左转 / 右转 |
| `1` / `2` / `3` | 速度预设 150 / 250 / 350 mm/s |
| `Space` | 硬停止：`DRIVE,0,0` + `QUEUE_STOP` |
| `H` | 打印帮助 |
| `Q` | 退出并恢复蓝牙输入 |

脚本启动时会发送 `BLE_DISABLE`，退出时会发送 `DRIVE,0,0 -> YAWRATE,0 -> BLE_ENABLE`，避免 PC 控制和 Xbox 手柄抢同一个目标量。

### 指令协议

实时直通控制：

```text
DRIVE,<speed_mm_s>,<yaw_mrad_s>
YAWRATE,<mrad_s>
```

`DRIVE` 和 `YAWRATE` 绕过队列，适合键盘/视觉这种需要连续刷新的控制。机器人端 500 ms 内没有收到新命令会自动归零。

队列动作：

```text
FORWARD,<percent>,<seconds>
BACKWARD,<percent>,<seconds>
LEFT,<degrees>,<seconds>
RIGHT,<degrees>,<seconds>
STOP
JUMP
STANDUP
CROSSLEG,0,<seconds>
INCREASELEGLENGTH,<units>
DECREASELEGLENGTH,<units>
```

队列控制：

```text
QUEUE_START
QUEUE_PAUSE
QUEUE_RESUME
QUEUE_STOP
QUEUE_STATUS
```

安全与输入仲裁：

```text
BALANCE_ON
BALANCE_OFF
BLE_DISABLE
BLE_ENABLE
BLE_STATUS
VISION_DISABLE
VISION_ENABLE
```

队列运行或暂停时，BLE 和实时 yaw/drive 输入会被抑制，防止脚本动作和手柄动作互相覆盖。

### 已验证内容

主要验证记录保存在 `Progress.md`，关键结果包括：

- `pio run` 固件编译通过。
- `colcon build --packages-select wheeleg_vision_bridge` 通过。
- Python `compileall` 对视觉桥代码通过。
- micro-ROS Agent 能接入 WiFi 摄像头。
- `/espRos/esp32camera` 能收到 `sensor_msgs/msg/CompressedImage`。
- 视觉桥 dry-run 能启动，`face` 模式能输出 `YAWRATE,0` 类命令。
- `gesture` 模式已实测张掌能输出 `DRIVE,250,0`；握拳识别还需要继续实机微调。

### 安全注意事项

- 第一次测试必须保持 `dry_run: true`，确认日志输出正确后再关闭。
- `BALANCE_ON` 会触发起立准备动作，机器人没有固定或周围不安全时不要发送。
- 键盘/视觉控制前，确认机器人已经进入平衡状态，否则 `DRIVE` 可能没有运动效果。
- WiFi 断开、TCP 客户端掉线或命令超时会触发停止逻辑，但物理断电/急停仍然是最后保险。
- 不要把真实 WiFi 密码提交到 GitHub；只提交 `include/wifi_config.example.h`。

### 更多文档

- `Progress.md`：开发进度、测试记录、已完成修改。
- `host/README_vision.md`：电脑端视觉桥和键盘控制的详细说明。
- `yahboom-camera-ros2-guide.md`：Yahboom WiFi 摄像头 + ROS 2 启动说明。
- `yahboom-wifi-mediapipe-plan.md`：WiFi 摄像头 + MediaPipe 视觉控制计划。
- `pc-wifi-keyboard-control-plan.md`：PC WiFi 键盘控制方案。
- `introduction.md`：面向导师/答辩的中文项目介绍。

### 项目状态

当前项目已经完成 GitHub 初始同步、固件编译验证、摄像头 ROS 2 图像链路验证、视觉桥 dry-run 验证、PC WiFi 键盘控制方案和工具落地。下一步更适合继续做实机台架验证：先 `dry_run` 手势/人脸，再验证 PC WiFi 控制，最后才关闭 `dry_run` 上机器人。

### 许可证

本仓库包含本项目自研机器人控制代码和第三方组件/库。Yahboom 相关部分仅用于 ROS 2 WiFi 摄像头模块；同时仓库包含第三方 vendored `NimBLE-Arduino` 库。请分别遵守摄像头模块、第三方库和相关工具链的许可证要求。当前自定义部分尚未单独整理许可证文件。

<p align="right"><a href="#top">返回顶部</a></p>

<a id="english-readme"></a>

## English README

### Overview

B-BOT is a self-designed wheel-legged self-balancing robot control project. The robot mechanical platform and ESP32 controller PCB were designed for this project; Yahboom is used only as the source of the separate ROS 2 WiFi camera module. This repository includes the ESP32 firmware, Xbox BLE controller support, UART/queue command handling, WiFi TCP command input, a PC-side ROS 2 + MediaPipe vision bridge, and a standalone WASD WiFi teleoperation tool.

The recommended vision-control path is:

```text
ROS 2 WiFi camera module
  -> WiFi + micro-ROS
  -> PC ROS 2 image topic /espRos/esp32camera
  -> MediaPipe vision processing
  -> WiFi TCP :23
  -> ESP32 robot firmware
```

The camera only streams images to the PC. Final control commands are sent directly from the PC to the robot over WiFi, without relying on the camera module to relay UART commands.

### Current Architecture

```text
Xbox controller
  -> BLE
  -> ESP32 robot firmware

ROS 2 WiFi camera module
  -> WiFi + micro-ROS
  -> PC ROS 2 / MediaPipe
  -> WiFi TCP :23
  -> ESP32 robot firmware

PC keyboard
  -> host/tools/keyboard_drive.py
  -> WiFi TCP :23
  -> ESP32 robot firmware

Optional UART device
  -> ESP32 UART2 RX/TX
  -> same serial command parser
```

### Main Features

- ESP32 + Arduino + PlatformIO firmware project, with `ENABLE_WIFI_CMD` enabled by default.
- FreeRTOS task-based firmware with CAN receive, motor output, IMU update, control loop, leg position update, BLE input, UART command, and WiFi TCP command tasks.
- Control stack with LQR balancing, PID leg length/roll/yaw control, VMC virtual model control, ground contact detection, jump, standup, and cross-leg actions.
- Xbox BLE remains the primary manual controller. PC WiFi control and vision control are extension inputs.
- The WiFi TCP command server defaults to `wheeleg.local:23`; the DHCP IP printed on the serial monitor can be used as a fallback.
- The ROS 2 vision bridge supports `idle`, `gesture`, `face`, and `stunt` modes. It defaults to `dry_run: true`, so tests log commands without driving the robot.

### Repository Structure

```text
.
├── platformio.ini
│   └── ESP32 PlatformIO build configuration
├── src/
│   ├── main.cpp
│   │   └── firmware startup: Serial, WiFi, CAN, IMU, motors, legs, control, BLE
│   ├── ctrl.cpp
│   │   └── balance control, LQR/PID/VMC, standup, jump, cross-leg behavior
│   ├── serial.cpp
│   │   └── UART2 command parser, queue commands, DRIVE/YAWRATE direct control
│   ├── wifi_cmd.cpp
│   │   └── WiFi TCP server, mDNS, disconnect watchdog, command injection
│   ├── ble.cpp
│   │   └── Xbox controller input and input arbitration
│   ├── can.cpp / motor.cpp / imu.cpp / legs.cpp / adc.cpp / pid.cpp
│   │   └── hardware drivers and control support code
│   └── matlab_code/
│       └── generated leg kinematics and LQR helper code
├── include/
│   ├── wifi_config.example.h
│   │   └── template for local WiFi credentials
│   ├── wifi_cmd.h / serial.h / ctrl.h / ble.h / ...
│   │   └── firmware headers
│   └── matlab_code/
│       └── generated math headers
├── host/
│   ├── tools/keyboard_drive.py
│   │   └── standalone PC WASD teleop over WiFi TCP
│   ├── scripts/camera_quickstart.sh
│   │   └── starts native or Docker micro-ROS Agent
│   ├── README_vision.md
│   │   └── detailed host-side vision and keyboard control notes
│   └── ros2_ws/src/wheeleg_vision_bridge/
│       ├── wheeleg_vision_bridge/bridge_node.py
│       │   └── ROS 2 node: camera image -> MediaPipe -> robot command
│       ├── wheeleg_vision_bridge/mediapipe_runner.py
│       │   └── hand, pose, and face detection
│       ├── wheeleg_vision_bridge/command_encoder.py
│       │   └── vision event to robot command mapping
│       ├── wheeleg_vision_bridge/transport.py
│       │   └── UART and TCP command transports
│       ├── config/config.yaml
│       │   └── default bridge parameters
│       └── launch/bridge.launch.py
│           └── ROS 2 launch entry
├── lib/NimBLE-Arduino/
│   └── vendored BLE library used by the Xbox controller code
├── Progress.md
│   └── development log, validation notes, and current task progress
├── introduction.md
│   └── Chinese project introduction for presentation/mentor review
├── yahboom-camera-ros2-guide.md
├── yahboom-wifi-mediapipe-plan.md
└── pc-wifi-keyboard-control-plan.md
```

`include/wifi_config.h` is the local WiFi credential file. It is ignored by `.gitignore` and should not be committed to GitHub.

### Hardware

- Self-designed ESP32 controller PCB; PlatformIO uses `esp32doit-devkit-v1` as a compatible ESP32 Arduino build target.
- MPU6050 IMU for attitude and angular velocity.
- Six motor interfaces: four leg joint motors and two wheel motors, communicating over CAN.
- ADS1115/ADC voltage sensing for battery monitoring and output compensation.
- Expansion interface and power-management circuitry on the custom controller PCB.
- Xbox BLE controller as the primary manual controller.
- Yahboom ROS 2 WiFi camera module for publishing images to the PC through micro-ROS.

### Software Requirements

Firmware side:

- PlatformIO
- ESP32 Arduino framework
- Dependencies from `platformio.ini`:
  - `electroniccats/MPU6050`
  - `adafruit/Adafruit ADS1X15`
  - `SPI`
  - `lib/NimBLE-Arduino`

Host side:

- Ubuntu / ROS 2 Humble
- `micro_ros_agent`
- Python 3
- ROS 2 packages: `rclpy`, `sensor_msgs`, `std_msgs`, `cv_bridge`, `launch`, `launch_ros`
- Python vision packages: OpenCV, MediaPipe, NumPy
- Optional Docker fallback: `host/scripts/camera_quickstart.sh` tries Docker if native `micro_ros_agent` is unavailable

### Firmware Setup

1. Configure local WiFi credentials:

```bash
cp include/wifi_config.example.h include/wifi_config.h
```

Edit `include/wifi_config.h`:

```c
#define WIFI_SSID "your-wifi-ssid"
#define WIFI_PASS "your-wifi-password"
#define WIFI_TCP_PORT 23
#define WIFI_WATCHDOG_MS 1500
```

2. Build firmware:

```bash
pio run
```

3. Upload firmware:

```bash
pio run -t upload
```

4. Open serial monitor:

```bash
pio device monitor
```

After the robot joins WiFi, it prints its IP address and advertises `wheeleg.local:23`. If mDNS does not work on your network, use the printed IP address.

### Host Quick Start

Start the camera micro-ROS Agent:

```bash
host/scripts/camera_quickstart.sh
```

Expected camera topic:

```bash
/espRos/esp32camera  sensor_msgs/msg/CompressedImage
```

Observed local validation:

- The camera published JPEG compressed images.
- The observed test frame was `320x240`.
- The observed image rate was about `5.6 Hz`.

Build the ROS 2 vision bridge:

```bash
source /opt/ros/humble/setup.bash
cd host/ros2_ws
colcon build --packages-select wheeleg_vision_bridge
source install/setup.bash
```

Run the bridge in dry-run mode:

```bash
ros2 launch wheeleg_vision_bridge bridge.launch.py
```

Default parameters live in `host/ros2_ws/src/wheeleg_vision_bridge/config/config.yaml`. Current defaults are `mode: idle`, `dry_run: true`, `transport: tcp`, and `tcp_host: wheeleg.local`. Dry-run logs commands only; it does not send real robot control.

Switch modes:

```bash
ros2 param set /wheeleg_vision_bridge mode gesture
ros2 param set /wheeleg_vision_bridge mode face
ros2 param set /wheeleg_vision_bridge mode stunt
ros2 param set /wheeleg_vision_bridge mode idle
```

Disable dry-run only after bench validation:

```bash
ros2 param set /wheeleg_vision_bridge dry_run false
```

### Vision Modes

| Mode | Input | Output |
|---|---|---|
| `idle` | no image processing | status only |
| `gesture` | MediaPipe Hands | continuous `DRIVE` commands + optional `JUMP` |
| `face` | MediaPipe Face Detection | `YAWRATE,<mrad_s>` yaw-follow command |
| `stunt` | MediaPipe Pose | queue actions such as `JUMP`, `CROSSLEG`, and leg-length changes |

Gesture mapping:

| Gesture | Label | Command |
|---|---|---|
| fist | `Zero` | `DRIVE,0,0` |
| open palm | `Five` | `DRIVE,250,0` |
| point left | `PointLeft` | `DRIVE,0,600` |
| point right | `PointRight` | `DRIVE,0,-600` |
| thumb up | `Thumb_up` | `JUMP` |

`gesture` mode periodically re-sends `DRIVE` to feed the robot-side 500 ms watchdog. If the hand disappears from the frame, it immediately falls back to `DRIVE,0,0`.

In `stunt` mode, `JUMP` and `CROSSLEG,0,5` are blocked by default. They require `stunt_armed=true`:

```bash
ros2 param set /wheeleg_vision_bridge stunt_armed true
ros2 param set /wheeleg_vision_bridge stunt_armed false
```

### Keyboard WiFi Teleop

Run with mDNS:

```bash
python3 host/tools/keyboard_drive.py
```

Run with explicit robot IP:

```bash
python3 host/tools/keyboard_drive.py --host 192.168.1.23 --rate 20
```

Keys:

| Key | Action |
|---|---|
| `W` / `S` | forward / backward |
| `A` / `D` | turn left / right |
| `1` / `2` / `3` | speed preset 150 / 250 / 350 mm/s |
| `Space` | hard stop: `DRIVE,0,0` + `QUEUE_STOP` |
| `H` | print help |
| `Q` | quit cleanly and re-enable BLE |

The script sends `BLE_DISABLE` on start and `DRIVE,0,0 -> YAWRATE,0 -> BLE_ENABLE` on exit, so PC teleop and Xbox BLE do not fight over the same motion targets.

### Command Protocol

Direct teleop commands:

```text
DRIVE,<speed_mm_s>,<yaw_mrad_s>
YAWRATE,<mrad_s>
```

`DRIVE` and `YAWRATE` bypass the queue and are intended for continuously refreshed keyboard/vision control. If no fresh command arrives within 500 ms, the robot zeros the direct target.

Queue commands:

```text
FORWARD,<percent>,<seconds>
BACKWARD,<percent>,<seconds>
LEFT,<degrees>,<seconds>
RIGHT,<degrees>,<seconds>
STOP
JUMP
STANDUP
CROSSLEG,0,<seconds>
INCREASELEGLENGTH,<units>
DECREASELEGLENGTH,<units>
```

Queue control:

```text
QUEUE_START
QUEUE_PAUSE
QUEUE_RESUME
QUEUE_STOP
QUEUE_STATUS
```

Safety and arbitration:

```text
BALANCE_ON
BALANCE_OFF
BLE_DISABLE
BLE_ENABLE
BLE_STATUS
VISION_DISABLE
VISION_ENABLE
```

When the queue is running or paused, BLE and direct yaw/drive input are suppressed to prevent scripted actions and manual input from overwriting each other.

### Validation Notes

The main validation log is in `Progress.md`. Key results include:

- Firmware build passed with `pio run`.
- ROS 2 bridge build passed with `colcon build --packages-select wheeleg_vision_bridge`.
- Python `compileall` passed for the vision bridge package.
- The micro-ROS Agent connected to the WiFi camera.
- `/espRos/esp32camera` published `sensor_msgs/msg/CompressedImage`.
- The bridge starts in dry-run mode, and `face` mode can emit commands such as `YAWRATE,0`.
- In `gesture` mode, open palm produced `DRIVE,250,0`; fist recognition still needs more physical tuning.

### Safety Notes

- Keep `dry_run: true` for first tests. Disable it only after logs are correct.
- `BALANCE_ON` triggers standup preparation. Do not send it unless the robot is physically safe.
- Before keyboard or vision control, confirm the robot is already balanced; otherwise `DRIVE` may have no visible effect.
- WiFi disconnect, TCP client drop, and command timeout trigger stop logic, but a physical power cutoff or emergency stop remains the final safety layer.
- Do not commit real WiFi credentials to GitHub; only commit `include/wifi_config.example.h`.

### More Documentation

- `Progress.md`: development log, validation notes, and completed changes.
- `host/README_vision.md`: detailed host-side vision bridge and keyboard control notes.
- `yahboom-camera-ros2-guide.md`: Yahboom WiFi camera + ROS 2 startup notes.
- `yahboom-wifi-mediapipe-plan.md`: WiFi camera + MediaPipe vision-control plan.
- `pc-wifi-keyboard-control-plan.md`: PC WiFi keyboard-control plan.
- `introduction.md`: Chinese presentation/mentor-review introduction.

### Project Status

The project has completed initial GitHub sync, firmware build validation, camera ROS 2 image-link validation, vision bridge dry-run validation, and the PC WiFi keyboard control plan/tooling. The next practical step is bench validation: dry-run gestures/face first, then PC WiFi control, and only then disable `dry_run` on the robot.

### License

This repository contains original robot-control work plus third-party components and libraries. Yahboom-related material is limited to the ROS 2 WiFi camera module; the repository also includes the third-party vendored `NimBLE-Arduino` library. Follow the license requirements of the camera module, third-party libraries and related toolchains. A separate license file for the custom additions has not been finalized yet.

<p align="right"><a href="#top">Back to top</a></p>
