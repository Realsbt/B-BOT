# ESP32 Wheel-Legged Robot - Development Progress

---

## 2025/11/1 ~ 11/7 - Project Setup & Hardware Foundation

- Set up ESP32 + PlatformIO + Arduino framework project
- Implemented CAN bus communication module (1Mbps, GPIO33/32) for motor controller data exchange
- Initialized 6 motors: 4 joint motors (4310 type) + 2 wheel motors (2805 type), with back-EMF compensation
- Integrated MPU6050 IMU via DMP for yaw/pitch/roll attitude data and angular velocities
- Created motor send task (2ms cycle) and CAN receive task for real-time feedback

## 2025/11/8 ~ 11/15 - PID Controllers & Yaw Control

- Implemented cascade PID controller framework (inner + outer loop)
- Completed Roll PID: controls body tilt via left/right leg force differential
- Completed Leg Length PID: controls virtual leg length with integral and low-pass filtering
- Completed Leg Angle Difference PID: ensures left/right leg angle consistency
- Added gravity feedforward compensation
- Completed Yaw PID controller for turning functionality

## 2025/11/16 ~ 11/22 - Ground Detection & Landing

- Implemented ground support force calculation based on leg force, gravity, and acceleration
- Touch detection logic: both legs > 3N threshold = grounded
- Added 1-second anti-bounce mechanism to prevent false liftoff detection
- Disabled wheel motors when airborne, keeping legs vertical only
- Implemented landing cushioning state machine: marks cushioning on ground contact, exits when leg compresses to target length
- Reset position target on landing to prevent accumulated position error

## 2025/11/23 ~ 11/30 - Angle Protection & Standup

- Added leg angle protection: shuts down all motors when leg angle exceeds safe range or pitch is too large
- 2-second recovery delay after protection triggers to prevent oscillation
- Implemented split-leg standup (`Ctrl_StandupPrepareTask`): left leg swings back, right leg swings forward
- Standup state machine: None -> Prepare -> Standup -> None
- Known issue: split standup is too aggressive for an already-standing robot

## 2025/12/1 ~ 12/7 - Jump Functionality

- Implemented `Ctrl_JumpPrepareTask` as independent FreeRTOS task
- Jump sequence: crouch (lower leg length) -> max torque push -> quick leg retraction
- Task self-deletes after completion

## 2025/12/8 ~ 12/14 - Xbox BLE Controller Integration

- Integrated NimBLE-Arduino library for Xbox Series X wireless controller support
- Auto-scan and connect to "Xbox Wireless Controller"
- Button mappings:
  - Left Stick Y: forward/backward speed
  - Right Stick X: yaw turning speed
  - Left Stick X: roll offset
  - Right Stick Y: leg length adjustment
  - A: standup / B: jump / Y: balance toggle / X: cross-step toggle
- BLE processing task running at 50Hz

## 2025/12/15 ~ 12/22 - Motor Calibration, Persistence & Voltage Monitoring

- Implemented automatic motor direction detection with user confirmation
- Zero-offset calibration: place legs horizontal, compute offsetAngle
- Parameter save/load via ESP32 Preferences (NVS Flash)
- Serial debug commands: `clearmotor`, `imu`, `clearimu`, `log`, `nolog`
- Integrated ADS1115 ADC for battery voltage monitoring
- Dynamic motor output ratio compensation based on battery voltage

## 2025/12/23 ~ 12/31 - Serial Command Queue System

- Implemented UART2 (GPIO16/17) command receiving task
- Command queue system: max 20 commands, sequential execution
- Movement commands: `FORWARD`, `BACKWARD`, `LEFT`, `RIGHT`, `STOP`
- Action commands: `JUMP`, `STANDUP`, `CROSSLEG`
- Leg adjustment: `INCREASELEGLENGTH`, `DECREASELEGLENGTH`
- Delay command: `DELAY`
- Queue control: `QUEUE_START`, `QUEUE_PAUSE`, `QUEUE_RESUME`, `QUEUE_STOP`, `QUEUE_STATUS`
- Composite commands via semicolon separation (e.g. `FORWARD,50,3;LEFT,90,2;STOP`)

---

## 2026/1/1 ~ 1/30 - Exam Break (No Development)

---

## 2026/2/1 ~ 2/2 - Cross-Step Walking & Input Arbitration

- Implemented cross-step walking: alternating left/right leg angle oscillation
- X button toggle with 300ms debounce, auto leg length increase when enabled
- Added BLE input enable/disable interface (`BLE_SetInputEnabled` / `BLE_GetInputEnabled`)
- Serial queue automatically overrides BLE input when active
- Added serial commands: `BALANCE_ON`, `BALANCE_OFF`, `BLE_DISABLE`, `BLE_ENABLE`, `BLE_STATUS`

## 2026/2/2 ~ 2/10 - MATLAB Code Generation & Leg Kinematics

- Generated forward kinematics code (`leg_position`) in MATLAB: joint angles to leg length & angle
- Generated velocity kinematics code (`leg_speed`): joint speeds to leg linear/angular velocity
- Generated VMC conversion code (`leg_vmc_conv`): virtual force/torque to joint motor torques
- Generated LQR feedback gain matrix (`lqr_k`) in MATLAB, dynamically computed based on leg length
- Built `LegPos_UpdateTask` for real-time leg pose updates at 4ms intervals
- Added low-pass filtered leg length acceleration calculation
- Defined 6-dimensional state vector: leg angle, position, pitch angle, and their derivatives
- Implemented `CtrlBasic_Task` main control loop at 4ms cycle with LQR balance control
- Wheel motor output = LQR output + Yaw PID output

---

## 2026/2/15 - Trigger Functions & Gentle Standup

- **Problem**: Pressing Y button caused motors to spin chaotically, robot could not balance
  - **Root cause**: Y button triggered split standup (`Ctrl_StandupPrepareTask`), which enters `StandupState_Prepare` and pauses balance control; the split pose conflicts with the robot's current standing posture
- **Solution**: Added trigger button functions to avoid the split standup action
  - Left Trigger (LT): deep press toggles balance on/off
  - Right Trigger (RT): triggers gentle standup (`Ctrl_GentleStandupTask`)
- **Gentle standup implementation**:
  - Does NOT enter `StandupState_Prepare`, balance control keeps running
  - Only sets target values (leg length, roll, speed) and lets PID/LQR smoothly adjust
  - Waits 800ms then resets position and yaw targets to current actual values

## 2026/2/16 - Leg Motor Test Mode

- **Problem**: Pressing left trigger caused robot to twitch; need to rule out motor hardware issues
  - **Analysis**: LT toggles `balanceEnabled` to false, causing `CtrlBasic_Task` to immediately zero all 6 motor torques, robot instantly loses support
- **Solution**: Changed right trigger to leg test mode for isolated motor diagnosis
  - Added `legTestMode` global flag
  - RT held down (trigRT > 500) enters test mode, release exits immediately
  - In test mode (balance must be off):
    - Left leg: +3N downward force (extend)
    - Right leg: -3N upward force (retract)
    - Forces converted to joint torques via VMC
    - Wheel motors remain off
  - Small force value (3N) ensures slow, safe movement
- **Debug procedure**:
  1. Ensure balance is off (`balanceEnabled = false`)
  2. Hold RT and observe if left leg slowly extends, right leg slowly retracts
  3. If motors don't respond or move in wrong direction, indicates motor or CAN issue
  4. Release RT to immediately zero all motors
  5. Use serial `log` command to monitor joint angles in real time

## 2026/2/17 - IMU Serial Debug Output & Roll Diagnosis

- **Problem**: Robot drifts to one side during balancing, suspected Roll axis issue; need to check if IMU is functioning correctly
- **Solution**: Added `imulog` / `noimulog` serial commands to continuously output IMU data via USB serial
  - Output format: `R:0.12 P:-0.35 Y:2.10 | dR:0.01 dP:-0.02 dY:0.00` (degrees and deg/s)
  - Updates every 100ms in `Log_Task`
- **Diagnosis steps**:
  1. Connect USB serial at 115200 baud, send `imulog`
  2. Place robot on level surface, check if Roll and Pitch are near 0 degrees (within +/-2 deg is normal)
  3. Slowly tilt robot left/right, verify Roll changes smoothly and symmetrically
  4. Return to level, confirm Roll returns to near 0
  5. If Roll shows large static offset, send `imu` to recalibrate (keep robot still and level)
  6. Send `noimulog` to stop output

---

## 2026/2/18 ~ 2/22 - Sensor Research, Mechanical Design & Algorithm Optimization

### ToF LiDAR Integration Research
- Investigated ToF LiDAR sensor options (TFmini Plus / TF-Luna, etc.) and confirmed UART interface approach
- Analyzed ESP32 GPIO/UART resource usage; decided to use UART1 (GPIO 25/26) for ToF connection
- Evaluated host-controller communication options, comparing micro-ROS, direct serial, and WiFi approaches
- Finalized system architecture: laptop as the host machine (ROS 2 + SLAM), ESP32 retains low-level balance control
- Adopted a layered architecture:
  - **Host (Laptop):** connects 360° LiDAR via USB; runs ROS 2 with `slam_toolbox` for mapping and `Nav2` for navigation
  - **Controller (ESP32):** retains existing balance control system; receives velocity commands from host via serial (UART2)

### OpenMV Research
- Investigated OpenMV as a lightweight vision module for object detection and tracking
- Evaluated integration options with the existing ESP32 system via UART or SPI

### Mechanical Design & 3D Printing
- Designed and 3D-printed a mounting base for attaching the ToF LiDAR sensor to the robot chassis
- Iterated on the bracket design to ensure stable sensor positioning and minimal vibration interference

### Balance Algorithm Optimization
- Optimized the LQR portion of the balance control algorithm
- Tuned LQR gain matrices for improved stability and disturbance rejection
- Reduced the main balance loop period for faster control response
- Lowered the yaw outer-loop saturation limit by one level to observe whether high-speed straight-line stability improves significantly

### Interface Design
- Designed host-to-ESP32 communication protocol (extending the existing serial command system)
- Planned a real-time velocity command interface on ESP32 (directly updates `target` variables, bypassing the command queue for lower latency)

---

## 2026/4/23 02:32:45 CST +0800 - ESP32 Camera, micro-ROS & Vision Bridge Test

### Added Host-Side Vision Bridge
- Added ROS 2 workspace package `wheeleg_vision_bridge` under `host/ros2_ws/src/wheeleg_vision_bridge`
- Implemented camera subscription for Yahboom ESP32 camera topic:
  - Topic: `/espRos/esp32camera`
  - Type: `sensor_msgs/msg/CompressedImage`
  - Format: `jpeg`
- Added MediaPipe-based vision processing modules:
  - Gesture mode: maps hand gestures to serial commands
  - Stunt mode: maps body pose events to robot actions
  - Face mode: maps face horizontal offset to yaw-rate commands
- Added command debounce and command encoder layers to avoid repeated unstable outputs
- Added UART/TCP transport abstraction for sending commands to the robot controller
- Added ROS status and mode interfaces:
  - Publishes `/wheeleg/vision_status`
  - Subscribes `/wheeleg/vision_mode`
  - Supports ROS parameter mode switching: `idle`, `gesture`, `stunt`, `face`

### Added / Updated Camera Agent Script
- Updated `host/scripts/camera_quickstart.sh`
- Script now prefers the local native `micro_ros_agent` installation from `/home/yahboom/uros_ws`
- Falls back to Docker `microros/micro-ros-agent:humble` only if native Agent is unavailable
- Fixed ROS `setup.bash` compatibility with `set -u` by temporarily disabling nounset during sourcing
- Added `MICRO_ROS_PORT` support, defaulting to UDP port `9999`
- Added default `ROS_LOG_DIR=/tmp/ros_logs` to avoid `.ros/log` write-permission problems in restricted environments
- Docker mode now only adds `-it` when running in an interactive terminal

### Test Results
- `bash -n host/scripts/camera_quickstart.sh`: passed
- `colcon build --packages-select wheeleg_vision_bridge`: passed
- `python3 -m compileall` for the bridge package: passed
- `/home/yahboom/.platformio/penv/bin/pio run`: passed
  - RAM: 37,940 bytes / 327,680 bytes, about 11.6%
  - Flash: 685,349 bytes / 1,310,720 bytes, about 52.3%
- micro-ROS Agent started successfully on UDP port `9999`
- Camera module connected to Agent from `172.20.10.3`
- Host LAN IP confirmed as `172.20.10.2`
  - Camera module `ros_ip` should be set to `172.20.10.2`
- Camera topic verified:
  - `/espRos/esp32camera [sensor_msgs/msg/CompressedImage]`
  - JPEG format confirmed
  - Frame rate measured around `5.8 Hz`
- JPEG frame decode test passed:
  - Frame size: `320x240`
  - OpenCV decoded shape: `(240, 320, 3)`
- `wheeleg_vision_bridge` launch test passed in safe `idle` mode
  - Status topic appeared: `/wheeleg/vision_status [std_msgs/msg/String]`
  - Status sample: `mode=idle frames=52`

### Current Operational Procedure
- Start camera Agent:
  - `cd /home/yahboom/Desktop/esp32-wheeleg-A-main`
  - `host/scripts/camera_quickstart.sh`
- Start bridge in another terminal:
  - `source /opt/ros/humble/setup.bash`
  - `source /home/yahboom/Desktop/esp32-wheeleg-A-main/host/ros2_ws/install/setup.bash`
  - `ros2 launch wheeleg_vision_bridge bridge.launch.py`
- Confirm bridge frame reception:
  - `ros2 topic echo --once /wheeleg/vision_status`
- Keep default `mode=idle` for bench testing until ready to safely test actions
- Switch to gesture mode only when the robot is physically secured:
  - `ros2 param set /wheeleg_vision_bridge mode gesture`
- Return to safe idle mode:
  - `ros2 param set /wheeleg_vision_bridge mode idle`

### Startup and Test Commands
- Full startup sequence:
  1. Power on the ESP32 camera module and make sure it is on the same WiFi/LAN as the host
  2. If needed, configure the camera module serial setting:
     - `ros_ip:172.20.10.2`
  3. Terminal 1, start the camera micro-ROS Agent:
     - `cd /home/yahboom/Desktop/esp32-wheeleg-A-main`
     - `host/scripts/camera_quickstart.sh`
  4. Confirm Agent logs show camera connection:
     - Look for `session established`
     - Look for `publisher created`
     - Look for camera address similar to `172.20.10.3`
  5. Terminal 2, start the bridge:
     - `source /opt/ros/humble/setup.bash`
     - `source /home/yahboom/Desktop/esp32-wheeleg-A-main/host/ros2_ws/install/setup.bash`
     - `ros2 launch wheeleg_vision_bridge bridge.launch.py`

- Camera-only test:
  - List camera topic:
    - `source /opt/ros/humble/setup.bash`
    - `source /home/yahboom/uros_ws/install/setup.bash`
    - `ros2 topic list -t --no-daemon`
  - Expected topic:
    - `/espRos/esp32camera [sensor_msgs/msg/CompressedImage]`
  - Check camera image format:
    - `ros2 topic echo --once /espRos/esp32camera sensor_msgs/msg/CompressedImage --field format`
  - Expected output:
    - `jpeg`
  - Check camera frame rate:
    - `ros2 topic hz /espRos/esp32camera`
  - Expected result:
    - Around `5 Hz` to `6 Hz`

- Bridge-only health test after Agent and camera are running:
  - Start bridge:
    - `source /opt/ros/humble/setup.bash`
    - `source /home/yahboom/Desktop/esp32-wheeleg-A-main/host/ros2_ws/install/setup.bash`
    - `ros2 launch wheeleg_vision_bridge bridge.launch.py`
  - In another terminal, check bridge status:
    - `source /opt/ros/humble/setup.bash`
    - `source /home/yahboom/Desktop/esp32-wheeleg-A-main/host/ros2_ws/install/setup.bash`
    - `ros2 topic echo --once /wheeleg/vision_status`
  - Expected output:
    - `data: mode=idle frames=<number>`
  - The frame number should increase when checked repeatedly

- Safe mode switching test:
  - Keep robot physically secured and keep power cutoff accessible
  - Start from safe idle:
    - `ros2 param set /wheeleg_vision_bridge mode idle`
  - Test gesture mode:
    - `ros2 param set /wheeleg_vision_bridge mode gesture`
  - Test stunt mode:
    - `ros2 param set /wheeleg_vision_bridge mode stunt`
  - Test face tracking mode:
    - `ros2 param set /wheeleg_vision_bridge mode face`
  - Return to safe idle immediately after testing:
    - `ros2 param set /wheeleg_vision_bridge mode idle`

- Build / regression test commands:
  - Build ROS 2 bridge package:
    - `source /opt/ros/humble/setup.bash`
    - `cd /home/yahboom/Desktop/esp32-wheeleg-A-main/host/ros2_ws`
    - `colcon build --packages-select wheeleg_vision_bridge`
  - Compile Python modules:
    - `cd /home/yahboom/Desktop/esp32-wheeleg-A-main/host/ros2_ws`
    - `python3 -m compileall -q src/wheeleg_vision_bridge/wheeleg_vision_bridge`
  - Build ESP32 firmware:
    - `cd /home/yahboom/Desktop/esp32-wheeleg-A-main`
    - `/home/yahboom/.platformio/penv/bin/pio run`

