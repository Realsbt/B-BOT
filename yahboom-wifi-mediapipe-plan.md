# Yahboom WiFi 摄像头 + MediaPipe 集成方案

> 在不改动 LQR/PID/VMC 控制核的前提下，把 Yahboom 的 WiFi 摄像头 + ROS2 Humble + MediaPipe 生态接到本项目的串口命令队列上，实现手势控制、姿态特技、人脸跟随三种视觉交互。
>
> 配套：[yahboom-camera-ros2-guide.md](yahboom-camera-ros2-guide.md)（摄像头模组的三步启动参考）

---

## 1. 背景与目标

现有项目是 ESP32 两轮足式自平衡机器人固件（PlatformIO + Arduino + FreeRTOS；LQR + 级联 PID + VMC；CAN 6 电机；MPU6050 IMU；NimBLE Xbox 手柄输入；UART2 串口命令队列），见 [introduction.md](introduction.md)。**当前没有任何 WiFi、摄像头或主机侧代码**。

Yahboom 摄像头模组是**独立的 ESP32 设备**（不插在机器人 ESP32 上），通过 WiFi 把图像发给主机；主机跑 `micro-ros-agent` + ROS2 Humble，发布图像 topic。Yahboom 同时提供 `yahboom_esp32_mediapipe` 演示包（手部/手势/姿态/人脸检测）。

**可行性结论**：完全可行。难点（WiFi 图像传输 + ROS2 + MediaPipe 生态）Yahboom 已经解决；本项目只需：

1. 主机侧：新建一个 ROS2 Python 桥接节点，把 MediaPipe 识别结果映射成**现有的**串口命令；
2. 固件侧：新增一个**薄薄**的 WiFi 命令接收模块，**复用同一个命令队列解析器**；新增一个 `YAWRATE` 直通命令供人脸跟随用。

核心控制代码（`ctrl.cpp` / `motor.cpp` / `can.cpp` / `imu.cpp` / `pid.cpp` / `legs.cpp` / `matlab_code/*` / `ble.cpp`）**零改动**。

目标功能（用户确认的三项）：

- **手势控制**：握拳/张掌/指向 → 前进/停止/转向
- **姿态触发特技**：挥手 → 跳跃，蹲下 → 趴下（姿态恢复 → 站起）
- **人脸跟随**：机器人朝向检测到的人脸（不主动靠近）

---

## 2. 系统架构

```
Yahboom ESP32-CAM ──WiFi/UDP:9999──▶ Host PC (Ubuntu 22.04 + ROS2 Humble)
                                      │
                                      ▼ micro-ros-agent
                                      /espRos/esp32camera  (sensor_msgs/CompressedImage)
                                      │
                                      ▼
                              wheeleg_vision_bridge  【新增 Python 节点】
                                 ├─ MediaPipe Hands / Pose / Face  (自己推理)
                                 ├─ Debouncer (N-of-M 帧投票)
                                 ├─ Command encoder (映射成已有串口命令)
                                 └─ Transport: pyserial 或 TCP socket
                                      │
                  ┌───────────────────┴───────────────────┐
                  ▼ USB-to-TTL → GPIO16/17               ▼ WiFi TCP:23
                Robot ESP32 UART2 (Serial2@115200)    Robot ESP32 WiFi Server【新增】
                  │                                      │
                  └──────── Serial_HandleCommandLine() ────┘
                                      │
                              命令队列 (cmdQueue, cap=20)
                                      │
                              CommandExecutorTask
                                      │
                                target.speedCmd / yawSpeedCmd / JumpTask
                                      │
                                   CAN × 6 motors
```

端到端延迟：约 200–400 ms（采集 30–40 + WiFi 20–50 + MediaPipe 30–80 + 去抖 100–200 + 下发 10–30）。手势/特技够用；人脸跟随对延迟敏感，因此 v1 直接用 `YAWRATE` 直通命令绕过队列轮询。

---

## 3. 改动范围

### 主机侧（全部新增，不碰机器人固件）

