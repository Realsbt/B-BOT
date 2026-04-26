# B-BOT Presentation Script and Demo Plan

目标时长：20-25 分钟，包括一个保守的 live demo。

使用方式：

- `中文理解`：帮助你理解这一页到底要表达什么。
- `English script`：可以直接在 presentation 里说的英文。
- `Transition`：页与页之间的英文过渡句。

核心讲述策略：不要讲成“机器人/视觉项目”。你的 individual project 主题是 embedded systems，所以主线应是：B-BOT 是一个实时嵌入式系统，轮腿机器人只是验证平台；真正贡献是 ESP32 本地实时控制、FreeRTOS 任务划分、传感器/电机 I/O、无线通信、看门狗和安全仲裁的系统级实现与测试。

## Overall Timing / 整体时间安排

| Block | Time | 中文目的 | English purpose |
|---|---:|---|---|
| Opening and aim | 2 min | 说明这是嵌入式系统项目 | Define the embedded-systems problem and objectives |
| Architecture | 4 min | 解释实时边界和任务划分 | Explain real-time boundary and task partitioning |
| Control and safety | 4 min | 讲嵌入式控制、I/O 和命令仲裁 | Explain embedded control, I/O and arbitration |
| Results | 7-8 min | 用实验数据支撑 O1/O2/O3 | Present measured evidence |
| Live demo | 4-6 min | 展示平衡、命令、安全边界 | Demonstrate balance and command safety |
| Limitations and conclusion | 2-3 min | 客观收尾 | Close with limitations and contribution |

如果总时长接近 20 分钟：demo 只做稳定平衡 + 一个小命令 + stop。  
如果总时长接近 25 分钟：可以额外展示 vision dry-run。

## Slide 1 — Title

Time: 30 seconds

中文理解：

这一页只需要把项目名字、embedded systems 定位和核心设计思想说清楚。重点不是“我做了一个机器人”，而是“我设计了一个 ESP32 实时嵌入式控制系统，用一个不稳定轮腿机器人作为验证平台”。

English script:

> Good morning, my name is Botao Su. My individual project is an embedded systems project built around B-BOT, a WiFi-enabled self-balancing wheel-legged robot.

> The robot is the test platform, but the core project is the embedded system: an ESP32 real-time control layer, sensor and motor I/O, FreeRTOS task scheduling, wireless command handling and safety arbitration.

> The key design idea is that balance-critical feedback must stay local on the ESP32, while WiFi, Xbox control and vision are only allowed to send supervisory target commands.

Transition:

> I will first introduce the problem and objectives, then explain the architecture, the control design, the measured results and the live demonstration.

## Slide 2 — Project Problem

Time: 1 minute

中文理解：

从 embedded systems 角度，问题是：一个资源受限的 ESP32 需要同时处理 IMU、CAN 电机反馈、控制环、BLE、WiFi、串口命令和安全逻辑。机器人不稳定，所以任务调度和实时边界非常关键。

English script:

> The problem is not only to make a robot move. From an embedded systems perspective, the difficult part is to run real-time sensing, motor feedback, control, communication and safety logic on a resource-constrained ESP32.

> The platform is intentionally challenging: it is unstable, it has coupled wheel-leg dynamics, and it receives commands from several non-deterministic sources.

> Therefore my design rule is strict: stabilising feedback remains local, and all remote inputs are treated as target requests with watchdog and arbitration logic.

Transition:

> Based on that design rule, I defined three objectives for the project.

## Slide 3 — Objectives

Time: 1 minute

中文理解：

三目标要按 embedded system 讲：O1 是实时嵌入式控制，O2 是通信/视觉输入接口，O3 是安全状态机和命令仲裁。要强调 vision 是 host-side supervisory input，不是核心嵌入式闭环。

English script:

> I organised the project around three objectives.

> O1 is embedded wheel-legged balance control on the ESP32. O2 is the WiFi and ROS 2 vision command interface. O3 is safe multi-source input arbitration.

> This objective structure is important because it defines how the evaluation is judged. I do not claim vision is part of the balance loop; I test it as a supervisory command layer.

Transition:

> The architecture follows directly from these objectives.

## Slide 4 — System Architecture

Time: 2 minutes

中文理解：

讲三层：物理 I/O 层、ESP32 firmware/tasks 层、host/command 源。重点是 embedded boundary：ESP32 owns the 4 ms control loop，host-side 只发 target request。

English script:

> This architecture separates time-critical and non-time-critical computation.

