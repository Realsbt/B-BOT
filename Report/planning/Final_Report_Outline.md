# B-BOT 第三学年个人项目 Final Report 写作大纲

本文档根据项目中提取的学校官方指南（EEEN30330 Handbook 2025/26、READ ME FIRST!.txt、Report Template.txt、EvidencingSoftwareForFinalReport.txt）、同学咨询总结与自查表（要求总结与自查表.md）以及当前仓库的实际项目内容（README.md、introduction.md 等）综合编制而成。

**⏰ 提交硬约束（Handbook §9.1）：**
- **截止时间**：**2026-05-01（周五）14:00** — 今日为 2026-04-23，**剩余 8 天**。
- **提交平台**：**Canvas**（PDF 格式，无需纸质提交）。
- **迟交惩罚**：延迟数分钟即可扣最多 10 分；重交仍按迟交计。必须**至少预留 2 小时缓冲**给最终上传与回执保存。
- **DASS/Mitigating Circumstances**：须在截止前按正式流程申请，否则无弹性。

**排版硬约束（Handbook §9.2）：**
- **正文篇幅**：不含摘要、目录、图表目录、缩写表、参考文献及附录，总计**不得超过 35 页编号 A4**，超页扣 5 分。
- **页边距**：四边（上/下/左/右）**均至少 2 cm**。当前 `main.tex` 设为 2.5 cm，合规。
- **字体**：Calibri 12（或近似等效）。
- **行距**：正文 1.5 倍；引文、脚注、参考文献可单倍。
- **对齐**：左对齐（**禁止** fully justified/两端对齐）。
- **编号约定（来自 Report Template 示例）**：图用 `Fig. 2.1`、表用 `Table 1.1`、公式用 `(1.1)` 的**分节编号**；所有图/表/公式必须在正文中先被引用再出现。

**评分权重 (Marking Rubric, §10.2)：**
- **25%** Overview, Background and Conclusions — Abstract、Background & motivation、Aim & objectives、Literature review / existing solutions、Conclusions、**Project Management 及其 artefacts**。
- **65%** Technical Achievement — Theoretical development、Design、Implementation、Testing & Analysis、Results & Discussion。
- **10%** Presentation and Content — 语法拼写、图表清晰度、排版一致性、逻辑结构、sections/appendices/references 的合理使用。

**可复用的既有材料（Handbook §9.2 明确允许）：**
- 此前提交的 Draft Introduction、Draft Methodology、Draft Final Report **可直接沿用并精修**，不构成 self-plagiarism。8 天冲刺下这是最重要的提速路径。

**语言**：必须以全英文撰写，此大纲使用中英双语以辅助理解和指导写作。

---

## 报告前置部分 (Front Matter)
*(不计入正文 35 页限制)*

- **Title Page (封面)**
  - 严格采用模板格式
  - Project Title: B-BOT: A WiFi-Enabled Self-Balancing Wheel-Legged Robot with ROS 2 Vision Teleoperation
  - 包含学生姓名、学号（仅7位数字）、指导教师 (Supervisor) 及提交日期。
- **Abstract (摘要)** 
  - 1页以内，高度概括：问题背景、动机、核心方法（LQR+PID+VMC 分层控制、FreeRTOS 实时任务、WiFi TCP 命令入口、ROS 2 + MediaPipe 视觉桥）、关键验证结果及系统主要局限。
- **Declaration of originality (原创性声明)** 
  - 采用模板规定文字。
- **Intellectual property statement (知识产权声明)** 
  - 采用模板规定文字。
- **Acknowledgements (致谢)** 
  - (可选)
- **Contents (目录)** 
  - Word 自动生成。
- **List of Figures / Tables (图表目录)** 
  - 强烈建议添加。
- **Nomenclature / Abbreviations (缩写与符号表)**
  - 例如：IMU, LQR, PID, VMC, ROS 2, QoS, XRCE-DDS 等。

---

## 正文部分 (Main Body)
*(严格控制在 35 页内，参考各节建议页数合理分配)*

