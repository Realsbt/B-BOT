# B-BOT ESP32 Wheel-Leg Robot / B-BOT ESP32 轮腿机器人

> 中文：这是一个基于 Yahboom ESP32 轮腿平衡小车改造的机器人控制项目。当前仓库包含 ESP32 固件、Xbox 蓝牙手柄控制、串口/队列命令系统、WiFi TCP 控制入口、PC 端 ROS 2 + MediaPipe 视觉桥，以及独立的 WASD WiFi 键盘控制工具。
>
> English: This project is a modified Yahboom ESP32 wheel-leg balancing robot workspace. It includes the ESP32 firmware, Xbox BLE control, UART/queue command handling, WiFi TCP command input, a PC-side ROS 2 + MediaPipe vision bridge, and a standalone WASD WiFi teleoperation tool.

## Current Architecture / 当前架构

```text
Xbox controller
  -> BLE
  -> ESP32 robot firmware

Yahboom WiFi camera module
  -> WiFi + micro-ROS
  -> PC ROS 2 image topic /espRos/esp32camera
  -> MediaPipe vision bridge
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

中文：目前推荐的扩展控制链路是 `摄像头 -> WiFi -> 电脑 ROS 2/MediaPipe -> WiFi -> 小车 ESP32`。摄像头只负责把图像发到电脑，真实控制指令由电脑直接通过 WiFi TCP 发给机器人，不依赖摄像头模块再转 UART。

English: The recommended extension path is `camera -> WiFi -> PC ROS 2/MediaPipe -> WiFi -> robot ESP32`. The camera only streams images to the PC. Final control commands are sent from the PC directly to the robot over WiFi TCP, without relying on the camera module to relay UART commands.

## Main Features / 主要功能

- 中文：ESP32 + Arduino + PlatformIO 固件工程，默认启用 `ENABLE_WIFI_CMD`。
- English: ESP32 + Arduino + PlatformIO firmware project, with `ENABLE_WIFI_CMD` enabled by default.

- 中文：FreeRTOS 多任务结构，包含 CAN 接收、电机下发、IMU 更新、控制主环、腿部位置更新、蓝牙输入、串口命令、WiFi TCP 命令等任务。
- English: FreeRTOS task-based firmware with CAN receive, motor output, IMU update, control loop, leg position update, BLE input, UART command, and WiFi TCP command tasks.

- 中文：控制核心包含 LQR 平衡、PID 腿长/横滚/偏航控制、VMC 虚拟模型控制、触地检测、跳跃/起立/交叉腿动作。
- English: The control stack includes LQR balancing, PID leg length/roll/yaw control, VMC virtual model control, ground contact detection, jump, standup, and cross-leg actions.

- 中文：Xbox 蓝牙手柄仍然是主要人工控制方式，PC WiFi 控制和视觉控制作为扩展输入。
- English: Xbox BLE remains the primary manual controller. PC WiFi control and vision control are extension inputs.

- 中文：WiFi TCP 指令服务默认使用 `wheeleg.local:23`，也可以使用机器人串口打印出来的 DHCP IP。
- English: The WiFi TCP command server defaults to `wheeleg.local:23`; the DHCP IP printed on the robot serial monitor can be used as a fallback.

- 中文：ROS 2 视觉桥支持 `idle`、`gesture`、`face`、`stunt` 模式，默认 `dry_run: true`，测试时只打印命令，不真实控制机器人。
- English: The ROS 2 vision bridge supports `idle`, `gesture`, `face`, and `stunt` modes. It defaults to `dry_run: true`, so tests log commands without driving the robot.

## Repository Structure / 程序结构

```text
.
├── platformio.ini
│   └── ESP32 PlatformIO build configuration / ESP32 固件构建配置
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
│   │   └── starts native or Docker micro-ROS agent for the WiFi camera
│   ├── README_vision.md
│   │   └── detailed host-side vision and keyboard control notes
│   └── ros2_ws/src/wheeleg_vision_bridge/
│       ├── wheeleg_vision_bridge/bridge_node.py
│       │   └── ROS 2 node: camera topic -> MediaPipe -> robot command
│       ├── wheeleg_vision_bridge/mediapipe_runner.py
│       │   └── hand, pose, and face detection
│       ├── wheeleg_vision_bridge/command_encoder.py
│       │   └── gesture/face/stunt event to command mapping
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

中文：`include/wifi_config.h` 是本地 WiFi 密码配置文件，已经被 `.gitignore` 排除，不应该提交到 GitHub。

