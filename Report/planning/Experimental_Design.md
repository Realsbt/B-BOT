# B-BOT Experimental Design Specification

> **作用**：定义 Final Report §4 Results & Discussion 所需的**所有实验设计**，独立于具体时间表。
> **相关文件**：`D2_Experiment_Plan.md`（执行日程）、`Final_Report_Outline.md`（报告结构）。
> **设计原则**：每个实验必须能回答 §1.2 Objectives 中某一条的一个可测子问题，并与 §2 Lit Review 中的某条基线对照。

---

## 0. 设计约束与术语

| 项 | 值 / 说明 |
|---|---|
| 采样主时钟 | ESP32 `micros()` (1 µs 分辨率) |
| 最小 CSV 字段 | `t_ms, pitch_deg, roll_deg, yaw_deg, leg_L_mm, leg_R_mm, wheel_L_rad_s, wheel_R_rad_s, cmd_vx, cmd_omega, src`（`src ∈ {ble, tcp, vision, auto}`）。电流/iq 只有在驱动反馈实际可用时才加入，不能在正文中虚构。 |
| 日志目录 | `Report/appendices/E_data/<EID>/run_<NN>.csv` |
| 文献基线 | 见各实验"Baseline"列，bib key 对应 `references.bib` |
| 样本量记号 | n = 单次实验内样本数；N = 重复 trial 数 |
| 统计表达 | `均值 ± 95% CI (n=..)` 或 `median [IQR]`，视分布选择 |

---

## 1. 实验目的 → 报告 Objective 的映射

| Objective (§1.2) | 直接证据 | 辅助证据 |
|---|---|---|
| **O1** — LQR+PID+VMC 融合底层平衡控制 | E1, E2, E3 | E4, E8 |
| **O2** — ROS 2 视觉输入链路 + WiFi TCP 机器人命令通道 | E5, E6, E7 | E8 |
| **O3** — 多源输入（Xbox/TCP/视觉）安全仲裁 | E4, E7 | — |
| *跨目标*：实时系统可行性 | E8 | 全部 |

*每个 objective 在 §5.1 Conclusions 必须逐条回应"是否达成"，否则 25% 权重直接扣分。*

---

## 2. 实验详细规格

### E1 — Static Balance Drift  *(O1 基线验证)*

| 字段 | 内容 |
|---|---|
| 研究问题 | 在无外扰动条件下，整车的静态姿态保持精度是否优于 IMU 原始噪声等级？ |
| 假设 | H0: pitch RMS ≥ 0.5°；H1: pitch RMS < 0.5°（IMU 名义零偏水平） |
| 独立变量 | 无（单一静止工况） |
| 因变量 | pitch/roll RMS、峰值漂移 |
| 控制 | 水平地面校平 ± 0.1°；启动后等 5 s 稳态再记录 |
| 样本 | n = 600 (60 s × 10 Hz)，N = 3 次重复 |
| 协议 | 机器人启动 → 进入平衡模式 → 静置 → 记录 60 s |
| 产出 | Fig.4.x：pitch/roll vs t；Table.4.x：RMS + peak + drift rate |
| Pass 准则 | pitch RMS < 0.5°，drift < 0.05°/s |
| Baseline | 两轮 LQR 平衡器典型值 ~0.3–1.0° RMS（`grasser2002joe`, `chan2013review`） |
| 风险 | 地面不平会系统性偏置；加 spirit level 校平 |

---

### E2 — Impulse Disturbance Recovery  ⭐⭐⭐  *(O1 核心证据)*