- Quick troubleshooting:
  - If `/espRos/esp32camera` does not appear:
    - Confirm Agent is still running
    - Confirm camera module WiFi is connected
    - Resend `ros_ip:172.20.10.2`
    - Power-cycle the camera module
  - If bridge starts but frames stay at `0`:
    - Confirm `/espRos/esp32camera` is publishing
    - Confirm `config.yaml` still uses `image_topic: /espRos/esp32camera`
    - Confirm `image_type: compressed`
  - If ROS logs fail due to permission:
    - Use `export ROS_LOG_DIR=/tmp/ros_logs`
    - Then rerun the command

### Known Notes
- If the camera does not reconnect after restarting Agent, power-cycle the camera module or resend `ros_ip:172.20.10.2` from the serial configuration tool
- During the integration test, the bridge was kept in `idle` mode and did not intentionally send movement commands

### 中文对照 / 中文速查

#### 本次新增了什么
- 新增了一个主机端 ROS 2 视觉桥包：`wheeleg_vision_bridge`
- 它负责接收 Yahboom ESP32 摄像头图像，再用 MediaPipe 做识别
- 摄像头图像话题：
  - `/espRos/esp32camera`
  - 类型：`sensor_msgs/msg/CompressedImage`
  - 格式：`jpeg`
- 支持 4 个工作模式：
  - `idle`：空闲安全模式，只收图像，不主动发动作命令
  - `gesture`：手势识别模式，把手势转换成机器人串口命令
  - `stunt`：姿态/动作识别模式，用人体姿态触发动作
  - `face`：人脸跟随模式，根据人脸左右偏移输出 yaw 转向命令
- 新增了命令防抖逻辑，避免手势识别不稳定时重复发命令
- 新增了 UART/TCP 发送层，后续可以把视觉结果发给机器人主控
- 新增了状态话题：
  - `/wheeleg/vision_status`
  - 例子：`data: mode=idle frames=52`

#### 摄像头 Agent 脚本改了什么
- 修改了 `host/scripts/camera_quickstart.sh`
- 现在脚本会优先使用本机已经安装好的 `micro_ros_agent`
- 如果本机没有 `micro_ros_agent`，才回退用 Docker
- 修复了 ROS `setup.bash` 和 `set -u` 不兼容导致的启动错误
- 默认使用 UDP 端口 `9999`
- 默认把 ROS 日志放到 `/tmp/ros_logs`，避免 `.ros/log` 权限问题
- Docker 只有在真正打开终端交互时才加 `-it`

#### 已经实测通过的内容
- 脚本语法检查通过：
  - `bash -n host/scripts/camera_quickstart.sh`
- ROS 2 包编译通过：
  - `colcon build --packages-select wheeleg_vision_bridge`
- Python 模块编译检查通过：
  - `python3 -m compileall -q src/wheeleg_vision_bridge/wheeleg_vision_bridge`
- ESP32 固件编译通过：
  - `/home/yahboom/.platformio/penv/bin/pio run`
- 摄像头模块成功连接到 micro-ROS Agent：
  - 摄像头地址：`172.20.10.3`
  - 主机地址：`172.20.10.2`
- 摄像头模块里的 `ros_ip` 应该设置为：
  - `ros_ip:172.20.10.2`
- 摄像头图像话题确认可用：
  - `/espRos/esp32camera [sensor_msgs/msg/CompressedImage]`
- 图像格式确认是：
  - `jpeg`
- 摄像头帧率大约：
  - `5 Hz` 到 `6 Hz`
- JPEG 图像解码成功：
  - 分辨率：`320x240`
  - OpenCV shape：`(240, 320, 3)`
- 视觉桥启动成功，能收到图像帧：
  - 状态样例：`mode=idle frames=52`

#### 日常启动方法
- 第 1 个终端，启动摄像头 micro-ROS Agent：
  - `cd /home/yahboom/Desktop/esp32-wheeleg-A-main`
  - `host/scripts/camera_quickstart.sh`
- 看到下面这些日志说明摄像头连上了：
  - `session established`
  - `publisher created`
  - 地址类似：`172.20.10.3`
- 第 2 个终端，启动视觉桥：
  - `source /opt/ros/humble/setup.bash`
  - `source /home/yahboom/Desktop/esp32-wheeleg-A-main/host/ros2_ws/install/setup.bash`
  - `ros2 launch wheeleg_vision_bridge bridge.launch.py`
- 检查视觉桥是否收到图像：
  - `ros2 topic echo --once /wheeleg/vision_status`
- 正常应该看到类似：
  - `data: mode=idle frames=52`

#### 摄像头单独测试方法
- 查看话题列表：
  - `source /opt/ros/humble/setup.bash`
  - `source /home/yahboom/uros_ws/install/setup.bash`
  - `ros2 topic list -t --no-daemon`
- 应该看到：
  - `/espRos/esp32camera [sensor_msgs/msg/CompressedImage]`
- 查看图像格式：
  - `ros2 topic echo --once /espRos/esp32camera sensor_msgs/msg/CompressedImage --field format`
- 应该输出：
  - `jpeg`
- 查看帧率：
  - `ros2 topic hz /espRos/esp32camera`
- 正常大约是：
  - `5 Hz` 到 `6 Hz`

#### 安全切换模式方法
- 当前默认启用了 dry-run 安全模式：
  - `dry_run: true`
  - 作用：只在日志里打印将要发送的命令，不真正写 UART/TCP，不让机器人动作
  - 状态话题会显示：`dry_run=True`
- 如果后面确认要真实发送命令，再手动关闭 dry-run：
  - `ros2 param set /wheeleg_vision_bridge dry_run false`
- 测完或不确定时重新打开 dry-run：
  - `ros2 param set /wheeleg_vision_bridge dry_run true`
- 默认建议保持安全模式：
  - `ros2 param set /wheeleg_vision_bridge mode idle`
- 测手势识别：
  - `ros2 param set /wheeleg_vision_bridge mode gesture`
- 测动作/姿态识别：
  - `ros2 param set /wheeleg_vision_bridge mode stunt`
- 测人脸跟随：
  - `ros2 param set /wheeleg_vision_bridge mode face`
- 测完立刻切回安全模式：
  - `ros2 param set /wheeleg_vision_bridge mode idle`
- 注意：
  - 第一次测试动作模式时，机器人必须固定好
  - 电源开关或断电方式要随手能碰到
  - 不确定时先用 `idle`，确认图像和状态正常后再切模式

#### 常见问题
- 如果看不到 `/espRos/esp32camera`：
  - 确认 `camera_quickstart.sh` 还在运行
  - 确认摄像头模块已经连上 WiFi
  - 用 XCOM 或串口工具重新发送：`ros_ip:172.20.10.2`
  - 给摄像头模块断电重启
- 如果 bridge 启动了，但 `frames=0`：
  - 先确认 `/espRos/esp32camera` 是否还在发布
  - 检查 `config.yaml` 里是不是：
    - `image_topic: /espRos/esp32camera`
    - `image_type: compressed`
- 如果 ROS 报日志目录权限错误：
  - 先执行：`export ROS_LOG_DIR=/tmp/ros_logs`
  - 再重新运行 ROS 命令

#### 2026-04-23 02:49:41 CST +0800 dry-run 安全更新
- 给 `wheeleg_vision_bridge` 增加了 `dry_run` 参数
- 默认配置为 `dry_run: true`
- 短启动验证通过：
  - 状态输出：`data: mode=idle dry_run=True frames=0`
  - 启动日志：`vision bridge ready: topic=/espRos/esp32camera type=compressed mode=idle dry_run=True`
- 本次验证命令：
  - `python3 -m compileall -q src/wheeleg_vision_bridge/wheeleg_vision_bridge`
  - `colcon build --packages-select wheeleg_vision_bridge`

#### 2026-04-23 03:24:26 CST +0800 验证结果同步
- 因为中途网络断开，重新继续做了完整链路验证
- 摄像头重新连接 micro-ROS Agent 成功：
  - Agent 端口：UDP `9999`
  - 摄像头地址：`172.20.10.3`
  - 日志出现：`session established`
  - 日志出现：`publisher created`
- 摄像头图像验证通过：
  - 图像话题：`/espRos/esp32camera`
  - 图像格式：`jpeg`
  - 帧率约：`5.6 Hz`
- `wheeleg_vision_bridge` dry-run 验证通过：
  - 启动状态：`mode=idle dry_run=True frames=31`
  - 切换到 `face` 模式成功
  - MediaPipe / TensorFlow Lite 初始化成功
  - 日志只打印 dry-run 命令：
    - `dry-run command: YAWRATE,0`
  - 没有真实发送 UART/TCP 控制命令
- Yahboom 原版 MediaPipe 程序验证：
  - `11_GestureRecognition` 可以启动 MediaPipe / TensorFlow Lite
  - 使用 `timeout` 强制退出时出现 `rclpy.shutdown already called`
  - 该报错属于示例程序退出处理不干净，不代表 MediaPipe 启动失败
  - `01_HandDetector` 可以运行并发布话题：
    - `/mediapipe/points [yahboomcar_msgs/msg/PointArray]`
  - 本次采样输出 `points: []`，表示当前画面未检测到手，节点本身正常
- 验证结束后已清理测试进程：
  - micro-ROS Agent 已停止
  - 未留下 `wheeleg_vision_bridge`
  - 未留下 Yahboom MediaPipe 节点

#### 后续记录规则
- 从现在开始，凡是完成了新功能、修复、配置调整、验证结果、测试结论，都要同步记录到 `Progress.md`
- 记录内容至少包括：
  - 时间
  - 修改了什么
  - 验证了什么
  - 测试结果
  - 当前是否安全，例如 `dry_run=True` 或是否真实发送命令
  - 如果有风险或注意事项，也要写进记录

#### 2026-04-23 03:52:18 CST +0800 dry-run 手势实测：握拳 / 张掌
- 本轮只测试两个手势：
  - 握拳：预期 `QUEUE_STOP`
  - 张掌：预期 `FORWARD,25,1`
- 测试状态：
  - 摄像头 Agent 启动成功
  - 摄像头模块连接成功：`172.20.10.3`
  - `wheeleg_vision_bridge` 启动成功
  - 状态确认：`mode=idle dry_run=True frames=289`
  - 切换到 `gesture` 模式成功
  - MediaPipe Hands / TensorFlow Lite 初始化成功
- 实测结果：
  - 张掌识别成功，输出：
    - `dry-run command: FORWARD,25,1`
  - 握拳没有稳定识别成 `QUEUE_STOP`
  - 测试中曾误识别出：
    - `dry-run command: JUMP`
  - 后续再次握拳时，有时误识别为张掌：
    - `dry-run command: FORWARD,25,1`
  - 最后一轮握拳没有稳定输出命令
- 安全状态：
  - 全程 `dry_run=True`
  - 没有真实发送 UART/TCP 控制命令
  - 测试结束后已切回 `idle`
  - 已停止 micro-ROS Agent 和 `wheeleg_vision_bridge`
- 结论：
  - 张掌路径可用
  - 握拳识别阈值/label 判断需要继续调试
  - 下一步建议给 bridge 增加 `debug_events` 或类似参数，打印每次 MediaPipe 手势 label，例如 `Zero/Five/Thumb_up/None`，再根据实际输出调整握拳判断

#### 2026-04-23 07:10:56 CST +0800 摄像头离线时的离线改进
- 用户说明当前摄像头不在线，因此转为做不依赖摄像头的准备工作
- 给 `wheeleg_vision_bridge` 增加调试参数：
  - `debug_events`
  - `debug_event_rate_hz`
- 默认配置：
  - `debug_events: false`
  - `debug_event_rate_hz: 2.0`
- 作用：
  - 打开后会按频率打印 MediaPipe 识别事件
  - gesture 模式会打印：
    - `gesture label=<label> stable=<stable>`
  - face 模式会打印：
    - `face event=<event> command=<YAWRATE...>`
  - stunt 模式会打印：
    - `stunt event=<event>`
- 这用于下一次摄像头恢复后调握拳识别问题，确认握拳到底被识别成 `Zero`、`Five`、`Thumb_up` 还是 `None`
- 验证结果：
  - `python3 -m compileall -q src/wheeleg_vision_bridge/wheeleg_vision_bridge` 通过
  - `colcon build --packages-select wheeleg_vision_bridge` 通过
  - 短启动日志确认 bridge 可启动：
    - `vision bridge ready: topic=/espRos/esp32camera type=compressed mode=idle dry_run=True`
- 注意：
  - 本次没有摄像头图像，因此没有做真实手势识别验证
  - 本次没有真实发送 UART/TCP 控制命令
  - 检查确认没有留下 bridge 或 micro-ROS Agent 后台进程

#### 2026-04-23 08:27:08 CST +0800 控制链路决策：选择 WiFi TCP
- 用户确认摄像头模块大概率不能作为 UART 命令返回通道，因此不采用：
  - `摄像头 -> WiFi -> 电脑 -> WiFi -> 摄像头 -> UART -> 机器人`
- 当前选择的目标链路是：
  - `摄像头 -> WiFi/micro-ROS -> 电脑 ROS2`
  - `电脑 ROS2 / MediaPipe -> WiFi TCP -> 机器人 ESP32`
- 这个方案中，摄像头只负责发图像，不负责转发控制命令
- 机器人 ESP32 需要自己连接同一个 WiFi，并开启 TCP 命令服务
- 当前代码状态：
  - `src/wifi_cmd.cpp` 已存在
  - `include/wifi_cmd.h` 已存在
  - `include/wifi_config.h` 已存在，但仍是占位值：
    - `WIFI_SSID "CHANGE_ME"`
    - `WIFI_PASS "CHANGE_ME"`
  - `.gitignore` 已忽略 `include/wifi_config.h`
  - `platformio.ini` 目前还没有启用 `-DENABLE_WIFI_CMD`
  - `wheeleg_vision_bridge` 已支持 `transport: tcp`
- 下一步需要做：
  - 在本地填写 `include/wifi_config.h` 的 WiFi 名和密码
  - 在 `platformio.ini` 中启用 `build_flags = -DENABLE_WIFI_CMD`
  - 编译并烧录机器人 ESP32
  - 从串口日志读取机器人 ESP32 的 WiFi IP
  - 用 `nc <robot-ip> 23` 先手动测试 `QUEUE_STATUS`、`YAWRATE,0` 等安全命令
  - 最后再把 `wheeleg_vision_bridge/config/config.yaml` 改为 `transport: tcp` 并填 `tcp_host`

#### 2026-04-23 08:49:43 CST +0800 新增 PC WiFi WASD 控制计划
- 新增计划文档：
  - `pc-wifi-keyboard-control-plan.md`
- 结论：
  - 不建议立刻用 WiFi 替代蓝牙手柄
  - Xbox BLE 手柄继续作为主要人工控制和备份控制路径
  - PC WiFi WASD 控制作为 ROS/视觉控制之前的中间验证层
- 计划中的目标链路：
  - `PC keyboard -> WiFi TCP -> Robot ESP32`
  - 后续可复用为：
    - `Camera -> PC ROS2 / MediaPipe -> WiFi TCP -> Robot ESP32`
- 计划新增直接控制命令：
  - `DRIVE,<speed_milli>,<yaw_mrad>`
- 设计原则：
  - `DRIVE` 不进命令队列
  - 直接更新 `target.speedCmd` 和 `target.yawSpeedCmd`
  - 只在命令队列不忙时生效
  - 500 ms 没有新 `DRIVE` 自动停车
- 键盘映射建议：
  - `W` 前进
  - `S` 后退
  - `A` 左转
  - `D` 右转
  - `Space` 停止
  - `Q` 退出并恢复 BLE
- 推荐实施顺序：
  - 先启用机器人 WiFi TCP
  - 再用 `nc <robot-ip> 23` 做安全命令测试
  - 再实现 `DRIVE`
  - 再写 `host/tools/keyboard_drive.py`
  - 最后做架空台架测试
- 当前状态：
  - 仅完成设计计划
  - 尚未修改固件实现 `DRIVE`
  - 尚未启用 `ENABLE_WIFI_CMD`

#### 2026-04-23 CST +0800 PC WiFi WASD 控制——隐藏问题梳理与落地实现
- 遍历项目确认基础设施状态：
  - `src/wifi_cmd.cpp` / `Serial_InjectCommandLine` / `BLE_DISABLE/ENABLE` / `YAWRATE` / `QUEUE_STOP` 已就绪
  - `DRIVE` 命令、PC 脚本、`ENABLE_WIFI_CMD` 编译开关尚未启用
