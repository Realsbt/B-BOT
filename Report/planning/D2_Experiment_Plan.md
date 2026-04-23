# D2 (2026-04-25) 实验矩阵与数据采集计划

> **目的**：为 Final Report §4 Results & Discussion（65% 权重的主战场）采集可画图的量化数据。
> **现状**：`Progress.md` 仅有开发记录，**没有任何可直接画进正文的时间序列 / CDF / 指标表**。
> **实现边界校正**：当前底盘 ESP32 控制器没有 micro-ROS client；micro-ROS 只用于 Yahboom 摄像头向 ROS 2 主机发布图像。机器人控制链路是 `PC/ROS2 -> WiFi TCP :23 -> ESP32 Serial_InjectCommandLine()`。
> **产出目标**：每项实验 → 1 份 CSV/bag 原始日志 + 1 张正文图 + 1 行表格指标。

## 实验矩阵

| # | 实验名 | 采集方式 | 输出文件 | 正文图表 | 文献基线对照 |
|---|---|---|---|---|---|
| E1 | 静态平衡漂移 | 机器人静止于水平地面 60 s，先把日志扩展为 CSV：`t_ms,pitch_deg,roll_deg,yaw_deg,leg_L_m,leg_R_m,cmd_vx,cmd_yaw,src` | `logs/E1_static_drift.csv` | Fig.4.x: Static pitch/roll drift | RMS < 0.5° |
| E2 | 脉冲扰动恢复 | 由侧推或标准摆锤施加扰动，连续 10 次；记录 pitch、roll、轮速/目标速度、腿长、保护状态 | `logs/E2_impulse_*.csv` | Fig.4.x: Pitch recovery ±3σ band | 恢复时间 / 超调对比 Ascento |
| E3 | 变腿长扰动恢复 | 分别在 leg_min / leg_mid / leg_max 下做 E2，比较性能衰减 | `logs/E3_leg_*.csv` | Fig.4.x: Recovery time vs leg length | 讨论重心变化代价 |
| E4 | 遥控前进/转向 | Xbox 摇杆阶跃命令，记录速度跟踪与 pitch 偏移 | `logs/E4_teleop_*.csv` | Fig.4.x: Velocity step response | — |
| E5 | WiFi TCP 命令入口延迟 | Host 脚本周期发送 `DRIVE,0,0`/`YAWRATE,0`，同时读取 USB 串口中 `WiFi命令:` / `DRIVE set:` 日志，统计 host send → serial receipt 的端到端延迟 | `logs/E5_tcp_latency.csv` | Fig.4.x: TCP command latency CDF | 作为本项目命令通道基线 |
| E6 | WiFi TCP 稳健性 / watchdog | 固定频率发送 `DRIVE`，主动断开 TCP / 停止发送 / 改变距离，验证 500 ms direct watchdog 与 1500 ms TCP idle watchdog 是否归零目标 | `logs/E6_tcp_watchdog.csv` | Fig.4.x: Command gap vs stop response | 对照安全遥操作设计原则 |
| E7 | 摄像头 micro-ROS + 视觉桥性能 | `ros2 topic hz /espRos/esp32camera` 记录输入帧率；gesture 模式记录 `Five -> DRIVE,250,0`、手消失 -> `DRIVE,0,0` 的 dry-run/live TCP 日志 | `logs/E7_vision.csv` | Fig.4.x: Vision pipeline event timeline | 若时间紧可只做定性验证 |
| E8 | 任务调度抖动 | FreeRTOS `CtrlBasic_Task` (4 ms) 周期偏差统计 | `logs/E8_jitter.csv` | Table 4.x: Control loop jitter | 验证实时性 |

## 最低可接受输出（若时间不够只保 ★ 项）

- ★ E2（扰动恢复）：最核心，缺它就没有平衡控制的核心证据
- ★ E5（WiFi TCP 命令延迟 CDF）：缺它通信章节只能写功能验证，不能写性能
- ★ E8（调度抖动）：一行简单统计即可，但极有说服力
- E6（watchdog/断线停止）：强烈建议保留，能证明安全工程价值
- E1/E3/E4：能做则做，不行则用单次演示加文字描述

## 采集脚本要点

### ESP32 端
- 现有 `Log_Task` 只输出关节角或格式化 IMU 文本；D2 第一优先级是扩展为 CSV 友好日志，并带 `millis()` 时间戳。
- 不要在报告里写 motor current / iq，除非你已经从电机反馈或驱动层采到对应字段；当前代码更稳妥的指标是姿态、轮速、腿长、target command 和 watchdog 触发时间。
- 若只能串口输出，用 `tee logs/E2_run01.log` + 一个后处理脚本切 CSV。

### 上位机端
- E5 延迟：同一台 host 同时运行 TCP sender 和 USB serial logger，用本地 monotonic clock 标记发送与串口回显时间；该指标包含 TCP 传输、ESP32 解析和 USB 串口打印，不要误写成纯网络单程延迟。
- E6 稳健性：记录最后一条 `DRIVE` 发送时间、ESP32 串口的 watchdog 日志、目标归零时间；断线测试必须架空或断开电机。
- E7 视觉：用 `ros2 topic hz /espRos/esp32camera` 作为真实帧率；用 bridge 日志记录 `dry-run command:` 或 `sent:` 事件。

## 当天执行顺序（建议 8 小时内闭环）

1. **09:00–10:00** 把 ESP32 `Log_Task` 扩展为 CSV 友好输出格式（逗号分隔、带 header）；编译烧录一次。
2. **10:00–11:30** E1 + E8（静态，无风险，顺便验证日志链路）。
3. **11:30–13:00** E2 / E3 扰动实验，连跑 30 组；数据直接存盘。
4. **14:00–15:30** E5 WiFi TCP 命令延迟脚本 + 10 分钟采样。
5. **15:30–17:00** E6 watchdog/断线停止测试 + E7 摄像头帧率/视觉桥事件日志。
6. **17:00–18:00** Python notebook 出所有正文图；每张图命名 `Fig_4x_*.pdf` 直接 `\includegraphics`。

## 收尾自查

- [ ] 每份 CSV 都有 header、单位、时间戳、采样率注释
- [ ] 每张图至少对应 1 条文献里的基线数值（否则 §4 又会退化为"我跑得还行"）
- [ ] 原始数据打包 → `Report/appendices/E_data/` → 作为 Appendix G 证据