English: `include/wifi_config.h` is the local WiFi credential file. It is ignored by `.gitignore` and should not be committed to GitHub.

## Hardware / 硬件组成

- 中文：ESP32 开发板，PlatformIO 配置为 `esp32doit-devkit-v1`。
- English: ESP32 development board, configured as `esp32doit-devkit-v1` in PlatformIO.

- 中文：MPU6050 IMU，用于姿态角和角速度。
- English: MPU6050 IMU for attitude and angular velocity.

- 中文：6 个电机：4 个腿部关节电机 + 2 个轮毂电机，通过 CAN 总线通信。
- English: Six motors: four leg joint motors and two wheel motors, communicating over CAN.

- 中文：ADS1115/ADC 电压检测，用于电池电压监测和输出补偿。
- English: ADS1115/ADC voltage sensing for battery monitoring and output compensation.

- 中文：Xbox 蓝牙手柄，用作主要人工遥控器。
- English: Xbox BLE controller as the primary manual controller.

- 中文：Yahboom ROS WiFi 摄像头模块，用于把图像通过 micro-ROS 发布到电脑。
- English: Yahboom ROS WiFi camera module for publishing images to the PC through micro-ROS.

## Software Requirements / 软件环境

### Firmware / 固件

- PlatformIO
- ESP32 Arduino framework
- Libraries from `platformio.ini`:
  - `electroniccats/MPU6050`
  - `adafruit/Adafruit ADS1X15`
  - `SPI`
  - vendored `lib/NimBLE-Arduino`

### Host / 电脑端

- Ubuntu/ROS 2 Humble environment
- `micro_ros_agent`
- Python 3
- ROS 2 packages: `rclpy`, `sensor_msgs`, `std_msgs`, `cv_bridge`, `launch`, `launch_ros`
- Python vision packages: OpenCV, MediaPipe, NumPy
- Optional fallback: Docker, used by `host/scripts/camera_quickstart.sh` if native `micro_ros_agent` is unavailable

## Firmware Setup / 固件设置

1. Configure local WiFi credentials / 配置本地 WiFi：

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

2. Build firmware / 编译固件：

```bash
pio run
```

3. Upload firmware / 烧录固件：

```bash
pio run -t upload
```

4. Open serial monitor / 打开串口监视器：

```bash
pio device monitor
```

中文：机器人连上 WiFi 后会打印 IP，并尝试注册 `wheeleg.local:23`。如果电脑不能解析 mDNS，就使用串口打印出的 IP。

English: After the robot joins WiFi, it prints its IP address and advertises `wheeleg.local:23`. If mDNS does not work on your network, use the printed IP address.

## Host Quick Start / 电脑端快速启动

### 1. Start the camera micro-ROS agent / 启动摄像头 micro-ROS Agent

```bash
host/scripts/camera_quickstart.sh
```

Expected camera topic / 期望摄像头话题：

```bash
/espRos/esp32camera  sensor_msgs/msg/CompressedImage
```

Observed local validation / 本地实测记录：

- 中文：摄像头发布 JPEG 压缩图像，测试帧为 `320x240`，约 `5.6 Hz`。
- English: The camera published JPEG compressed images. The observed test stream was `320x240` at about `5.6 Hz`.

### 2. Build the ROS 2 vision bridge / 编译 ROS 2 视觉桥

```bash
source /opt/ros/humble/setup.bash
cd host/ros2_ws
colcon build --packages-select wheeleg_vision_bridge
source install/setup.bash
```

### 3. Run the bridge in dry-run mode / dry-run 模式运行视觉桥

```bash
ros2 launch wheeleg_vision_bridge bridge.launch.py
```

中文：默认参数在 `host/ros2_ws/src/wheeleg_vision_bridge/config/config.yaml`。当前默认值是 `mode: idle`、`dry_run: true`、`transport: tcp`、`tcp_host: wheeleg.local`。dry-run 只打印命令，不向机器人发送真实控制。

English: Default parameters live in `host/ros2_ws/src/wheeleg_vision_bridge/config/config.yaml`. Current defaults are `mode: idle`, `dry_run: true`, `transport: tcp`, and `tcp_host: wheeleg.local`. Dry-run logs commands only; it does not send real robot control.

Switch modes / 切换模式：

```bash
ros2 param set /wheeleg_vision_bridge mode gesture
ros2 param set /wheeleg_vision_bridge mode face
ros2 param set /wheeleg_vision_bridge mode stunt
ros2 param set /wheeleg_vision_bridge mode idle
```

