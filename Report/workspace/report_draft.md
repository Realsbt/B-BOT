# B-BOT Final Report — Draft (EN)

> **用法**：先在这里写英文段落（速度比 LaTeX 快），定稿后 copy 进 `../main.tex` 对应 `\section{}` 里。
> **硬约束**：正文 ≤35 页 / Calibri 12 / 1.5 倍行距 / 左对齐 / IEEE 引用。
> **截止**：2026-05-01 14:00 Canvas 提交。
> **可复用**：Canvas 上的 Draft Introduction / Methodology / Draft Final Report 拿到后先贴进对应节点，再精修。

---

## Front Matter

### Abstract  *(1 页 / ~300 words)*
*Must cover: problem, motivation, method, key results, limitations, contribution. Self-contained (no citations, no undefined abbreviations).*

B-BOT is a self-balancing wheel-legged robot developed to investigate how real-time embedded balance control can be combined with safe wireless and vision-based teleoperation. Wheel-legged robots offer more mobility than conventional two-wheeled balancing robots because they can change body height and coordinate wheel and leg motion, but this also increases the coupling between body pitch, wheel torque and leg geometry. The main design constraint in this project was therefore that stabilising feedback must remain local to the embedded controller and must not depend on WiFi, camera processing or host-side software timing.

The implemented system uses an ESP32 controller running FreeRTOS tasks for motor feedback, inertial sensing, leg kinematics, target updating and balance control. The balance controller combines linear quadratic regulation for sagittal balance, PID loops for yaw, roll and leg-length regulation, and virtual model control to map virtual leg forces and torques to joint motor commands. A host-side ROS 2 vision bridge receives images from a Yahboom camera path, runs MediaPipe-based perception, and sends supervisory commands to the robot through a WiFi TCP line protocol. Xbox BLE, UART commands, WiFi TCP commands and vision-generated commands are coordinated through shared command parsing, queue logic, watchdogs and safety gates.

The system was evaluated using static balance, disturbance recovery, leg-length variation, control-loop jitter, WiFi command-entry latency, watchdog fault injection and vision event tests. The final results showed [insert key control result], [insert key timing/latency result] and [insert key safety/vision result]. The main limitation is that the vision and WiFi layers are suitable only for supervisory teleoperation, not for closing the stabilising control loop. The project contributes a practical embedded wheel-legged balancing architecture extended with safety-aware multi-source command arbitration and ROS 2 vision teleoperation.

### Declaration of Originality
*(模板原文，整页照抄，无需改写)*

### Intellectual Property Statement
*(模板原文，整页照抄，无需改写)*

### Acknowledgements  *(可选)*

<!-- Optional: add acknowledgements here after confirming names/titles. Keep this short, for example supervisor support, lab access, and any technical advice. -->

---

## 1. Introduction  *(≈3–4 pages)*

### 1.1 Background and motivation
*Wheel-legged platform 的工程价值 + 引入 WiFi / ROS 2 vision 的动机（ESP32 实时底环 vs. PC 视觉识别与命令生成分层）。明确：底盘 ESP32 当前不是 micro-ROS 节点；micro-ROS 只用于 Yahboom camera → ROS 2 image topic。*

Self-balancing robots are useful engineering platforms because they combine unstable dynamics, embedded sensing, real-time control and actuator coordination in a compact system. A conventional two-wheeled balancing robot mainly regulates body pitch while moving through wheel torque. A wheel-legged robot extends this concept by adding controllable leg geometry, which can change body height, support dynamic actions and improve mobility. The additional mechanical capability also increases the control challenge because body pitch, wheel motion, leg length and joint torque become strongly coupled.

This project developed B-BOT, a WiFi-enabled self-balancing wheel-legged robot based on an ESP32 embedded controller. The main engineering problem was not only to make the robot stand and move, but to do so while integrating multiple command sources safely. The robot can receive input from an Xbox BLE controller, UART scripted commands, WiFi TCP commands from a host computer, and a ROS 2 / MediaPipe vision bridge. These inputs all affect the same physical robot, so the system must avoid conflicting commands and must fail safely when a command source disappears.

The central design decision was to keep the stabilising control loop local to the ESP32. The robot's pitch, wheel and leg feedback are processed on the embedded controller, and the LQR/PID/VMC control computation is executed in FreeRTOS tasks. Host-side software is deliberately kept outside the balance loop. This is necessary because WiFi latency, camera frame rate, ROS 2 scheduling and MediaPipe inference are not deterministic at the 4 ms timescale required by the balance controller.

The ROS 2 part of the project is therefore used as a supervisory perception layer rather than as the low-level control bus. The Yahboom camera provides images to the host ROS 2 system through a camera-side micro-ROS path. The host-side `wheeleg_vision_bridge` processes those images and converts recognised visual events into text commands. Those commands are then sent to the ESP32 over a WiFi TCP line protocol. In the current implementation, the bottom ESP32 robot controller is not a micro-ROS node.

The motivation for this architecture is practical safety. Vision teleoperation is useful for demonstration and human interaction, but an incorrect gesture classification or network delay should not directly destabilise the robot. By treating vision and WiFi commands as temporary target requests with watchdog expiry, B-BOT can combine real-time embedded balance control with higher-level remote inputs in a controlled way.

### 1.2 Aims and objectives
*总目标一句话 + 3 条可测 objectives：*
*  O1 — LQR/PID/VMC 融合底层平衡控制*
*  O2 — ROS 2 视觉输入链路 + WiFi TCP 机器人命令通道*
*  O3 — 多源输入（Xbox / TCP / 视觉）安全仲裁*

The aim of the project was to design, implement and evaluate a self-balancing wheel-legged robot that combines real-time embedded balance control with safe wireless and vision-based teleoperation.

The project objectives were:

**O1 — Embedded wheel-legged balance control.**  
Develop an ESP32-based control system that combines LQR, PID loops and VMC to stabilise the robot, regulate leg geometry and command wheel/joint torques. This objective is evaluated through static balance, disturbance recovery, leg-length variation and control-loop jitter tests.

**O2 — ROS 2 vision input and WiFi TCP command channel.**  
Implement a host-side ROS 2 vision pipeline and WiFi TCP command path that can generate and transmit supervisory robot commands without entering the stabilising feedback loop. This objective is evaluated through TCP command-entry latency, watchdog/disconnect testing and camera/vision event logs.

**O3 — Safe multi-source input arbitration.**  
Support Xbox BLE, UART scripted commands, WiFi TCP commands and vision-generated commands without allowing uncontrolled conflicts between input sources. This objective is evaluated through teleoperation response tests, command queue behaviour, `dry_run` vision tests, stunt arming behaviour and disconnect-stop validation.

The success criteria are not based on maximum speed or fully autonomous navigation. Instead, the project is judged by whether the implemented robot demonstrates stable embedded balancing, predictable command handling and evidence-based safety behaviour under realistic communication failures.

### 1.3 Report structure

Chapter 2 reviews the relevant literature on two-wheeled and wheel-legged balancing robots, control strategies for unstable mobile robots, and ROS 2 / micro-ROS communication in non-deterministic networks. Chapter 3 presents the implemented system design, including hardware integration, embedded task structure, sensing, state estimation, control algorithms, WiFi TCP communication and input arbitration. Chapter 4 evaluates the system using experiments mapped to the three objectives. Chapter 5 concludes the report by summarising the technical contribution, identifying limitations and proposing future work.

### 1.4 Project Management  *(≤1 页，Handbook §9.3 强制)*
*Draw on appendices: Gantt, Risk Register, CPD Log. Discuss plan deviations, risks, CPD, initiative.*

The project was managed as an iterative engineering build rather than as a single linear implementation. The initial plan separated the work into hardware bring-up, embedded control, communication integration, host-side vision, testing and final reporting. Appendix B contains the project plan and Gantt chart, including the final schedule used during the report-writing phase. The main deviation from the original plan was that low-level balance control and safety handling required more time than expected, while the ROS 2 vision layer had to be scoped as a supervisory teleoperation feature rather than as part of the stabilising control loop.