### 1. Introduction (引言) *[约 3-4 页]*
- **1.1 Background and motivation (背景与动机)**
  - 轮腿平衡机器人在复杂地形及机动性上的工程价值。
  - 引入 WiFi 与 ROS 2 主机侧视觉的动机：ESP32 保留高频底盘实时控制，PC 负责摄像头图像接入、MediaPipe 识别与行为命令生成。
  - 明确系统边界：当前底盘 ESP32 不是 micro-ROS 节点；micro-ROS 用于 Yahboom 摄像头向主机 ROS 2 发布图像，控制命令由 PC 通过 WiFi TCP 直接发送到机器人。
- **1.2 Aims and objectives (目标与成功判据)**
  - **总目标**：开发并验证一套融合多任务实时调度与分布式通信的自平衡轮腿系统。
  - **具体目标**：
    1. 实现稳定可靠的 LQR/PID/VMC 融合底层平衡控制。
    2. 构建并验证 ROS 2 视觉输入链路与 WiFi TCP 机器人命令通道，包括断线停止与命令 watchdog。
    3. 支持多源输入（Xbox BLE、上位机脚本与 MediaPipe 视觉命令）的安全仲裁。
- **1.3 Report structure (报告结构)**
  - 简述后文各章节安排。
- **1.4 Project Management (项目管理)** *(注：Handbook 明确要求必须有此独立小节，篇幅不超过 1 页)*
  - 反思项目的计划与执行过程（结合附录中的 Gantt 图、CPD 记录和风险登记册）。
  - 说明如何监控进度、应对计划偏差，以及个人在自我学习（CPD）和风险管理上的主动性。

### 2. Literature review (文献综述) *[约 5-6 页]*
- **2.1 Introduction**
- **2.2 Wheel-legged and Self-balancing Robotics (轮腿与自平衡技术脉络)**
  - 从两轮自平衡到轮腿复合结构的演进（解决高低调节、地形适应与重心变化）。
- **2.3 Control Strategies Comparison (控制方法对比)**
  - PID、LQR、ADRC、VMC 的对比分析。阐述本项目选择 LQR 负责大闭环平衡、PID 处理辅助约束、VMC 实现力到关节力矩映射的理论依据与算力代价。
- **2.4 Embedded ROS, WiFi Teleoperation and Lossy Networks (嵌入式 ROS、WiFi 遥操作与有损网络)**
  - camera micro-ROS agent → ROS 2 host → MediaPipe → WiFi TCP robot command 的分层意义。
  - WiFi 控制链路中的 TCP 延迟、断线检测、watchdog 和输入仲裁；ROS 2 QoS 仅用于讨论图像/状态 topic，不应被写成底盘控制总线。
- **2.5 Summary**
  - 指出技术缺口与本项目的系统架构选择依据。

### 3. Methods (系统设计与实现) *[约 8-10 页]*
- **3.1 Introduction (Top-level Requirements)**
  - 质量、功耗、控制频率、通信延迟、算力分配等整体工程约束。
- **3.2 System Architecture (总体系统架构)**
  - “底层驱动 → 状态估计/控制 → WiFi TCP 命令服务 → ROS 2/MediaPipe 视觉桥”的数据流图与时序分配。
- **3.3 Mechanical and Electrical Design (机械与电气集成)**
  - ESP32 + MPU6050 + 6路电机 (CAN总线) + ADC 电源监测的选型依据与物理集成。
- **3.4 Perception and State Estimation (感知与状态估计)**
  - IMU 高频滤波、腿长及姿态运动学结算（含 MATLAB 辅助代码生成集成）。
- **3.5 Control Architecture and Algorithms (控制架构与算法实现)**
  - LQR 整车平衡公式设计与状态空间定义。
  - 级联 PID (Leg Length, Roll, Yaw) 辅助控制逻辑。
  - VMC 映射细节及触地检测、跳跃等状态机逻辑。
