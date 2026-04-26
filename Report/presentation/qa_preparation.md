# B-BOT Presentation Q&A Preparation

Use this document to prepare concise answers. The safest answering style is: answer directly, give one piece of evidence, then state the limitation if relevant.

## Control and Robotics Questions

### Why did you use LQR instead of only PID?

Answer:

> PID is useful for local objectives such as yaw, roll and leg length, but the sagittal balance problem couples pitch, pitch rate, wheel position and wheel speed. LQR is better suited for that coupled state-space problem. I still use PID where the objective is local and simpler.

Evidence:

- E9 compares FULL against FIXED_LQR and shows the full controller improves the tested recovery behaviour.

### What exactly does VMC add?

Answer:

> VMC lets the controller reason in terms of virtual leg forces and torques, then map them to joint motor commands. That is more natural for a wheel-legged robot than commanding each joint independently.

Limitation:

> The current VMC implementation is practical and lightweight; it is not a full whole-body optimisation controller.

### Why is gain scheduling needed?

Answer:

> Leg length changes the effective inverted-pendulum geometry. A gain that works at one body height may be less suitable at another. Scheduling the LQR gain by virtual leg length keeps the controller closer to the current operating point.

Evidence:

- E3 tests leg-length sensitivity.
- E9 shows FULL outperforming FIXED_LQR in the tested recovery comparison.

### Is your controller optimal?

Answer:

> No. LQR is optimal only for its linearised model and chosen cost function. My claim is more limited: the implemented controller is practical on the ESP32 and is supported by measured engineering tests. I do not claim global optimality.

## Experimental Evidence Questions

### Are 10 trials enough?

Answer:

> Ten trials are enough for engineering validation in a final-year hardware project, but not enough for a population-level reliability claim. That is why I report the result as small-sample engineering evidence and retain failures and limitations.

If challenged:

> The next improvement would be to increase E2 and E9 to 20 trials per key condition and report Wilson confidence intervals and bootstrap confidence intervals.

### Why did you keep the failed forward disturbance trial?

Answer:

> Because removing it would overstate the result. The forward direction is the weaker case, and the failure exposes a real tuning, saturation or disturbance-limit issue. Keeping it makes the conclusion more objective.

### Why is E8 acceptable if there is a 53.365 ms outlier?

Answer:

> The mean and median show that the nominal loop timing is centred on 4 ms, but the outlier shows the embedded timing is not fully deterministic. I do not hide that. The architectural point is that this timing risk is local to the ESP32 workload and not caused by putting WiFi or vision inside the balance loop.

### Why not use WiFi or vision for closed-loop balance?

Answer:

> The latency and jitter are too large and variable. The balance loop targets 4 ms, while WiFi and vision latencies are tens to hundreds of milliseconds. Therefore WiFi and vision can update human-level targets but should not close the stabilising feedback loop.

### How do you know the vision system is useful if accuracy is only 85.3%?

Answer:

> The vision system is useful for controlled supervisory commands, not for autonomous high-speed control. The retained failure cases justify dry-run preview, debouncing, stunt gating and watchdogs. I treat vision as a convenience layer with safety constraints.

## Safety and Arbitration Questions

### What happens if the WiFi connection drops?

Answer:

> The firmware detects socket close or command timeout and injects stop behaviour. In E6, TCP close was detected in all 10 trials, and TCP idle produced full-stop events in all 10 idle trials.

### What happens if Xbox and PC commands conflict?

Answer:

> The PC tool can disable BLE target updates while it is active, and the supplementary O3 arbitration test measured the BLE/PC gate with the Xbox controller connected. It passed 5 out of 5 trials.

### What prevents a queue command and direct DRIVE command fighting?

Answer:

> Queue execution suppresses or rejects direct drive commands. The O3 supplement tested this case and observed `DRIVE ignored: command queue busy` in 5 out of 5 trials.

### Is the safety testing exhaustive?

Answer:

> No. It covers the implemented main command paths and realistic fault cases, but it is not exhaustive over every possible simultaneous-input race condition. The report states this limitation explicitly.

## Software and Repository Questions

### What code did you write yourself?

Answer:

> The ESP32 firmware integration, balance-control structure, command parsing, WiFi TCP command server, arbitration behaviour, ROS 2 vision bridge integration and experiment tools are project work. Third-party libraries such as ESP32 Arduino, ROS 2, MediaPipe, OpenCV and NimBLE are reused and attributed.

### Why is the report not in the GitHub repository?

Answer:

> The public repository is a software evidence snapshot. The report and experimental appendices are submitted separately as assessment material. Appendix F explains this boundary and links the public repository commit.

### Is the repository open source?

Answer:

> It is public for assessment visibility, but it is not open source. The custom project code uses a restricted project-code license, and third-party components retain their own licenses.

## Hardware Questions

### What is custom in the hardware?

Answer:

> The robot mechanical platform and ESP32 controller PCB are project-specific. The Yahboom component is the separate ROS 2 WiFi camera module, used as an image source.

### Why use ESP32 instead of Raspberry Pi for balance?

Answer:

> ESP32 gives a simple embedded real-time boundary for the balance loop. A Raspberry Pi or Jetson would be useful as a companion computer for vision and logging, but I would still keep final stabilising control and safety stop behaviour local to the microcontroller.

## Project Management Questions

### What was the biggest project risk?

Answer:

> The biggest risk was spending too much time on low-level balance and not leaving enough time for measured evaluation. I managed this by narrowing the contribution to local balance plus supervisory teleoperation, and by organising the report around objective-linked experiments.

### What would you do next with more time?

Answer:

> I would improve the logging and tuning toolchain first: automatic trial markers, parameter versioning, repeatable gain sweeps and larger E2/E9 datasets. After that, I would improve state estimation and move ROS 2 vision onto an onboard companion computer while keeping balance local to the ESP32.

## Difficult Questions and Safe Answers

### Is this really autonomous robotics?

Answer:

> It is not full autonomy. It is an embedded balance and supervisory teleoperation project. The autonomy-related part is the vision-to-command layer, but I deliberately limit it to supervisory commands because of safety and timing constraints.

### Did the robot achieve all original ambitions?

Answer:

> Not every possible ambition, especially aggressive dynamic behaviours and exhaustive race-condition testing. But the core implemented contribution is complete: balance-critical control runs locally, remote command paths are integrated, and the main behaviours are measured.

### What is the single strongest result?

Answer:

> The strongest result is the integration evidence: the robot combines local balance, measured 4 ms loop timing, controller ablation, WiFi/vision command paths and safety fault handling in one implemented system.

### What is the weakest result?

Answer:

> The physical control trials are still small-sample and manually disturbed. That limits statistical strength. I handle that by being explicit about the limitation and by treating the results as engineering validation rather than proof of general reliability.

## Short Closing Answers

Use these if the Q&A is running long:

- "The balance loop is local; WiFi and vision are supervisory."
- "The result supports engineering validation, not statistical proof."
- "The outlier is reported because it is a real limitation."
- "Safety behaviour is measured on the main command paths, but not exhaustive over every race condition."
- "The next technical step is better logging, parameter versioning and larger E2/E9 datasets."