Risk management was important because the project involved an unstable robot, high-torque motors, batteries, WiFi control and vision-triggered actions. Appendix C contains the risk register, and Appendix E contains the health and safety risk assessment. The most important technical risks were uncontrolled motor output, stale remote commands, IMU calibration error and mechanical damage during disturbance testing. These risks directly influenced the design: balance-disabled states produce zero torque, direct commands expire through watchdogs, WiFi disconnects inject a full-stop command sequence, and the vision bridge defaults to `dry_run`.

The project also required continuing professional development across embedded control, FreeRTOS scheduling, ROS 2, micro-ROS camera integration, MediaPipe and experimental data analysis. Appendix D contains the CPD log. This self-directed learning affected the final architecture: instead of attempting to place the whole robot inside ROS 2, the design separates the hard real-time ESP32 controller from the host-side perception pipeline. This was a practical project-management decision as well as a technical one, because it reduced integration risk while preserving a clear demonstration of vision-based teleoperation.

---

## 2. Literature Review  *(≈5–6 pages)*

### 2.1 Introduction

This literature review is organised by design problem rather than by individual paper. The project combines three areas: self-balancing wheel-legged robotics, embedded control of coupled unstable systems, and remote robot command interfaces over non-deterministic communication links. Reviewing these areas separately makes it possible to justify the architecture used in this project: real-time stabilisation remains on the ESP32, while ROS 2 vision and WiFi communication are used only as supervisory command inputs.

Section 2.2 reviews the development from two-wheeled inverted-pendulum robots to wheel-legged robots. Section 2.3 compares the main control approaches relevant to this project, including PID, LQR, ADRC and VMC. Section 2.4 reviews ROS 2, micro-ROS and lossy-network communication from the perspective of safe teleoperation. Section 2.5 then summarises the technical gaps that motivate the design choices presented in Chapter 3.

### 2.2 Wheel-legged & Self-balancing Robotics
*Two-wheeled → wheel-legged 演进；地形适应、高度调节、重心变化的代价。*
*Cite: `grasser2002joe`, `chan2013review`, `klemm2019ascento`, `feng2023wheellegged`, `xin2025unified`.*

Two-wheeled self-balancing robots are commonly modelled as mobile inverted pendulums. A representative early example is JOE, which demonstrated that a compact two-wheeled robot can balance and move using feedback control around an unstable upright equilibrium \cite{grasser2002joe}. Later reviews show that this class of robot is attractive because the mechanical structure is simple, but the control problem is non-trivial: the robot must regulate body pitch while simultaneously responding to wheel motion and external disturbances \cite{chan2013review}.

Wheel-legged robots extend this problem by adding controllable leg geometry. This increases mobility because the robot can change height, absorb impacts, step over small obstacles or perform dynamic actions. However, the additional degrees of freedom also change the balance dynamics. Leg length changes the centre of mass and the effective inverted-pendulum geometry, while joint motion introduces coupling between support force, body pitch and wheel torque. For this reason, a wheel-legged robot cannot be treated as only a two-wheeled inverted pendulum with extra actuators.

Ascento is a useful reference point because it shows the mobility benefit of a two-wheeled jumping wheel-legged platform \cite{klemm2019ascento}. Its design demonstrates that wheel-legged morphology can provide behaviours beyond ordinary two-wheeled balancing, but it also highlights the need for careful coordination between wheel control, leg actuation and body stabilisation. More recent wheel-legged studies have investigated combined control structures, including LQR with disturbance rejection and unified control frameworks for model variations \cite{feng2023wheellegged,xin2025unified}.

The relevance to B-BOT is the trade-off between capability and implementation complexity. The project uses a small ESP32-based platform rather than a high-power research robot. This means the design must prioritise a controller that is computationally light, robust enough for demonstration, and compatible with the available sensors and motor feedback. The wheel-legged structure motivates the use of leg kinematics and virtual leg forces, but the embedded hardware motivates keeping the implementation simple and deterministic.

### 2.3 Control Strategies Comparison
*PID / LQR / ADRC / VMC 的假设、算力、鲁棒性对比。*
*Cite: `han2009adrc`, `pratt2001vmc`, `kim2015dynamic`.*
*⭐ 建议表：Representative Systems — Metrics Baselines（为 §4 的对比留锚点）*

Control methods for balancing robots can be compared by asking what part of the system they control well. PID control is attractive for embedded implementation because it is simple, computationally cheap and easy to tune on individual variables. It is well suited to local objectives such as yaw-rate correction, roll correction or leg-length regulation. Its weakness is that it does not naturally account for the coupled dynamics between body pitch, wheel position, wheel velocity and leg geometry.

LQR is commonly used for inverted-pendulum and wheel-legged balance problems because it controls a vector of coupled states through a single feedback gain. Dynamic models of two-wheeled inverted pendulum robots show why body pitch, pitch rate, wheel position and wheel velocity should be considered together rather than as independent loops \cite{kim2015dynamic}. For B-BOT, this makes LQR a suitable core controller for the sagittal balance problem. The limitation is that the quality of LQR depends on the model, gain tuning and operating point. A fixed gain may work over a narrow range, while a wheel-legged platform benefits from gain scheduling as leg length changes.

ADRC addresses disturbance and model uncertainty by estimating and rejecting the total disturbance acting on a system \cite{han2009adrc}. This is attractive for wheel-legged robots because contact changes, modelling errors and external pushes are difficult to model exactly. However, ADRC also introduces additional observer dynamics and tuning parameters. For this project, the implementation risk and tuning effort were higher than the expected benefit within the available development time. ADRC is therefore treated as a literature comparator rather than as the selected embedded controller.

VMC provides a different abstraction. Instead of commanding each joint directly, the controller defines virtual forces and torques acting on the robot body or leg, then maps those virtual quantities to actuator torques \cite{pratt2001vmc}. This is particularly useful for a wheel-legged mechanism because leg support force and hip torque are more meaningful for balance than individual joint torques. In B-BOT, VMC is used after the LQR and PID layers: LQR and PID determine the desired virtual support and body effects, and VMC maps them to the two joint motors on each side.

**Table 2.1. Control strategy comparison for B-BOT.**

| Strategy | Strength | Limitation | Role in this project |
|---|---|---|---|
| PID | Simple, fast, easy to tune locally | Weak for strongly coupled whole-body dynamics | Used for yaw, roll, leg length and auxiliary regulation |
| LQR | Handles coupled state feedback in one controller | Depends on model quality and operating point | Main sagittal balance controller with leg-length gain scheduling |
| ADRC | Robust to unmodelled disturbances | More observer and tuning complexity | Literature comparator, not implemented |
| VMC | Maps meaningful virtual forces to joint torques | Requires kinematic mapping and careful force limits | Used to convert virtual leg force/torque to joint motor commands |

The resulting design choice is a hybrid controller rather than a single-method controller. LQR is used where coupling is strongest, PID is used where local regulation is sufficient, and VMC bridges the gap between high-level virtual forces and actuator-level torques.

### 2.4 Embedded ROS & Lossy-Network Communication
*Camera micro-ROS agent → ROS 2 host → MediaPipe → WiFi TCP robot command 的分层；TCP 延迟、断线检测、watchdog；ROS 2 QoS 只用于图像/状态 topic 背景，不写成底盘控制链路。*
*Cite: `macenski2022ros2`, `omg_ddsxrce`, `microros_docs`, `eprosima_microxrcedds`, `ros2_qos_design`.*

ROS 2 is widely used for robot software because it provides a modular communication model, standard message types, launch tooling and integration with perception libraries \cite{macenski2022ros2}. Its middleware design includes quality-of-service policies that allow developers to choose trade-offs such as reliability, history depth and durability for different data streams \cite{ros2_qos_design}. These features are useful for camera images, status topics and host-side processing, but they do not remove the real-time constraints of a balancing controller.

micro-ROS extends ROS 2 concepts to resource-constrained embedded devices through the DDS-XRCE model \cite{omg_ddsxrce,microros_docs}. In a typical micro-ROS system, a microcontroller communicates with a host-side agent, and the agent bridges between DDS-XRCE and the ROS 2 graph. eProsima's Micro XRCE-DDS documentation describes the transport-layer options used by such systems \cite{eprosima_microxrcedds}. This architecture is valuable when a microcontroller needs to publish or subscribe to ROS 2 topics directly.