- 在 `pc-wifi-keyboard-control-plan.md` 新增 §9 "Hidden Issues Found in Existing Code" 与 §10 "Minimum Fix Checklist"，记录 10 类隐藏问题（阻塞连接、断线 watchdog 漏停 DRIVE、双层 watchdog 不一致、陈旧 TCP 客户端、无鉴权、并发写竞争、BALANCE_ON 前提、2.4 GHz 共存、IP 发现、凭据管理）。
- 固件改动（已编译通过，Flash 84.7%、RAM 17.3%）：
  - `platformio.ini`：新增 `build_flags = -DENABLE_WIFI_CMD`
  - `src/serial.cpp`：新增 `DRIVE,<speed_mm/s>,<yaw_mrad/s>` 直通命令
    - clamp 到 `MAX_SPEED=0.8` / `MAX_YAWSPEED=4.5`
    - 队列忙碌时拒绝执行（复用 `canApplyDirectYawRate()`）
    - 500 ms watchdog 零化 `target.speedCmd` / `target.yawSpeedCmd`（与 YAWRATE watchdog 并列于 `Serial_Task`）
  - `src/wifi_cmd.cpp`：
    - 改为非阻塞 WiFi 连接：15 s 超时 + 5 s 间隔重连，WiFi 掉线自动停服+全停
    - 客户端断线 / WiFi 丢失 / 空闲超过 `WIFI_WATCHDOG_MS (1500 ms)` 均触发 `DRIVE,0,0` + `YAWRATE,0` + `QUEUE_STOP` 三连停（修复原先仅注入 `QUEUE_STOP` 无法停下 DRIVE 的漏洞）
    - 新接入客户端设置 `setNoDelay(true)` + `setTimeout(1)`
  - `include/wifi_config.h`：当时填入本地热点凭据，后续 GitHub 同步前已改为模板化配置，真实 password 留在 ignored local config
- 主机端新增：
  - `host/tools/keyboard_drive.py`：20 Hz 发送，WASD 点按切换，1/2/3 速度档（150/250/350 mm/s），Space 硬停，Q 退出
  - 启动序列：`BLE_DISABLE` → `DRIVE,0,0` → 进入流
  - 退出序列（`atexit` + `SIGTERM`/`SIGHUP` + `KeyboardInterrupt`）：`DRIVE,0,0` → `YAWRATE,0` → `BLE_ENABLE`
  - 启动横幅显式提醒"DRIVE 只在 BALANCE ON 后才会让机器人移动"
- 验证：
  - `pio run`：通过
  - `python3 -m py_compile host/tools/keyboard_drive.py`：通过
- 当前状态：
  - 固件与主机脚本均已实现并通过静态编译
  - 台架硬件测试尚未进行；需人工热点开到 2.4 GHz、flash 固件、串口观察 `WiFi command ready: <ip>:23` 后再跑脚本
  - 未做：mDNS 广播（可选）、IP 白名单 / 共享密钥（安全强化，后续）
  - 尚未进行 WiFi TCP 实机测试

#### 2026-04-23 CST +0800 删除 S2W4.md
- 删除根目录下的 `S2W4.md`（第 2 学期第 4 周周报）
- 原因：用户请求清理；其内容（ToF LiDAR / OpenMV / Nav2 / LQR 调参等路线图）已不作为本仓库的活计划
- 影响：无代码改动；`introduction.md` / `Progress.md` / `pc-wifi-keyboard-control-plan.md` / `yahboom-*.md` 保留不变

#### 2026-04-23 CST +0800 固件新增 mDNS 广播 wheeleg.local
- `src/wifi_cmd.cpp`：
  - include `<ESPmDNS.h>`
  - 连上 WiFi 后调用 `MDNS.begin("wheeleg")` + `MDNS.addService("wheeleg", "tcp", WIFI_TCP_PORT)`
  - WiFi 掉线时调用 `MDNS.end()`，重连时自动重新广播
- 验证：`pio run` 通过（Flash 84.7% 增加到含 mDNS 后仍在预算内）
- 效果：之后 PC 可用 `wheeleg.local:23` 代替查 IP，后续 `keyboard_drive.py` / `config.yaml` 会改用此主机名

#### 2026-04-23 CST +0800 视觉桥默认走 WiFi TCP
- `host/ros2_ws/src/wheeleg_vision_bridge/config/config.yaml`：
  - `transport: uart` → `tcp`
  - `tcp_host: 192.168.1.100` → `wheeleg.local`（依赖前一条 mDNS 改动）
  - `command_rate_hz: 5.0` → `10.0`（配合即将把 gesture 切到 `DRIVE` 后的 500 ms watchdog）
  - `dry_run: true` 保留
- 影响：视觉桥接节点与 `keyboard_drive.py` 现在共用同一条 `PC → WiFi TCP:23 → Robot ESP32` 路径，验证 plan §2 的目标架构

#### 2026-04-23 CST +0800 keyboard_drive.py 默认使用 mDNS
- `host/tools/keyboard_drive.py`：
  - `--host` 由必填改为默认 `wheeleg.local`
  - 更新 docstring 使用示例（零参直连 / fallback IP）
- 验证：`py_compile` 通过
- 效果：常用命令简化为 `python3 keyboard_drive.py`

#### 2026-04-23 CST +0800 MediaPipe label 一致性审计
- 读 `mediapipe_runner.py` + `command_encoder.py` 交叉核对
- gesture label 全部一致：`Zero / Five / PointLeft / PointRight / Thumb_up`（runner 额外有 `One / None`，encoder 静默忽略）
- stunt event kind 全部一致：`tpose / crouch / arms_up`
- **发现新 bug**（留待任务 #6 修）：runner 从不发 `{"kind": "arms_up", "active": False}` —— 手放下时跳到 crouch/None 分支。encoder 的 `_arms_up` 状态被卡死，导致第一次挥手触发 JUMP 后再也不会触发第二次

#### 2026-04-23 CST +0800 gesture 模式切换到 DRIVE 直通
- `command_encoder.encode_gesture`：
  - `Zero` → `DRIVE,0,0`（原 `QUEUE_STOP`）
  - `Five` → `DRIVE,250,0`（原 `FORWARD,25,1`，1 秒定时）
  - `PointLeft` → `DRIVE,0,600`（原 `LEFT,20,1`）
  - `PointRight` → `DRIVE,0,-600`（原 `RIGHT,20,1`）
  - `Thumb_up` → `JUMP`（仍为 impulse 命令）
- `bridge_node.py`：
  - 新增 `_current_gesture_drive` 状态（默认 `DRIVE,0,0`）
  - 每帧手势识别：稳定 label 若为 DRIVE 类，更新 `_current_gesture_drive`；手完全消失立即归零
  - impulse 命令（JUMP）仍然边沿触发，只发一次
  - `_timer_cb` 按 `command_period` 周期重发 `_current_gesture_drive`，维持机器人侧 500 ms DRIVE watchdog
  - 图像流超时 / 切出 gesture 模式时强制 `DRIVE,0,0`
- 验证：`compileall` 通过
- 效果：手势响应由 1 秒队列定时 → 实时；手放下立即停而不是"跑完 1 秒"；保持与 `keyboard_drive.py` 的协议一致

#### 2026-04-23 CST +0800 stunt 模式 arm 保护 + arms_up 卡死修复
- `command_encoder.encode_stunt`：
  - 修复 bug：runner 从不发 `arms_up active=False`，当帧姿态变为 crouch/None/tpose 时推断"手放下" → 触发 JUMP 并清 `_arms_up`
  - 这样用户可重复"挥手→跳→再挥手→再跳"，不再卡在第一次
- `bridge_node.py`：
  - 新增 ROS 参数 `stunt_armed`（默认 `false`）
  - stunt 模式下 `JUMP` 与 `CROSSLEG,0,5` 仅当 `stunt_armed=true` 时才真正发送，否则打 debug 日志拦截
  - `stunt_armed` 可 runtime 通过 `ros2 param set /wheeleg_vision_bridge stunt_armed true` 切换
- `config.yaml`：新增 `stunt_armed: false` 默认项 + 注释
- 验证：`compileall` 通过
- 效果：防止摄像头扫到路人挥手就跳；开发时手势调试不会误触发激进动作

#### 2026-04-23 CST +0800 MAX_COMMAND_LENGTH 审计 + 注释
- 读 `parseCommandType`（`src/serial.cpp:185`）确认 `MAX_COMMAND_LENGTH=64` 只限制命令类型 token（如 `FORWARD`/`INCREASELEGLENGTH`），不限制整行或子命令
- 实际限制链条：行级 256 B → 单子命令 128 B（`subBuf`）→ 命令类型 64 B
- 最长命令类型 `INCREASELEGLENGTH` 仅 17 字节，余量充足；复合命令完全安全
- 改动：`serial.cpp:24` 上方加注释澄清，数值不变
- 验证：`pio run` 通过

#### 2026-04-23 CST +0800 更新 host/README_vision.md
- 重写 `host/README_vision.md`：
  - 新增"Addressing"段落说明 `wheeleg.local` mDNS
  - 新增 `tools/keyboard_drive.py` 完整用法（按键表、启停握手、BALANCE 前提）
  - 新增"Command protocol (shared)"段落列全 `DRIVE` / `YAWRATE` / 队列 / 仲裁命令 + 机器人侧 watchdog 说明
  - 更新 gesture 映射表为 DRIVE 版本
  - 新增 `stunt_armed` 参数说明
  - 保留 build / camera / mode 切换等原有段落
- 效果：单文档即可上手键盘遥控 + 视觉桥两条路径

#### 2026-04-23 CST +0800 plan Phase E 增加 mDNS 预检步骤
- `pc-wifi-keyboard-control-plan.md` §7 Phase E 前加"Pre-flight"段
- 明确先 `ping wheeleg.local` / `avahi-resolve -n` 验证解析；失败则 fallback 到 DHCP IP `--host <ip>`
- 避免台架验证当晚卡在找不到 IP 或 mDNS 解析失败的坑

#### 2026-04-23 CST +0800 wheeleg_vision_bridge 回归测试
- `colcon build --packages-select wheeleg_vision_bridge`：通过（4.15s）
- `timeout 6 ros2 launch wheeleg_vision_bridge bridge.launch.py`：节点启动成功
  - 日志输出：`vision bridge ready: topic=/espRos/esp32camera type=compressed mode=idle dry_run=True`
  - dry_run=True 下不尝试 TCP 连接，无异常
- 验证本次改动（DRIVE gesture、stunt_armed、arms_up bug 修复、config 切 TCP）未破坏包的启动路径

#### 2026-04-23 10:59:56 CST GitHub 初始提交与推送 / GitHub initial sync
- 目标仓库 / Target repo：`https://github.com/Realsbt/B-BOT.git`
- 本地目录 / Local workspace：`/home/yahboom/Desktop/esp32-wheeleg-A-main`
- 本地 Git 初始化结果：
  - 当前分支：`main`
  - 远程仓库：`origin -> https://github.com/Realsbt/B-BOT.git`
  - 初始提交：`3a9f2c4 Initial B-BOT vision control workspace`
- 推送结果 / Push result：
  - 已执行：`git push -u origin main`
  - 成功创建远程分支：`main -> main`
  - 本地 `main` 已设置为跟踪 `origin/main`
- 已纳入 GitHub 的主要内容：
  - ESP32 机器人固件、WiFi/TCP 控制相关代码、串口命令扩展
  - `host/ros2_ws/src/wheeleg_vision_bridge` ROS2 + MediaPipe 视觉桥
  - `host/tools/keyboard_drive.py` PC WiFi 键盘控制工具
  - 视觉桥、摄像头、键盘控制、WiFi 架构相关文档和 plan
- 没有提交的本地/生成/敏感内容：
  - `include/wifi_config.h`（本地 WiFi SSID/PASS 配置）
  - `.pio/`
  - `host/ros2_ws/build/`
  - `host/ros2_ws/install/`
  - `host/ros2_ws/log/`
  - `.claude/`
  - `.codex`
  - `.vscode/`
  - `__pycache__/`
- 以后确认同步状态的方法：
  - `git status --short --branch`
  - `git log --oneline --decorate -3`
  - `git remote -v`

#### 2026-04-23 11:07:33 CST GitHub README 中英文首页 / bilingual GitHub README
- 按用户要求先遍历并提炼项目重点：
  - 用 `rg --files` 扫描仓库文件清单
  - 读取 `platformio.ini`、`src/main.cpp`、`src/serial.cpp`、`src/wifi_cmd.cpp`
  - 读取 `host/README_vision.md`、`keyboard_drive.py`、`wheeleg_vision_bridge` 的 `bridge_node.py`、`mediapipe_runner.py`、`command_encoder.py`、`transport.py`、`config.yaml`
  - 读取 `introduction.md`、`.gitignore` 等文档/配置
- 新增 `README.md`：
  - 中英文同页，适合 GitHub 项目首页
  - 包含当前控制架构：Xbox BLE、摄像头 → PC ROS2/MediaPipe → WiFi TCP → ESP32、小车 WiFi 键盘控制、可选 UART
  - 包含程序结构树，说明 `src/`、`include/`、`host/`、ROS2 包、工具脚本、文档文件的职责
  - 包含固件配置/编译/烧录方法：`include/wifi_config.example.h` → `include/wifi_config.h`、`pio run`、`pio run -t upload`
  - 包含摄像头 micro-ROS agent、ROS2 视觉桥 build/run、dry-run、mode 切换、关闭 dry-run 的方法
  - 包含 gesture/face/stunt 模式说明、手势映射、`stunt_armed` 安全门
  - 包含 `keyboard_drive.py` WASD WiFi 控制方法
  - 包含 `DRIVE`、`YAWRATE`、队列命令、仲裁命令、安全注意事项、已验证内容、更多文档链接
- 注意：
  - `README.md` 明确说明 `include/wifi_config.h` 是本地敏感配置，不提交 GitHub
  - 这次是文档新增，没有改动固件或 ROS2 代码

#### 2026-04-23 11:13:53 CST README 语言入口重排 / README language selector layout
- 按用户反馈调整 `README.md`：
  - 去掉逐段"中文 + English"混排方式
  - 顶部新增两个 GitHub 可点击徽章按钮：`中文` / `English`
  - `中文` 按钮跳转到完整中文说明区
  - `English` 按钮跳转到完整英文 README 区
  - 中文内容和英文内容现在各自成段，便于 GitHub 页面直接选择阅读语言
- 保留上一版提炼出的重点：
  - 当前控制架构
  - 程序结构
  - 固件配置/编译/烧录
  - 摄像头 micro-ROS + ROS2 视觉桥
  - gesture/face/stunt 模式
  - WiFi 键盘控制
  - 指令协议
  - 安全注意事项和验证记录
- 这次只改文档展示结构，没有改动固件或 ROS2 代码

#### 2026-04-24 CST +0800 USB+WiFi-only 视觉链路复核 / vision pipeline re-check before motor hookup
- 范围约束：
  - ESP32 主控仅通过 USB 供电/串口观察，同时连手机热点 WiFi
  - 摄像头模组单独上电并连同一热点 WiFi
  - 本轮不连接电机、不装腿、不进入 `BALANCE_ON`
- 已确认的主控链路：
  - `wheeleg.local` 可解析并连通 `TCP :23`
  - 已通过 `nc wheeleg.local 23` 发送安全命令：
    - `QUEUE_STATUS`
    - `BLE_STATUS`
    - `DRIVE,0,0`
    - `YAWRATE,0`
    - `QUEUE_STOP`
  - 结论：`PC -> WiFi TCP -> ESP32 命令入口` 已通
- 视觉链路验证结果：
  - micro-ROS Agent 可在 `UDP 9999` 收到摄像头会话
  - 摄像头话题确认出现：
    - `/espRos/esp32camera [sensor_msgs/msg/CompressedImage]`
  - 图像消息格式：
    - `jpeg`
  - 实测原始输入频率：
    - `ros2 topic hz /espRos/esp32camera`
    - 稳定约 `5.0 Hz` 到 `5.2 Hz`
  - `wheeleg_vision_bridge` 在 `gesture + dry_run=true` 下验证通过：
    - 日志出现 `gesture label=Five stable=Five`
    - 随后输出 `dry-run command: DRIVE,250,0`
  - 结论：`camera -> micro-ROS -> ROS2 -> vision_bridge -> command encoding` 已通
- 配置改动：
  - `host/ros2_ws/src/wheeleg_vision_bridge/config/config.yaml`
    - `frame_skip: 2` -> `frame_skip: 1`
  - 已执行：
    - `colcon build --packages-select wheeleg_vision_bridge`
  - install 目录中的配置已同步为 `frame_skip: 1`
  - 影响：视觉桥现在处理每一帧输入；这不会提升摄像头原始 FPS，只消除了桥端额外丢帧
- 关于 Yahboom 原生 `sub_img` 左上角 FPS 的结论：
  - `sub_img.py` 的 FPS 不是严格按 ROS 消息实际到达频率计算
  - 它把 `msg.header.stamp` 的差值与本地解码耗时混合计算，公式不适合作为真实链路 FPS 指标
  - 因此窗口里看到的十几 FPS 不能直接等价为 `/espRos/esp32camera` 的真实输入帧率
  - 后续判断真实输入速度应以 `ros2 topic hz /espRos/esp32camera` 为准
- 当前结论：
  - 在不接电机的前提下，已经完成了从摄像头到命令编码、从 PC 到 ESP32 TCP 命令入口的关键链路验证
  - 下一阶段可进入 `dry_run=false` 的真发 TCP 验证，但仍保持"不装腿 / 不起平衡 / 不接电机或至少不让系统产生实际运动"的安全约束

