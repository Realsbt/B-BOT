# B-BOT Presentation Script and Demo Plan

Target duration: 20-25 minutes, including a short live demonstration.

Recommended style: do not try to explain every implementation detail. The strongest story is that B-BOT is an unstable embedded robotics system where the real contribution is the integration of local balance control, supervisory wireless/vision control, and safety-aware command arbitration.

## High-Level Structure

| Block | Time | Purpose |
|---|---:|---|
| Opening and project aim | 2 min | Define the problem and the three objectives |
| System architecture | 4 min | Explain why balance stays local to ESP32 |
| Control implementation | 4 min | Explain LQR/PID/VMC and command arbitration |
| Evidence and results | 7-8 min | Show O1/O2/O3 measurements and baselines |
| Live demo | 4-6 min | Demonstrate stable balance, command path, and safety behaviour |
| Limitations and conclusion | 2-3 min | Be objective and close with contribution |

If the session is closer to 20 minutes, reduce the demo to one balance/teleop demonstration and one safety explanation. If the session is closer to 25 minutes, include the vision dry-run demonstration.

## Slide-by-Slide Script

### Slide 1 — Title

Time: 30 seconds

Say:

> Good morning, my name is Botao Su. My project is B-BOT, a WiFi-enabled self-balancing wheel-legged robot with ROS 2 vision teleoperation.

> The key idea is that the robot must balance locally on the ESP32, while WiFi, Xbox control and vision are only allowed to send supervisory target commands.

Transition:

> I will first explain the system architecture, then the control design, then the measured results and the live demonstration.

### Slide 2 — Project Problem

Time: 1 minute

Main point:

- Wheel-legged robots are more capable than normal two-wheeled balancing robots, but leg geometry makes balance control more coupled.
- Wireless and vision control improve usability, but they are too variable for stabilising feedback.

Say:

> The problem is not only to make a robot move. The difficult part is to combine an unstable balance controller with non-deterministic communication and vision layers without letting those layers destabilise the robot.

> Therefore my design rule is strict: stabilising feedback remains local, and all remote inputs are treated as target requests with watchdog and arbitration logic.

### Slide 3 — Objectives

Time: 1 minute

Say:

> I organised the project around three objectives. O1 is embedded wheel-legged balance control. O2 is ROS 2 vision input and WiFi command communication. O3 is safe multi-source input arbitration.

> This objective structure is important because it also defines how the evaluation is judged. I do not claim vision is part of the balance loop; I test it as a supervisory command layer.

### Slide 4 — System Architecture

Time: 2 minutes

Explain:

- Bottom layer: physical robot, IMU, CAN motors, legs, battery.
- Middle layer: ESP32 firmware, FreeRTOS tasks, control loop, safety logic.
- Top layer: Xbox BLE, UART queue, WiFi TCP, ROS 2 vision bridge.

Say:

> This architecture separates time-critical and non-time-critical computation. The ESP32 owns the 4 ms balance loop. The host PC and ROS 2 vision bridge only produce high-level command lines such as DRIVE, YAWRATE or QUEUE commands.

> This separation is why the robot can tolerate WiFi and camera latency. A delayed vision command may affect teleoperation responsiveness, but it should not directly break the stabilising feedback loop.

### Slide 5 — Hardware and Firmware

Time: 1.5 minutes

Say:

> The robot uses an ESP32 controller, an MPU6050 IMU, CAN-connected wheel and joint motors, battery monitoring, and a custom PCB. On the firmware side, FreeRTOS tasks separate CAN feedback, IMU update, motor output, command parsing, BLE, WiFi and the control task.

> The implementation constraint is that all of this has to remain lightweight enough for the ESP32 while still being safe to operate on a physical robot.

### Slide 6 — Balance Control

Time: 2 minutes

Say:

> The balance controller is hierarchical. LQR provides the sagittal-plane balance action. PID loops regulate local objectives such as yaw, roll and leg length. VMC maps desired virtual leg forces and torques into joint motor commands.