The B-BOT implementation uses a narrower boundary. The bottom ESP32 controller is not a micro-ROS node. Instead, micro-ROS is used only in the camera image path: the Yahboom camera publishes images to the host ROS 2 system, and the host-side vision bridge processes those images. Robot commands are then transmitted to the ESP32 over a WiFi TCP line protocol. This distinction is important because it avoids overstating the role of ROS 2 in the balance-critical path.

Wireless command links introduce failure modes that are not present in a local feedback loop. Packets can be delayed, TCP clients can disconnect, the host process can crash, and a vision algorithm can output stale or incorrect events. For a self-balancing robot, these failures should not be allowed to hold a non-zero motion command indefinitely. The literature on ROS 2 and micro-ROS supports the idea of modular distributed robot software, but the safety requirement in this project is more direct: remote commands must be treated as temporary target requests with watchdog expiry, not as hard real-time control signals.

This motivates the command architecture used in Chapter 3. WiFi TCP and vision commands update target variables or enqueue scripted actions, while the local ESP32 balance loop continues to use local IMU and motor feedback. Watchdogs, disconnect handling, `dry_run` mode and explicit stunt arming are therefore not secondary features; they are required to make remote and vision-based control acceptable for a physically unstable robot.

### 2.5 Summary
*Gap → Design Choice 表；把综述收束到本文方法。*

The literature shows that B-BOT sits between two established areas. From balancing-robot work, it inherits the need for fast local feedback around an unstable body. From ROS 2 and micro-ROS work, it inherits the opportunity to use modular host-side perception and communication. The main engineering challenge is to combine these areas without allowing non-deterministic host-side processing to destabilise the robot.

**Table 2.2. Literature gap to design choice.**

| Gap identified from literature | Design choice in B-BOT |
|---|---|
| Wheel-legged robots have coupled pitch, wheel and leg dynamics | Use LQR for sagittal balance, PID for auxiliary loops and VMC for joint torque mapping |
| Leg length changes the operating point | Schedule the LQR gain using the virtual leg length |
| Embedded hardware has limited computation and timing margin | Keep the balance loop local to ESP32 FreeRTOS tasks |
| Host-side vision and wireless communication are non-deterministic | Treat ROS 2 vision and WiFi TCP as supervisory command inputs only |
| Remote commands can become stale after host or network failure | Add direct-command watchdogs, TCP idle/disconnect full-stop and command arbitration |
| Vision-generated actions can be unsafe if misclassified | Default the bridge to `dry_run` and block high-risk actions unless armed |

These design choices define the Methods chapter. The report does not claim that B-BOT solves general autonomous wheel-legged locomotion. Its contribution is a practical embedded wheel-legged balancing system with a safety-aware wireless and vision teleoperation layer.

---

## 3. Methods  *(≈8–10 pages)*

### 3.1 Introduction — Top-level Requirements

The system was designed around one primary constraint: the balance loop must remain local to the ESP32 controller and must not depend on WiFi, ROS 2, camera processing, or any host-side software. Wireless communication and vision processing were therefore treated as supervisory command inputs rather than components of the stabilising feedback loop. This separation reduces the risk that variable WiFi latency, camera frame-rate variation, or MediaPipe inference delay can directly destabilise the robot.

The top-level requirements used to guide the implementation are summarised in Table 3.1. The timing values are implementation targets from the firmware task structure and are later checked experimentally where possible.

**Table 3.1. Top-level implementation requirements.**

| Requirement area | Target / implementation choice | Rationale |
|---|---|---|
| Balance control locality | All balance-critical computation runs on the ESP32 | Prevents wireless or host-side delays from entering the stabilising loop |
| Main control period | 4 ms target period for `CtrlBasic_Task` | Provides a sufficiently fast update rate for pitch and wheel-leg stabilisation |
| Leg kinematics update | 4 ms target period | Keeps leg length and leg angle estimates aligned with the control loop |
| IMU update | 5 ms target period using MPU6050 DMP packets | Provides attitude and angular-rate feedback at a comparable rate to the control loop |
| CAN motor feedback/output | 2 ms receive/send polling in firmware tasks | Maintains fresh wheel and joint motor state for the controller |
| Manual control input | Xbox BLE processing at approximately 50 Hz | Gives responsive human teleoperation without entering the hard real-time path |
| WiFi direct-command safety | 500 ms watchdog for `DRIVE` and `YAWRATE` direct commands | Prevents stale remote commands from continuing after host or network failure |
| TCP client safety | 1500 ms idle watchdog plus full-stop on client drop / WiFi loss | Ensures the robot is commanded to stop when the TCP command stream fails |
| Vision safety | `dry_run` default enabled; `stunt_armed` default disabled | Prevents unverified vision outputs from driving the robot or triggering high-risk actions |

These requirements define the structure of this chapter. Section 3.2 introduces the overall architecture and task timing. Section 3.3 describes the mechanical and electrical integration. Section 3.4 explains sensing and state estimation. Section 3.5 presents the LQR/PID/VMC control design. Section 3.6 describes the ROS 2 vision bridge, WiFi TCP command interface, and input arbitration logic.

### 3.2 System Architecture

The implemented system uses a layered architecture, shown conceptually in Fig. 3.1. The lowest layer consists of the physical robot: the ESP32 controller, MPU6050 inertial measurement unit (IMU), CAN-connected wheel and joint motors, battery monitoring circuitry, and the wheel-leg mechanism. The middle layer is the ESP32 firmware, which performs motor feedback processing, leg kinematics, state estimation, balance control, command parsing, and safety handling. The upper layer consists of optional command sources: Xbox BLE manual control, UART2 scripted commands, WiFi TCP commands from a PC tool, and ROS 2 / MediaPipe vision commands generated on the host computer.

**Fig. 3.1 to add: System architecture and data flow.**  
Recommended blocks: robot hardware, ESP32 firmware tasks, BLE input, UART2 command input, WiFi TCP server, Yahboom camera, micro-ROS agent, ROS 2 vision bridge, MediaPipe, command encoder.

The key architectural decision is that the ESP32 is not used as a micro-ROS node in the current implementation. Instead, micro-ROS is used only in the camera-to-host image path: the Yahboom camera publishes compressed image messages to the ROS 2 host via a micro-ROS agent. The host-side `wheeleg_vision_bridge` subscribes to the camera topic, runs MediaPipe-based perception, encodes the resulting visual event into the same textual command protocol used by other tools, and sends the command to the robot over WiFi TCP. The robot therefore receives vision commands through the same parser as keyboard or scripted commands.

This architecture keeps the fast balance loop isolated. The ESP32 control loop uses local IMU, wheel, and leg states. Host-side vision can request a target velocity, yaw rate, jump, or other high-level action, but it cannot directly close the balance loop. This is important because the camera frame rate, ROS 2 scheduling, MediaPipe inference time, and WiFi latency are all non-deterministic relative to the 4 ms control period.

Fig. 3.2 should show the firmware execution model. The most time-critical tasks are the CAN feedback/output tasks, the leg kinematics task, the IMU task, the target update task, and the main control task. Lower-priority tasks handle BLE input, UART2 commands, WiFi TCP command reception, motor calibration, and diagnostic logging.

**Fig. 3.2 to add: Firmware execution and communication timing.**

| Firmware component | Main function | Nominal timing / behaviour |
|---|---|---|
| `CAN_RecvTask` | Polls CAN motor feedback | 2 ms polling |
| `Motor_SendTask` | Sends motor voltage commands over CAN | 2 ms loop delay |
| `IMU_Task` | Reads MPU6050 DMP packet and gyro data | 5 ms target period |
| `LegPos_UpdateTask` | Computes virtual leg length, angle and derivatives | 4 ms target period |
| `Ctrl_TargetUpdateTask` | Applies speed ramping, position target limiting and yaw target integration | 4 ms target period |
| `CtrlBasic_Task` | Computes LQR/PID/VMC control output | 4 ms target period |
| `BLE_TestTask` | Processes Xbox controller notifications | 20 ms target period |
| `UART2_CommandTask` | Parses UART2 command lines | 10 ms target period |
| `WiFiCmdTask` | Accepts TCP client, parses command lines, handles disconnects | 10 ms loop delay when connected |
| `Serial_Task` | Applies direct-command watchdogs | 50 ms loop delay |