| 字段 | 内容 |
|---|---|
| 研究问题 | LQR+VMC 融合控制对瞬时外扰动的恢复性能如何？与文献同类系统差距？ |
| 假设 | H1: 恢复时间 < 1.5 s；overshoot < 10°（相对平衡点） |
| 独立变量 | 扰动方向（前/后各 N=10 trials） |
| 因变量 | ① settling time (|pitch| < 2° 持续 500 ms 视为恢复)；② peak overshoot；③ 恢复期间最大轮速/目标命令/电机输出量（以实际日志字段为准）；④ 保护状态触发比例 |
| 控制 | 固定腿长 = leg_mid；扰动由**标定过的标准砝码摆锤**施加（建议 500 g 从 15 cm 摆下），**同一操作者**执行全部 trials |
| 样本 | 每方向 N = 10 trials，记录从 t=−0.2 s 到 t=+3 s 全波形 |
| 协议 | 静止平衡 → 释放摆锤 → 触发标记（打一个 impulse flag）→ 持续记录 3 s → 自动保存 |
| 产出 | Fig.4.x：pitch vs t，10 条叠加 + ±3σ 包络；Fig.4.x：wheel speed / command / leg length 同步曲线；Table：settling time / overshoot / peak command 均值±CI |
| Pass 准则 | 10/10 trials 无保护触发；恢复时间 95% CI 上界 < 1.5 s |
| Baseline | Ascento 扰动恢复 ~0.5–1.0 s（`klemm2019ascento`）；Feng 2023 LQR+ADRC ~1.2 s（`feng2023wheellegged`） |
| 风险 | 扰动能量不可重复 → 用摆锤而非手推；trial 间等待 5 s 让系统回到相同初态 |

---

### E3 — Leg-Length Variation  *(O1 扩展)*

| 字段 | 内容 |
|---|---|
| 研究问题 | 腿长变化（重心升高）如何影响平衡性能？ |
| 假设 | 恢复时间随腿长单调上升；超调与腿长呈正相关 |
| 独立变量 | leg_length ∈ {min, mid, max}（按机械可用量程等分） |
| 因变量 | 同 E2 |
| 样本 | 每腿长 N = 5 trials |
| 协议 | 同 E2，分三组 |
| 产出 | Fig.4.x：recovery_time vs leg_length（箱线图）；讨论重心高度代价 |
| Pass 准则 | max 腿长工况仍能恢复（无保护触发） |
| Baseline | `klemm2019ascento` 报告的腿长调节下性能衰减 |

---

### E4 — Teleop Step Response  *(O3 + 顺带 O1)*

| 字段 | 内容 |
|---|---|
| 研究问题 | Xbox BLE 摇杆阶跃指令下，速度跟踪与平衡之间的耦合代价多大？ |
| 独立变量 | 阶跃幅度 ∈ {0.3, 0.6, 1.0 m/s}，转向 ∈ {0, ±1 rad/s} |
| 因变量 | 速度跟踪延迟、稳态速度误差、阶跃过程 pitch 峰值偏移 |
| 样本 | 每参数组合 N = 3 trials |
| 协议 | 静止 → 摇杆突然推到目标值 → 保持 3 s → 归零 → 记录 |
| 产出 | Fig.4.x：vx(t) 与 cmd_vx(t) 对比；Table：latency, steady-state error |
| Pass 准则 | 速度响应上升时间 < 0.5 s；pitch 峰值偏移 < 5° |
| Baseline | 两轮平衡车遥控响应典型值（`grasser2002joe`） |

---

### E5 — WiFi TCP Command-Entry Latency  ⭐⭐⭐  *(O2 核心证据)*

| 字段 | 内容 |
|---|---|
| 研究问题 | PC/ROS 2 主机发出的 WiFi TCP 命令到达 ESP32 命令解析入口的延迟分布如何？尾延迟是否足够支持遥操作？ |
| 假设 | Median < 50 ms，p95 < 150 ms（目标工况：同房间 2.4 GHz WiFi） |
| 独立变量 | 命令类型 ∈ {`DRIVE,0,0`, `YAWRATE,<small_mrad>`}；距离/RSSI 可作为可选变量 |
| 因变量 | host send timestamp → USB serial receipt (`WiFi命令:` / `DRIVE set:` / `YAWRATE set:`) 的延迟 |
| 控制 | 机器人 balance off 或架空；同一 AP；host 同时运行 TCP sender 和 USB serial logger |
| 样本 | n ≥ 1000 条命令（例如 10 Hz × 100 s） |
| 协议 | Host 发送带可识别序列的安全小命令（例如小幅 `YAWRATE` 编码序号）；串口 logger 记录 ESP32 打印；按序号或 FIFO 匹配发送与接收时间 |
| 产出 | Fig.4.x：TCP command latency CDF；Table：min / median / p95 / p99 / max |
| Pass 准则 | p95 < 150 ms；无乱序/长时间卡死；断线后能进入 E6 的停止逻辑 |
| Baseline | 本项目控制通道基线；与 ROS 2/micro-ROS 理论通信能力只能定性比较，不能写成同类协议 benchmark |
| 风险 | 该测量包含 ESP32 串口打印和 USB serial 回传开销，因此应表述为 command-entry acknowledgement latency 的保守上界，不是纯网络单程延迟 |

