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
  - `include/wifi_config.h`：填入本地热点凭据（`BT26` / `asdfghjkl`），文件已在 `.gitignore`
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