The data flow inside the firmware is deliberately simple. Sensor and motor tasks update global state variables. The target update task smooths external target commands. The control task reads the current state and target values, calculates wheel and joint torque commands, and writes them to the motor abstraction. Command sources do not drive actuators directly; they only update target values or enqueue scripted actions.

### 3.3 Mechanical & Electrical Design

The robot platform is based on a Yahboom ESP32 wheel-legged balancing robot that was extended with additional firmware, host-side software, and safety logic. The mechanical layout consists of two wheel modules and two articulated legs. Each side has one wheel motor and two leg joint motors, giving six motors in total: four joint motors for changing the virtual leg geometry and two wheel motors for ground contact and balance control.

The ESP32 was selected as the embedded controller because it provides sufficient processing capability for the control loop while also supporting Bluetooth Low Energy (BLE), WiFi, FreeRTOS tasks, and Arduino/PlatformIO development. The firmware is built using PlatformIO for the `esp32doit-devkit-v1` board with the Arduino framework. This choice reduced the development overhead for integrating the MPU6050 IMU, ADS1115 battery monitoring, BLE controller support, and WiFi command server.

The MPU6050 IMU provides body attitude and angular-rate feedback. The motor controllers communicate with the ESP32 over CAN, allowing joint and wheel angle/speed feedback to be used by the leg kinematics and balance controller. Battery voltage is monitored through an ADC path, allowing the firmware to observe the supply condition and support future output compensation or low-voltage safety logic.

**Fig. 3.3 to add: Photograph of the assembled robot with labelled components.**

**Fig. 3.4 to add: Electrical and communication block diagram.**  
Recommended blocks: ESP32, MPU6050 over I2C, ADS1115 / battery monitoring, CAN bus to six motors, BLE controller, WiFi AP/host PC, UART2 optional input.

**Table 3.2. Main hardware components.**

| Component | Role in the system |
|---|---|
| ESP32 development board | Main embedded controller running FreeRTOS tasks, balance control, command parsing, BLE and WiFi |
| MPU6050 IMU | Provides yaw, pitch, roll and angular velocity for attitude feedback |
| Four joint motors | Control the left and right virtual leg geometry |
| Two wheel motors | Provide wheel torque for balancing and forward/yaw motion |
| CAN bus | Transfers motor feedback and output commands between ESP32 and motor drivers |
| ADS1115 / ADC voltage sensing | Monitors battery voltage for diagnostics and future compensation |
| Xbox BLE controller | Primary human manual input |
| Yahboom ROS WiFi camera | Provides compressed images to the ROS 2 host through a micro-ROS agent |

The hardware design was constrained by safety and debugging needs. The robot can be tested with motors disconnected or the body supported so that WiFi, command parsing, and vision-command generation can be validated without producing physical motion. This was important because the host-side vision bridge can generate movement commands from camera input, and those commands must be verified in `dry_run` mode before being allowed to drive the robot.

### 3.4 Perception & State Estimation

The controller uses two categories of state information: body attitude from the IMU and virtual leg state from joint motor feedback. These states are calculated on the ESP32 and are used directly by the balance controller.

The MPU6050 is initialised over I2C and configured to use its Digital Motion Processor (DMP). During startup, the firmware loads stored accelerometer and gyroscope offsets from non-volatile preferences. If no saved offsets are present, the IMU calibration routine is run and the resulting offsets are stored for future use. This calibration step is important because pitch and angular-rate bias directly affect the stability margin of the balancing controller.

During the IMU task, the firmware reads the latest DMP FIFO packet and extracts quaternion, gravity and yaw-pitch-roll values. The body pitch and roll are used directly by the controller, and angular rates are read from the raw gyroscope and converted from degrees per second to radians per second. The yaw angle is unwrapped across the \( \pm \pi \) discontinuity by tracking the number of yaw revolutions, which allows the yaw controller to use a continuous heading target rather than a wrapped angle.

The leg state is computed from joint motor angles using MATLAB-generated kinematic functions. For each side, `leg_position()` maps the two joint angles to virtual leg length and virtual leg angle. `leg_speed()` maps joint speeds and joint angles to virtual leg length rate and virtual leg angle rate. The leg length acceleration is estimated by differentiating the leg length rate and applying a first-order low-pass filter. These virtual leg variables are updated every 4 ms so that they remain aligned with the main control period.

The resulting state variables are:

| Symbol / variable | Source | Use |
|---|---|---|
| body pitch \( \phi \) | MPU6050 DMP | LQR balance state |
| pitch rate \( \dot{\phi} \) | MPU6050 gyroscope | LQR balance state |
| body roll | MPU6050 DMP | Roll PID feedback |
| roll rate | MPU6050 gyroscope | Roll PID feedback |
| yaw | Unwrapped MPU6050 yaw | Yaw PID feedback |
| yaw rate | MPU6050 gyroscope | Yaw PID feedback |
| wheel position \( x \) | Mean wheel angle multiplied by wheel radius | LQR state and position target limiting |
| wheel velocity \( \dot{x} \) | Mean wheel speed multiplied by wheel radius | LQR state and speed limiting |
| virtual leg length | `leg_position()` | Leg length PID and gain scheduling |
| virtual leg angle \( \theta \) | `leg_position()` and body pitch | LQR state |

The state estimation design is intentionally lightweight. It uses the MPU6050 DMP rather than implementing a custom attitude filter on the ESP32. More advanced filters such as Madgwick or nonlinear complementary filters are relevant background methods \cite{madgwick2011imu,mahony2008complementary}, but the current implementation relies on the DMP output and joint-based kinematics to keep the embedded computation simple.

### 3.5 Control Architecture & Algorithms

The balance controller uses a hierarchical structure. LQR provides the main sagittal-plane balance control, PID loops handle auxiliary objectives such as leg length, roll and yaw, and virtual model control (VMC) maps desired virtual leg forces and torques into individual joint motor torques. This structure was chosen because the robot is strongly coupled, but the ESP32 implementation must remain simple enough to run at a 4 ms control period.

The main control task first constructs the LQR state vector:

```text
x = [theta, dtheta, position_error, velocity_error, pitch, pitch_rate]
```

Here, `theta` is the mean virtual leg angle relative to the body, `dtheta` is its derivative, `position_error` is the wheel position relative to the current target position, `velocity_error` is the wheel velocity relative to the target speed, and `pitch` / `pitch_rate` are measured from the IMU. The target position and target speed are not applied directly from external inputs. Instead, `Ctrl_TargetUpdateTask` applies a speed ramp, limits the target position to remain within a local window around the current robot position, and limits the speed target relative to the measured wheel velocity. This prevents sudden command changes from injecting large discontinuities into the balance loop.

The LQR gain is scheduled as a function of the current virtual leg length using the MATLAB-generated function `lqr_k(legLength)`. This produces a gain matrix for the current body height. The controller multiplies this gain by the state vector to produce two main outputs: a wheel torque component and a hip/leg-angle torque component. The wheel torque component is applied symmetrically to the left and right wheel motors, with a yaw PID correction added differentially for turning.

The auxiliary PID loops are:

| PID loop | Feedback | Control effect |
|---|---|---|
| Yaw PID | yaw angle and yaw rate | Adds differential wheel torque for turning |
| Roll PID | body roll and roll rate | Adds left/right leg force difference for lateral stabilisation |
| Leg length PID | mean virtual leg length and leg length rate | Generates the base virtual support force |
| Leg angle PID | left-right leg angle difference and rate | Coordinates the two legs and supports cross-step behaviour |

The leg length PID generates a virtual vertical support force. The roll PID modifies this force asymmetrically between the left and right legs, allowing the controller to compensate for lateral body tilt. The leg angle PID controls the difference between the left and right virtual leg angles and can also generate a deliberate oscillating offset during cross-step behaviour.

The VMC stage converts the virtual leg force and hip torque into individual joint torques. For each side, `leg_vmc_conv(F, Tp, phi1, phi4)` maps the desired virtual force \(F\), virtual torque \(T_p\), and the two joint angles into two joint motor torque commands. This allows the high-level controller to reason in terms of virtual leg force and body torque while the motor layer receives actuator-level torque targets. VMC is a useful abstraction for legged systems because it allows virtual forces to be designed around the body and leg geometry rather than directly around individual joint commands \cite{pratt2001vmc}.