- **3.6 ROS 2 Vision, WiFi TCP and Input Arbitration (视觉链路、WiFi TCP 与输入仲裁机制)**
  - Xbox BLE、UART2 命令队列、PC WiFi TCP、视觉桥命令复用同一目标量/队列系统的仲裁逻辑。
  - 说明 `DRIVE`/`YAWRATE` 直通命令、500 ms direct-command watchdog、1500 ms TCP idle watchdog、断线三连停（`DRIVE,0,0` + `YAWRATE,0` + `QUEUE_STOP`）。
  - 说明 ROS 2 侧节点、topic、参数与状态发布：摄像头图像 topic、`/wheeleg/vision_status`、`/wheeleg/vision_mode`、`dry_run` 与 `stunt_armed` 安全门控。
- **3.7 Summary**

### 4. Results and discussion (结果与讨论) *[约 8-10 页]*
*(🚨 高分预警：必须在此章将测试结果与第 2 章文献综述中的现有方案/数据进行对比闭环，这是拿到 70 分以上 First Class 的关键判分标准)*
- **4.1 Introduction**
  - 测试方案、实验矩阵与指标（如恢复时间、延迟、吞吐量）说明。
- **4.2 System Bring-up and Baseline Validation (系统启动与基础功能验证)**
  - 固件编译、网络连接、传感器校准结果及 FreeRTOS 任务调度稳健性展示。
- **4.3 Balance and Motion Control Performance (平衡与运动控制性能)**
  - **图表展示**：受扰动后的俯仰角 (Pitch) 恢复曲线、多电机同步响应。
  - **讨论**：LQR 与 VMC 组合下的系统抗扰能力及姿态保护逻辑的实际表现。探讨因结构或传感器噪声引入的超调问题。
- **4.4 WiFi TCP, Camera micro-ROS and Vision Teleop Performance (WiFi TCP、摄像头 micro-ROS 与视觉遥操作评估)**
  - **数据展示**：PC → WiFi TCP → ESP32 命令入口延迟/成功率，摄像头 `/espRos/esp32camera` 帧率，MediaPipe 视觉桥 dry-run 与 live TCP 发送记录。
  - **讨论**：TCP/watchdog 策略如何降低失控风险；摄像头帧率和 MediaPipe 识别延迟为何适合遥操作/事件触发，而不适合替代底层闭环控制。
- **4.5 Summary**

### 5. Conclusions and future work (结论与未来工作) *[约 2-3 页]*
- **5.1 Conclusions (结论)**
  - 逐项回应 1.2 节的 Objectives 是否达成。
  - 强调本项目在受限硬件条件下完成从控制、通信到全系统验证工程化落地的核心贡献。
- **5.2 Future work (未来工作)**
  - 基于当前局限（如调参困难、抗网络抖动不足），提出：
    1. 建立控制参数在线整定与扫描工具链。
    2. 增强状态估计（更鲁棒的滤波融合算法）。
    3. 步态规划与对非平整地面的适应。

---

## References (参考文献)
- 采用 IEEE 格式列出所有引用的论文、文档（如 ROS 2 / micro-ROS camera-agent 相关文档）、第三方库及教科书。

---

## Appendices (附录与证据包)
*(不计入正文 35 页内，Handbook 第 9.4 节明确规定了以下【强制包含】的项目管理与代码证据)*

- **Appendix A: Preliminary Project Proposal (初步项目提案)**
  - 项目初期提交的 2 页 Outline。
- **Appendix B: Project Plan and Gantt Chart (项目计划与甘特图)**
  - 项目最终版（更新后）的实际执行计划甘特图。
- **Appendix C: Risk Register (风险登记册)**
  - 项目生命周期内识别、审查和管理的风险记录。
- **Appendix D: Continuing Professional Development (CPD) Log (持续职业发展日志)**
  - 与项目技术需求相关的自我学习和技能发展记录。
- **Appendix E: Health & Safety Risk Assessment (健康与安全风险评估)**
  - 针对实验室、带电测试及机器人操作的安全评估。