```
host/
  ros2_ws/src/wheeleg_vision_bridge/
    package.xml                             [NEW]
    setup.py / setup.cfg                    [NEW]
    wheeleg_vision_bridge/
      bridge_node.py                        [NEW] 主节点
      mediapipe_runner.py                   [NEW] 按模式切换 detector
      command_encoder.py                    [NEW] 识别 → 串口命令
      transport.py                          [NEW] UART / TCP 双后端
      debouncer.py                          [NEW] N-of-M 帧投票
      config.yaml                           [NEW] 阈值/映射/端口
    launch/bridge.launch.py                 [NEW]
  scripts/camera_quickstart.sh              [NEW] Yahboom micro-ROS Agent 启动封装
  README_vision.md                          [NEW] 运行手册
```

### 机器人固件（极小、纯增量）

**修改**（非破坏性）：

- [platformio.ini](platformio.ini) — 可加 `build_flags = -DENABLE_WIFI_CMD`（WiFi 是 Arduino-ESP32 内置，不需加 lib_deps）
- [src/main.cpp](src/main.cpp) — 在 `Serial_Init()` 之后加一行 `WiFiCmd_Init();`
- [include/serial.h](include/serial.h) — 导出公共整行命令分发函数：
  ```c
  int  Serial_HandleCommandLine(const char *line);
  int  Serial_InjectCommandLine(const char *line);
  void Serial_TryStartQueue(void);
  ```
- [src/serial.cpp](src/serial.cpp) — 两件事：
  1. 把 UART2 里“特殊命令 + 普通入队 + 启动队列”的整行分发逻辑抽成 `Serial_HandleCommandLine()`，UART2 和 WiFi TCP 都调用它。**不要只暴露 `parseAndEnqueueSequence()`**，否则 `QUEUE_STOP` / `BALANCE_OFF` / `BLE_DISABLE` 这类特殊命令在 WiFi 通道上不会生效；
  2. **新增 `YAWRATE` verb**（见第 4 节协议）——这是唯一的**新逻辑**增量，预计 ~30 行。

**新增文件**：

- [include/wifi_cmd.h](include/wifi_cmd.h) — `WiFiCmd_Init()`、`WiFiCmd_SetInputEnabled(bool)`
- [include/wifi_config.h](include/wifi_config.h) — `WIFI_SSID` / `WIFI_PASS` / `WIFI_TCP_PORT=23` / `WIFI_WATCHDOG_MS=1500`（⚠ 加入 `.gitignore`，不提交凭证）
- [src/wifi_cmd.cpp](src/wifi_cmd.cpp) — WiFi STA 连接 + `WiFiServer` 监听 TCP 23，FreeRTOS 任务按行读入 → 调用 `Serial_InjectCommandLine()`；带看门狗（TCP 断且队列跑 TCP 源命令 → 注入 `QUEUE_STOP`）

**完全不碰**：`ctrl.cpp` / `motor.cpp` / `can.cpp` / `imu.cpp` / `pid.cpp` / `legs.cpp` / `adc.cpp` / `ble.cpp` / `matlab_code/*`。

---

## 4. 命令协议

### 4.1 复用现有行协议

[src/serial.cpp](src/serial.cpp) 的行协议（`\n` 结尾、`\r` 兼容、`;` 串联）直接沿用：