The controller also includes state-dependent safety behaviour. When balance is disabled, all motor torques are set to zero unless the firmware is in a dedicated leg test mode. When the robot is detected as airborne, wheel motor output is disabled and the feedback matrix is modified so that the controller prioritises maintaining leg posture rather than applying wheel torque. Ground contact is estimated from the commanded support forces, the leg mass term, leg length acceleration and vertical acceleration. A short memory of recent contact is used to avoid false airborne detection caused by brief bouncing.

Several action states are implemented as separate behaviours on top of the stabilising controller. Stand-up preparation commands the legs into a suitable starting posture. Jump preparation briefly lowers the body and then applies joint torques for extension and retraction. Cross-step behaviour applies a controlled left-right virtual leg angle offset. These behaviours are useful for demonstration, but the report treats them as auxiliary states rather than the primary control contribution.

**Fig. 3.5 to add: Hierarchical control block diagram.**  
Recommended blocks: target command processing, state estimation, LQR, yaw PID, roll PID, leg length PID, leg angle PID, VMC, motor torque output.

**Fig. 3.6 to add: Control state and safety behaviour diagram.**  
Recommended states: balance disabled, stand-up preparation, balance enabled, airborne / cushioning, jump, cross-step, protection / stop.

### 3.6 ROS 2 Vision, WiFi TCP & Input Arbitration

The robot supports multiple command sources: Xbox BLE, UART2 command lines, WiFi TCP command lines, and ROS 2 / MediaPipe vision commands. All non-BLE command sources are routed through the same text-based command parser. This design reduces duplicated command logic and makes it possible to apply the same queue handling and safety rules to UART, PC keyboard control and vision-generated commands.

The UART2 command system implements a queue for scripted actions. Commands such as `FORWARD`, `BACKWARD`, `LEFT`, `RIGHT`, `JUMP`, `STANDUP`, `CROSSLEG`, `INCREASELEGLENGTH` and `DECREASELEGLENGTH` are parsed into command objects and executed by `CommandExecutorTask`. Queue execution can be started, paused, resumed, stopped, and queried. When the command queue is running or paused, direct yaw/drive commands are rejected and BLE input is suppressed, preventing scripted actions and manual control from fighting over the same target variables.

For low-latency teleoperation, the firmware also provides direct commands:

```text
DRIVE,<speed_mm_s>,<yaw_mrad_s>
YAWRATE,<mrad_s>
```

These commands bypass the queue and directly update `target.speedCmd` and `target.yawSpeedCmd`, subject to speed and yaw-rate limits. They are used by the PC keyboard teleoperation tool and by the vision bridge because those sources need to refresh a continuous target rather than enqueue fixed-duration actions.

The direct command path is protected by watchdogs. If no non-zero `DRIVE` command is refreshed for 500 ms, the firmware clears the direct speed and yaw targets. The same 500 ms timeout is applied to direct `YAWRATE` commands. The WiFi TCP layer adds a second level of protection: if the TCP client disconnects, the WiFi link is lost, or no line is received for `WIFI_WATCHDOG_MS` (1500 ms in the current configuration), the firmware injects:

```text
DRIVE,0,0
YAWRATE,0
QUEUE_STOP
```

This full-stop sequence is necessary because `DRIVE` bypasses the queue; a queue stop alone would not necessarily clear a stale direct target. The WiFi command task also uses a non-blocking connection strategy with a connection timeout and retry interval, so a missing WiFi network does not permanently block the rest of the firmware from running.

The host-side vision path is implemented as a ROS 2 Python package named `wheeleg_vision_bridge`. The node subscribes to the Yahboom camera image topic, which is expected as `/espRos/esp32camera` using `sensor_msgs/msg/CompressedImage`. The camera image reaches the host through a camera-side micro-ROS agent. The robot controller itself does not publish or subscribe to ROS 2 topics in the current implementation.

The vision bridge supports several operating modes:

| Mode | Input processing | Command output |
|---|---|---|
| `idle` | No image processing | No motion command |
| `gesture` | MediaPipe hand gesture recognition | Continuous `DRIVE` commands and optional `JUMP` |
| `face` | Face horizontal offset | `YAWRATE` command for yaw following |
| `stunt` | Human pose events | Queue actions such as leg length changes, `JUMP`, or `CROSSLEG` |

The bridge includes two safety parameters. First, `dry_run` defaults to `true`, meaning detected commands are printed but not transmitted. This allows camera, ROS 2 and MediaPipe behaviour to be tested without moving the robot. Second, `stunt_armed` defaults to `false`, blocking high-risk stunt commands such as `JUMP` and `CROSSLEG,0,5` unless explicitly armed at runtime.

The gesture mode uses continuous command refresh to match the robot-side direct-command watchdog. For example, an open palm (`Five`) is encoded as `DRIVE,250,0`, pointing left is encoded as `DRIVE,0,600`, and losing the hand returns the command to `DRIVE,0,0`. This behaviour makes vision teleoperation fail-safe with respect to hand detection: if the hand disappears from the image stream, the bridge stops commanding motion rather than holding the previous non-zero target.

**Table 3.3. Command source arbitration summary.**

| Source | Path into firmware | Priority / safety behaviour |
|---|---|---|
| Xbox BLE | Directly updates target variables when enabled | Suppressed when queue is busy or when disabled by PC control |
| UART2 | Text command parser | Can enqueue scripted actions or send direct commands |
| WiFi TCP keyboard tool | TCP line protocol → command parser | Sends `BLE_DISABLE` on start and restores BLE on exit |
| Vision bridge | ROS 2 / MediaPipe → TCP line protocol | Defaults to `dry_run`; continuous commands are protected by robot watchdogs |
| Command queue | `CommandExecutorTask` | Suppresses BLE and direct drive/yaw while running or paused |

This command architecture makes O3 testable. The report can evaluate not only whether the robot accepts multiple input sources, but also whether conflicting inputs are rejected or suppressed in a predictable way.

### 3.7 Summary

This chapter has described the implemented design rather than an idealised architecture. The ESP32 performs the balance-critical computation locally using IMU feedback, motor feedback, leg kinematics, LQR, PID loops and VMC torque mapping. Host-side ROS 2 and MediaPipe processing are deliberately outside the balance loop and are used only to generate supervisory commands. WiFi TCP, UART2 and BLE commands are integrated through a shared command and arbitration model with watchdog-based safety behaviour. The following results chapter evaluates whether these design decisions produce stable balance behaviour, acceptable real-time execution, safe command loss handling and usable vision teleoperation.

---

## 4. Results and Discussion  *(≈8–10 pages，65% 权重主战场)*

*⚠️ 每张图 → 现象 / 原因 / 意义 三层解释；至少对照 §2 文献基线做一次量化比较。*

### 4.1 Introduction — Test Plan
*Experiment matrix (E1–E8) 与 pass criteria。引用 `D2_Experiment_Plan.md`。*

This chapter evaluates whether the implemented system satisfies the three objectives defined in Section 1.2. The evaluation is organised around three questions. First, can the ESP32 firmware run the balance controller with sufficiently stable timing and sensor feedback? Second, does the LQR/PID/VMC controller provide usable wheel-legged balance and motion behaviour? Third, do the WiFi TCP and ROS 2 vision command paths provide safe supervisory control without entering the real-time balance loop?

The experiments were designed before the final measurement campaign so that each result maps directly to an objective. Table 4.1 summarises the experiment matrix, the evidence expected from each test, and the pass criterion used to interpret the result.

**Table 4.1. Evaluation matrix.**