Disable dry-run only after bench validation / 台架验证通过后再关闭 dry-run：

```bash
ros2 param set /wheeleg_vision_bridge dry_run false
```

## Vision Modes / 视觉模式

| Mode / 模式 | Input / 输入 | Output / 输出 |
|---|---|---|
| `idle` | No processing / 不处理图像 | status only / 只发布状态 |
| `gesture` | MediaPipe Hands / 手势识别 | continuous `DRIVE` commands + optional `JUMP` |
| `face` | MediaPipe Face Detection / 人脸检测 | `YAWRATE,<mrad_s>` yaw-follow command |
| `stunt` | MediaPipe Pose / 姿态识别 | queue actions such as `JUMP`, `CROSSLEG`, leg-length changes |

Gesture mapping / 手势映射：

| Gesture / 手势 | Label / 标签 | Command / 命令 |
|---|---|---|
| Fist / 握拳 | `Zero` | `DRIVE,0,0` |
| Open palm / 张掌 | `Five` | `DRIVE,250,0` |
| Point left / 向左指 | `PointLeft` | `DRIVE,0,600` |
| Point right / 向右指 | `PointRight` | `DRIVE,0,-600` |
| Thumb up / 点赞 | `Thumb_up` | `JUMP` |

中文：`gesture` 模式会周期性重发 `DRIVE`，喂机器人端 500 ms 看门狗；手从画面中消失时会立即改为 `DRIVE,0,0`。

English: `gesture` mode periodically re-sends `DRIVE` to feed the robot-side 500 ms watchdog. If the hand disappears from the frame, it immediately falls back to `DRIVE,0,0`.

Stunt safety / 特技安全门：

```bash
ros2 param set /wheeleg_vision_bridge stunt_armed true
ros2 param set /wheeleg_vision_bridge stunt_armed false
```

中文：`stunt` 模式默认不允许 `JUMP` 和 `CROSSLEG,0,5` 真实发送，必须手动设置 `stunt_armed=true`。

English: In `stunt` mode, `JUMP` and `CROSSLEG,0,5` are blocked by default. They require `stunt_armed=true`.

## Keyboard WiFi Teleop / WiFi 键盘控制

Run with mDNS / 使用 mDNS：

```bash
python3 host/tools/keyboard_drive.py
```

Run with explicit robot IP / 使用机器人 IP：

```bash
python3 host/tools/keyboard_drive.py --host 192.168.1.23 --rate 20
```

Keys / 按键：

| Key / 按键 | Action / 动作 |
|---|---|
| `W` / `S` | forward / backward, 前进 / 后退 |
| `A` / `D` | turn left / right, 左转 / 右转 |
| `1` / `2` / `3` | speed preset 150 / 250 / 350 mm/s |
| `Space` | hard stop: `DRIVE,0,0` + `QUEUE_STOP` |
| `H` | print help / 打印帮助 |
| `Q` | quit cleanly and re-enable BLE / 退出并恢复蓝牙输入 |

中文：脚本启动时会发送 `BLE_DISABLE`，退出时会发送 `DRIVE,0,0 -> YAWRATE,0 -> BLE_ENABLE`，避免 PC 控制和 Xbox 手柄抢同一个目标量。

English: The script sends `BLE_DISABLE` on start and `DRIVE,0,0 -> YAWRATE,0 -> BLE_ENABLE` on exit, so PC teleop and Xbox BLE do not fight over the same motion targets.

## Command Protocol / 指令协议

Direct teleop commands / 实时直通控制：

```text
DRIVE,<speed_mm_s>,<yaw_mrad_s>
YAWRATE,<mrad_s>
```

中文：`DRIVE` 和 `YAWRATE` 绕过队列，适合键盘/视觉这种需要连续刷新的控制；机器人端 500 ms 内没有收到新命令会自动归零。

English: `DRIVE` and `YAWRATE` bypass the queue and are intended for continuously refreshed keyboard/vision control. If no fresh command arrives within 500 ms, the robot zeros the direct target.

Queue commands / 队列动作：

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

Queue control / 队列控制：

```text
QUEUE_START
QUEUE_PAUSE
QUEUE_RESUME
QUEUE_STOP
QUEUE_STATUS
```

Safety and arbitration / 安全与输入仲裁：

```text
BALANCE_ON
BALANCE_OFF
BLE_DISABLE
BLE_ENABLE
BLE_STATUS
VISION_DISABLE
VISION_ENABLE
```