| 意图 | 发送行 | 备注 |
|---|---|---|
| 前进 30%，2 秒 | `FORWARD,30,2` | param1=%（1–100，映射到 MAX_SPEED=0.8 m/s）；param2=秒 |
| 后退 | `BACKWARD,30,2` | |
| 左转 20°，1 秒 | `LEFT,20,1` | 角速度 = angle/duration，clamp 到 MAX_YAWSPEED=4.5 rad/s |
| 右转 | `RIGHT,20,1` | |
| 停止 | `QUEUE_STOP` | 立即清队列并清零 speedCmd / yawSpeedCmd；视觉安全停机优先用它 |
| 跳跃 | `JUMP` | 触发 [`Ctrl_JumpPrepareTask`](src/ctrl.cpp#L112) |
| 趴下（腿缩） | `DECREASELEGLENGTH,3` | 单位 ×0.01 m，param1 范围 1–10 |
| 站起（腿伸） | `INCREASELEGLENGTH,3` | |
| 走交叉步 5 秒 | `CROSSLEG,0,5` | |
| 清队列 | `QUEUE_STOP` | 已有 |
| 暂停/恢复 | `QUEUE_PAUSE` / `QUEUE_RESUME` | 已有 |
| 平衡开/关 | `BALANCE_ON` / `BALANCE_OFF` | 已有，⚠ 见 6.1 节警告 |
| BLE 开/关 | `BLE_DISABLE` / `BLE_ENABLE` | 已有 |

**关键约束**：`param2 = atoi(s) × 1000`（[serial.cpp:392](src/serial.cpp#L392)），**只能传整数秒，最短 1 秒**；`atoi("0.5") == 0` 会被 fallback 改成默认值（3 秒）——因此不要试图用 `LEFT,20,0.5` 做短脉冲，那是人脸跟随需要 YAWRATE 的根本原因。

### 4.2 新增：`YAWRATE` 直通命令（v1 必需）

**用途**：人脸跟随需要连续的小角度转向（≤ 500 ms 响应），现有的 LEFT/RIGHT 最短 1 秒、走队列，延迟和粒度都不够。新增 `YAWRATE` 绕过队列直接写 `target.yawSpeedCmd`。

**协议**：

```
YAWRATE,<mrad_per_sec>
```

- 单位：**毫弧度每秒（mrad/s）**，整数，正为左转、负为右转；
- 范围：±4500（对应 ±4.5 rad/s = `MAX_YAWSPEED`），超界自动 clamp；
- 例：`YAWRATE,500` = 0.5 rad/s 左转；`YAWRATE,0` = 停止转向；
- **不入队**，直接覆盖 `target.yawSpeedCmd`；
- **仅当队列未 RUNNING/PAUSED 时生效**（`EXEC_IDLE` / `EXEC_STOPPED` 都可），否则静默忽略（保证队列命令的原子性，不和 LEFT/RIGHT 打架）；
- **自动归零看门狗**：如果 500 ms 没收到新的 YAWRATE，自动归零（防主机崩溃后持续转向）。

**实现要点**（[src/serial.cpp](src/serial.cpp) 新增 verb 分支）：

```c
// 在 UART2_CommandTask 的 verb 分发里新增一支，大约位于第 561 行之后
else if (strncmp(rxBuffer, "YAWRATE,", 8) == 0) {
    int mrad = atoi(rxBuffer + 8);
    if (mrad >  4500) mrad =  4500;
    if (mrad < -4500) mrad = -4500;
    if (cmdQueue.state != EXEC_RUNNING && cmdQueue.state != EXEC_PAUSED) {
        target.yawSpeedCmd = mrad * 0.001f;
        sLastYawRateMs = xTaskGetTickCount() * portTICK_PERIOD_MS;
    }
}
```

看门狗挂在 `Serial_Task`（[serial.cpp:598](src/serial.cpp#L598)，当前是空循环）里：

```c
void Serial_Task(void *pvParameters) {
    while (1) {
        uint32_t now = xTaskGetTickCount() * portTICK_PERIOD_MS;
        if (sLastYawRateMs != 0 &&
            now - sLastYawRateMs > 500 &&
            cmdQueue.state != EXEC_RUNNING && cmdQueue.state != EXEC_PAUSED) {
            target.yawSpeedCmd = 0;
            sLastYawRateMs = 0;
        }
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}
```

增量：约 30 行，`serial.cpp` 内部新增 1 个 static 变量 + 1 个 verb 分支 + 在 `Serial_Task` 填内容。不触动任何现有逻辑。

---

## 5. 桥接节点设计（`wheeleg_vision_bridge`）

### 5.1 总体

- **单节点 + mode 参数**，不做三个节点 + mux（单模式轮换，CPU 只够跑一种 MediaPipe pipeline）。
- 默认订阅 Yahboom 原始压缩图 `/espRos/esp32camera`（`sensor_msgs/CompressedImage`），也保留 `/esp32_img` + `sensor_msgs/Image` 作为备用兼容；发布 `/wheeleg/vision_status`（调试）。
- 模式切换：`ros2 param set /wheeleg_vision_bridge mode gesture|stunt|face|idle`。
- **启动默认 `mode: idle`**（安全）。
- ⚠ Yahboom 自带的 `yahboom_esp32_mediapipe` 节点（`01_HandDetector` 等）**只作 Phase 0 验证用**（确认摄像头与 MediaPipe 通畅）。它们很可能不发布识别结果 topic，只弹窗显示，因此**生产桥接节点必须自己订阅图像、自己跑 MediaPipe**。读 Yahboom 节点源码是为了对齐手势 label 和 landmark 编号，避免重复造概念。

### 5.2 ROS2 参数（`config.yaml`）

```yaml
image_topic: /espRos/esp32camera
image_type: compressed      # compressed | raw
transport: uart             # uart | tcp
uart_port: /dev/ttyUSB0
uart_baud: 115200
tcp_host: 192.168.x.x       # 机器人 WiFi IP
tcp_port: 23
mode: idle                  # idle | gesture | stunt | face
debounce_frames: 5
command_rate_hz: 5
watchdog_ms: 1000
face_yaw_gain_mrad: 1500    # 像素偏移 1.0 → 1.5 rad/s
face_deadband: 0.1          # |dx| < 0.1 不动
mediapipe_confidence: 0.6
frame_skip: 2               # 每 2 帧推理 1 次
debug_window: false         # 可选 cv2.imshow 叠加画面
```

### 5.3 三种模式的映射（`command_encoder.py`）

**gesture（入队命令）**：
- 握拳 → `QUEUE_STOP`
- 张掌 → `FORWARD,25,1`
- 食指左指 → `LEFT,20,1`
- 食指右指 → `RIGHT,20,1`
- 点赞 → `JUMP`

**stunt（状态机触发，入队命令）**：
- 状态 = "蹲姿"进入（髋 y > 膝 y 持续 ≥0.5 s）→ `DECREASELEGLENGTH,3`
- 状态 = "蹲姿"退出（恢复站立持续 ≥0.5 s）→ `INCREASELEGLENGTH,3`
- 双手举过头挥手（双腕高于双肩持续 ≥0.5 s，然后离开此状态）→ `JUMP`（边沿触发，不在持续状态中重复发）
- T-pose → `CROSSLEG,0,5`

> ⚠ stunt 用**姿态状态机**而不是定时器。定时复位（比如"蹲下 2 秒后自动 INCREASE"）会导致用户一直保持蹲姿时机器人在下-上-下-上振荡。

**face（YAWRATE 直通，不入队）**：
- `dx = (face_center_x - W/2) / (W/2)`，`|dx| < face_deadband` 发 `YAWRATE,0`；
- 否则 `YAWRATE,<sign(-dx) * face_yaw_gain_mrad * |dx|>`（符号取负是因为脸在画面左边时机器人应左转）；
- 以 `command_rate_hz`（默认 5 Hz）持续发送，充当主机侧心跳；
- **face 模式绝不发 FORWARD 或其他入队命令**，否则 YAWRATE 会被忽略（因为队列 RUNNING/PAUSED）。

**idle**：不发任何命令。

### 5.4 去抖
N-of-M 帧投票（默认 5 连续帧）才触发正向动作；但**模糊帧或看门狗超时触发 `QUEUE_STOP`**（立即清队列，失败偏安全方向）。face 模式不走去抖（需要实时响应），用死区 + 限速替代。

### 5.5 传输层（`transport.py`）

```python
class Transport:
    def write_line(self, s: str) -> None
    def is_healthy(self) -> bool
```

`UartTransport`（pyserial + 自动重连）、`TcpTransport`（后台 writer 线程 + TCP_NODELAY + 重连）共享接口。`config.transport` 选一种，**默认 uart**。

---

## 6. 安全与仲裁

### 6.1 `BALANCE_ON` 会自动触发劈叉起立 — 重要警告

[src/serial.cpp:541-544](src/serial.cpp#L541)：
```c
} else if (strcmp(rxBuffer, "BALANCE_ON") == 0) {
    balanceEnabled = true;
    if (standupState == StandupState_None) {
        xTaskCreate(Ctrl_StandupPrepareTask, ...);   // 自动劈叉起立
        standupState = StandupState_Standup;
    }
}
```

**含义**：第一次发 `BALANCE_ON` 会让机器人**主动做劈叉起立动作**。在架空/台架上直接发 `BALANCE_ON` 可能导致腿剧烈张开撞到台架。

**正确上机流程**：
1. 摆正机器人（双腿自然竖直，近似起立姿态）→ 上电；
2. 上电后按原有流程连上 Xbox 或发 `BALANCE_ON` 触发起立（只发一次）；
3. 调试桥接节点**不要**重复发 `BALANCE_ON`——信号链路用 `QUEUE_STATUS` / 观察串口 log 验证即可，看到 `收到命令: FORWARD,20,1` 就算通路正常。

### 6.2 输入仲裁（自动继承）

核心：[src/ble.cpp:102](src/ble.cpp#L102) 已经实现"队列忙 → BLE 禁用"：
```c
if (sBleInputEnabled && !Serial_IsQueueBusy()) { … }
```
桥接注入的命令走**同一个队列**，所以视觉自动获得"比 BLE 高优先级"，**BLE 侧零改动**。

**优先级**（由队列机制自然强制）：
1. 人手通过 minicom 直发 `QUEUE_STOP` / `BALANCE_OFF`（紧急制动）；
2. 串口队列 RUNNING/PAUSED（UART 和 TCP 注入共享同一队列）→ 压制 BLE；
3. BLE Xbox（仅在队列空闲时）；
4. 视觉 `mode=idle` → 不发。

**YAWRATE 的插入点**：因为它只在队列未 RUNNING/PAUSED 时生效，所以它**不会抢 LEFT/RIGHT 的占有期**。face 模式下队列应保持不运行入队命令，YAWRATE 才能连续生效。如果 gesture 模式的 FORWARD 正在跑，同时用户切到 face，YAWRATE 会被忽略直到 FORWARD 结束——这是预期行为。

### 6.3 视觉使能开关（可选护栏）

在 [src/wifi_cmd.cpp](src/wifi_cmd.cpp) 维护 `sVisionInputEnabled`，新增 UART verb `VISION_DISABLE` / `VISION_ENABLE`（仿 [serial.cpp:551-560](src/serial.cpp#L551) 的 BLE 开关写法）。禁用时 TCP 仍收字节但丢弃，操作员可通过 USB 口秒停视觉。

### 6.4 双层看门狗

- **主机侧**：桥接在 `watchdog_ms` 内无检测结果 → 发一次 `QUEUE_STOP`，暂停发送新运动命令。防 MediaPipe 卡死。
- **机器人侧**（[src/wifi_cmd.cpp](src/wifi_cmd.cpp)）：跟踪上次 TCP 收行时间；TCP 断开且队列在跑 TCP 源命令 → 注入 `QUEUE_STOP`（1.5 s 内生效）。防 WiFi 掉线或主机崩溃。
- **YAWRATE 看门狗**：见 4.2 节，500 ms 无新 YAWRATE 自动归零。

### 6.5 紧急制动路径（诚实说明）

**当前系统没有专门的硬件急停按钮**。所谓"紧急制动"的可行手段按可靠度排序：

1. **物理切电源**（最可靠）；
2. 桥接节点 Ctrl+C，**但这会让 UART2 端口停发命令，机器人将按最后一条 FORWARD 继续跑，直到它的 param2 时间耗尽自动停**——所以桥接崩 ≠ 机器人立刻停；
3. 另开终端用 minicom 打开同一 USB-to-TTL 设备手敲 `QUEUE_STOP` + `BALANCE_OFF`（⚠ 需要桥接先释放端口，否则两个进程争抢设备）；
4. Xbox 手柄在队列 RUNNING 期间**被压制**，不能作为急停。

**建议**：调试阶段**始终有人守着物理电源开关**。v2 可考虑加一个 GPIO 按键中断 → `balanceEnabled = false; target.speedCmd = 0; ...`，硬件实现 ~1 小时。

### 6.6 JUMP / CROSSLEG 的特殊小心

Progress.md 提到"起立过猛是已知问题"。stunt 模式的 JUMP 和 CROSSLEG 是开环激进动作，必须**由操作员显式切到 stunt 模式**（默认 idle），避免"摄像头扫到一个挥手就跳"。

---

## 7. WiFi 备用通道的固件实现

### 7.1 库选择

Arduino-ESP32 内置 `WiFi.h` + `WiFiServer` + `WiFiClient` 的阻塞读模式。**不用** AsyncTCP——它自己起 task、让优先级分析复杂化。

### 7.2 任务与优先级

- 新任务 `WiFiCmdTask`：优先级 **1**（同 `UART2_CommandTask`），pin 到 `APP_CPU`（core 1），栈 4096。
- 现有控制任务（CAN/Motor/Ctrl）不动，不和 4 ms 控制环抢 CPU。
- `vTaskDelay(10)` 节流，行协议无需高频轮询。

### 7.3 注入路径

```c
WiFiClient c = server.available();
if (c && c.available()) {
    readLine(&c, buf, sizeof(buf));
    Serial_InjectCommandLine(buf);   // = parseAndEnqueueSequence + TryStartQueue
}
```

**零重复解析、零重复队列**。复合命令（`FORWARD,20,1;JUMP`）自动支持。YAWRATE 经此同样走 verb 分发。

### 7.4 凭证

v1：硬编码在 [include/wifi_config.h](include/wifi_config.h)，加进 `.gitignore`。v2（可选）：通过 UART verb `WIFI_SSID:xxx` / `WIFI_PASS:xxx` 写 NVS（Preferences 已在 [Progress.md](Progress.md) 2025/12/15 记录在用）。

### 7.5 BLE + WiFi 共存（已知坑）

ESP32 单芯片 2.4 GHz 要分给 NimBLE + WiFi STA。官方支持但可能让 BLE 丢包 / 延迟上升。
- 默认配置先测；若 Xbox 明显卡顿 → 加 build flag `DISABLE_WIFI_WHEN_BLE_CONNECTED`：`BLE_IsConnected()` 为真时 `WiFi.disconnect()`，断开时重连。
- **主控通道推荐 UART**，WiFi 仅方便剪线。

---

## 8. 分层实施顺序

**每层通过后再进下一层**，严格不跳步。

### Phase 0：环境预检（零代码）

1. `ros2 --version` 返回 Humble；
2. `ros2 pkg list | grep yahboom` 显示 `yahboom_esp32_camera`、`yahboom_esp32_mediapipe`；
3. 按 [yahboom-camera-ros2-guide.md](yahboom-camera-ros2-guide.md) 三步启动；
4. `ros2 topic list` 应看到 `/espRos/esp32camera`，`ros2 topic info /espRos/esp32camera` 应为 `sensor_msgs/msg/CompressedImage`；如要走 `sub_img` 中间节点，则备用填 `/esp32_img` + `image_type: raw`；
5. `ros2 run yahboom_esp32_camera sub_img` 看到画面 ≥15 FPS；
6. `ros2 run yahboom_esp32_mediapipe 11_GestureRecognition` / `02_PoseDetector` / `07_FaceDetection` 各跑一次，读其源码对齐 label 和 landmark 定义（别自己造）。

### Phase 1：桥接节点骨架（机器人不参与）

7. `colcon build` 通过 `wheeleg_vision_bridge`，idle 模式只打印帧率；
8. 加 MediaPipe runner，`mode=gesture` 只打印识别结果（`debug_window: true` 帮助调参），调 `debounce_frames` 到手势稳定；
9. 加 transport，回环测试：`uart_port` 接 USB-to-TTL，另一端 minicom 看命令流。

### Phase 2：首次上机（机器人架空）

10. 按 6.1 节流程正确 `BALANCE_ON`（机器人要摆正）；
11. USB-to-TTL 接 GPIO16/17 → PC；
12. `mode=gesture`，握拳/张掌对相机，观察轮子反应（**不要重发 BALANCE_ON**，用 QUEUE_STATUS 确认命令入队即可）；
13. `mode=stunt`，挥手触发 JUMP（台架要稳固）；
14. `mode=face`，初始 `face_yaw_gain_mrad=500` 起步，确认 YAWRATE 让机器人缓慢跟脸。

### Phase 3：WiFi 通道

15. 加 `src/wifi_cmd.cpp` + `include/wifi_cmd.h` + `include/wifi_config.h`，在 [main.cpp](src/main.cpp) 加 `WiFiCmd_Init();`；
16. 烧录后 `nc <robot-ip> 23` 手敲 `FORWARD,10,1` / `QUEUE_STOP` / `YAWRATE,300` / `YAWRATE,0`，逐条验证等价于 UART；
17. 桥接切 `transport: tcp` 复跑 gesture / face；
18. 对比 UART vs TCP 的端到端延迟；评估是否仍要用 UART 作为主。

### Phase 4：落地与压测

19. 移除台架，gesture 模式只测 `FORWARD` / `QUEUE_STOP`（USB-to-TTL 线保持连接，守着物理电源开关）；
20. 仲裁压测：视觉发 FORWARD 同时摇 Xbox → Xbox 应被忽略；从 USB 另起终端发 `VISION_DISABLE` → Xbox 恢复；
21. 看门狗测：拔 WiFi / 杀桥接 / 拔 USB — 各观察是否 1.5 s 内 `QUEUE_STOP` 生效；
22. BLE + WiFi 共存：同时用 Xbox 手柄 + WiFi 桥接 → 评估 BLE 延迟是否可接受。

### Phase 5：收尾

23. 写 `host/README_vision.md`（三步启动 + 模式切换 + 急停步骤）；
24. 把 `include/wifi_config.h` 加 `.gitignore`，提交 `.h.example` 模板。

---

## 9. 验证清单

| 层 | 通过标准 | 失败排查 |
|---|---|---|
| Phase 0 摄像头流 | `sub_img` ≥15 FPS 稳定 | 查 WiFi 信号、靠近 AP |
| Phase 0 MediaPipe demo | 检测框稳定 | CPU 满 → `frame_skip=2`、降分辨率 |
| Phase 1 桥接 idle | 控制台心跳、不发命令 | 检查 image topic 订阅是否成功 |
| Phase 1 Transport 回环 | minicom 看到命令原样 | `\r\n` 对 `\n` — serial.cpp 已剥 `\r` ([L517](src/serial.cpp#L517)) |
| Phase 2 UART 架空 | `FORWARD,20,1` 轮子转 1 秒停 | 看 UART log 是否收到；param2 单位是秒 |
| Phase 2 仲裁 | 视觉发命令时 Xbox 无反应 | `Serial_IsQueueBusy()` 对 TCP 源也返 true（同队列） |
| Phase 2 手势去抖 | 手抖不抖命令 | 提高 `debounce_frames` |
| Phase 2 挥手→跳 | 一次挥手只跳一次 | 边沿触发，不在持续态中重发 |
| Phase 2 face 跟随 | 头左右 ≤500 ms 内机器人跟上 | 抖动 → 加大 deadband；振荡 → 降 gain |
| Phase 2 YAWRATE 看门狗 | 主机停发 → 500 ms 内归零 | 查 `sLastYawRateMs` 逻辑 |
| Phase 3 TCP 等价 | `nc` 命令效果同 UART | 看 serial.cpp log 是否收行 |
| Phase 4 主机看门狗 | MediaPipe 冻 → 1 秒内 `QUEUE_STOP` | `asyncio.wait_for` 包 `process()` |
| Phase 4 机器人看门狗 | TCP 断 → 1.5 秒内 `QUEUE_STOP` | 只在 TCP 源命令运行时触发 |
| Phase 4 BLE+WiFi 共存 | Xbox 延迟可接受 | 明显卡顿 → 开 `DISABLE_WIFI_WHEN_BLE_CONNECTED` |

---

## 10. 关键风险与取舍

1. **Ubuntu 22.04 是隐性前提**。Humble 绑 Jammy；Yahboom `yahboom_esp32_mediapipe` 包也是 Humble。若主机是 24.04，用 Docker `microros/micro-ros-agent:humble`；桥接节点也放 humble 容器。
2. **端到端 200–400 ms**。face 跟随若仍迟钝：(a) `frame_skip=2`（常反而降总延迟，CPU 追上来）；(b) MediaPipe GPU delegate（TFLite，非平凡）。
3. **MediaPipe CPU 占用**：Hands ~30%/核、Pose ~50%、Face ~15%。**只允许单模式**。默认 `frame_skip: 2`。
4. **WiFi + BLE 2.4 GHz 共存**：见 7.5。主控保 UART 最稳。
5. **UART2 物理接入**：[serial.cpp:611](src/serial.cpp#L611) 是 GPIO16/17，**不是烧录 USB 口**；需要单独 USB-to-TTL 模块。
6. **没有硬件急停**：见 6.5 的坦白说明。调试阶段物理电源开关是最可靠的退路。
7. **命令队列容量 20**（[serial.cpp:20](src/serial.cpp#L20) `MAX_COMMAND_QUEUE_SIZE`）：gesture/stunt 够用；face 用 YAWRATE 不入队，不受此限。
8. **无遥测上行**：v1 是单向开环（主机→机器人）。v2 可加 telemetry 通道（反向发 yaw/pitch/状态）。
9. **`BALANCE_ON` 副作用**：见 6.1。架空与落地上机流程不同，必须分别写清。
10. **人脸跟随禁 FORWARD**：基于"只朝向不靠近"的需求。若后续想让机器人靠近，需要加距离估计（头宽像素数 / 深度）和安全阈值。

---

## 11. 关键文件索引

**阅读理解用**：
- [src/serial.cpp](src/serial.cpp) — 命令队列、解析、verb 分发（[L98](src/serial.cpp#L98) `Serial_IsQueueBusy`，[L392](src/serial.cpp#L392) param2×1000，[L467](src/serial.cpp#L467) `parseAndEnqueueSequence`，[L505-596](src/serial.cpp#L505) verb 分发，[L541-544](src/serial.cpp#L541) BALANCE_ON 副作用，[L611](src/serial.cpp#L611) UART2 引脚）
- [src/ble.cpp](src/ble.cpp) — 仲裁模式参考（[L102](src/ble.cpp#L102) `sBleInputEnabled && !Serial_IsQueueBusy()`）
- [src/ctrl.cpp](src/ctrl.cpp) — JUMP / CROSSLEG 任务
- [include/ble.h](include/ble.h) — 仲裁 API
- [introduction.md](introduction.md) — 项目总体说明
- [yahboom-camera-ros2-guide.md](yahboom-camera-ros2-guide.md) — 摄像头三步启动

**需要修改**（最小增量）：
- [platformio.ini](platformio.ini)、[src/main.cpp](src/main.cpp)、[include/serial.h](include/serial.h)、[src/serial.cpp](src/serial.cpp)（仅加 YAWRATE verb + 公共命令入口导出）

**新增**：
- [include/wifi_cmd.h](include/wifi_cmd.h)、[include/wifi_config.h](include/wifi_config.h)、[src/wifi_cmd.cpp](src/wifi_cmd.cpp)
- `host/ros2_ws/src/wheeleg_vision_bridge/`（整个 Python 包）
- `host/scripts/camera_quickstart.sh`、`host/README_vision.md`