- **Appendix F: Software Repository Link & README (代码仓库链接与 README)** *(Handbook §9.5 & §14)*
  - **仓库必须在提交时点 public**（提交前务必切换 private→public 并打 release tag，锁定评审版本）。
  - README **七项必备内容**（§14.4 原文硬要求）：
    1. **Title** — 项目/组件名。
    2. **Introduction** — 1–2 段描述软件作用及其在项目中的角色。
    3. **Contextual overview** — 架构图/数据流/控制结构图。
    4. **Installation instructions** — 依赖、库、环境搭建逐步说明。
    5. **How to run the software** — 运行命令或最小示例。
    6. **Technical details** — 算法、公式、设计假设。
    7. **Known issues and future improvements** — 局限、已知 bug、后续扩展。
  - **第三方代码声明（§9.5 & §14.5 硬要求）**：清单必须列出所有 imported/reused/third-party 代码及其 **license**——至少涵盖 Yahboom 原始项目、NimBLE-Arduino、ESP32 Arduino/FreeRTOS、MPU6050 驱动、Adafruit ADS1X15、ROS 2、micro-ROS Agent/Yahboom camera image pipeline、MediaPipe、OpenCV 等，明确哪些文件/目录来自外部，违反将影响学术诚信。
- **Appendix G: Validation Logs, Data Samples & Extra Proofs (验证数据与其他支撑材料) [可选但强烈建议]**
  - 用于支撑主报告核心图表的原始日志、加长版推导或额外实验数据。

---

## 📌 Final Demonstration / Presentation 提示
*(独立于报告的考核项，与 Final Report 分开计分)*
- **时间窗**：2026-05-05 至 2026-05-15（学期二 Week 11/12）。
- **要求**：≤15 分钟演讲 + ≤15 分钟 Q&A，共不超过 30 分钟。由 Supervisor + Independent Marker 现场评分。
- **强制出席**：无故缺席该环节直接记 0 分；DASS 延期**不适用**于现场考核，如需变更必须走 Mitigating Circumstances 流程。
- **场地**：若需在实验室展示硬件（而非普通教室），**必须提前与 Supervisor 协商安排**，勿等提交后再开始。

---

## 🚨 8 天冲刺倒排（真实日历）

| 日期 | 里程碑 | 关键产出 |
|---|---|---|
| **D1 2026-04-24 (周五)** | 附录证据冻结 | 更新版 Gantt、Risk Register、CPD Log、H&S Risk Assessment 全部落稿成 PDF |
| **D2 2026-04-25 (周六)** | 实验数据冻结 | Pitch 恢复曲线、电机响应、WiFi TCP 命令入口延迟、摄像头 ROS 2 帧率/视觉桥发送记录采齐；图表先出草图 |
| **D3 2026-04-26 (周日)** | Methods 初稿 | §3 全章落稿（架构图 + 公式 + 任务频率/命令协议表）|
| **D4 2026-04-27 (周一)** | Results & Discussion 初稿 | §4 全章落稿，每张图都对照文献基线做对比讨论 |
| **D5 2026-04-28 (周二)** | Intro + Lit Review + Conclusion | §1、§2、§5 落稿；Objectives 与 Conclusions 一一闭环 |
| **D6 2026-04-29 (周三)** | Abstract + 排版 + 引用 | Abstract 定稿；图表/公式编号、IEEE 引用一致性核查；附录 F 的 README 冻结版 + 第三方代码清单 |
| **D7 2026-04-30 (周四)** | 试提交 + 交叉检查 | 导出 PDF 检查字体/分页；Canvas 试提交；仓库切 public 并打 tag |
| **D8 2026-05-01 (周五) ≤14:00** | **正式提交 + 回执保存** | 上传最终 PDF，保存 Canvas confirmation；冗余时间用于处理突发问题 |

**硬性优先级规则**：
1. 没测到的数据 = 没有 Results 章节 = 直接丢 65% 权重的大分——**D2 前必须定完实验矩阵**。
2. 前期已提交的 Draft Intro/Methodology/Final Report **直接改写**，不要重写。
3. Intro 总写作时间 ≤1 天；Methods + Results 合计 ≥3 天。
4. **绝不**把提交压到 14:00 前最后半小时——Canvas 拥堵时延迟几分钟就扣 10 分。