| ID | Experiment | Objective | Main evidence | Pass criterion |
|---|---|---|---|---|
| E1 | Static balance drift | O1 | Pitch/roll time series, RMS and peak drift | Pitch RMS below 0.5 deg and no protection trigger |
| E2 | Impulse disturbance recovery | O1 | Pitch recovery curves, settling time, overshoot | Recovery within 1.5 s and no failed trial |
| E3 | Leg-length variation | O1 | Recovery time at minimum, middle and maximum leg length | Stable recovery across all tested leg lengths |
| E4 | Teleoperation step response | O1/O3 | Command step, pitch deviation and wheel response | Controlled response without excessive pitch excursion |
| E5 | WiFi TCP command-entry latency | O2 | Host-send to ESP32 command-entry acknowledgement latency CDF | Median below 50 ms and p95 below 150 ms |
| E6 | WiFi TCP watchdog and disconnect robustness | O2/O3 | Fault-injection timeline and stop latency | Direct commands clear near 500 ms; TCP idle full-stop near 1500 ms |
| E7 | Camera micro-ROS and vision teleoperation | O2/O3 | Camera topic rate and vision command event log | Stable image topic and correct event-to-command mapping |
| E8 | Control-loop jitter | O1 | `CtrlBasic_Task` period distribution | Mean/p50 near 4 ms, p95 below 4.5 ms, and tail outliers quantified |

<!-- DATA NEEDED: values marked * [PROVISIONAL] are synthetic planning placeholders, not measured data. Replace them from Report/appendices/E_data/ before final submission. -->

The analysis uses time-series plots for balance behaviour, cumulative distribution functions (CDFs) for communication latency, and pass/fail tables for safety arbitration. Where repeated trials are available, the report should present mean values with a 95% confidence interval. Where latency distributions are long-tailed, median, interquartile range, p95 and p99 are more informative than the arithmetic mean.

The most important limitation of the evaluation method is that the WiFi TCP latency measurement is not a pure one-way network latency measurement. The planned method records the host send timestamp and matches it to an ESP32 serial acknowledgement. This includes TCP delivery, firmware parsing, serial printing and USB serial logging. It should therefore be interpreted as a conservative host-to-command-entry acknowledgement latency, which is the practically relevant metric for teleoperation.

### 4.2 System Bring-up & Baseline
*E1 静态漂移；E8 FreeRTOS 调度抖动；bring-up checklist。*

The first stage of testing verified that the full embedded and host-side system could be started consistently. The firmware was built using PlatformIO for the ESP32 target, the IMU calibration routine was executed, the CAN motor feedback loop was checked, and the WiFi TCP command server was tested from the host PC. On the ROS 2 side, the Yahboom camera image stream was checked on `/espRos/esp32camera`, and the `wheeleg_vision_bridge` node was run in `dry_run` mode before any live command transmission was enabled.

**Table 4.2. Bring-up checklist.**

| Check | Evidence to report | Result |
|---|---|---|
| ESP32 firmware build | PlatformIO build log and git commit hash | [pass/fail, commit hash] |
| IMU calibration | Stored offset values and stable yaw/pitch/roll output | [pass/fail] |
| CAN motor feedback | Six motor feedback streams visible in firmware logs | [pass/fail] |
| Balance mode safety | Balance disabled produces zero torque output | [pass/fail] |
| WiFi TCP server | Host can connect to robot command port and send line commands | [pass/fail] |
| Camera ROS 2 topic | `/espRos/esp32camera` visible on host | [pass/fail, mean FPS] |
| Vision bridge dry-run | Gesture events produce printed commands without transmission | [pass/fail] |

E1 measured the static stability of the robot under no intentional external disturbance. The robot was placed on a level surface, allowed to settle after startup, and then logged for [60] s over [N] trials. Fig. 4.1 should show pitch and roll as a function of time, with the steady-state mean removed if necessary to separate bias from short-term oscillation.

**Fig. 4.1 to add: Static pitch and roll drift during E1.**

The expected analysis is summarised in Table 4.3. Pitch RMS indicates short-term balance quality, peak-to-peak pitch indicates the worst observed body motion, and drift rate indicates whether the IMU or controller develops a slow bias over the measurement window.

**Table 4.3. Static balance metrics.**

| Metric | Value | Interpretation |
|---|---:|---|
| Pitch RMS | [x.xx deg] | Should be below 0.5 deg for the planned pass criterion |
| Roll RMS | [x.xx deg] | Indicates lateral body stability |
| Pitch peak-to-peak | [x.xx deg] | Captures worst short-term body motion |
| Roll peak-to-peak | [x.xx deg] | Captures lateral oscillation |
| Pitch drift rate | [x.xxx deg/s] | Should remain close to zero after IMU calibration |
| Failed/protected trials | [0/N] | Any protection event must be discussed |

E8 measured whether the FreeRTOS task structure was fast enough for the 4 ms balance-control target. The recommended measurement is to record `micros()` at the start of `CtrlBasic_Task`, compute the period between consecutive samples, and plot the distribution. Fig. 4.2 should show the task-period histogram, while Table 4.4 should report the mean, standard deviation, p99.9 and maximum period.

**Fig. 4.2 to add: `Report/figures/e8_loop_jitter_15000_2026-04-24.png`.**

**Table 4.4. Control-loop timing jitter.**

| Metric | Value |
|---|---:|
| Mean period | 3.9998 ms |
| Standard deviation | 1000.2 us |
| p50 period | 4.000 ms |
| p95 period | 4.300 ms |
| p99 period | 5.600 ms |
| p99.9 period | 10.600 ms |
| Maximum observed period | 53.365 ms |
| Samples | 15000 |

The E8 result shows that the mean and median loop period are very close to the 4 ms design target, which supports the decision to keep the stabilising control loop on the ESP32. However, the p99, p99.9 and maximum values show occasional scheduling outliers. This should be discussed as a real-time limitation of the current FreeRTOS task structure and logging configuration rather than hidden. The result is still useful because the outliers occur in the embedded loop measurement, while WiFi and vision are kept outside the balance feedback path.

These baseline tests are important because they validate the assumptions used in the Methods chapter. If the measured control period remains close to 4 ms and the static attitude remains bounded, the later disturbance and communication experiments can be interpreted as system-level performance tests rather than basic bring-up failures. If either E1 or E8 fails, the discussion should prioritise timing interference, IMU noise, motor feedback freshness and task priority allocation before interpreting higher-level teleoperation results.

### 4.3 Balance and Motion Control Performance
*E2 脉冲扰动恢复（pitch 曲线 ± 3σ）；E3 变腿长；E4 遥控响应。*
*对照 `feng2023wheellegged` / `klemm2019ascento` 的恢复时间与超调指标。*

E2 is the main evidence for O1 because it tests whether the controller can reject an external disturbance and return the robot to a stable posture. The planned test applies a repeatable impulse disturbance while recording pitch, pitch rate, wheel speed, virtual leg length, command target and protection state. The primary metric is settling time, defined as the time from the disturbance marker to the first point where the pitch remains within +/-2 deg for at least 500 ms.

**Fig. 4.3 to add: Impulse disturbance pitch recovery curves.**  
Recommended plot: all trials aligned at the impact marker, mean curve, and +/-3 sigma envelope.

**Table 4.5. Impulse recovery metrics.**

| Metric | Forward disturbance | Backward disturbance |
|---|---:|---:|
| Trials | 10* [PROVISIONAL] | 10* [PROVISIONAL] |
| Successful recoveries | 9/10* [PROVISIONAL] | 10/10* [PROVISIONAL] |
| Peak pitch deviation | 8.4 +/- 1.1 deg* [PROVISIONAL] | 7.6 +/- 0.9 deg* [PROVISIONAL] |
| Settling time | 0.86 +/- 0.12 s* [PROVISIONAL] | 0.79 +/- 0.10 s* [PROVISIONAL] |
| Maximum wheel speed | 18.5 rad/s* [PROVISIONAL] | 16.9 rad/s* [PROVISIONAL] |
| Protection triggers | 0* [PROVISIONAL] | 0* [PROVISIONAL] |

The result should be interpreted against both the system objective and the literature. Two-wheeled inverted-pendulum robots are often evaluated by pitch regulation and recovery from external disturbance \cite{grasser2002joe,chan2013review}. Wheel-legged systems add a changing centre of mass and leg configuration, so the same disturbance can produce different behaviour depending on leg length and support force. Ascento demonstrates the advantage of wheel-legged morphology for dynamic recovery and jumping, while Feng et al. report a wheel-legged controller that combines LQR with disturbance rejection \cite{klemm2019ascento,feng2023wheellegged}. The comparison in this report should therefore focus on recovery time, peak overshoot and failure rate rather than claiming direct equivalence between platforms with different size, actuator power and mechanical design.

