# B-BOT Presentation Q&A Preparation

用法：

- `中文理解`：你需要理解的回答逻辑。
- `English answer`：可以直接回答老师的英文。
- 回答原则：先直接回答，再给一个证据，最后承认限制。不要绕。

## Embedded Control and Robotics Platform / 嵌入式控制与机器人平台

### Is this an embedded systems project or a robotics project?

中文理解：

这是最需要准备的问题。回答要明确：主题是 embedded systems，机器人是验证平台。核心工作是 ESP32 firmware、实时控制、传感器/电机 I/O、通信接口、watchdog、安全仲裁和系统测试。

English answer:

> It is an embedded systems project using a wheel-legged robot as the validation platform. The core work is the ESP32 firmware, real-time control loop, sensor and motor I/O, FreeRTOS task structure, WiFi/BLE/UART command interfaces, watchdogs and safety arbitration. The robotics platform makes the embedded constraints visible and testable.

### Why did you use LQR instead of only PID?

中文理解：

PID 适合局部目标，比如 yaw、roll、腿长；但平衡问题是 pitch、pitch rate、wheel position、wheel speed 耦合的问题，所以 LQR 更合适。

English answer:

> PID is useful for local objectives such as yaw, roll and leg length, but the sagittal balance problem couples pitch, pitch rate, wheel position and wheel speed. LQR is better suited for that coupled state-space problem. I still use PID where the objective is local and simpler.

Evidence:

> E9 compares the full controller against a fixed-gain LQR variant and shows that the full controller improves the tested recovery behaviour.

### What exactly does VMC add?

中文理解：

VMC 让你从“虚拟腿部力/力矩”的角度控制，而不是直接单独控制每个关节。这对轮腿结构更自然。

English answer:

> VMC lets the controller reason in terms of virtual leg forces and torques, then map them to joint motor commands. That is more natural for a wheel-legged robot than commanding each joint independently.

Limitation:

> The current VMC implementation is practical and lightweight; it is not a full whole-body optimisation controller.

### Why is gain scheduling needed?

中文理解：

腿长变了，等效倒立摆几何就变了。一个固定 LQR gain 不一定适合所有腿长。

English answer:

> Leg length changes the effective inverted-pendulum geometry. A gain that works at one body height may be less suitable at another. Scheduling the LQR gain by virtual leg length keeps the controller closer to the current operating point.

Evidence:

> E3 tests leg-length sensitivity, and E9 shows the full controller outperforming the fixed-gain variant in the tested recovery comparison.

### Is your controller optimal?

中文理解：

不要说 optimal。LQR 只是在给定线性模型和 cost function 下最优。你的 claim 是 practical and measured，不是 global optimal。

English answer:

> No. LQR is optimal only for its linearised model and chosen cost function. My claim is more limited: the implemented controller is practical on the ESP32 and is supported by measured engineering tests. I do not claim global optimality.

### Why not use model predictive control?

中文理解：

MPC 更强但对 ESP32 和项目时间不现实。你的选择是轻量、可解释、可实测。

English answer:

> MPC would be interesting, but it is heavier computationally and would require a more mature model and solver workflow. For this project, LQR/PID/VMC is a more realistic embedded design: it is lightweight enough for the ESP32, interpretable, and testable on the physical robot.

## Experimental Evidence / 实验证据

### Are 10 trials enough?

中文理解：

10 次对工程验证可以，但不能证明总体可靠性。主动承认小样本，反而更客观。

English answer:

> Ten trials are enough for engineering validation in a final-year hardware project, but not enough for a population-level reliability claim. That is why I report the result as small-sample engineering evidence and retain failures and limitations.

If challenged:

> The next improvement would be to increase E2 and E9 to 20 trials per key condition and report Wilson confidence intervals and bootstrap confidence intervals.

### Why did you keep the failed forward disturbance trial?

中文理解：

因为删掉失败会过度美化结果。失败说明 forward direction 是弱项，也显示你客观。

English answer:

> Because removing it would overstate the result. The forward direction is the weaker case, and the failure exposes a real tuning, saturation or disturbance-limit issue. Keeping it makes the conclusion more objective.

### Why is E8 acceptable if there is a 53.365 ms outlier?

中文理解：

mean/median 说明正常情况下接近 4 ms，outlier 说明不是完全 deterministic。重点：WiFi/vision 没进闭环，所以这个风险是本地任务结构风险。

English answer:

> The mean and median show that the nominal loop timing is centred on 4 ms, but the outlier shows the embedded timing is not fully deterministic. I do not hide that. The architectural point is that this timing risk is local to the ESP32 workload and not caused by putting WiFi or vision inside the balance loop.