> The reason I used this hierarchy is that a simple PID-only design would not express the coupled pitch and wheel dynamics clearly, while a heavy model-predictive controller would be unrealistic for this ESP32 implementation.

Possible detail if asked during the slide:

> The LQR gain is scheduled by virtual leg length, because leg length changes the effective inverted-pendulum geometry.

### Slide 7 — Command and Safety Architecture

Time: 1.5 minutes

Say:

> The robot accepts multiple input sources: Xbox BLE, UART scripts, WiFi keyboard commands and vision-generated commands. The risk is that these sources could conflict.

> To control that risk, the firmware uses command queues, direct command watchdogs, BLE enable/disable gating, dry-run mode for vision, stunt arming and full-stop injection on command loss.

> O3 is about whether those safety behaviours are predictable, not just whether the robot can receive commands.

### Slide 8 — Evaluation Strategy

Time: 1 minute

Say:

> I evaluated the system with eleven measured experiments plus a supplementary O3 arbitration bench test. The key point is that the evaluation is objective-linked: E1 to E4 and E8/E9 mainly support O1, E5/E7/E10/E11 support O2, and E6 plus O3-S support O3.

> The physical trials are engineering validation rather than population-level statistical experiments. I report failures and outliers instead of hiding them.

### Slide 9 — O1 Static Balance and Recovery

Time: 2 minutes

Use figures: E1 static balance and E2 recovery.

Say:

> For static balance, the robot achieved 0.291 degrees pitch RMS over three 60-second trials, below the 0.5 degree pass criterion.

> For impulse recovery, the robot recovered 9 out of 10 forward disturbances and 10 out of 10 backward disturbances. The forward direction is the weaker case, with one protection event, so I treat this as usable recovery with a tuning or saturation limit, not as perfect robustness.

Emphasis:

> The important point is that failure cases are still part of the evidence.

### Slide 10 — O1 Timing Boundary

Time: 1.5 minutes

Use figure: E8 loop jitter.

Say:

> E8 tests whether the local control timing is consistent with the 4 ms design target. Over 15,000 samples, the mean was 3.9998 ms and the median was 4.000 ms.

> However, the tail is not perfect. The maximum observed interval was 53.365 ms. I explicitly report this because it is a real limitation of the current task structure and logging load.

> The architectural conclusion is still valid: the timing risk is local to the ESP32 task structure, not caused by ROS 2, MediaPipe or WiFi being inside the balance loop.

### Slide 11 — O1 Controller Ablation

Time: 2 minutes

Use figure: E9 controller ablation.

Say:

> E9 is the main comparative baseline. The full controller is compared against a fixed-gain LQR variant and a no-ramp variant.

> FULL recovered 10 out of 10 impulse trials. FIXED_LQR recovered 9 out of 10 and had one protected or failed trial. The response metric improved from 1.049 seconds to 0.826 seconds, which is a 21.3 percent reduction. Peak pitch reduced from 9.85 degrees to 8.09 degrees, a 17.9 percent reduction.

> I interpret this as engineering ablation evidence that gain scheduling is useful on this platform. I do not claim it proves optimal control.

### Slide 12 — O2 WiFi and Vision Teleoperation

Time: 2 minutes

Use figures: E10 confusion matrix and E11 latency.

Say:

> The WiFi TCP command path achieved a 37.41 ms median acknowledgement latency and 88.31 ms p95 over 300 samples. That is acceptable for human target updates.

> The vision bridge produced a clean 6 out of 6 command-class matrix on selected live trials, with 85.3 percent selected-frame label accuracy. The bridge-to-ESP32 ACK median latency was 66.13 ms across 71 safe commands.

> But the full human-gesture-to-command latency is slower because the camera frame rate is around 4.85 Hz and gesture debouncing can require extra frames. This is why vision remains supervisory.

### Slide 13 — O3 Safety and Arbitration

Time: 2 minutes