If the measured settling time is below [1.5] s and no protection state is triggered, the result supports the claim that the LQR/PID/VMC hierarchy provides usable balance recovery on the ESP32 platform. If recovery is slower than the literature examples, the discussion should link that limitation to the smaller hardware platform, manually tuned gains, IMU vibration, motor saturation, mechanical compliance, or limited repeatability of the disturbance input.

E3 extends E2 by repeating the disturbance test at multiple virtual leg lengths. This experiment is important because leg length changes the body height and therefore changes the effective inverted-pendulum dynamics. Fig. 4.4 should plot recovery time and peak pitch deviation against leg length.

**Fig. 4.4 to add: Recovery time and pitch overshoot versus virtual leg length.**

**Table 4.6. Leg-length sensitivity.**

| Leg setting | Mean leg length | Settling time | Peak pitch deviation | Failure/protection count |
|---|---:|---:|---:|---:|
| Minimum | 0.055 m* [PROVISIONAL] | 0.68 s* [PROVISIONAL] | 6.3 deg* [PROVISIONAL] | 0/5* [PROVISIONAL] |
| Middle | 0.070 m* [PROVISIONAL] | 0.82 s* [PROVISIONAL] | 7.8 deg* [PROVISIONAL] | 0/5* [PROVISIONAL] |
| Maximum | 0.085 m* [PROVISIONAL] | 1.10 s* [PROVISIONAL] | 10.5 deg* [PROVISIONAL] | 1/5* [PROVISIONAL] |

The expected trend is that a taller leg configuration increases recovery difficulty because the centre of mass is higher and the same pitch deviation corresponds to a larger gravitational moment. A result showing increased settling time or overshoot at larger leg length would therefore not be a failure by itself; it would show that the gain-scheduled LQR and leg-length PID are operating in a more demanding region of the robot dynamics. A failure at maximum leg length should be reported honestly and used to define a safe operating range.

E4 evaluates the coupling between teleoperation commands and balance. Unlike E2 and E3, this test does not apply an external impulse. Instead, it applies a step command in forward speed or yaw rate and observes how the balance controller responds while the target update task ramps the command. Fig. 4.5 should show the commanded velocity or yaw rate, the measured wheel response, and the pitch deviation on the same time axis.

**Fig. 4.5 to add: Teleoperation step response showing command, wheel response and pitch deviation.**

**Table 4.7. Teleoperation response metrics.**

| Command type | Command amplitude | Rise time | Steady-state error | Peak pitch deviation |
|---|---:|---:|---:|---:|
| Forward speed | [x.xx m/s] | [x.xx s] | [x.xx m/s] | [x.xx deg] |
| Reverse speed | [x.xx m/s] | [x.xx s] | [x.xx m/s] | [x.xx deg] |
| Yaw rate | [x.xx rad/s] | [x.xx s] | [x.xx rad/s] | [x.xx deg] |

The main point of E4 is not to show perfect velocity tracking. The robot is a balancing system, so aggressive speed commands necessarily create pitch transients. The engineering question is whether the target update logic limits these transients enough for safe teleoperation. A successful result is therefore one where speed and yaw commands are accepted smoothly, the robot remains balanced, and the maximum pitch deviation remains inside the chosen safe envelope.

### 4.4 WiFi TCP, Camera micro-ROS & Vision Teleop Performance
*E5 WiFi TCP 命令入口延迟 CDF；E6 watchdog/断线停止验证；E7 摄像头 `/espRos/esp32camera` 帧率与视觉桥 dry-run/live TCP 事件日志。*
*讨论 TCP/watchdog 的安全价值、camera micro-ROS 图像链路的实际帧率，以及为何视觉只作为遥操作/事件触发，不进入底层闭环控制。*

E5 evaluates the direct WiFi TCP command path used by both keyboard teleoperation and the ROS 2 vision bridge. The host sends safe command lines to the robot and records the host-side send timestamp. The ESP32 prints an acknowledgement when the command line reaches the parser or when the resulting direct target is updated. Matching these events gives the host-to-command-entry acknowledgement latency.

**Fig. 4.6 to add: WiFi TCP command-entry acknowledgement latency CDF.**

**Table 4.8. WiFi TCP command-entry latency.**

| Metric | Value |
|---|---:|
| Samples | 300 |
| Minimum | 14.07 ms |
| Mean | 50.05 ms |
| Median | 37.41 ms |
| p95 | 88.31 ms |
| p99 | 143.47 ms |
| Maximum | 368.89 ms |
| Lost / unmatched commands | 0 |

The p95 and p99 values are more important than the mean because teleoperation quality is usually affected by tail latency rather than average latency. If p95 remains below [150] ms, the WiFi TCP path is adequate for supervisory teleoperation commands such as `DRIVE` and `YAWRATE`. However, even a good E5 result should not be used to justify closing the balance loop over WiFi. The balance loop runs at a 4 ms target period, while the WiFi, TCP stack, host scheduling and serial acknowledgement path have non-deterministic delay. This supports the architectural decision in Section 3.2: WiFi commands should update targets, not replace local attitude feedback.

E6 tests the failure behaviour of the command path. Three fault types should be evaluated: the host stops sending commands while keeping the socket open, the TCP socket is closed, and the WiFi link is interrupted or becomes unavailable. The expected robot-side response is that direct `DRIVE` and `YAWRATE` commands are cleared by their 500 ms watchdogs, while the TCP layer applies a full stop on idle timeout, client drop or WiFi loss.

**Fig. 4.7 to add: Watchdog and disconnect fault-injection timeline.**

**Table 4.9. Watchdog and disconnect response.**

| Fault type | Trials | Direct-command stop latency | TCP full-stop latency | Correct stop sequence |
|---|---:|---:|---:|---|
| Stop sending `DRIVE` refresh | 10 | median 517.93 ms from ACK; p95 538.81 ms | N/A | 10/10 |
| TCP socket close | 10 | N/A | median 33.35 ms; p95 85.47 ms | 10/10 |
| TCP idle | 10 | N/A | median 1481.08 ms; p95 1510.11 ms | 10/10 |

This experiment is a safety result rather than a performance result. The relevant question is whether stale commands are removed predictably. The direct-command watchdog protects the robot from a lost refresh stream, while the TCP full-stop sequence protects against a disconnected or idle client. The combination is necessary because `DRIVE` bypasses the command queue; stopping the queue alone would not necessarily clear a non-zero direct speed target.

E7 evaluates the camera and vision path. The camera-side micro-ROS path should first be measured independently using `ros2 topic hz /espRos/esp32camera`. The vision bridge should then be tested in `dry_run` mode to verify recognition and command encoding without moving the robot. Only after this should live TCP command transmission be enabled, and high-risk actions should remain blocked unless `stunt_armed` is explicitly enabled.

**Fig. 4.8 to add: Vision event timeline from camera frame to command output.**  
**Fig. 4.9 to add: `Report/figures/e11_vision_bridge_ack_latency_2026-04-24.png`.**

**Table 4.10. Camera and vision bridge metrics.**

| Metric | Value |
|---|---:|
| Camera topic measured rate | 5.6-6.0 Hz in earlier retests; 4.07 Hz in latest reconnect retest |
| Camera topic rate during E11 | 4.85 Hz |
| Camera topic minimum observed rate | 4.07 Hz in the latest reconnect retest |
| Vision events tested | 14 pilot/retest events |
| Correct gesture-to-command events | 3/8 command-gesture trials plus safety passes |
| Hand-lost to stop-command behaviour | `QUEUE_STOP` + `DRIVE,0,0` observed |
| Dry-run false live command trials | 71 ACK-logged safe bridge commands |
| Vision bridge-to-ESP32 ACK median | 66.13 ms |
| Vision bridge-to-ESP32 ACK p95 | 301.93 ms |
| Vision bridge-to-ESP32 ACK p99 | 361.15 ms |
| Vision bridge-to-ESP32 ACK max | 392.95 ms |
| Blocked stunt commands with `stunt_armed=false` | stable `Thumb_up` retest blocked `JUMP` once |