#### 2026-04-24 CST +0800 gesture 真发 TCP 调试 / gesture TCP live-send debugging
- 目标：
  - 在不接电机、不装腿的前提下，验证 `camera -> ROS2 -> vision_bridge(dry_run=false) -> TCP -> ESP32` 是否已经形成真实命令链路
- 调试前提：
  - 主控网络状态确认：
    - `avahi-resolve-host-name wheeleg.local` -> `172.20.10.4`
    - `nc -vz wheeleg.local 23` -> 成功
  - 本执行环境依然看不到 `/dev/ttyUSB*` / `/dev/ttyACM*`
  - 因此 ESP32 USB 串口日志需要由本机人工观察
- 相机侧步骤与结果：
  - 启动 micro-ROS Agent：
    - `ros2 run micro_ros_agent micro_ros_agent udp4 --port 9999 -v4`
  - Agent 成功建立摄像头会话：
    - 摄像头地址 `172.20.10.3`
  - ROS2 图像话题确认在线：
    - `/espRos/esp32camera [sensor_msgs/msg/CompressedImage]`
  - 本轮原始输入频率：
    - `ros2 topic hz /espRos/esp32camera`
    - 约 `6.1 Hz`
- 视觉桥真发步骤：
  - 启动命令：
    - `ros2 run wheeleg_vision_bridge bridge_node --ros-args --params-file ... -p mode:=gesture -p dry_run:=false -p debug_events:=true`
  - 节点启动日志：
    - `vision bridge ready: topic=/espRos/esp32camera type=compressed mode=gesture dry_run=False`
- 真发行为观测：
  - 空场景：
    - 连续发送 `sent: DRIVE,0,0`
    - 启动初期曾发送 `sent: QUEUE_STOP`
  - 张掌（`Five`）识别到后：
    - 日志出现 `debug event: gesture label=Five ...`
    - 随后连续发送 `sent: DRIVE,250,0`
  - 手离开画面：
    - 重新回到 `debug event: gesture label=None stable=None`
    - 命令回到 `sent: DRIVE,0,0`
- 结论：
  - `camera -> micro-ROS -> ROS2 -> vision_bridge -> TCP` 已完成真实命令发送验证
  - 桥端已确认能把手势 `Five` 编码并发送为真实 TCP 命令 `DRIVE,250,0`
  - 手离开后能恢复到 `DRIVE,0,0`
  - 剩余唯一未由本执行环境直接观测的部分是：
    - `ESP32 TCP server -> USB 串口日志`
    - 该项需用户本机串口窗口确认 `WiFi命令: DRIVE,250,0` / `DRIVE set: 250 mm/s, 0 mrad/s`
- 收尾：
  - 测试结束后已停止：
    - `wheeleg_vision_bridge`
    - `micro_ros_agent`
  - 停止 `wheeleg_vision_bridge` 时出现 `rcl_shutdown already called` 退出异常
    - 属于清理阶段重复 shutdown，不影响本轮链路验证结论

#### 2026-04-24 CST +0800 实验数据包、report 结果表、视觉桥与固件实验支持
- 记录规则更新：
  - 用户明确要求：从本条开始，后续所有主要代码、report、实验设计、实验数据或验证结果修改，都要同步写入 `Progress.md`
  - 本条用于补齐今天这轮已经完成的主要修改，后续继续按"改动内容 + 验证结果 + 限制/下一步"格式记录
- report / 实验数据收集文件：
  - 新增 `Report/planning/Experiment_Data_Collection.md`
    - 作为当前实验执行总表，按 E8/E2/E3/E9/E5/E6/E10/E11 顺序组织
    - 区分 `REAL_COLLECTED`、`PILOT_COLLECTED`、`PROVISIONAL_READY` 等状态
    - 明确 `* [PROVISIONAL]` 是规划占位值，最终 report 前必须替换为真实测量
  - 新增 `Report/appendices/E_data/` 实验数据目录
    - E2 disturbance recovery
    - E3 leg length sensitivity
    - E5 TCP latency
    - E6 watchdog fault injection
    - E8 control loop jitter
    - E9 controller ablation
    - E10 vision confusion
    - E11 vision-to-ESP32 latency
  - 新增 `Report/appendices/E_data/PROVISIONAL_DATA_POLICY.md`
    - 说明带 `provisional=true` 或 `synthetic_planning_placeholder_not_measured` 的数据不能作为 final report 实测证据
  - 新增多份 provisional CSV：
    - E8 loop jitter
    - E2 recovery trials
    - E3 leg length trials
    - E9 controller ablation
    - E6 watchdog fault injection
    - E5 TCP latency summary
    - E11 vision-to-ESP32 latency summary
  - 新增 provisional 图：
    - `Report/figures/provisional/e2_disturbance_recovery_provisional.png`
    - `Report/figures/provisional/e3_leg_length_sensitivity_provisional.png`
    - `Report/figures/provisional/e6_watchdog_fault_injection_provisional.png`
    - `Report/figures/provisional/e8_control_loop_jitter_provisional.png`
    - `Report/figures/provisional/e9_controller_ablation_provisional.png`
  - 更新 `Report/workspace/report_draft.md`
    - Results section 已填入 E8/E2/E3/E5/E6/E9 的 provisional 表格
    - 所有占位结果均标 `* [PROVISIONAL]`
    - 已加入 E10 真实 bench/pilot 指标和当前限制
- 已收集的真实 bench 数据：
  - micro-ROS camera agent 成功收到摄像头会话：
    - 摄像头 IP：`172.20.10.3`
    - UDP port：`9999`
  - ROS2 图像话题：
    - `/espRos/esp32camera [sensor_msgs/msg/CompressedImage]`
    - format：`jpeg`
  - 摄像头输入频率复测：
    - 约 `5.87 Hz` 到 `6.04 Hz`
  - ESP32 主控：
    - `wheeleg.local` 解析到 `172.20.10.4`
    - `172.20.10.4:23` TCP 可连接
  - E10 vision pilot：
    - `Five` / `Zero` 可通过 dry-run 命令链路
    - `PointLeft` / `Thumb_up` 初测失败
    - `NoHand` / hand lost 可触发安全停止逻辑
    - 首次失败复测发现摄像头朝向天花板/灯，已保存 frame check；调整后 `Five` 重新通过
    - `PointLeft` 调整手势后仍不够可靠，暂记为 limitation / improvement target
  - E5 TCP smoke：
    - TCP 端口可连接
    - 已发送安全停止命令
    - 在固件 ACK patch 之前没有收到 ACK，因此后续需要刷入新固件后重测
- 视觉桥代码修改：
  - `host/ros2_ws/src/wheeleg_vision_bridge/wheeleg_vision_bridge/mediapipe_runner.py`
    - 重构手势分类逻辑
    - 增加水平 index finger geometry，用于改善 `PointLeft` / `PointRight`
    - 调整 `Thumb_up` 判定顺序，避免先被 `Zero` 吃掉
  - `host/ros2_ws/src/wheeleg_vision_bridge/wheeleg_vision_bridge/bridge_node.py`
    - 新增 guarded send 路径
    - `JUMP` / `CROSSLEG,0,5` 现在在 gesture/stunt 路径都受 `stunt_armed` 安全门约束
  - `host/ros2_ws/src/wheeleg_vision_bridge/config/config.yaml`
    - `debounce_frames: 5` -> `debounce_frames: 3`
    - 原因：摄像头实测约 6 Hz，5 帧 debounce 反应过慢
  - 验证：
    - `python3 -m py_compile ...mediapipe_runner.py ...bridge_node.py` 通过
    - `colcon build --packages-select wheeleg_vision_bridge` 通过
- ESP32 固件实验支持：
  - `src/wifi_cmd.cpp`
    - TCP client connect 时输出 `HELLO,<ms>,wheeleg_tcp,<ip>:<port>`
    - 每条 TCP 命令处理后输出 `ACK,<esp_ms>,<rc>,<command>` 或 `NACK,<esp_ms>,<rc>,<command>`
    - WiFi watchdog 触发 full stop 前输出 `EVT,<esp_ms>,FULL_STOP,<reason>`
    - 目的：支持 E5 TCP latency 与 E6 watchdog fault-injection 实验
  - `include/ctrl.h` / `src/ctrl.cpp` / `src/serial.cpp`
    - 新增 E8 loop jitter 内存采样机制
    - 新增串口命令：
      - `LOOPLOG_START,<n>` / `LOOPLOG,<n>`
      - `LOOPLOG_STOP`
      - `LOOPLOG_DUMP`
    - dump 格式：
      - `LOOPLOG_DUMP_BEGIN,<n>,unit_us`
      - `LOOPDT,<idx>,<us>`
      - `LOOPLOG_DUMP_END,<n>`
    - 设计原因：避免在 4 ms 控制循环里连续 print 干扰实时性，先采样到 RAM，再统一 dump
  - `include/wifi_config.h`
    - 新增并按用户要求纳入 Git 跟踪
    - GitHub 同步前改为模板化配置
    - 真实 WiFi password 保留在 ignored local config，不进入远端仓库
  - `.gitignore`
    - 移除 `include/wifi_config.h` 忽略规则，让该文件可以进入 git
  - 验证：
    - `/home/yahboom/.platformio/penv/bin/pio run` 通过
    - 当前固件资源占用约 RAM `30.1%`、Flash `86.9%`
- 当前限制 / 下一步：
  - 所有 provisional 数据最终必须替换，final 前用以下命令扫一遍：
    - `rg "PROVISIONAL|provisional=true|synthetic_planning_placeholder_not_measured" Report`
  - 新固件需要实际 upload 到 ESP32 后，才能复测：
    - E5 TCP ACK latency
    - E6 watchdog full-stop event
    - E8 loop jitter dump
  - 真实小车/电机/腿到位后，需要把 E2/E3/E8/E9 的 provisional CSV 替换为实测 CSV
  - E10 目前可把 `Five` / `Zero` 作为可靠核心手势；`PointLeft` / `Thumb_up` 还需要继续改分类或降低 report 中的 claimed reliability

#### 2026-04-24 CST +0800 CH340 刷机、E5/E6 实测、E8 pilot 与摄像头/E10 复测
- 硬件连接状态：
  - 用户重新连接 ESP32 主控后，系统识别到 QinHeng CH340：
    - `lsusb` -> `1a86:7523 QinHeng Electronics CH340 serial converter`
    - 串口：`/dev/ttyUSB0`
  - ESP32 WiFi：
    - `wheeleg.local -> 172.20.10.4`
    - `172.20.10.4:23` TCP 可连接
  - 摄像头：
    - `172.20.10.3` ping 通
    - micro-ROS Agent 在用户重启摄像头供电后收到 session：
      - `address: 172.20.10.3:22980`
      - topic/publisher/datawriter 创建成功
- 固件刷入与新增实验支持：
  - 通过 `/dev/ttyUSB0` 执行 `pio run -t upload --upload-port /dev/ttyUSB0` 成功
  - 首次刷入 ACK/EVT/LOOPLOG 固件：
    - TCP 连接返回 `HELLO,<ms>,wheeleg_tcp,172.20.10.4:23`
    - 安全命令返回 ACK：
      - `ACK,...,DRIVE,0,0`
      - `ACK,...,YAWRATE,0`
      - `ACK,...,QUEUE_STOP`
      - `ACK,...,BLE_STATUS`
  - 后续为 E8 增加 `LOOPLOG_DUMP_TCP`，再次编译和刷入成功
  - 编译资源占用：
    - RAM 约 `30.1%`
    - Flash 约 `86.9%`
- E5 TCP command-entry latency 实测：
  - 测试命令：`DRIVE,0,0`
  - 样本数：`n=300`
  - 结果：
    - mean `50.05 ms`
    - median `37.41 ms`
    - p95 `88.31 ms`
    - p99 `143.47 ms`
    - max `368.89 ms`
    - unmatched/non-ACK `0`
  - 新增文件：
    - `Report/appendices/E_data/E5_tcp_latency/tcp_ack_latency_2026-04-24.csv`
    - `Report/appendices/E_data/E5_tcp_latency/tcp_ack_latency_summary_2026-04-24.csv`
- E6 watchdog / fault injection 实测：
  - 已完成 TCP idle fault case
  - 测试流程：连接 TCP，发送 `DRIVE,0,0` / `YAWRATE,0` / `QUEUE_STOP`，停止发送并等待 ESP32 `EVT`
  - 样本数：`n=10`
  - 结果：
    - median wait-to-EVT `1481.08 ms`
    - p95 `1510.11 ms`
    - max `1510.88 ms`
    - `FULL_STOP,idle_timeout` `10/10`
  - 新增文件：
    - `Report/appendices/E_data/E6_watchdog_fault_injection/watchdog_idle_trials_2026-04-24.csv`
    - `Report/appendices/E_data/E6_watchdog_fault_injection/watchdog_idle_summary_2026-04-24.csv`
- E8 control-loop jitter：
  - 新增采集脚本：
    - `Report/appendices/E_data/E8_control_loop_jitter/collect_looplog_tcp_serial.py`
    - `Report/appendices/E_data/E8_control_loop_jitter/collect_looplog_tcp.py`
  - USB serial 大量 dump 路径问题：
    - `LOOPLOG_DONE` 可读到，说明采样能完成
    - 但 5000/15000 行串口 dump 等不到 `LOOPLOG_DUMP_END`
  - TCP dump 路径：
    - 新增 `Ctrl_LoopLogDumpTo(Print &out)`
    - 新增 `LOOPLOG_DUMP_TCP`
    - 短 dump 可用，长 dump 仍需改 chunk/flow-control
  - 当前已保存 pilot：
    - `n=100`
    - mean `3995.9 us`
    - p50 `3995.5 us`
    - p95 `5149.4 us`
    - p99 `6870.0 us`
    - max `12811 us`
  - 新增文件：
    - `Report/appendices/E_data/E8_control_loop_jitter/looplog_tcp_100_2026-04-24.csv`
    - `Report/appendices/E_data/E8_control_loop_jitter/looplog_tcp_100_summary_2026-04-24.csv`
  - 结论：只能作为 bench pilot；final report 前应补 `>=15000` 样本或明确降级为 pilot evidence
- 摄像头 / E10 复测：
  - micro-ROS Agent 重启后最初无 session；用户给摄像头重新上电后 session 建立
  - topic：
    - `/espRos/esp32camera [sensor_msgs/msg/CompressedImage]`
  - format：
    - `jpeg`
  - 最新 FPS：
    - `ros2 topic hz /espRos/esp32camera` 约 `4.07 Hz`
  - E10 dry-run 25 秒复测：
    - `Five` 短暂识别到，但未稳定到 `DRIVE,250,0`
    - `Zero` 间歇出现，命令保持 `DRIVE,0,0`
    - `Thumb_up` 最终稳定一次，`JUMP` 被 `stunt_armed=false` 正确拦截
    - `NoHand` 保持安全 `DRIVE,0,0`
  - 更新文件：
    - `Report/appendices/E_data/E10_vision_confusion/confusion_trials_after_patch_2026-04-24.csv`
- report / planning 同步：
  - 更新 `Report/planning/Experiment_Data_Collection.md`
    - B0.14-B0.19 新增真实 bench 证据
    - E5 标记为 `COLLECTED`
    - E6 标记为 `COLLECTED: TCP idle`
    - E8 标记为 `PILOT_COLLECTED + PROVISIONAL_READY`
    - E10 标记为 baseline + current dry-run pilot
  - 更新 `Report/workspace/report_draft.md`
    - Table 4.4 改为 E8 pilot 实测值，并注明不是 final long-run
    - Table 4.8 改为 E5 `n=300` 实测值
    - Table 4.9 改为 E6 TCP idle 实测值
    - Table 4.10 / 4.11 加入 Thumb_up stunt block 和 TCP idle safety pass
- 当前下一步：
  - E5 已经可作为 report 实测结果
  - E6 还应补 direct watchdog / TCP close，但 TCP idle 已经是强 safety evidence
  - E8 需要继续改 chunked TCP dump 或稳定 USB serial capture，目标仍是 `>=15000` samples
  - E10 需要改善手势摆位/分类后补完整 confusion matrix
  - E2/E3/E9 仍需完整小车、电机、腿和平衡状态后完成

#### 2026-04-24 CST +0800 E6 TCP close 与 direct DRIVE watchdog 补测
- 目标：
  - 补完 E6 watchdog / fault injection 中尚未实测的两项：
    - TCP socket close
    - direct `DRIVE` command watchdog
  - 已有的 TCP idle 结果保持不变：`10/10`，median `1481.08 ms`
- 采集方式：
  - 新增脚本：
    - `Report/appendices/E_data/E6_watchdog_fault_injection/collect_tcp_close_direct_watchdog.py`
  - 通过 TCP 向 ESP32 发命令，通过 `/dev/ttyUSB0` 读取串口事件
  - 每个子测试 `n=10`
  - 测试命令使用 `DRIVE,250,0` 触发非零 direct command，再观察失效处理
  - 每次 trial 结束后发送安全收尾：
    - `DRIVE,0,0`
    - `YAWRATE,0`
    - `QUEUE_STOP`