中文：队列运行或暂停时，BLE 和实时 yaw/drive 输入会被抑制，防止脚本动作和手柄动作互相覆盖。

English: When the queue is running or paused, BLE and direct yaw/drive input are suppressed to prevent scripted actions and manual input from overwriting each other.

## Validation Notes / 已验证内容

中文：当前仓库中的主要验证记录保存在 `Progress.md`，关键结果包括：

- `pio run` 固件编译通过。
- `colcon build --packages-select wheeleg_vision_bridge` 通过。
- Python `compileall` 对视觉桥代码通过。
- micro-ROS Agent 能接入 WiFi 摄像头。
- `/espRos/esp32camera` 能收到 `sensor_msgs/msg/CompressedImage`。
- 视觉桥 dry-run 能启动，`face` 模式能输出 `YAWRATE,0` 类命令。
- `gesture` 模式已实测张掌能输出 `DRIVE,250,0`；握拳识别还需要继续实机微调。

English: The main validation log is in `Progress.md`. Key results include:

- Firmware build passed with `pio run`.
- ROS 2 bridge build passed with `colcon build --packages-select wheeleg_vision_bridge`.
- Python `compileall` passed for the vision bridge package.
- The micro-ROS Agent connected to the WiFi camera.
- `/espRos/esp32camera` published `sensor_msgs/msg/CompressedImage`.
- The bridge starts in dry-run mode, and `face` mode can emit commands such as `YAWRATE,0`.
- In `gesture` mode, open palm produced `DRIVE,250,0`; fist recognition still needs more physical tuning.

## Safety Notes / 安全注意事项

- 中文：第一次测试必须保持 `dry_run: true`，确认日志输出正确后再关闭。
- English: Keep `dry_run: true` for first tests. Disable it only after logs are correct.

- 中文：`BALANCE_ON` 会触发起立准备动作，机器人没有固定或周围不安全时不要发送。
- English: `BALANCE_ON` triggers standup preparation. Do not send it unless the robot is physically safe.

- 中文：键盘/视觉控制前，确认机器人已经进入平衡状态，否则 `DRIVE` 可能没有运动效果。
- English: Before keyboard or vision control, confirm the robot is already balanced; otherwise `DRIVE` may have no visible effect.

- 中文：WiFi 断开、TCP 客户端掉线或命令超时会触发停止逻辑，但物理断电/急停仍然是最后保险。
- English: WiFi disconnect, TCP client drop, and command timeout trigger stop logic, but a physical power cutoff or emergency stop remains the final safety layer.

- 中文：不要把真实 WiFi 密码提交到 GitHub；只提交 `include/wifi_config.example.h`。
- English: Do not commit real WiFi credentials to GitHub; only commit `include/wifi_config.example.h`.

## More Documentation / 更多文档

- `Progress.md`：开发进度、测试记录、已完成修改。
- `host/README_vision.md`：电脑端视觉桥和键盘控制的详细说明。
- `yahboom-camera-ros2-guide.md`：Yahboom WiFi 摄像头 + ROS 2 启动说明。
- `yahboom-wifi-mediapipe-plan.md`：WiFi 摄像头 + MediaPipe 视觉控制计划。
- `pc-wifi-keyboard-control-plan.md`：PC WiFi 键盘控制方案。
- `introduction.md`：面向导师/答辩的中文项目介绍。

## Project Status / 项目状态

中文：当前项目已经完成 GitHub 初始同步、固件编译验证、摄像头 ROS 2 图像链路验证、视觉桥 dry-run 验证、PC WiFi 键盘控制方案和工具落地。下一步更适合继续做实机台架验证：先 `dry_run` 手势/人脸，再验证 PC WiFi 控制，最后才关闭 `dry_run` 上机器人。

English: The project has completed initial GitHub sync, firmware build validation, camera ROS 2 image-link validation, vision bridge dry-run validation, and the PC WiFi keyboard control plan/tooling. The next practical step is bench validation: dry-run gestures/face first, then PC WiFi control, and only then disable `dry_run` on the robot.

## License / 许可证

中文：本仓库基于 Yahboom 原始项目继续开发，并包含第三方 vendored `NimBLE-Arduino` 库。请分别遵守原始项目和第三方库的许可证要求。当前自定义部分尚未单独整理许可证文件。

English: This repository continues from the original Yahboom project and includes the third-party vendored `NimBLE-Arduino` library. Follow the license requirements of the original project and third-party libraries. A separate license file for the custom additions has not been finalized yet.