> The bottom layer is the physical I/O: the IMU, CAN-connected motors, wheel-leg mechanism and battery system. The middle layer is the embedded firmware on the ESP32, including FreeRTOS tasks, command parsing, watchdogs and the balance controller. The top layer contains optional command sources such as Xbox BLE, UART scripts, WiFi TCP and the ROS 2 vision bridge.

> The ESP32 owns the 4 ms balance loop. The host PC and ROS 2 vision bridge only produce high-level command lines such as DRIVE, YAWRATE or queue commands.

> This separation is why the robot can tolerate WiFi and camera latency. A delayed vision command may affect teleoperation responsiveness, but it should not directly break the stabilising feedback loop.

Transition:

> I will now explain what was implemented on the robot and firmware side.

## Slide 5 — Hardware and Firmware

Time: 1.5 minutes

中文理解：

说明硬件不是纯买来的套件，更要说明 embedded system 内容：ESP32 控制 PCB、IMU、CAN 电机 I/O、电池监测、FreeRTOS 多任务、WiFi/BLE/UART 接口。Yahboom 摄像头只作为外部 ROS 2 图像源。

English script:

> The embedded platform uses an ESP32 controller, an MPU6050 IMU, CAN-connected wheel and joint motors, battery monitoring and a custom PCB.

> On the firmware side, FreeRTOS tasks separate CAN feedback, IMU update, motor output, command parsing, BLE, WiFi and the 4 ms control task.

> The implementation constraint is that all of this has to remain lightweight enough for the ESP32 while still being safe to operate on a physical robot.

Transition:

> The balance controller is built as a hierarchy rather than a single simple loop.

## Slide 6 — Balance Control

Time: 2 minutes

中文理解：

LQR 负责 sagittal balance，PID 负责 yaw/roll/leg length，VMC 把虚拟腿力映射到关节电机。不要讲太深公式，讲为什么这样设计。

English script:

> The balance controller is hierarchical. LQR provides the sagittal-plane balance action. PID loops regulate local objectives such as yaw, roll and leg length. VMC maps desired virtual leg forces and torques into joint motor commands.

> I used this hierarchy because a PID-only design would not express the coupled pitch and wheel dynamics clearly, while a heavy model-predictive controller would be unrealistic for this ESP32 implementation.

> The LQR gain is scheduled by virtual leg length, because leg length changes the effective inverted-pendulum geometry.

Transition:

> Control is only one part of the problem. The other part is making multiple command sources safe.

## Slide 7 — Command and Safety Architecture

Time: 1.5 minutes

中文理解：

讲 Xbox、UART、WiFi、vision 都能发命令，所以需要 arbitration。关键词：watchdog、BLE_DISABLE、dry_run、stunt_armed、queue suppression。

English script:

> The robot accepts multiple input sources: Xbox BLE, UART scripts, WiFi keyboard commands and vision-generated commands. The risk is that these sources could conflict.

> To control that risk, the firmware uses command queues, direct command watchdogs, BLE enable and disable gating, dry-run mode for vision, stunt arming and full-stop injection on command loss.

> O3 is about whether those safety behaviours are predictable, not just whether the robot can receive commands.

Transition:

> The evaluation is designed to test these architecture decisions directly.

## Slide 8 — Evaluation Strategy

Time: 1 minute

中文理解：

不要逐个念 11 个实验。说它们如何映射到 O1/O2/O3，并说明物理实验是 engineering validation，不是大样本统计证明。

English script:

> I evaluated the system with eleven measured experiments plus a supplementary O3 arbitration bench test.

> The key point is that the evaluation is objective-linked. E1 to E4 and E8/E9 mainly support O1. E5, E7, E10 and E11 support O2. E6 plus the O3 supplement support O3.

> The physical trials are engineering validation rather than population-level statistical experiments. I report failures and outliers instead of hiding them.

Transition:

> I will start with the O1 balance results.

## Slide 9 — O1 Static Balance and Recovery

Time: 2 minutes

中文理解：

先讲静态平衡 0.291 deg RMS，然后讲 E2 恢复 9/10 和 10/10。关键是不要说完美，主动说 forward 是 weaker case。

English script:

> For static balance, the robot achieved 0.291 degrees pitch RMS over three 60-second trials, below the 0.5 degree pass criterion.

> For impulse recovery, the robot recovered 9 out of 10 forward disturbances and 10 out of 10 backward disturbances.

> The forward direction is the weaker case, with one protection event, so I treat this as usable recovery with a tuning or saturation limit, not as perfect robustness.

> The important point is that failure cases are still part of the evidence.

Transition:

> Balance performance also depends on whether the embedded controller can maintain its timing boundary.

## Slide 10 — O1 Timing Boundary

Time: 1.5 minutes

中文理解：

E8 是强点，但要客观。mean/median 很好，max outlier 53.365 ms 是限制。重点：这说明 WiFi/vision 不能进闭环。

English script:

> E8 tests whether the local control timing is consistent with the 4 ms design target. Over 15,000 samples, the mean was 3.9998 ms and the median was 4.000 ms.

> However, the tail is not perfect. The maximum observed interval was 53.365 ms. I explicitly report this because it is a real limitation of the current task structure and logging load.

> The architectural conclusion is still valid: the timing risk is local to the ESP32 task structure, not caused by ROS 2, MediaPipe or WiFi being inside the balance loop.

Transition:

> The next result checks whether the full controller is actually better than simpler variants.

## Slide 11 — O1 Controller Ablation

Time: 2 minutes

中文理解：

这是 baseline 对比的核心。FULL vs FIXED_LQR 是直接比较。NO_RAMP 是命令阶跃，不要过度解释。

English script:

> E9 is the main comparative baseline. The full controller is compared against a fixed-gain LQR variant and a no-ramp variant.

> FULL recovered 10 out of 10 impulse trials. FIXED_LQR recovered 9 out of 10 and had one protected or failed trial.

> The response metric improved from 1.049 seconds to 0.826 seconds, which is a 21.3 percent reduction. Peak pitch reduced from 9.85 degrees to 8.09 degrees, a 17.9 percent reduction.

> I interpret this as engineering ablation evidence that gain scheduling is useful on this platform. I do not claim it proves optimal control.

Transition:

> With the local balance boundary established, I then evaluated the supervisory WiFi and vision layers.

## Slide 12 — O2 WiFi and Vision Teleoperation

Time: 2 minutes

中文理解：

讲 WiFi latency 和 vision accuracy/latency。核心是 “good for supervisory teleoperation, not balance feedback”。

English script:

> The WiFi TCP command path achieved a 37.41 ms median acknowledgement latency and 88.31 ms p95 over 300 samples. That is acceptable for human target updates.

> The vision bridge produced a clean 6 out of 6 command-class matrix on selected live trials, with 85.3 percent selected-frame label accuracy.

> The bridge-to-ESP32 ACK median latency was 66.13 ms across 71 safe commands.

> But the full human-gesture-to-command latency is slower because the camera frame rate is around 4.85 Hz and gesture debouncing can require extra frames. This is why vision remains supervisory.

Transition:

> The final objective is safety: what happens when commands are lost or command sources conflict?

## Slide 13 — O3 Safety and Arbitration

Time: 2 minutes

中文理解：

O3 是安全贡献。讲 E6 三类 fault injection，然后讲 O3-S 两个补充测试。要主动说不是 exhaustive proof。

English script:

> O3 tests whether the robot fails safely when command sources are lost or conflict.

> The direct-command watchdog cleared commands in all 10 watchdog trials. TCP close was detected in all 10 close trials. TCP idle produced full-stop events in all 10 idle trials.

> The supplementary arbitration test also passed 5 out of 5 BLE/PC gate trials with the Xbox controller connected, and 5 out of 5 queue/direct-command suppression trials.

> This is not exhaustive proof of every possible race condition, but it demonstrates the implemented safety behaviour on the main command paths.

Transition:

> I will now show a conservative live demonstration of the same architecture.

## Slide 14 — Live Demonstration Plan

Time: 4-6 minutes

中文理解：

demo 不要贪。目标是展示 architecture，不是炫动作。最好顺序：稳定平衡、小命令、stop、vision dry-run。危险动作不要做。

English script before demo:

> I will keep the live demo conservative. The aim is not to show the most aggressive movement, but to demonstrate the architecture: local balance remains active, remote commands update targets, and safety logic can return the robot to zero motion.

Demo order:

1. Robot already powered on, stable and in a safe area.
2. Show stable balance briefly.
3. Use Xbox or keyboard to send a small forward/backward or yaw command.
4. Trigger stop or release command and show return to safe state.
5. If safe and prepared, show vision bridge dry-run: gesture generates a printed command without driving the robot.
6. Mention watchdog rather than intentionally causing risky movement.

If robot fails:

> This is exactly why the report treats the physical tests as engineering validation and keeps WiFi and vision outside the stabilising loop. I will switch to the recorded evidence and explain the measured data.

If WiFi or ROS 2 fails:

> The balance controller is independent of this failure. The failed layer is supervisory communication, which is why the architecture uses watchdog-protected target commands.

Transition:

> Finally, I will summarise the limitations and the main contribution.

## Slide 15 — Limitations and Future Work

Time: 1.5 minutes

中文理解：

限制要主动说：手动调参、小样本、人工扰动、IMU 震动、机械柔性、ESP32 timing outlier、WiFi/vision 不能闭环。用 embedded systems 角度说，这是实时调度和 I/O 负载的边界。

English script:

> The main limitations are manual gain tuning, manually applied physical disturbances, small-sample physical trials, IMU vibration, mechanical compliance, actuator saturation, and the non-deterministic latency of WiFi and vision.

> These limitations do not invalidate the project. They define the boundary of the current contribution: a practical embedded control system with measured real-time behaviour, supervisory teleoperation and safety arbitration.

> With more time, I would improve the logging and tuning toolchain first, then collect larger E2 and E9 datasets, and then move ROS 2 vision to an onboard companion computer while keeping balance local to the ESP32.

Transition:

> I will close with the main conclusion.

## Slide 16 — Conclusion

Time: 1 minute

中文理解：

最后重复 thesis：这是 embedded system 项目，核心是 ESP32 本地闭环、任务调度、I/O、WiFi/Xbox/vision 监督级输入、安全仲裁和实测证据。

English script:

> In conclusion, B-BOT meets the main embedded-systems aim: the ESP32 owns the balance-critical control loop, while WiFi, Xbox and ROS 2 vision are integrated as supervisory command sources with watchdogs and arbitration.

> The strongest evidence is the combination of physical balance tests, 4 ms loop timing measurement, controller ablation, WiFi and vision latency data, and safety fault-injection tests.

> Thank you. I am happy to answer questions.

## Slide 17 — Backup Key Numbers

Time: only use during Q&A

中文理解：

这页不是正式讲，除非被问数据。你可以快速引用关键数字。

English phrases:

> The key O1 numbers are 0.291 degrees pitch RMS, 9 out of 10 forward recovery, 10 out of 10 backward recovery, and a 4 ms median control-loop period.

> The key teleoperation numbers are 37.41 ms TCP median acknowledgement latency and 66.13 ms vision bridge-to-ESP32 median acknowledgement latency.

> The key safety results are 10 out of 10 watchdog, close and idle fault-injection passes, plus 5 out of 5 BLE gate and queue suppression arbitration tests.

## Demo Checklist / 演示检查清单

Before presentation / 展示前：

- Charge robot battery. 给机器人电池充电。
- Check controller gains and firmware version. 确认控制参数和固件版本。
- Check safe floor area and physical stop access. 确认地面安全，手能随时停机。
- Confirm Xbox controller connection. 确认手柄连接。
- Confirm robot can balance for at least 30 seconds. 确认机器人能至少稳定 30 秒。
- Confirm WiFi IP or `wheeleg.local` is reachable. 确认 WiFi 连接。
- If using vision, start ROS 2 camera agent and vision bridge in `dry_run=true`. 如果演示视觉，先用 dry-run。
- Keep terminal windows already open and readable. 终端提前打开。
- Have report figures ready as fallback. 准备好图表作为失败 fallback。

During demo / 演示时：

- Use small commands only. 只用小命令。
- Avoid jump/cross-leg unless explicitly safe and rehearsed. 不要临时展示危险动作。
- Narrate safety boundaries while demonstrating. 一边演示一边解释安全边界。
- Stop after showing the architecture. 展示到位就停，不要越演越多。

Fallback / 失败时：

- If balance fails, show E1/E2/E9 figures. 平衡失败就切回实验图。
- If WiFi fails, explain watchdog and show E5/E6 evidence. WiFi 失败就讲 watchdog。
- If vision fails, show E10/E11 figures and state that vision is supervisory. 视觉失败就强调它是监督级层。

## One-Minute Backup Summary / 一分钟备用总结

中文理解：

如果时间被砍，用这一段快速总结。

English script:

> B-BOT is an embedded systems project using a self-balancing wheel-legged robot as the validation platform. The key design decision is to keep stabilising feedback local to the ESP32.

> The implemented controller combines LQR, PID and VMC. WiFi, Xbox and ROS 2 vision are integrated only as supervisory command sources through watchdogs and arbitration.

> The evidence includes measured static balance, disturbance recovery, 4 ms loop timing, controller ablation, WiFi and vision latency, and safety fault injection.

> The main limitation is that physical trials are small-sample engineering validation, and vision is not suitable for balance feedback.