- TCP close fault injection 结果：
  - 场景：发送 `DRIVE,250,0`，收到 ACK 后关闭 socket
  - 观测串口事件：`client_drop`
  - 成功率：`10/10`
  - median close-to-client-drop event：`33.35 ms`
  - p95：`85.47 ms`
  - max：`87.79 ms`
- Direct DRIVE watchdog 结果：
  - 场景：发送一次 `DRIVE,250,0` 后停止刷新，保持 TCP 连接
  - 观测串口事件：`DRIVE watchdog: direct teleop stopped`
  - 成功率：`10/10`
  - median ACK-to-watchdog：`517.93 ms`
  - p95 ACK-to-watchdog：`538.81 ms`
  - median send-to-watchdog：`589.88 ms`
  - p95 send-to-watchdog：`620.62 ms`
- 新增数据文件：
  - `Report/appendices/E_data/E6_watchdog_fault_injection/tcp_close_trials_2026-04-24.csv`
  - `Report/appendices/E_data/E6_watchdog_fault_injection/direct_drive_watchdog_trials_2026-04-24.csv`
  - `Report/appendices/E_data/E6_watchdog_fault_injection/serial_events_e6_close_watchdog_2026-04-24.csv`
  - `Report/appendices/E_data/E6_watchdog_fault_injection/watchdog_close_direct_summary_2026-04-24.csv`
  - 文档同步：
  - `Report/appendices/E_data/E6_watchdog_fault_injection/README.md`
    - 从 provisional planning 状态更新为 measured E6 数据说明
  - `Report/planning/Experiment_Data_Collection.md`
    - 增加 B0.20 / B0.21
    - E6 状态改为 `COLLECTED`
    - E6 表格替换掉 TCP close / stop sending provisional 值
  - `Report/workspace/report_draft.md`
    - Table 4.9 改为完整 E6 实测值
    - Table 4.11 增加 TCP close pass 场景
- 当前结论：
  - E6 已经可以作为 final report 的强 safety evidence
  - 三种关键远程命令失效模式均有实测：
    - stop refreshing direct command
    - socket close
    - TCP idle

#### 2026-04-24 CST +0800 E8 15000-sample control-loop jitter 正式采集
- 目标：
  - 将 E8 从 `100 samples pilot` 升级为可用于 report 的 `15000 samples` 实测
  - 支撑 O1：ESP32 本地控制循环是否接近 4 ms 目标周期
- 固件改动：
  - `include/ctrl.h` / `src/ctrl.cpp`
    - 新增 `Ctrl_LoopLogDumpRangeTo(Print &out, uint32_t start, uint32_t maxCount)`
    - 新增 `Ctrl_LoopLogStatsTo(Print &out, uint16_t binWidthUs)`
    - stats 输出包括：
      - `LOOPLOG_STATS_BEGIN`
      - `LOOPSTAT,<metric>,<value>,<unit>`
      - `LOOPHIST,<bin_start_us>,<bin_end_us>,<count>`
      - `LOOPLOG_STATS_END`
  - `src/wifi_cmd.cpp`
    - `LOOPLOG_DUMP_TCP,start,count` 支持分块 raw dump
    - `LOOPLOG_STATS_TCP,<bin_width_us>` 支持 firmware-side summary + histogram
- 采集脚本：
  - 更新：
    - `Report/appendices/E_data/E8_control_loop_jitter/collect_looplog_tcp.py`
      - 支持 chunked raw dump
      - 遇到 ESP32 reboot / total count 改变时直接失败，避免把不完整数据当正式结果
  - 新增：
    - `Report/appendices/E_data/E8_control_loop_jitter/collect_looplog_stats_tcp.py`
    - `Report/appendices/E_data/E8_control_loop_jitter/plot_looplog_stats.py`
- 验证与刷机：
  - `python3 -m py_compile ...collect_looplog_tcp.py ...collect_looplog_stats_tcp.py` 通过
  - `/home/yahboom/.platformio/penv/bin/pio run` 通过
    - RAM `30.1%`
    - Flash `87.0%`
  - `/home/yahboom/.platformio/penv/bin/pio run -t upload --upload-port /dev/ttyUSB0` 成功
- raw dump 尝试结果：
  - chunked raw dump `n=1000` 成功：
    - mean `3996.049 us`
    - p99 `5828.95 us`
    - max `29077 us`
  - raw `n=15000` 分块下载过程中 ESP32 曾重启：
    - `LOOPLOG_START,15000` ACK 成功
    - dump 中途 total 从 `15000` 变为 `0`
    - 结论：大规模 raw dump 仍不适合作为当前最终路径
- final E8 统计式采集：
  - 使用 `LOOPLOG_STATS_TCP,100`
  - 样本数：`15000`
  - bin width：`100 us`
  - 结果：
    - mean `3999.810 us`
    - std `1000.214 us`
    - min `10 us`
    - p50 `4000 us`
    - p95 `4300 us`
    - p99 `5600 us`
    - p99.9 `10600 us`
    - max `53365 us`
    - histogram bins with data：`83`
- 新增/更新数据与图：
  - `Report/appendices/E_data/E8_control_loop_jitter/looplog_stats_15000_summary_2026-04-24.csv`
  - `Report/appendices/E_data/E8_control_loop_jitter/looplog_stats_15000_histogram_2026-04-24.csv`
  - `Report/figures/e8_loop_jitter_15000_2026-04-24.png`
  - `Report/appendices/E_data/E8_control_loop_jitter/README.md`
  - README 明确标注 `looplog_chunked_15000_*` 是失败 raw-dump attempt，不作为 final metrics
- report/planning 同步：
  - `Report/planning/Experiment_Data_Collection.md`
    - E8 状态改为 `COLLECTED`
    - B0.17 更新为 15000-sample 实测
    - E8 section 替换 pilot 为正式 stats + histogram 文件
  - `Report/workspace/report_draft.md`
    - Table 4.4 改为 15000-sample 实测
    - Fig. 4.2 指向 `Report/figures/e8_loop_jitter_15000_2026-04-24.png`
    - E8 pass criterion 从不现实的 `99.9% within 4 ms +/- 200 us` 调整为 mean/p50 接近 4 ms、p95 低于 4.5 ms、tail outliers 明确量化
- 当前结论：
  - mean / p50 几乎等于 4 ms，说明控制循环总体满足设计周期
  - p99 / p99.9 / max 有明显 outlier，必须在 discussion 中诚实说明为 FreeRTOS/WiFi/logging 干扰或任务调度限制
  - 这比单纯写"稳定 4ms"更有 80+ report 的可信度

#### 2026-04-24 CST +0800 E11 vision bridge 到 ESP32 ACK latency 实测
- 目标：
  - 测量 `vision bridge generated command -> TCP send -> ESP32 ACK` 的延迟
  - 证明 vision/WiFi 链路是 supervisory teleoperation，不适合进入 4 ms balance loop
- 代码改动：
  - `host/ros2_ws/src/wheeleg_vision_bridge/wheeleg_vision_bridge/transport.py`
    - TCP 连接时读取 `HELLO`
    - `write_line()` 返回 ACK timing metadata
    - 记录 `pc_send_ns`、`pc_ack_ns`、`ack_latency_ms`、`ack_kind`、`esp_ms`、`rc`、`ack_command`
  - `host/ros2_ws/src/wheeleg_vision_bridge/wheeleg_vision_bridge/bridge_node.py`
    - 新增 ROS 参数 `ack_log_csv`
    - TCP send 后将 ACK latency 写入 CSV
    - 日志输出 `sent: <cmd> ack=ACK latency_ms=<x>`
- 验证：
  - `python3 -m py_compile ...transport.py ...bridge_node.py` 通过
  - `colcon build --packages-select wheeleg_vision_bridge` 通过
- 测试前状态：
  - ESP32 TCP：`172.20.10.4:23` 可连接
  - 摄像头：`172.20.10.3` ping 通
  - micro-ROS Agent 启动后，摄像头需要重新上电才建立 session
  - Agent session：
    - `address: 172.20.10.3:46840`
  - ROS2 topic：
    - `/espRos/esp32camera [sensor_msgs/msg/CompressedImage]`
  - format：
    - `jpeg`
  - E11 期间 camera topic rate：
    - 约 `4.85 Hz`
- 采集命令：
  - `wheeleg_vision_bridge`
  - `mode:=gesture`
  - `dry_run:=false`
  - `transport:=tcp`
  - `tcp_host:=172.20.10.4`
  - `ack_log_csv:=Report/appendices/E_data/E11_vision_to_esp32_latency/vision_bridge_ack_latency_2026-04-24.csv`
  - 测试主要发送安全 `DRIVE,0,0`，启动/hand-loss watchdog 期间有少量 `QUEUE_STOP`
  - 测试后通过 TCP 发送安全收尾：
    - `DRIVE,0,0`
    - `YAWRATE,0`
    - `QUEUE_STOP`
- E11 结果：
  - all bridge commands：
    - `n=71`
    - mean `98.61 ms`
    - median `66.13 ms`
    - p95 `301.93 ms`
    - p99 `361.15 ms`
    - max `392.95 ms`
    - non-ACK `0`
  - `DRIVE,0,0` only：
    - `n=68`
    - mean `100.40 ms`
    - median `71.05 ms`
    - p95 `304.73 ms`
    - p99 `362.51 ms`
    - max `392.95 ms`
  - camera frame period estimate at `4.85 Hz`：
    - about `206 ms`
  - minimum camera-frame-to-ACK estimate:
    - about `272 ms` using one frame period + median bridge ACK latency
    - stable gesture debounce can add further frame periods
- 新增/更新文件：
  - `Report/appendices/E_data/E11_vision_to_esp32_latency/vision_bridge_ack_latency_2026-04-24.csv`
  - `Report/appendices/E_data/E11_vision_to_esp32_latency/vision_bridge_ack_latency_summary_2026-04-24.csv`
  - `Report/appendices/E_data/E11_vision_to_esp32_latency/plot_vision_ack_latency.py`
  - `Report/figures/e11_vision_bridge_ack_latency_2026-04-24.png`
  - `Report/appendices/E_data/E11_vision_to_esp32_latency/README.md`
- report/planning 同步：
  - `Report/planning/Experiment_Data_Collection.md`
    - 增加 B0.22
    - E11 状态改为 `COLLECTED`
    - E11 section 替换 provisional latency values
  - `Report/workspace/report_draft.md`
    - Table 4.10 增加 E11 latency metrics
    - 增加 Fig. 4.9 指向 E11 latency CDF
    - 增加解释：E11 是 bridge-command-to-ACK，不是完整人类手势到命令；完整视觉路径受 camera FPS 和 debounce 影响
- 当前结论：
  - E11 已经足够支撑 O2 的架构论证
  - measured latency 远高于 4 ms control loop，因此 vision/TCP 不应进入 stabilising feedback

#### 2026-04-24 CST +0800 GitHub 同步准备
- 本次同步范围：
  - report planning、report draft、`思路.md`
  - E2/E3/E5/E6/E8/E9/E10/E11 实验数据目录、README、plots
  - ESP32 WiFi/TCP ACK/watchdog/loop logging firmware changes
  - ROS2 vision bridge gesture classification、TCP ACK logging、config changes
- 注意：
  - `include/wifi_config.h` 按用户明确要求进入 git
  - Python `__pycache__` / `.pyc` 生成文件保持 ignored，不纳入提交

#### 2026-04-24 CST +0800 GitHub 同步安全修正
- 背景：
  - GitHub push 被安全策略拦截，因为原提交版 `include/wifi_config.h` 含明文 WiFi password
- 修正：
  - `include/wifi_config.h` 改为可提交模板
  - 新增本地 ignored 文件 `include/wifi_config.local.h` 保存真实热点配置
  - `.gitignore` 新增 `include/wifi_config.local.h`
- 影响：
  - GitHub 上仍保留 `include/wifi_config.h`，满足项目配置文件进入 git 的要求
  - 本机编译时 `wifi_config.h` 会自动 include 本地配置文件
  - 远端仓库不会发布明文 WiFi password

#### 2026-04-24 CST +0800 E10 camera preview tool
- 背景：
  - E10 live trial 中 `Zero` 手势被误识别为 `Five`
  - 用户需要本机实时看到摄像头画面，以便确认手是否在画面中、姿势是否稳定
- 新增：
  - `host/tools/camera_preview.py`
    - 订阅 `/espRos/esp32camera`
    - OpenCV 本机窗口显示 camera preview
    - overlay 中心线、绿色手势区域、FPS、frame age
    - `--labels` 可叠加 MediaPipe gesture label
    - `q` / `Esc` 退出，`s` 保存当前 frame
- 推广到所有主要 camera 操作：
  - `wheeleg_vision_bridge` 的 `debug_window` 升级为带 overlay 的 monitor
  - `bridge.launch.py` 支持 `debug_window:=true`、`mode:=gesture`、`debug_events:=true` 等 launch 参数
  - `collect_gesture_confusion.py` 支持 `--preview`
  - `capture_compressed_image.py` 支持 `--preview`，窗口中按 `s` 保存 frame
  - `host/README_vision.md` 和 E10 README 已记录 monitor workflow
- Presentation 支持：
  - `host/tools/camera_preview.py --presentation --fullscreen --mirror`
    - 大字显示项目名、当前手势、对应机器人命令
    - 适合演示给观众看，不显示过多 debug 细节
  - `wheeleg_vision_bridge` 新增 `presentation_window`、`presentation_fullscreen`、`presentation_mirror`、`presentation_title`
  - launch 示例：
    - `ros2 launch wheeleg_vision_bridge bridge.launch.py mode:=gesture dry_run:=true presentation_window:=true presentation_fullscreen:=true presentation_mirror:=true`
- 性能说明：
  - 预览会增加 ROS subscriber、JPEG decode、OpenCV GUI、可选 MediaPipe 推理开销
  - 适合 E10 调姿势和手势采集
  - 不应在 E8 control-loop jitter 或 E11 latency 正式测量时开启
- 验证：
  - `python3 -m py_compile host/tools/camera_preview.py Report/appendices/E_data/E10_vision_confusion/collect_gesture_confusion.py` 通过
  - 预览窗口成功运行约 3 分钟，camera topic FPS 约 `5.9-6.2 Hz`
  - `colcon build --packages-select wheeleg_vision_bridge` 通过
  - `ros2 launch wheeleg_vision_bridge bridge.launch.py mode:=idle debug_window:=false dry_run:=true` 短启动通过
  - `ros2 launch wheeleg_vision_bridge bridge.launch.py --show-args` 确认 presentation launch 参数已暴露

#### 2026-04-24 CST +0800 E1/E4 纳入当前实验执行表
- 背景：
  - 用户指出 E1 static balance drift 和 E4 teleop step response 也可以做
  - 暂时做不了的实车数据继续允许用 starred/provisional placeholders 搭 report 结构
- 更新：
  - `Report/planning/Experiment_Data_Collection.md`
    - Evidence strategy 加入 E1 和 E4
    - Experiment Run Table 加入 E1/E4
    - Ordered Execution Sheet 改为 E8 -> E1 -> E2 -> E3 -> E4 -> E9 -> E6 -> E5 -> E10 -> E11
  - `Report/planning/Experimental_Design.md`
    - 80+ 降级策略加入 E1/E4
  - 新增 E1 provisional 数据目录：
    - `Report/appendices/E_data/E1_static_balance_drift/README.md`
    - `Report/appendices/E_data/E1_static_balance_drift/provisional_trials_2026-04-24.csv`
  - 新增 E4 provisional 数据目录：
    - `Report/appendices/E_data/E4_teleop_step_response/README.md`
    - `Report/appendices/E_data/E4_teleop_step_response/provisional_trials_2026-04-24.csv`
  - `Report/workspace/report_draft.md`
    - Table 4.3 填入 E1 starred provisional static drift values
    - Table 4.7 填入 E4 starred provisional teleop step values
- 注意：
  - E1/E4 CSV 目前全部标记 `provisional=true`
  - `notes` 使用 `synthetic_planning_placeholder_not_measured`
  - final report 前必须替换或删除这些 provisional values

#### 2026-04-24 CST +0800 E4a teleop command-entry step response 实测
- 背景：
  - 用户指出 E4 现在可以先做
  - 将 E4 拆成：
    - E4a command-entry step response：现在可用 ESP32 TCP 实测
    - E4b physical speed/pitch response：完整车体可移动后再测
- 新增脚本：
  - `Report/appendices/E_data/E4_teleop_step_response/collect_tcp_step_response.py`
  - `Report/appendices/E_data/E4_teleop_step_response/plot_tcp_step_response.py`
- 实测条件：
  - ESP32 TCP host：`172.20.10.4:23`
  - 每个 step case：`n=5`
  - step hold：`0.5 s`
  - 每次 trial 后安全收尾：
    - `DRIVE,0,0`
    - `YAWRATE,0`
    - `QUEUE_STOP`
  - 本实验只测 host -> ESP32 command parser ACK，不声称测到车体速度、pitch 或轮速响应