---

### E6 — WiFi TCP Watchdog and Disconnect Robustness  ⭐⭐  *(O2 安全性验证)*

| 字段 | 内容 |
|---|---|
| 研究问题 | WiFi TCP 客户端停止发送、主动断开或链路异常时，机器人是否会在设计时间内清零 direct command 并停止队列动作？ |
| 独立变量 | fault type ∈ {停止发送、关闭 TCP socket、弱信号/断 WiFi} |
| 因变量 | 最后一条 `DRIVE` 到 `DRIVE watchdog` 的时间；最后一条 TCP line 到 `idle_timeout/client_drop/wifi_lost` 三连停的时间 |
| 控制 | 机器人架空或断开电机；固定 command rate；同一 AP |
| 样本 | 每种 fault N ≥ 10 trials |
| 协议 | Host 连续发送 `DRIVE,250,0` 或安全等效命令 → 注入 fault → 串口记录 watchdog / full-stop 日志 → 验证 `DRIVE,0,0 + YAWRATE,0 + QUEUE_STOP` |
| 产出 | Fig.4.x：fault injection timeline；Table：stop latency median / p95 / max |
| Pass 准则 | direct command watchdog 约 500 ms 内清零；TCP idle watchdog 约 1500 ms 内强制断开并 full stop |
| Baseline | 安全遥操作设计原则；与 ROS 2 QoS 文档只做背景讨论，不做定量对标 |
| 注意 | 这不是 ROS 2 QoS 对比实验；报告中应强调当前底盘命令通道是 TCP line protocol |

---

### E7 — Vision Bridge Latency  *(O3 可选)*

| 字段 | 内容 |
|---|---|
| 研究问题 | Yahboom camera micro-ROS 图像输入、MediaPipe 识别和 WiFi TCP 命令发送组成的视觉遥操作链路是否可用？ |
| 独立变量 | 手势类型（若系统支持多类） |
| 因变量 | `/espRos/esp32camera` 帧率；gesture label → `dry-run command` / `sent:` 的事件延迟；手丢失到 `DRIVE,0,0` 的恢复时间 |
| 样本 | n ≥ 50 视觉事件；若时间紧至少记录 5 min topic hz + 3 个手势事件 |
| 协议 | `ros2 topic hz /espRos/esp32camera` 记录帧率；bridge 开 `debug_events`，分别跑 dry-run 与 `dry_run=false`；串口/TCP 日志确认 `Five -> DRIVE,250,0`、hand lost -> `DRIVE,0,0` |
| 产出 | Fig.4.x：vision event timeline；Table：camera FPS、command event latency、success rate |
| Pass 准则 | 摄像头图像 topic 稳定在线；`Five` 能稳定触发 `DRIVE,250,0`；手消失能回到 `DRIVE,0,0` |
| 风险 | 该链路不进入底层闭环控制；若延迟/帧率不足，应在 §4.4 明确限制为遥操作/事件触发 |

---

### E8 — Control Loop Jitter  ⭐⭐  *(实时性验证)*

| 字段 | 内容 |
|---|---|
| 研究问题 | FreeRTOS 调度下 `CtrlBasic_Task` (4 ms 周期) 的周期偏差？是否保证硬实时？ |
| 因变量 | 每周期的 `Δt = t_k − t_{k-1}` 的分布 |
| 控制 | 系统在正常平衡工况下（非空载）；所有任务按生产配置启用 |
| 样本 | n ≥ 15000 周期（约 60 s） |
| 协议 | 在 `CtrlBasic_Task` 开头写 `micros()` 到环形缓冲；离线批量导出 |
| 产出 | Fig.4.x：Δt 直方图 + 99.9% 线；Table：mean / stddev / p99.9 / max |
| Pass 准则 | 99.9% 周期在 4 ms ± 200 µs 以内 |
| Baseline | FreeRTOS 实时性公认指标 |

---

## 3. 数据管理规范

### 3.1 文件命名
```
Report/appendices/E_data/
├── E1_static/
│   ├── run_01.csv
│   ├── run_02.csv
│   └── README.md        # 含该实验全部元数据（见下）
├── E2_impulse/
│   └── ...
└── ...
```