The expected result is not that vision is fast enough for stabilising feedback. Instead, the expected result is that the camera and MediaPipe pipeline can generate useful supervisory events, such as open-palm forward commands or hand-lost stop commands, while the ESP32 continues to handle the balance loop locally. A low or variable camera frame rate should therefore be discussed as a limitation of vision teleoperation, not as a failure of the balance controller.

The E11 ACK result should be interpreted as bridge-command-to-ESP32 acknowledgement latency, not full perception latency. During the E11 run, the camera topic was approximately 4.85 Hz, corresponding to a frame period of about 206 ms. Combining one frame period with the measured median bridge-to-ACK latency gives a minimum camera-frame-to-ACK estimate of about 272 ms. Stable gesture recognition can require additional debounced frames, so the full human-gesture-to-command latency is slower than the TCP ACK metric. This supports the architectural decision that vision remains supervisory and does not enter the 4 ms balance loop.

The input arbitration behaviour should be reported as a short pass/fail table because it is a major engineering contribution of the system. Table 4.11 should be filled from direct tests of conflicting input sources.

**Table 4.11. Command arbitration tests.**

| Scenario | Expected behaviour | Result |
|---|---|---|
| PC tool starts while BLE controller is active | `BLE_DISABLE` prevents BLE from overwriting PC targets | [pass/fail] |
| Command queue is running and `DRIVE` is received | Direct drive command is rejected or suppressed | [pass/fail] |
| TCP client closes during non-zero command | Robot logs `client_drop` and injects `DRIVE,0,0`, `YAWRATE,0`, `QUEUE_STOP` | pass: 10/10 close trials |
| TCP client becomes idle | Robot emits `FULL_STOP,idle_timeout` and injects `DRIVE,0,0`, `YAWRATE,0`, `QUEUE_STOP` | pass: 10/10 idle trials |
| Vision bridge runs with `dry_run=true` | Commands are printed but not transmitted | pass |
| `stunt_armed=false` and a stunt event is detected | High-risk command is blocked | pass: stable `Thumb_up` blocked `JUMP` |

These results close the loop for O2 and O3. O2 is supported if the camera topic, vision bridge and WiFi TCP command path operate with acceptable latency and predictable failure handling. O3 is supported if conflicting command sources are suppressed in a deterministic way and if safety gates prevent unverified vision events from directly triggering risky robot actions.

### 4.5 Summary
*Objective vs Evidence vs Limitation 表。*

Table 4.12 summarises the evidence from the results chapter against the three objectives.

**Table 4.12. Objective, evidence and limitation summary.**

| Objective | Evidence | Current limitation |
|---|---|---|
| O1: LQR/PID/VMC embedded balance control | E1 static stability, E2 impulse recovery, E3 leg-length variation, E8 loop jitter | Manual gain tuning, IMU vibration, mechanical compliance and actuator saturation may limit recovery performance |
| O2: ROS 2 vision input and WiFi TCP command channel | E5 command-entry latency, E6 watchdog response, E7 camera/vision event logs | Vision and WiFi are suitable for supervisory teleoperation only, not for the stabilising control loop |
| O3: Safe multi-source command arbitration | E4 teleoperation response, E6 disconnect tests, E7 dry-run/stunt gates, arbitration pass/fail tests | Not every possible simultaneous-input race condition can be exhaustively tested within the project time |

Overall, the results should be interpreted as a system-level validation of the architecture rather than a claim of optimal robot performance. The core achievement is that the ESP32 controller can run the real-time balance loop locally while WiFi TCP and ROS 2 vision provide supervised command inputs with watchdog-based safety behaviour. The remaining weaknesses are mainly in measurement quality, controller tuning, state-estimation robustness and the limited autonomy of the vision layer.

---

## 5. Conclusions and Future Work  *(≈2–3 pages)*

### 5.1 Conclusions
*逐项回答 §1.2 的 O1/O2/O3 是否达成；强调工程化贡献。*

This project designed and implemented B-BOT, a WiFi-enabled self-balancing wheel-legged robot with an ESP32-based real-time control layer and a host-side ROS 2 / MediaPipe vision teleoperation layer. The main contribution is the integration of embedded wheel-legged balance control with safety-aware wireless command handling, rather than the use of vision as a replacement for local stabilising feedback.

For O1, the project implemented an embedded control architecture combining LQR, PID and VMC. The ESP32 firmware estimates attitude from the MPU6050 DMP, computes virtual leg state from motor feedback, schedules the LQR gain by leg length, and maps virtual support forces to joint torques through VMC. The evidence for this objective is provided by the static balance, disturbance recovery, leg-length variation and control-loop jitter tests in Chapter 4. The final measured conclusion should state: [O1 achieved / partially achieved], supported by [key E1/E2/E8 metrics].

For O2, the project implemented a ROS 2 vision input pipeline and a WiFi TCP robot command channel while keeping the ESP32 outside the ROS 2 control graph. The Yahboom camera image stream is processed on the host, MediaPipe events are encoded as text commands, and the commands are transmitted to the robot over TCP. The evidence for this objective is provided by the command-entry latency, watchdog/disconnect and camera/vision event tests. The final measured conclusion should state: [O2 achieved / partially achieved], supported by [key E5/E6/E7 metrics].

For O3, the project implemented multi-source input handling across Xbox BLE, UART commands, WiFi TCP commands and vision-generated commands. The command queue, direct-command watchdogs, BLE suppression, TCP full-stop behaviour, `dry_run` default and `stunt_armed` gate reduce the chance that two sources command the robot unsafely at the same time. The final measured conclusion should state: [O3 achieved / partially achieved], supported by [queue/arbitration pass-fail evidence].

The most important engineering lesson is that unstable mobile robots require a strict boundary between real-time stabilisation and non-deterministic supervisory software. In B-BOT, WiFi and vision improve usability and demonstration value, but they are not suitable for the balance loop. The implemented architecture reflects this constraint by keeping the feedback controller local and treating remote inputs as temporary, watchdog-protected target requests.

### 5.2 Future work
*基于当前局限的 3 条：(1) 控制参数在线整定工具链；(2) 更鲁棒的状态估计融合；(3) 步态规划与非平整地面适应。*

The first area for future work is a stronger control tuning and logging toolchain. The current controller depends on manually tuned gains and manually designed experiments. A more systematic workflow would include a unified CSV telemetry logger, event markers, parameter versioning, automatic plot generation and repeatable gain-sweep scripts. This would make it easier to compare controller changes and would reduce the risk of relying on subjective demonstration performance.

The second area is state-estimation robustness. The current implementation uses the MPU6050 DMP and joint-based leg kinematics, which is suitable for the present embedded platform. Future work should investigate better vibration isolation, wheel-speed and leg-state fusion, and a more explicit attitude-estimation comparison against complementary or gradient-based filters. This would be especially useful during jumping, fast leg-length changes and high-vibration ground contact.

The third area is higher-level locomotion and autonomy. The current vision layer is mainly a teleoperation and event-triggering interface. Future work could add ROS 2 telemetry from the robot, authenticated command transport, structured command sequencing, terrain-aware gait planning and safer autonomous behaviours. These additions should preserve the same architectural principle used in this project: perception and planning may run on the host, but the balance-critical feedback loop should remain local to the embedded controller.

---

## 写作守则（写之前瞥一眼）

1. **先图后文**：每节开头先确认图表已定稿，再围绕图表写。
2. **每个 paragraph 一个 claim**：Topic sentence → evidence → implication。
3. **被动语态慎用**：IEEE 报告允许主动语态（"We designed…" / "The system uses…"）。
4. **数字带单位 + 不确定度**：`recovery time = 0.82 ± 0.07 s (n = 10)`。
5. **每张图/表/公式先在正文中被引用再出现**（`as shown in Fig. 4.3`）。
6. **引用立即写 bib key**，别拖到最后："LQR has been shown effective [`feng2023wheellegged`]." 后面再批量转 `\cite{}`。
7. **八天冲刺优先级**：Methods + Results > Lit Review > Intro > Abstract > Conclusion。
8. **每写完一节立即 copy 进 `main.tex`**，实时看编译产物的页数，避免超页发现太晚。