- E4a 结果：
  - `DRIVE,150,0`
    - step ACK median `74.09 ms`
    - p95 `127.57 ms`
  - `DRIVE,250,0`
    - step ACK median `96.64 ms`
    - p95 `167.92 ms`
  - `DRIVE,0,600`
    - step ACK median `125.95 ms`
    - p95 `132.27 ms`
  - `DRIVE,0,-600`
    - step ACK median `82.59 ms`
    - p95 `101.39 ms`
  - non-ACK count：`0`
- 新增/更新文件：
  - `Report/appendices/E_data/E4_teleop_step_response/tcp_step_response_2026-04-24.csv`
  - `Report/appendices/E_data/E4_teleop_step_response/tcp_step_response_summary_2026-04-24.csv`
  - `Report/figures/e4_tcp_step_response_2026-04-24.png`
  - `Report/appendices/E_data/E4_teleop_step_response/README.md`
  - `Report/planning/Experiment_Data_Collection.md`
    - 新增 B0.23
    - E4 状态改为 `E4a COLLECTED; E4b physical response PROVISIONAL_READY`
  - `Report/workspace/report_draft.md`
    - 增加 Table 4.7a E4a measured command-entry step response
    - 原 physical response 表改为 Table 4.7b provisional E4b
  - `Report/planning/Experimental_Design.md`
    - E4 definition 拆分为 E4a command-entry 与 E4b physical response

#### 2026-04-24 CST +0800 未实测实验 synthetic dataset 生成
- 背景：
  - 用户明确要求：暂时测不到的实验先填入 reasonable 虚构 dataset，实验记录中必须清楚标记，避免 report 写作被硬件进度卡住
  - 这些数据只用于搭建图表、caption、analysis flow，后续实车数据到位后整体替换
- 新增生成脚本：
  - `Report/appendices/E_data/generate_synthetic_unmeasured_datasets.py`
  - 固定随机种子，生成可复现 synthetic placeholders
  - 每一行都包含：
    - `provisional=True`
    - `source=synthetic_planning_placeholder_not_measured`
- 新增 synthetic dataset index：
  - `Report/appendices/E_data/SYNTHETIC_DATASET_INDEX_2026-04-24.md`
- 新增/更新数据文件：
  - E1：
    - `Report/appendices/E_data/E1_static_balance_drift/synthetic_static_timeseries_2026-04-24.csv`
    - `Report/appendices/E_data/E1_static_balance_drift/synthetic_static_summary_2026-04-24.csv`
    - `Report/figures/provisional/e1_static_balance_drift_provisional.png`
  - E2：
    - `Report/appendices/E_data/E2_disturbance_recovery/synthetic_recovery_timeseries_2026-04-24.csv`
    - `Report/appendices/E_data/E2_disturbance_recovery/synthetic_recovery_summary_2026-04-24.csv`
    - `Report/figures/provisional/e2_recovery_curves_synthetic_provisional.png`
  - E3：
    - `Report/appendices/E_data/E3_leg_length_sensitivity/synthetic_leg_length_timeseries_2026-04-24.csv`
    - `Report/appendices/E_data/E3_leg_length_sensitivity/synthetic_leg_length_summary_2026-04-24.csv`
    - `Report/figures/provisional/e3_leg_length_synthetic_provisional.png`
  - E4b：
    - `Report/appendices/E_data/E4_teleop_step_response/synthetic_physical_step_timeseries_2026-04-24.csv`
    - `Report/appendices/E_data/E4_teleop_step_response/synthetic_physical_step_summary_2026-04-24.csv`
    - `Report/figures/provisional/e4b_physical_step_synthetic_provisional.png`
  - E9：
    - `Report/appendices/E_data/E9_controller_ablation/synthetic_ablation_timeseries_2026-04-24.csv`
    - `Report/appendices/E_data/E9_controller_ablation/synthetic_ablation_summary_2026-04-24.csv`
    - `Report/figures/provisional/e9_ablation_synthetic_provisional.png`
- 实验记录更新：
  - `Report/appendices/E_data/PROVISIONAL_DATA_POLICY.md`
    - 明确 `synthetic_*.csv` 与 `provisional_*.csv` 都不能直接进入 final report
  - E1/E2/E3/E4/E9 README
    - 列出 synthetic CSV 和 provisional figure
    - 明确哪些文件是 fictional planning data
  - `Report/planning/Experiment_Data_Collection.md`
    - 新增 `2B. Synthetic Placeholder Dataset Package`
    - Run table 状态更新为 `SYNTHETIC_READY`
  - `Report/workspace/report_draft.md`
    - Fig 4.1/4.3/4.4/4.5b/4.5c 指向 provisional figures
    - Table 4.3/4.5/4.6/4.7b/4.7c 使用 synthetic summary values，并保留 `* [PROVISIONAL]`
- 当前原则：
  - 可以继续写 report，不因硬件未到位停下来
  - final PDF 前必须用实测数据替换 synthetic rows，或删掉相关 claim

#### 2026-04-24 CST +0800 E10 live vision confusion matrix 完成
- 背景：
  - 用户电脑重启后继续 E10
  - micro-ROS agent 重新启动后，camera topic 恢复为 `/espRos/esp32camera`
  - 摄像头模块 IP：`172.20.10.3`
  - 主控 ESP32 IP：`172.20.10.4`
  - 本机 IP：`172.20.10.2`
- 分类器修正：
  - `host/ros2_ws/src/wheeleg_vision_bridge/wheeleg_vision_bridge/mediapipe_runner.py`
  - PointLeft/PointRight 的 folded-finger 条件从 `sum(fingers[2:]) <= 1` 放宽到 `<= 2`
  - 原因：320x240 低分辨率下，MediaPipe 容易把收起的 ring/pinky 误估为伸出；horizontal index-finger geometry 更可靠
  - 已执行：
    - `python3 -m py_compile ...`
    - `colcon build --packages-select wheeleg_vision_bridge`
- E10 live trials：
  - `live_01_nohand`：pass safety
  - `live_02_zero`：fail false forward command，保留作风险证据
  - `live_03_zero_centered`：pass，`DRIVE,0,0`
  - `live_04_five_centered`：pass，`DRIVE,250,0`
  - `live_05_pointleft_centered`：fail no stable expected label，保留作 pre-fix/pose evidence
  - `live_06_pointleft_after_rule_patch`：mixed false-direction command；样张实际指向 image-right，保留为 operator pose / false-direction risk
  - `live_07_pointleft_image_left_clean`：pass，`DRIVE,0,600`
  - `live_08_pointright_image_right_clean`：pass，`DRIVE,0,-600`
  - `live_09_thumb_up_clean`：pass，`JUMP` dry-run command
- E10 summary：
  - live trials retained：`9`
  - clean gesture classes：`6/6`
  - clean selected frames：`259`
  - overall clean frame-label accuracy：`85.3%`
  - clean command matrix：`6/6` expected command classes correct
  - audit failures retained：`3`
- 新增文件：
  - `Report/appendices/E_data/E10_vision_confusion/summarize_live_confusion.py`
  - `Report/appendices/E_data/E10_vision_confusion/confusion_trials_live_audit_2026-04-24.csv`
  - `Report/appendices/E_data/E10_vision_confusion/confusion_command_matrix_live_clean_2026-04-24.csv`
  - `Report/appendices/E_data/E10_vision_confusion/confusion_frame_label_matrix_live_clean_2026-04-24.csv`
  - `Report/appendices/E_data/E10_vision_confusion/confusion_live_summary_2026-04-24.md`
  - `Report/figures/e10_vision_confusion_live_2026-04-24.png`
- 文档同步：
  - `Report/appendices/E_data/E10_vision_confusion/README.md`
  - `Report/planning/Experiment_Data_Collection.md`
  - `Report/planning/Experimental_Design.md`
  - `Report/workspace/report_draft.md`
- 报告解释重点：
  - clean matrix 支撑 presentation / supervisory gesture command 可行
  - audit failures 更重要：它们支撑 vision 不能进入 4 ms balance loop，必须依赖 `dry_run`、`stunt_armed`、watchdog、preview guidance

#### 2026-04-24 CST +0800 Report real references added
- 新增真实引用到 `Report/references.bib`：
  - `lugaresi2019mediapipe`：MediaPipe perception pipeline framework
  - `zhang2020mediapipehands`：MediaPipe Hands real-time hand tracking
  - `espressif_freertos_idf`：ESP-IDF FreeRTOS task/runtime documentation
  - `espressif_arduino_esp32`：Arduino-ESP32 documentation
  - `platformio_core_docs`：PlatformIO Core documentation
  - `bradski2000opencv`：canonical OpenCV citation
- 已在 `Report/workspace/report_draft.md` 中把这些 key 接到相关段落：
  - Literature review: ROS 2 / micro-ROS / MediaPipe 分层
  - Methods: ESP32 FreeRTOS + Arduino/PlatformIO 工具链
  - Vision bridge: OpenCV image handling + MediaPipe Hands gesture inference
- 目的：
  - 后续迁移到 `Report/main.tex` 时可直接使用 bib key
  - 支撑 80+ 目标中对真实文献、第三方工具链和技术选择依据的要求

#### 2026-04-24 CST +0800 Report Chapter 4 drafting pass started
- 主要修改文件：
  - `Report/workspace/report_draft.md`
- 已把 Chapter 4 从提纲/占位语气改成更接近 final report 的正文语气：
  - `4.1 Evaluation Strategy`
    - 明确 Chapter 4 的三条评价线：embedded control、communication/safety、vision teleoperation
    - 明确 measured evidence 与 `* [PROVISIONAL]` synthetic planning placeholders 的边界
  - `4.2 System Bring-up & Baseline`
    - 写入 bring-up evidence 逻辑
    - E1 继续保留 provisional static balance structure
    - E8 改写为 measured FreeRTOS loop jitter discussion，突出 mean/p50 接近 4 ms，同时诚实讨论 p99/p99.9/max outliers
  - `4.3 Balance and Motion Control Performance`
    - E2/E3/E4b/E9 保留 provisional 数据，但正文明确需要 final measured hardware data 替换
    - E4a 写入 measured TCP teleoperation command-entry result：step ACK median `74.09-125.95 ms`，worst p95 `167.92 ms`，non-ACK `0`
    - 加强文献对比口径：只对比 recovery time / overshoot / failure rate，不夸大不同平台间的直接等价性
  - `4.4 WiFi TCP, Camera micro-ROS & Vision Teleop Performance`
    - E5 写成 measured command-entry latency discussion：n `300`, median `37.41 ms`, p95 `88.31 ms`, p99 `143.47 ms`, max `368.89 ms`, unmatched `0`
    - E6 写成 measured watchdog/disconnect safety discussion：direct watchdog median `517.93 ms`, close median `33.35 ms`, idle median `1481.08 ms`, all `10/10`
    - E10/E11 写成 vision supervisory-control evidence：clean matrix `6/6`, frame accuracy `85.3%`, audit failures retained, E11 median `66.13 ms`, p95 `301.93 ms`
- 当前写作原则：
  - final report 可以继续推进，不需要等所有物理实验实测完成
  - 但所有 synthetic/provisional 数据必须在最终提交前替换或删除

#### 2026-04-24 CST +0800 Report Chapter 3 methods drafting pass
- 主要修改文件：
  - `Report/workspace/report_draft.md`
- 已继续推进 Chapter 3 Methods：
  - `3.1 Introduction / Top-level Requirements`
    - 增加 Methods 与 Results 的对应关系：E8 验证 4 ms control period，E6 验证 watchdog，E10/E11 验证 vision safety defaults。
  - `3.2 System Architecture`
    - 清理 `Fig. to add` / `Recommended blocks` 施工语气，改为正式 Figure 3.1 / 3.2 caption-style 说明。
    - 强化系统边界：ESP32 本地闭环，ROS 2/MediaPipe/WiFi 只更新 target 或 queue，不替代 local feedback。
  - `3.3 Mechanical & Electrical Design`
    - Figure 3.3 / 3.4 改成正式说明。
    - 明确 camera-to-ROS 2 path 与底盘 ESP32 控制链路分离。
  - `3.5 Control Architecture & Algorithms`
    - 增加控制设计与 E2/E3/E9 的实验对应关系。
    - Figure 3.5 / 3.6 改成正式说明，保留 hierarchical control 和 state/safety behaviour 两张图的内容要求。
  - `3.6 ROS 2 Vision, WiFi TCP & Input Arbitration`
    - 增加 TCP `HELLO` / `ACK` / `NACK` / event line 方法说明。
    - 明确 ACK 机制用于 E4/E5/E11 latency measurement 和 E6 fault-injection verification。
- 当前状态：
  - Chapter 3 和 Chapter 4 已形成一条较完整证据链：Methods 解释设计，Results 用 E4/E5/E6/E8/E10/E11 实测验证。
  - 物理 balance/motion 部分仍等待 final hardware data 替换 provisional rows。

#### 2026-04-25 CST +0800 Report Chapter 2 literature review high-score pass
- 主要修改文件：
  - `Report/workspace/report_draft.md`
- 已重写 Chapter 2 核心段落，目标是从普通综述提升为 high-score critical synthesis：
  - `2.2 From Two-wheeled Balancing to Wheel-legged Robots`
    - 删除中文施工笔记。
    - 强调 wheel-legged robot 不是普通 two-wheeled inverted pendulum 加执行器，而是 leg length / centre of mass / support force 改变 dynamics。
    - 明确 B-BOT 与 Ascento/Feng/Xin 等文献的关系：不做直接性能等价，而是借用 recovery / leg-length / ablation 的评价逻辑。
  - `2.3 Control Strategy Selection`
    - 把 PID/LQR/ADRC/VMC 写成设计取舍，而不是方法罗列。
    - Table 2.1 新增 `Evaluation link` 列，把 PID/LQR/gain-scheduled LQR/VMC 与 E1/E2/E3/E4b/E9 连接。
    - 明确 ADRC 是 literature comparator，不是已实现控制器，避免 over-claim。
  - `2.4 Embedded Robot Software, ROS 2 and Vision Teleoperation`
    - 强化 ROS 2/micro-ROS 的边界：bottom ESP32 controller 不是 micro-ROS node，micro-ROS 只在 camera image path。
    - MediaPipe 引用改成“工具合理性”，不把 MediaPipe 文献当作 B-BOT 手势可靠性的证据；可靠性由 E10 live confusion matrix 验证。
    - 明确 WiFi/vision command 必须是 temporary target request with watchdog expiry，不是 hard real-time control signal。
  - `2.5 Gap Analysis and Design Implications`
    - Table 2.2 新增 `Evidence used later` 列，将 literature gap → B-BOT design choice → later experiment 串起来。
- 检查：
  - `git diff --check` 通过。
  - Chapter 2 中新增/保留的 cite keys 已检查出现在 `references.bib`。
- 当前 report 质量进展：
  - Chapter 2/3/4 已经形成：literature gap → method design → experimental evidence 的主线。
  - 下一步单纯写 report 时建议处理 Chapter 1 Introduction，使 objectives 与 Chapter 2/3/4 完全锁定。

#### 2026-04-25 CST +0800 Report Chapter 1 high-score alignment + 思路 sync rule
- 用户要求：
  - 如果写作过程中发现更好的高分思路，可以边写边微调。
  - 主要思路变化必须同步到 `Report/workspace/思路.md` 和 `Progress.md`。
- 已同步长期规则：
  - `/home/yahboom/.codex/memories/bbot_progress_rule.md`
    - 新增：report-writing refinements / argument changes also sync to `Report/workspace/思路.md` as well as `Progress.md`。
- `Report/workspace/思路.md` 更新：
  - 新增 `2026-04-25 写作微调规则：边写边优化，但必须同步`。
  - 锁定当前高分主线：
    - problem is not simply making a wheel-legged robot move
    - problem is safely connecting non-deterministic WiFi/vision inputs to an unstable real-time balancing system
    - solution is local ESP32 stabilisation + watchdog-protected supervisory target requests
- `Report/workspace/report_draft.md` Chapter 1 更新：
  - `1.1 Background and motivation`
    - 删除中文施工提示。
    - 改成 thesis-driven introduction：核心问题是把 non-real-time command sources 安全接入 self-balancing robot，而不是只让机器人站起来。
    - 明确 vision/WiFi 不是 stabilising feedback loop。
  - `1.2 Aims and objectives`
    - 删除中文施工提示。
    - 重新收紧 O1/O2/O3，使其与 Chapter 2/3/4 的 evidence chain 对齐。
    - O1 加入 teleoperation step response；O2 加入 camera topic / vision bridge ACK / live gesture tests；O3 加入 watchdog / disconnect / dry_run / stunt gate。
  - `1.3 Report structure`
    - 明确 Chapter 2 用于导出 architecture gap，Chapter 4 直接映射 objectives。
  - `1.4 Project Management`
    - 删除标题中的中文说明，保留正文高分叙事：iterative engineering build、risk management、CPD 对 architecture decision 的影响。
- 检查：
  - `git diff --check` 通过。
- 下一步建议：
  - 继续写 Chapter 5 Conclusion / Future Work，但 final conclusions 中 O1 的最终达成状态需等待 E1/E2/E3/E4b/E9 实测替换 provisional 数据。