### 3.2 每个实验 README 必含字段
- 日期 / 操作者
- 固件版本（git commit hash）
- 硬件配置（腿长、电池电压、IMU 偏置校准值）
- 环境（温度、地面材质、WiFi RSSI）
- 异常 trials 的列表（哪一组数据作废、原因）

### 3.3 CSV 元数据
每份 CSV 第 1 行为 `# timestamp_unit=ms, pitch_unit=deg, fw=<hash>`；第 2 行为 header；之后数据。只有实际采到电流/iq 时才加入 `iq_unit=A`。

---

## 4. 分析计划

| 实验 | 统计方法 | 图类型 |
|---|---|---|
| E1 | RMS、漂移斜率线性拟合 | 时间序列 + 直方图 |
| E2/E3 | 均值 + 95% CI (t-分布, N 小)；箱线图比较腿长 | 叠加曲线 + ±3σ 包络；箱线图 |
| E4 | 上升时间定义 = 10%→90% | 阶跃响应图 |
| E5 | 分位数（非均值，延迟通常长尾） | CDF / CCDF |
| E6 | fault injection timeline；stop latency 分位数 | timeline + summary table |
| E7 | topic hz 统计；事件成功率；事件延迟 | timeline + 条形/表格 |
| E8 | 分位数 + 直方图 + CDF 尾部 | 直方图 + log-scale 尾部 |

- **统一画图工具**：Python `matplotlib` + `pandas`；脚本放在 `Report/scripts/plots/`（D3 前搭好）
- **图格式**：`.pdf` 矢量，字号 ≥ 9 pt 以保证正文缩放后仍可读
- **色盲友好调色板**：避免只用红绿区分

---

## 5. 实验 → 报告章节映射

| 实验 | 图/表出现在 | 讨论出现在 |
|---|---|---|
| E1 | §4.2 System Bring-up | §4.2 简短 |
| E2 | §4.3 Balance Performance（主图） | §4.3 深入讨论 + 对照 `feng2023wheellegged`、`klemm2019ascento` |
| E3 | §4.3 补充图 | §4.3 重心代价讨论 |
| E4 | §4.3 最后 | §4.3 末段 |
| E5 | §4.4 Communication（主图） | §4.4 深入讨论 WiFi TCP 命令通道的延迟上界 |
| E6 | §4.4 | §4.4 watchdog / disconnect safety 讨论 |
| E7 | §4.4 末段（若做） | §4.4 或 §5.2 future work |
| E8 | §4.2 末段或 §3.2 附近 | §4.2 简短 |

---

## 6. 执行前检查表

- [ ] 所有实验均已与 §1.2 objectives / §2 lit baseline 显式绑定
- [ ] 固件版本已打 git tag，实验过程中不再改代码（冻结）
- [ ] 每实验先跑 1 次 smoke test 确认日志字段齐全、单位正确
- [ ] 每 CSV 第一行元数据 OK，不能只是数字堆
- [ ] 出图脚本跑得通、生成的 pdf 可直接 `\includegraphics` 到 `main.tex`
- [ ] 所有原始数据提交前复制到 `Report/appendices/E_data/`（Appendix G 证据）
- [ ] 异常 / 失败 trials 在 README 里诚实记录（这是学术诚信要求）

---

## 7. 风险与降级策略

| 风险 | 降级方案 |
|---|---|
| 扰动摆锤能量不可复现 | 改为记录"施加的角动量"而非"力"，或用数据后处理按初始 pitch_rate 分组 |
| E5 串口日志延迟包含 USB/打印开销，不能代表纯网络延迟 | 明确报告为 host-to-command-entry acknowledgement latency 的保守上界 |
| E6 弱信号/断 WiFi 不可重复 | 至少完成停止发送和 TCP socket close 两种可重复 fault；弱信号只做定性补充 |
| E7 视觉延迟测不出 / 回归失败 | 单次演示 + 定性描述，核心结论移 §5.2 future work；不影响 §4 主结论 |
| 整体时间不够 | 只保留 ⭐⭐⭐ 三项（E2, E5, E8），其余改为定性描述并清楚承认 |

---

## 8. 与 `D2_Experiment_Plan.md` 的关系

- 本文件 = **设计规格**（每个实验为什么这样设计、测什么、怎么分析）
- D2 文件 = **执行日程**（2026-04-25 那天几点做什么）
- 两者互补：执行前读 D2；撰写 §4 时读本文件；答辩准备时两者都要复习