Use figure: E6 watchdog fault injection.

Say:

> O3 tests whether the robot fails safely when command sources are lost or conflict. The direct-command watchdog cleared commands in all 10 watchdog trials. TCP close was detected in all 10 close trials. TCP idle produced full-stop events in all 10 idle trials.

> The supplementary arbitration test also passed 5 out of 5 BLE/PC gate trials with the Xbox controller connected, and 5 out of 5 queue/direct-command suppression trials.

> This is not exhaustive proof of every possible race condition, but it demonstrates the implemented safety behaviour on the main command paths.

### Slide 14 — Live Demonstration Plan

Time: 4-6 minutes

Recommended live demo order:

1. Robot already powered on, stable and in a safe area.
2. Show stable balance briefly.
3. Use Xbox or keyboard to send a small forward/backward or yaw command.
4. Trigger stop / release command and show return to safe state.
5. If safe and prepared, show vision bridge dry-run: gesture generates printed command without driving the robot.
6. Mention watchdog rather than intentionally causing risky movement.

Say before demo:

> I will keep the live demo conservative. The aim is not to show the most aggressive movement, but to demonstrate the architecture: local balance remains active, remote commands update targets, and safety logic can return the robot to zero motion.

If the robot fails to balance:

> This is exactly why the report treats the physical tests as engineering validation and keeps WiFi and vision outside the stabilising loop. I will switch to the recorded evidence and explain the measured data.

If WiFi or ROS 2 fails:

> The balance controller is independent of this failure. The failed layer is supervisory communication, which is why the architecture uses watchdog-protected target commands.

### Slide 15 — Limitations

Time: 1.5 minutes

Say:

> The main limitations are the manually tuned controller, manually applied physical disturbances, IMU vibration, mechanical compliance, actuator saturation, and the non-deterministic latency of WiFi and vision.

> These limitations do not invalidate the project. They define the boundary of the current contribution: a practical embedded wheel-legged balancing architecture with measured supervisory teleoperation and safety arbitration.

### Slide 16 — Conclusion

Time: 1 minute

Say:

> In conclusion, B-BOT meets the main project aim: the ESP32 owns the balance-critical control loop, while WiFi, Xbox and ROS 2 vision are integrated as supervisory command sources with watchdogs and arbitration.

> The strongest evidence is the combination of physical balance tests, 4 ms loop timing measurement, controller ablation, WiFi and vision latency data, and safety fault-injection tests.

> Thank you. I am happy to answer questions.

## Demo Checklist

Before presentation:

- Charge robot battery.
- Check controller gains and firmware version.
- Check safe floor area and physical stop access.
- Confirm Xbox controller connection.
- Confirm robot can balance for at least 30 seconds.
- Confirm WiFi IP or `wheeleg.local` is reachable.
- If using vision, start ROS 2 camera agent and vision bridge in `dry_run=true`.
- Keep terminal windows already open and readable.
- Have report figures ready as fallback if live demo fails.

During demo:

- Use small commands only.
- Avoid jump/cross-leg unless explicitly safe and already rehearsed.
- Narrate safety boundaries while demonstrating.
- Stop after showing the architecture; do not extend the demo just because it is working.

Fallback:

- If balance fails, show E1/E2/E9 figures.
- If WiFi fails, explain watchdog and show E5/E6 evidence.
- If vision fails, show E10/E11 figures and state that vision is supervisory.

## One-Minute Backup Summary

If time is cut short, say:

> B-BOT is a self-balancing wheel-legged robot where the key design decision is to keep stabilising feedback local to the ESP32. The implemented controller combines LQR, PID and VMC. WiFi, Xbox and ROS 2 vision are integrated only as supervisory command sources through watchdogs and arbitration. The evidence includes measured static balance, disturbance recovery, 4 ms loop timing, controller ablation, WiFi and vision latency, and safety fault injection. The main limitation is that physical trials are small-sample engineering validation, and vision is not suitable for balance feedback.