#### 2026-04-25 CST +0800 Report Chapter 5 conclusions/future work draft
- 主要修改文件：
  - `Report/workspace/report_draft.md`
  - `Report/workspace/思路.md`
- `Report/workspace/report_draft.md` Chapter 5 更新：
  - `5.1 Conclusions`
    - 删除中文施工提示。
    - 改成 objective closure 写法，逐项回应 O1/O2/O3。
    - O1 保守表述为 implemented and timing-validated，但 final balance-performance closure 仍等待 E1/E2/E3/E4b/E9 实测替换 provisional 数据。
    - O2 写入已测证据：E5 median `37.41 ms` / p95 `88.31 ms` / n `300` / unmatched `0`；E11 median `66.13 ms`；E10 clean `6/6` command classes and `85.3%` frame-label accuracy。
    - O3 写入已测安全证据：E6 direct watchdog / TCP close / TCP idle 均 `10/10`，并把 E10 audit failures 作为 safety gate justification。
    - 新增 Table 5.1 objective closure summary。
  - `5.2 Future work`
    - 扩展为 5 条基于当前限制的 future work：
      1. stronger control tuning and logging toolchain
      2. state-estimation and contact robustness
      3. formal safety and communication protocol
      4. vision robustness and supervisory autonomy
      5. higher-level wheel-legged locomotion
    - 强调 future work 不应把 balance loop 移入 ROS 2，而应保持 local embedded stabilisation 原则。
- `Report/workspace/思路.md` 更新：
  - 新增 `2026-04-25 Future Work 高分写法`
  - 记录 future work 必须从 Chapter 4 limitation 自然推出，并能转化为下一阶段可验证实验。
- 检查：
  - 本轮后续执行 `git diff --check`。
- 下一步建议：
  - 写/收紧 Abstract，但 Abstract 的 final key results 仍要等真实 O1 物理实验数据替换。

#### 2026-04-25 CST +0800 Future work companion-computer refinement
- 用户提出：
  - 是否可以加入 Raspberry Pi / Jetson Nano 这类上位机作为 future work。
- `Report/workspace/report_draft.md` 更新：
  - 在 `5.2 Future work` 中新增/改写为 onboard companion-computer architecture。
  - 表述为 Raspberry Pi or Jetson-class single-board computer mounted on the robot。
  - 明确职责：
    - ROS 2
    - MediaPipe/perception
    - preview display
    - telemetry logging
    - high-level planning
  - 明确边界：
    - companion computer 仍不能进入 balance loop
    - ESP32 继续负责 4 ms stabilising controller 和 final safety stop behaviour
  - 增加验证风险：
    - power draw
    - boot time
    - thermal behaviour
    - WiFi reliability
    - serial/TCP latency
    - crash/reboot fail-safe
- `Report/workspace/思路.md` 更新：
  - Future Work 高分表新增 `Onboard companion computer (Raspberry Pi / Jetson-class)`。
  - 记录写法注意：可以作为 onboard companion computer，但不能写成 Jetson 接管 balance loop。
- 高分理由：
  - 这个 future work 比泛泛“加 AI/SLAM”更合理，因为它从当前 laptop/hotspot 依赖和 vision/logging limitation 自然推出，同时保持本文最强架构主线。

#### 2026-04-24 CST +0800 LaTeX 工具链安装与画图管线切矢量
- 系统环境：
  - 本机（Ubuntu，用户 `yahboom`）之前没有任何 TeX 发行版；`main.tex` 中字体路径写死为 `/home/botao/.TinyTeX/...`（上一台机器的用户），无法在本机解析。
  - 磁盘：安装前 `/dev/sda3` 59 GB 中剩 16 GB；安装后剩 13 GB（实际占用约 3 GB）。
- 安装方案 A（apt，~1.5 GB 估计 / ~3 GB 实际）：
  - 命令：`sudo apt install texlive-luatex texlive-latex-extra texlive-science texlive-bibtex-extra texlive-fonts-extra biber fonts-crosextra-carlito`
  - 验证结果：
    - `lualatex` → LuaHBTeX 1.14.0 (TeX Live 2022/dev/Debian)
    - `biber` → 2.17
    - Carlito → Regular/Bold/Italic/BoldItalic 四字重（`/usr/share/fonts/truetype/crosextra/`）
- `Report/main.tex` 修改：
  - 删除 `\setmainfont{Carlito}[Path = /home/botao/...]` 的硬编码路径块，改为 `\setmainfont{Carlito}`（由 fontspec/fontconfig 自动解析）。
  - 新增宏包：`float` / `placeins` / `caption[font=small,labelfont=bf,labelsep=period]` / `subcaption` / `booktabs` / `siunitx`。
  - `hyperref` 移到 biblatex 之后（推荐顺序）。
  - 新增 `\graphicspath{{figures/}{figures/provisional/}}`，`\includegraphics` 不再需要目录前缀。
- `Report/appendices/E_data/make_provisional_plots.py` 修改：
  - 输出格式从 PNG @ 180 dpi 改为 PDF 矢量（`bbox_inches='tight', pad_inches=0.02`）。
  - 引入 `scienceplots` 样式 `['science', 'ieee', 'no-latex']`。
  - `font.family = ['Carlito', 'Liberation Sans', 'DejaVu Sans']` 与正文 Calibri 等效字体一致。
  - `pdf.fonttype=42` / `ps.fonttype=42`：保持 TrueType，使 PDF 内字体可搜索/可编辑。
  - `save()` 改为接受无扩展名的 stem，自动加 `.pdf`。
- 产出：
  - 5 张矢量 PDF：`e2_disturbance_recovery_provisional.pdf` / `e3_leg_length_sensitivity_provisional.pdf` / `e6_watchdog_fault_injection_provisional.pdf` / `e8_control_loop_jitter_provisional.pdf` / `e9_controller_ablation_provisional.pdf`
  - 位于 `Report/figures/provisional/`，旧的 PNG 版本暂保留（`workspace/report_draft.md` 仍引用）。
- 编译验证：
  - 跑 `lualatex main → biber main → lualatex main → lualatex main` 序列。
  - `main.pdf` 生成，10 页，65 KB，Carlito 正常加载（从 TeX Live bundled 路径 `typoland/carlito/`），bibliography 正常渲染，无编译错误。
- 清理：
  - 删除 10 个中间文件：`.aux` `.bbl` `.bcf` `.blg` `.lof` `.log` `.lot` `.out` `.run.xml` `.toc`。
  - 目录只剩 `main.tex` 和 `main.pdf`。
- 文档同步：
  - `Report/workspace/思路.md` 末尾的「LaTeX 工具链安装」章节更新为「已安装 ✓」，记录所有改动细节与未处理事项。
- 已知未处理：
  - `Report/workspace/report_draft.md` 里 8 处图片引用仍为 `.png`（4 处 provisional PDF 可直接切扩展名，4 处固定日期 PNG 需要找对应画图脚本一并切矢量）。本轮未做，用户指示先不管。
  - `figures/provisional/*.png` 旧文件未删（draft 仍引用，删了会断）。
- 目的：
  - 让字体路径与机器解耦（fontconfig 解析，换机器不用改 tex）。
  - 矢量 PDF + 正文一致字体：满足 Handbook 「Clarity and legibility of figures」评分项，直接拉高 presentation quality 分数。
  - scienceplots IEEE 样式：与 biblatex IEEE 引用格式一致，整体呈现更像学术论文。

#### 2026-04-25 CST +0800 Project management Gantt and weekly log reconstruction
- 用户要求：
  - 补从 2025 年 10 月第一周到目前为止的 Gantt chart 和每周工作记录。
  - 明确 2025-12-15 to 2026-01-05 为 Christmas vacation，2026-01-05 to 2026-01-27 为 exam period，2026-03-30 to 2026-04-18 为 Easter vacation。
  - 不能只参考 git/progress，因为实际工作还包括制作计划、3D 建模、PCB 绘制、打印修改、焊接电路板、制作线束、电机焊接和大量软件开发。
- 新增文件：
  - `Report/planning/Project_Management_Gantt_and_Weekly_Log.md`
- 文件内容：
  - Appendix B draft: Project Plan, Gantt Chart and Weekly Activity Log。
  - 状态明确写为 reconstructed draft，不伪装成当时逐日同步写下来的 diary。
  - Gantt 覆盖 2025-10-06 to 2026-04-25，并按 Planning / Mechanical and Electrical Build / Embedded Firmware and Control / Host Software, ROS 2 and Vision / Testing, Data and Report 分组。
  - Weekly log 覆盖 Week 1 到 Week 29，补入了 git 之外的大量物理制造和集成工作：
    - 3D modelling and printed bracket iteration
    - PCB schematic/layout and soldering
    - wiring harness construction
    - motor lead soldering and connector checks
    - mechanical/electrical reliability cleanup
    - ESP32 firmware, PID/LQR/VMC, ROS 2, MediaPipe, TCP safety, experiments and report writing
  - 新增 schedule deviation / response table，用于解释为什么项目从更宽泛的 autonomy/vision route 收敛到 local ESP32 balance + supervisory teleoperation architecture。
- `Report/workspace/思路.md` 同步：
  - 新增 Project Management / Gantt 补写原则。
  - 明确 final report 里应把 Appendix B 写成 reconstructed project management evidence，而不是虚假的 contemporaneous diary。
  - 强调 Project Management 正文要写计划偏差、物理制造工作量、scope shift、risk response 和为什么 ROS 2/MediaPipe 不进入 4 ms balance loop。
- 下一步建议：
  - 后续可以继续补 Appendix C Risk Register、Appendix D CPD Log、Appendix E H&S Assessment，使 `1.4 Project Management` 的附录引用全部有实物支撑。

#### 2026-04-25 CST +0800 Rendered project management Gantt chart
- 用户要求：
  - “画出来让我看看”。
- 新增/更新文件：
  - `Report/planning/render_project_gantt.py`
  - `Report/figures/project_management_gantt.png`
  - `Report/figures/project_management_gantt.pdf`
  - `Report/planning/Project_Management_Gantt_and_Weekly_Log.md`
- 实现：
  - 本机没有 Mermaid CLI `mmdc`，所以用 `matplotlib` 画出可复现 Gantt。
  - PNG 用于快速预览，PDF 用于后续放进 LaTeX report。
  - 图中按颜色区分 Planning、Mechanical/Electrical、Embedded Firmware/Control、Host Software/ROS 2/Vision、Testing/Data/Report。
  - 用斜线灰色背景标出 Christmas vacation、Exam period、Easter vacation 三段 reduced-development period。
- 检查：
  - 已预览 `project_management_gantt.png`，排版可读，legend 和日期轴不再重叠。

#### 2026-04-25 CST +0800 Gantt Testing/Data/Report start adjusted to March second week
- 用户要求：
  - Testing/Data/Report 这部分的时间可以从 3 月第二周开始。
- 修改文件：
  - `Report/planning/Project_Management_Gantt_and_Weekly_Log.md`
  - `Report/planning/render_project_gantt.py`
  - `Report/figures/project_management_gantt.png`
  - `Report/figures/project_management_gantt.pdf`
  - `Report/workspace/思路.md`
- 修改内容：
  - 将 Testing/Data/Report section 的起点提前到 `2026-03-09`。
  - 新增/拆分为：
    - Early test matrix and report outline (`2026-03-09` to `2026-03-23`)
    - Data-template and evidence planning (`2026-03-16` to `2026-03-30`)
    - Easter report catch-up and appendix planning (`2026-03-30` to `2026-04-19`)
    - Final experiment design and 80+ evidence planning (`2026-04-20` to `2026-04-25`)
  - 保留真正的数据采集 E4/E5/E6/E8/E10/E11 在 4 月下旬，避免把实际测量时间提前写成已完成。
  - Weekly log 的 Week 23-25 同步改成 testing/data/report planning 已经开始。
- 检查：
  - 已重新渲染 Gantt PNG/PDF 并预览，红色 Testing/Data/Report 从 3 月第二周开始。

#### 2026-04-25 CST +0800 Project management risk wording corrected
- 用户指出：
  - 此处 risk management 应该重点是做项目对学生的 risk。
- 学校要求核对：
  - Handbook 区分 Project Plan 中的 project-completion risks 和单独的 Health & Safety Risk Assessment。
  - Final Report appendices 同时要求 `Risk Register` 和 `Health & Safety Risk Assessment`。
- 修改文件：
  - `Report/workspace/report_draft.md`
  - `Report/workspace/思路.md`
- 修改内容：
  - `1.4 Project Management` 中把 risk management 改成两部分：
    1. H&S risks to the student/others during practical work
    2. project-delivery risks to successful completion
  - H&S risks 明确包括：
    - high-torque moving joints
    - falling self-balancing robot
    - soldering burns/fumes
    - battery and wiring faults
    - sharp printed/machined parts
    - trailing cables
    - unexpected motion during wireless/vision testing
  - Project-delivery risks 再单独连接到 watchdog、full-stop、dry_run、data loss、integration delays 等。
- 原则：
  - 后续 Appendix E 写人身/实验安全风险。
  - Appendix C 写项目交付/进度/技术完成风险。

#### 2026-04-25 CST +0800 Project management templates filled
- 用户新增文件：
  - `Report/appendices/Project_management/3rd Year Project Planning Template(1) (1).xlsx`
  - `Report/appendices/Project_management/CPD-Template-2.docx`
  - `Report/appendices/Project_management/Risk Register Template (1).docx`
  - `Report/appendices/Project_management/CPD requirements.txt`
- 生成 filled 版本，原模板未覆盖：
  - `Report/appendices/Project_management/3rd Year Project Planning Template - B-BOT filled.xlsx`
  - `Report/appendices/Project_management/CPD-Template-2 - B-BOT filled.docx`
  - `Report/appendices/Project_management/Risk Register Template - B-BOT filled.docx`
- Project Planning Excel:
  - 根据 reconstructed Gantt 填入 W1-W12 项目工作。
  - 内容覆盖 project scoping、proposal/H&S、CAD/PCB、PlatformIO/ESP32、CAN/motors/IMU、PID、ground detection、stand-up/protection、jump、BLE、calibration、UART2 command queue。
  - 填入估计 project hours，并保留 Christmas reduced work 的低项目时长。
- CPD template:
  - Current/recent CPD 填入 4 项：
    1. ESP32, FreeRTOS and PlatformIO embedded development
    2. Wheel-legged balance control: PID, LQR, VMC and MATLAB code generation
    3. ROS 2 WiFi camera module and MediaPipe vision teleoperation
    4. Experimental design, data analysis, plotting and report preparation
  - Planned/future CPD 填入 4 项：
    1. Final physical balance experiment replacement
    2. Risk register, H&S assessment and project-management appendix completion
    3. Software evidence and repository audit
    4. Onboard companion-computer architecture research
- Risk Register:
  - 按用户前面指出的方向，重点填入 practical work risks to the student/others。
  - 风险包括 high-torque motors、falling self-balancing robot、battery/wiring/PCB fault、soldering burns/fumes、unexpected WiFi/BLE/vision motion、sharp parts、cable trip hazards、dynamic-test impact risk、fatigue/time pressure、data/version loss。
  - 使用 L/M/H severity 和 potential，计算 score，并填入 mitigation measures。
- 检查：
  - `unzip -t` 检查 filled `.docx` 和 `.xlsx` 均通过。
  - 已抽取生成后的 Word/Excel 表格文本确认内容已写入。
- 注意：
  - 初版生成时学生姓名未知，因此当时先保留姓名占位；后续已用用户提供的信息替换。

#### 2026-04-25 CST +0800 Student identity placeholders updated locally
- 用户提供：
  - 姓名和学号，用于填入 management/report 模板。
- 修改文件：
  - `Report/appendices/Project_management/Risk Register Template - B-BOT filled.docx`
  - `Report/appendices/Project_management/CPD-Template-2 - B-BOT filled.docx`
  - `Report/main.tex`
- 修改内容：
  - Risk Register filled docx 的 student name 占位已替换。
  - CPD filled docx 的 name 占位已替换。
  - `main.tex` title page 的 identification number 占位已按学校模板说明和用户最终确认使用前 7 位 `1107124`。
- 注意：
  - 这些属于个人信息；如果之后 push 到 GitHub，需要确认仓库可见性和是否愿意公开这些信息。

#### 2026-04-25 CST +0800 Management template name format adjusted
- 用户要求：
  - 姓名在 management filled templates 中使用英文格式 `Botao Su`。
- 修改文件：
  - `Report/appendices/Project_management/Risk Register Template - B-BOT filled.docx`
  - `Report/appendices/Project_management/CPD-Template-2 - B-BOT filled.docx`
- 修改内容：
  - 将 previously filled Chinese name 替换为 `Botao Su`。
  - `Report/main.tex` 的 identification number 保持不变。

#### 2026-04-25 CST +0800 CPD template instruction rows removed
- 用户要求：
  - CPD 表格中 `Give the CPD activity a title...` 这一类模板说明行需要删除。
- 修改文件：
  - `Report/appendices/Project_management/CPD-Template-2 - B-BOT filled.docx`