### Why not use WiFi or vision for closed-loop balance?

中文理解：

平衡环是 4 ms，WiFi/vision 是几十到几百 ms，而且 jitter 大。只能做目标更新，不能做稳定反馈。

English answer:

> The latency and jitter are too large and variable. The balance loop targets 4 ms, while WiFi and vision latencies are tens to hundreds of milliseconds. Therefore WiFi and vision can update human-level targets but should not close the stabilising feedback loop.

### How do you know the vision system is useful if accuracy is only 85.3%?

中文理解：

它不是自动驾驶系统，只是监督级遥操作。失败案例正好证明 dry-run、debounce、stunt gate、watchdog 是必要的。

English answer:

> The vision system is useful for controlled supervisory commands, not for autonomous high-speed control. The retained failure cases justify dry-run preview, debouncing, stunt gating and watchdogs. I treat vision as a convenience layer with safety constraints.

### Does the E9 ablation prove gain scheduling is always better?

中文理解：

不要说 always。说它在 tested conditions 下支持 gain scheduling。

English answer:

> No, it does not prove that gain scheduling is always better. It shows that under the tested physical conditions, the full controller performed better than the fixed-gain variant on recovery success, response metric and peak pitch. I interpret it as engineering ablation evidence, not a universal proof.

## Safety and Arbitration / 安全与命令仲裁

### What happens if the WiFi connection drops?

中文理解：

socket close 或 command timeout 会触发停止逻辑。引用 E6 10/10。

English answer:

> The firmware detects socket close or command timeout and injects stop behaviour. In E6, TCP close was detected in all 10 trials, and TCP idle produced full-stop events in all 10 idle trials.

### What happens if Xbox and PC commands conflict?

中文理解：

PC active 时可以 disable BLE target update。O3-S 已测 Xbox connected 的情况。

English answer:

> The PC tool can disable BLE target updates while it is active, and the supplementary O3 arbitration test measured the BLE/PC gate with the Xbox controller connected. It passed 5 out of 5 trials.

### What prevents a queue command and direct DRIVE command fighting?

中文理解：

队列运行时 direct DRIVE 会被抑制/拒绝。引用 serial log。

English answer:

> Queue execution suppresses or rejects direct drive commands. The O3 supplement tested this case and observed `DRIVE ignored: command queue busy` in 5 out of 5 trials.

### Is the safety testing exhaustive?

中文理解：

不是。覆盖主要路径和现实 fault case，但不是所有 race condition。主动承认。

English answer:

> No. It covers the implemented main command paths and realistic fault cases, but it is not exhaustive over every possible simultaneous-input race condition. The report states this limitation explicitly.

### What is the most important safety design?

中文理解：

最重要的是 remote commands 只是 target requests，且会过期/被仲裁，不是永久控制量。

English answer:

> The most important safety design is that remote commands are treated as temporary target requests. They can expire, be suppressed, or be overwritten by stop behaviour. That prevents stale remote commands from becoming persistent unsafe motion.

## Software and Repository / 软件与仓库

### What code did you write yourself?

中文理解：

说清楚你写的是 integration、控制结构、命令解析、WiFi server、仲裁、ROS 2 bridge、实验工具。第三方库要承认。

English answer:

> The ESP32 firmware integration, balance-control structure, command parsing, WiFi TCP command server, arbitration behaviour, ROS 2 vision bridge integration and experiment tools are project work. Third-party libraries such as ESP32 Arduino, ROS 2, MediaPipe, OpenCV and NimBLE are reused and attributed.

### Why is the report not in the GitHub repository?

中文理解：

GitHub 是软件证据快照，report 和实验 appendix 是单独提交的 assessment material。

English answer:

> The public repository is a software evidence snapshot. The report and experimental appendices are submitted separately as assessment material. Appendix F explains this boundary and links the public repository commit.

### Is the repository open source?

中文理解：

public 不等于 open source。它是为了评审可见，但 license 不是开源授权。

English answer:

> It is public for assessment visibility, but it is not open source. The custom project code uses a restricted project-code license, and third-party components retain their own licenses.

### How can the marker reproduce the software state?

中文理解：

Appendix F 有 repo link 和 commit，README 有 build/run。实验数据在 report appendices。

English answer:

> Appendix F gives the public repository link and submitted commit. The README explains the main firmware and host-side build steps. The experimental datasets are submitted with the report appendices rather than inside the software-only repository.

## Hardware / 硬件

### What is custom in the hardware?

中文理解：