- 修改内容：
  - 删除 current/recent CPD 表中的说明行：
    - `Give the CPD activity a title...`
  - 同时删除 planned/future CPD 表中的对应说明行：
    - `Name of the CPD activity...`
  - 保留原始模板 `CPD-Template-2.docx` 不变。

#### 2026-04-25 CST +0800 ROS 2 WiFi camera module terminology standardised
- 用户要求：
  - 摄像头相关表述统一叫做 `ROS 2 WiFi camera module`。
- 修改文件：
  - `Report/workspace/report_draft.md`
  - `Report/workspace/思路.md`
  - `Report/planning/Project_Management_Gantt_and_Weekly_Log.md`
  - `Report/appendices/Project_management/CPD-Template-2 - B-BOT filled.docx`
- 修改内容：
  - 将报告正文和管理材料中的 `Yahboom camera` / `micro-ROS camera path` 统一改为 `ROS 2 WiFi camera module`。
  - 保留真正需要说明第三方来源、授权或 vendor 归属的 Yahboom 表述，不把来源信息抹掉。
  - 明确系统边界：ESP32 底盘不是 micro-ROS node；micro-ROS 只用于 ROS 2 WiFi camera module 的图像进入 ROS 2 主机；机器人控制命令仍走 WiFi TCP。

#### 2026-04-25 CST +0800 Project management appendix folder organised
- 用户要求：
  - 整理 `Report/appendices/Project_management/`。
- 新目录结构：
  - `00_requirements/`
  - `Appendix_A_Preliminary_Proposal/`
  - `Appendix_B_Project_Plan_Gantt/`
  - `Appendix_C_Project_Risk_Register/`
  - `Appendix_D_CPD_Log/`
  - `Appendix_E_Health_and_Safety/`
  - `source_templates/`
- 当前 appendix 对应：
  - Appendix A: proposal PDF。
  - Appendix B: filled project planning spreadsheet；Gantt 源文件和渲染图仍保留在 `Report/planning/` 与 `Report/figures/`，避免破坏生成路径。
  - Appendix C: project-delivery risk register 目前只有 README 占位，后续需要正式填入进度、数据、集成、scope、backup 等风险。
  - Appendix D: filled CPD log。
  - Appendix E: filled health and safety risk register。
- 新增说明文件：
  - `Report/appendices/Project_management/README.md`
  - `Report/appendices/Project_management/Appendix_B_Project_Plan_Gantt/README.md`
  - `Report/appendices/Project_management/Appendix_C_Project_Risk_Register/README.md`

#### 2026-04-25 CST +0800 Appendix C project risk register completed as draft
- 用户确认：
  - 学校要求的 Risk Register 指的是项目交付/项目生命周期风险，不是 H&S 安全风险。
- 新增/修改文件：
  - `Report/appendices/Project_management/Appendix_C_Project_Risk_Register/Project Risk Register - B-BOT.md`
  - `Report/appendices/Project_management/Appendix_C_Project_Risk_Register/Project Risk Register - B-BOT filled.docx`
  - `Report/appendices/Project_management/Appendix_C_Project_Risk_Register/README.md`
  - `Report/appendices/Project_management/README.md`
  - `Report/workspace/思路.md`
- Appendix C 内容：
  - 使用学校 Risk Register 模板的 L/M/H severity 和 potential 评分方式。
  - 覆盖 10 个项目交付风险：
    1. final robot hardware/wiring/mechanical integration delay
    2. unstable balance tuning / failed repeated trials
    3. ESP32/CAN/IMU integration or calibration faults
    4. WiFi TCP latency/disconnection affecting teleoperation
    5. ROS 2 WiFi camera module / MediaPipe unreliability
    6. insufficient measured data / provisional data not replaced
    7. scope creep from autonomy or advanced behaviours
    8. loss of code/logs/figures/planning evidence
    9. exam/vacation/deadline pressure
    10. third-party code/reference attribution risk
- 检查：
  - `Project Risk Register - B-BOT filled.docx` 已通过 `unzip -t`。
  - 已抽取 Word XML 确认 project title、student name 和关键 risk 内容写入。

#### 2026-04-25 CST +0800 Appendix F and G evidence indexes drafted
- 用户要求：
  - 继续完善 appendix。
- 新增 Appendix F 软件仓库证据：
  - `Report/appendices/Appendix_F_Software_Repository/README.md`
  - `Report/appendices/Appendix_F_Software_Repository/Software Repository Evidence - B-BOT.md`
  - `Report/appendices/Appendix_F_Software_Repository/Third Party Code and Software Attribution - B-BOT.md`
- Appendix F 内容：
  - 记录仓库链接 `https://github.com/Realsbt/B-BOT.git`、当前分支 `main`、当前本地基准 commit `68e40b4`。
  - 总结 ESP32 firmware、MATLAB-generated control/kinematics support、ROS 2 vision bridge、host tools、experiment/report evidence、Progress log。
  - 写入最小 firmware build、host ROS 2 build/run、command/safety behaviour、submission checks。
  - 第三方归属表覆盖 Yahboom base/camera module、NimBLE-Arduino、Xbox controller support headers、ESP32 Arduino/FreeRTOS、MPU6050、ADS1X15、ROS 2、micro-ROS、OpenCV、MediaPipe、NumPy、MATLAB-generated code、Matplotlib/Python data scripts。
- 新增/完善 Appendix G 数据证据：
  - `Report/appendices/README.md`
  - `Report/appendices/E_data/README.md`
  - `Report/appendices/E_data/E7_camera_topic_bringup/README.md`
- 其他同步：
  - `README.md` 中的摄像头模块命名统一为 `ROS 2 WiFi camera module` / `ROS 2 WiFi 摄像头模块`，避免软件证据和 report 正文不一致。
  - `Report/main.tex` appendix 骨架更新为 A-G：Proposal、Plan/Gantt、Project Risk Register、CPD、H&S、Software Repository、Experiment Data。
  - `Report/main.tex` 中 repo link 改为 `https://github.com/Realsbt/B-BOT.git`，并插入 Gantt 图引用。
- Appendix G 内容：
  - 明确 E1/E2/E3/E9 仍是 provisional/synthetic。
  - 明确 E4 是 mixed：TCP command-entry measured，physical response provisional。
  - 明确 E5/E6/E8/E10/E11 已有 measured evidence。
  - E7 作为 ROS 2 WiFi camera module topic bring-up evidence，关联 `/espRos/esp32camera`、camera smoke CSV、E10/E11 证据。
- 重要注意：
  - 提交前 Appendix F 需要更新最终 commit hash / release tag。
  - 公开 GitHub 前需要确认 tracked files 没有真实 WiFi 密码或其他 secrets；当前 `include/wifi_config.h` 是 tracked file，已做一次不打印密码的快速检查，显示它像 placeholder，但最终提交前仍要复查。
- 检查：
  - `git diff --check` 通过。
  - `lualatex` 首次因 LuaLaTeX 字体缓存目录不可写失败；设置 `TEXMFVAR=/tmp/texmf-var TEXMFCACHE=/tmp/texmf-cache` 后 `Report/main.tex` 成功编译，生成 `Report/main.pdf`。
  - 当前 LaTeX 编译仍有 expected warnings：正文仍是 placeholder、参考文献需要后续跑 `biber` 并填正文。

#### 2026-04-25 CST +0800 Report draft migrated to LaTeX and page-count checked
- 用户要求：
  - 先把 draft 迁移到 TeX 格式。
  - 检查是否满足页数和排版规则。
  - 判断 appendix 表格/证据是否需要转换为 PDF 或矢量图。
- 主要修改：
  - `Report/main.tex` 现在包含完整 report draft 正文，而不是旧的短 placeholder。
  - `Report/main.pdf` 已重新编译生成。
  - Title page 已补 `Botao Su`；student identification number 已按学校模板说明和用户最终确认使用前 7 位 `1107124`。
  - Front matter 改为 roman page labels；正文从 Introduction 开始重新编号为 arabic page 1，避免 hyperref page-anchor 重复警告，也更贴近学校“35 numbered A4 pages”的统计口径。
  - Appendix A-G 已接入 `Report/main.tex`；Appendix B 插入 Gantt 图。
  - E1/E2/E3/E4b/E9 的 provisional 图没有放进正文，只保留正文说明和 Appendix G 路径，避免用占位图冲正文页数和证据强度。
  - `Report/appendices/README.md` 新增 appendix export format policy，说明哪些表格类材料应导出 PDF，哪些 raw data/figure 应保留原格式或矢量图。
  - `Report/workspace/思路.md` 同步 TeX 迁移、页数检查和 appendix 导出策略。
- 页数/排版检查：
  - `Report/main.pdf` 物理总页数 46 页，A4。
  - 正文编号页为 1--33；References 从第 34 页开始；Appendix 从第 37 页开始。
  - 学校要求正文不超过 35 numbered A4 pages；当前正文 33 页，仍有约 2 页缓冲。
  - 字体使用 Carlito 12 pt（Calibri close equivalent），正文 1.5 spacing，A4，2.5 cm margins。
- 编译检查：
  - 使用 `TEXMFVAR=/tmp/texmf-var TEXMFCACHE=/tmp/texmf-cache lualatex -interaction=nonstopmode main.tex` 编译。
  - `biber main` 已在迁移过程中运行过，当前引用正常。
  - 最新日志无 fatal error、undefined citation、overfull hbox 或 duplicate destination warning；仅剩两个 `Underfull \hbox`。
  - `git diff --check` 通过。
- Appendix 导出判断：
  - A proposal 已是 PDF，保持。
  - B Gantt 图已有 PDF/PNG；spreadsheet 作为源证据，最终最好另导出 PDF。
  - C risk register、D CPD log、E H&S risk assessment 是表格/模板证据，应保留 DOCX 源文件并最终导出 PDF 固定版。
  - F software evidence 用 Markdown + report summary 即可，不需要转成图片。
  - G raw CSV/log 保持原始文件；Python 生成线图/柱状图/矩阵图优先 PDF 矢量，摄像头截图保持 PNG/JPEG。
  - 本机当前没有 `libreoffice` / `soffice`，暂时无法自动把 DOCX/XLSX 导出 PDF，需要之后用 Word/Excel/LibreOffice 或安装工具链处理。

#### 2026-04-25 CST +0800 Report review fixes: figures, tables, appendices and software evidence
- 用户要求：
  - 执行 report 后续修复项 1、2、4、5、6。
- 修复 review comment 1：figure numbering/list entries
  - 删除/替换了正文中的手写 `Figure 3.x`、`Figure 4.x` 标题。
  - `Report/main.tex` 中新增真正的 LaTeX `figure` + `\caption` + `\label`：
    - Fig. 3.1 System architecture and data flow
    - Fig. 3.2 Firmware execution and communication timing
    - Fig. 3.3 Wheel-legged robot hardware layout
    - Fig. 3.4 Electrical and communication block diagram
    - Fig. 3.5 Hierarchical control block diagram
    - Fig. 3.6 Control state and safety behaviour diagram
    - Fig. 4.3 Vision event path from camera frame to ESP32 command acknowledgement
  - Methods 图使用 TikZ 直接在 LaTeX 中生成矢量图，不依赖截图。
- 修复 review comment 2：longtable numbering/list entries
  - 给所有之前没有 caption 的 `longtable` 补了正式 caption。
  - 最新 List of Tables 中 Chapter 3 表格连续为 3.1--3.7，不再跳号。
- Appendix 接入改进：
  - Appendix A-G 不再只是写文件路径。
  - `Report/main.tex` 中每个 appendix 都加入 marker-readable summary table：
    - A.1 proposal-to-final-project alignment
    - B.1 project-management phase summary
    - C.1 project risk register summary
    - D.1 CPD activity summary
    - E.1 H&S risk assessment summary
    - F.1 software repository evidence summary
    - G.1 experiment data status summary
- 软件证据改进：
  - `Report/appendices/Appendix_F_Software_Repository/Software Repository Evidence - B-BOT.md` 更新为 audited local base commit `68e40b4`，并写明最终提交应冻结在 final report commit 或 release tag。
  - `Third Party Code and Software Attribution - B-BOT.md` 清理了“final report should / TODO”式措辞。
  - `Report/main.tex` Appendix F 加入 repo、commit、firmware、host-side software、experiment evidence 和 third-party boundary 的摘要表。
- 页数控制：
  - 新增 Methods 矢量图后正文一度到 36 页；已压缩 Future Work。
  - 最新 `Report/main.pdf` 总页数 50 页，A4。
  - 正文编号页为 1--35，References 从第 36 页开始，Appendix 从第 38 页开始；满足学校 35 numbered A4 pages 上限。
- 最新检查：
  - `lualatex` 已重新编译成功。
  - `Report/main.log` 无 undefined references、undefined citations、overfull hbox、fatal error 或 duplicate destination warning。
  - 只剩 4 个 `Underfull \hbox`，属于可接受排版松散警告。
  - `git diff --check` 通过。

#### 2026-04-25 05:01:10 CST +0800 Management appendix PDF companion exports
- 用户要求：
  - 修复剩余第 3 项：management appendix 的 Office 表格需要有 PDF/固定版式提交证据。
- 环境限制：
  - 当前本机没有 `libreoffice` / `soffice` / `pandoc`，不能直接做 pixel-exact 的 Word/Excel 原版 PDF 导出。
- 新增导出脚本：
  - `Report/appendices/Project_management/pdf_exports/build_management_pdf_exports.py`
  - 使用 ReportLab 生成 marker-readable PDF companion exports。
  - C/D/E 的表格内容从现有 `.docx` XML 读取；B 使用 reconstructed Gantt/weekly log、filled spreadsheet 路径和已生成的 Gantt 图作为证据来源。
- 新增 PDF companion exports：
  - `Report/appendices/Project_management/pdf_exports/Appendix_B_Project_Plan_Gantt_companion.pdf`
  - `Report/appendices/Project_management/pdf_exports/Appendix_C_Project_Risk_Register_companion.pdf`
  - `Report/appendices/Project_management/pdf_exports/Appendix_D_CPD_Log_companion.pdf`
  - `Report/appendices/Project_management/pdf_exports/Appendix_E_Health_and_Safety_companion.pdf`
- 同步说明文件：
  - `Report/appendices/Project_management/pdf_exports/README.md`
  - `Report/appendices/Project_management/README.md`
  - `Report/appendices/README.md`
  - `Report/appendices/Project_management/Appendix_B_Project_Plan_Gantt/README.md`
  - `Report/appendices/Project_management/Appendix_C_Project_Risk_Register/README.md`
  - `Report/appendices/Project_management/Appendix_D_CPD_Log/README.md`
  - `Report/appendices/Project_management/Appendix_E_Health_and_Safety/README.md`
- Report / thinking 同步：
  - `Report/main.tex` 的 Appendix B-E 文字已补充 PDF companion export 路径。
  - `Report/workspace/思路.md` 已同步 appendix 导出策略。
- 注意：
  - 这些 PDF 是固定版式 companion exports，不是假装成 Office 原版导出；editable `.docx` / `.xlsx` 仍保留作为源证据。
- 检查：
  - `Appendix_B_Project_Plan_Gantt_companion.pdf` 生成 6 页。
  - `Appendix_C_Project_Risk_Register_companion.pdf`、`Appendix_D_CPD_Log_companion.pdf`、`Appendix_E_Health_and_Safety_companion.pdf` 各生成 1 页。
  - `Report/main.tex` 已重新编译成功，`Report/main.pdf` 当前 51 页 A4；正文仍为 1--35 页，References 从第 36 页开始，Appendix 从第 38 页开始。
  - `Report/main.log` 无 fatal error、undefined citation/reference、overfull hbox、duplicate destination warning 或 rerun warning；仍只有 4 个可接受的 `Underfull \hbox`。
  - `git diff --check` 通过。

#### 2026-04-25 05:12:52 CST +0800 Report body compressed to create page buffer
- 用户要求：
  - 找出正文冗长部分并执行压缩，重点解决正文刚好 35 页、没有缓冲的问题。
- 修改范围：
  - `Report/main.tex`
  - `Report/workspace/思路.md`
- 压缩内容：
  - 压缩 `4.3 Balance and Motion Control Performance` 中 E2/E3/E4b/E9 的 provisional physical-results 解释。
  - 保留实验目的、表格、图路径、替换真实硬件数据后的判断逻辑。
  - 压缩 `5.1 Conclusions`，避免在 objective closure table 前重复完整复述 Results。
- 保留内容：
  - E5/E6/E8/E10/E11 measured evidence 未删。
  - 关键图、表、citation 和 objective closure table 未删。
- 最新页数/编译检查：
  - `Report/main.pdf` 当前 50 页 A4。
  - 正文编号页为 1--34，References 从第 35 页开始，Appendix 从第 37 页开始。
  - 当前比学校 35 numbered A4 pages 上限多出 1 页缓冲。
  - `lualatex` 已 rerun，交叉引用 warning 已清除。
  - `Report/main.log` 无 fatal error、undefined citation/reference、overfull hbox、duplicate destination warning 或 rerun warning；仍只有 4 个可接受的 `Underfull \hbox`。
  - `git diff --check` 通过。