强调 robot platform 和 ESP32 controller PCB 是项目相关；Yahboom 只是 ROS 2 WiFi camera source。

English answer:

> The robot mechanical platform and ESP32 controller PCB are project-specific. The Yahboom component is the separate ROS 2 WiFi camera module, used as an image source.

### Why use ESP32 instead of Raspberry Pi for balance?

中文理解：

ESP32 给清楚的实时控制边界。Pi/Jetson 适合 vision/logging，但不适合作为最后安全闭环。

English answer:

> ESP32 gives a simple embedded real-time boundary for the balance loop. A Raspberry Pi or Jetson would be useful as a companion computer for vision and logging, but I would still keep final stabilising control and safety stop behaviour local to the microcontroller.

### What is the biggest hardware limitation?

中文理解：

IMU 振动、机械柔性、执行器饱和。不要说 WiFi，硬件问题就讲硬件。

English answer:

> The biggest hardware limitations are IMU vibration, mechanical compliance and actuator saturation during stronger disturbances. These affect recovery behaviour and are part of why the report treats the physical results as practical engineering validation.

## Project Management / 项目管理

### What was the biggest project risk?

中文理解：

最大风险是低层平衡太耗时，导致实测和 report 时间不足。你通过缩小范围和 objective-linked experiments 管理风险。

English answer:

> The biggest risk was spending too much time on low-level balance control and not leaving enough time for measured evaluation. I managed this by narrowing the contribution to local balance plus supervisory teleoperation, and by organising the report around objective-linked experiments.

### What would you do next with more time?

中文理解：

先 logging/tuning，再更大 E2/E9 数据，再 state estimation，再 onboard companion computer。

English answer:

> I would improve the logging and tuning toolchain first: automatic trial markers, parameter versioning, repeatable gain sweeps and larger E2/E9 datasets. After that, I would improve state estimation and move ROS 2 vision onto an onboard companion computer while keeping balance local to the ESP32.

## Difficult Questions / 尖锐问题

### Is this really autonomous robotics?

中文理解：

不是 full autonomy，也不要硬说 autonomous robotics。主题是 embedded systems：实时控制 + 监督级遥操作。

English answer:

> It is not full autonomy. The project is primarily embedded real-time control with supervisory teleoperation. The vision-to-command layer is an interface on top of the embedded system, but I deliberately limit it to supervisory commands because of safety and timing constraints.

### Did the robot achieve all original ambitions?

中文理解：

不要说全部。说核心贡献完成，但 aggressive dynamic behaviours 和 exhaustive race testing 没完全做。

English answer:

> Not every possible ambition, especially aggressive dynamic behaviours and exhaustive race-condition testing. But the core implemented contribution is complete: balance-critical control runs locally, remote command paths are integrated, and the main behaviours are measured.

### What is the single strongest result?

中文理解：

最强不是单个数字，而是 integrated system evidence。

English answer:

> The strongest result is the integration evidence: the robot combines local balance, measured 4 ms loop timing, controller ablation, WiFi and vision command paths, and safety fault handling in one implemented system.

### What is the weakest result?

中文理解：

小样本人工扰动。主动承认，显得客观。

English answer:

> The physical control trials are still small-sample and manually disturbed. That limits statistical strength. I handle that by being explicit about the limitation and by treating the results as engineering validation rather than proof of general reliability.

### Why should this be considered a strong embedded systems project?

中文理解：

强在嵌入式系统集成和证据链，不是某一个单独算法。要点是实时任务、I/O、通信、安全和物理验证同时成立。

English answer:

> I think it is strong because it is not just a simulation or isolated algorithm. It integrates real-time embedded control, IMU and CAN motor I/O, FreeRTOS task scheduling, WiFi/BLE/UART command paths, watchdog-based safety arbitration and measured evaluation on final hardware.

## Short Emergency Answers / 简短备用回答

Use these if the Q&A is running long:

- 中文：平衡闭环是本地的；WiFi 和视觉只是监督级输入。  
  English: "The balance loop is local; WiFi and vision are supervisory."

- 中文：这是工程验证，不是统计证明。  
  English: "The result supports engineering validation, not statistical proof."

- 中文：outlier 被报告出来，因为它是真实限制。  
  English: "The outlier is reported because it is a real limitation."

- 中文：安全测试覆盖主要路径，但不是所有 race condition。  
  English: "Safety behaviour is measured on the main command paths, but not exhaustive over every race condition."

- 中文：下一步是更好的 logging、参数版本管理和更大的 E2/E9 数据集。  
  English: "The next technical step is better logging, parameter versioning and larger E2/E9 datasets."
