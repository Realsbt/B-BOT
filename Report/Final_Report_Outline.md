# B-BOT 第三学年个人项目 Final Report 写作大纲

本文档根据项目中提取的学校官方指南（READ ME FIRST!.txt、Report Template.txt）、同学咨询总结与自查表（要求总结与自查表.md）以及当前仓库的实际项目内容（README.md、introduction.md 等）综合编制而成。

**约束说明与评分权重（根据 Y3 Project Handbook）：**
- **正文篇幅**：不含摘要、目录、图表目录、缩写表、参考文献及附录，总计**不得超过 35 页**（A4，按官方模板样式，Calibri 12号字体，1.5倍行距，左对齐）。超页数将面临 **5 分的扣分惩罚**。
- **评分权重 (Marking Rubric)**：
  - **25%**：Overview, Background and Conclusions（包括摘要、背景、目标、综述、结论以及项目管理）。
  - **65%**：Technical Achievement（核心技术实现，包括理论、设计、实现、测试与分析讨论）。
  - **10%**：Presentation and Content（语法、拼写、图表清晰度、排版格式及结构）。
- **语言**：必须以全英文撰写，此大纲使用中英双语以辅助理解和指导写作。

---

## 报告前置部分 (Front Matter)
*(不计入正文 35 页限制)*

- **Title Page (封面)**
  - 严格采用模板格式
  - Project Title: B-BOT: A micro-ROS and WiFi Enabled Self-Balancing Wheel-Legged Robot
  - 包含学生姓名、学号（仅7位数字）、指导教师 (Supervisor) 及提交日期。
- **Abstract (摘要)** 
  - 1页以内，高度概括：问题背景、动机、核心方法（LQR+PID+VMC分层控制，micro-ROS 通信架构）、关键验证结果及系统主要局限。
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
  - 引入 micro-ROS 与 WiFi 的动机：实现资源受限的 MCU（底盘实时控制）与高算力 ROS 2 主机（视觉识别、行为编排）的分离与协同。
- **1.2 Aims and objectives (目标与成功判据)**
  - **总目标**：开发并验证一套融合多任务实时调度与分布式通信的自平衡轮腿系统。
  - **具体目标**：
    1. 实现稳定可靠的 LQR/PID/VMC 融合底层平衡控制。
    2. 构建低延迟、高可靠的 micro-ROS/WiFi 数据通信桥。
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
- **2.4 Embedded ROS and Communication in Lossy Networks (嵌入式 ROS 与有损网络通信)**
  - MCU—agent—host 分层架构的意义。
  - WiFi 拓扑在机器人遥测中的应用及 QoS 策略（Best effort vs. Reliable）对传感器数据与控制命令的影响。
- **2.5 Summary**
  - 指出技术缺口与本项目的系统架构选择依据。

### 3. Methods (系统设计与实现) *[约 8-10 页]*
- **3.1 Introduction (Top-level Requirements)**
  - 质量、功耗、控制频率、通信延迟、算力分配等整体工程约束。
- **3.2 System Architecture (总体系统架构)**
  - “底层驱动 → 状态估计/控制 → 网络代理 → 顶层视觉与决策”的数据流图与时序分配。
- **3.3 Mechanical and Electrical Design (机械与电气集成)**
  - ESP32 + MPU6050 + 6路电机 (CAN总线) + ADC 电源监测的选型依据与物理集成。
- **3.4 Perception and State Estimation (感知与状态估计)**
  - IMU 高频滤波、腿长及姿态运动学结算（含 MATLAB 辅助代码生成集成）。
- **3.5 Control Architecture and Algorithms (控制架构与算法实现)**
  - LQR 整车平衡公式设计与状态空间定义。
  - 级联 PID (Leg Length, Roll, Yaw) 辅助控制逻辑。
  - VMC 映射细节及触地检测、跳跃等状态机逻辑。
- **3.6 micro-ROS & Communication Design (通信与输入仲裁机制)**
  - Xbox 蓝牙输入与 TCP/micro-ROS 串口/网络任务的仲裁（防抢夺机制）。
  - QoS 策略配置、Topic/Service 规划及其与 FreeRTOS 任务队列的协同运作。
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
- **4.4 micro-ROS, WiFi and Vision Teleop Performance (通信链路与视觉遥操作评估)**
  - **数据展示**：端到端通信延迟 CDF 曲线、有损 WiFi 环境下的指令丢包率。
  - **讨论**：QoS 配置在实际网络波动中的容错能力；MediaPipe 视觉桥（dry-run与实际测试）延迟对底层闭环控制的冲击与系统稳定性折衷。
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
- 采用 IEEE 格式列出所有引用的论文、文档（如 micro-ROS 官方文档）、第三方库及教科书。

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
- **Appendix F: Software Repository Link & README (代码仓库链接与 README)**
  - 包含公开的 GitHub/GitLab 链接。
  - README 应包含：标题、简介、系统架构图、安装说明、运行步骤、技术细节及未来改进。
- **Appendix G: Validation Logs, Data Samples & Extra Proofs (验证数据与其他支撑材料) [可选但强烈建议]**
  - 用于支撑主报告核心图表的原始日志、加长版推导或额外实验数据。

---

## 📌 Final Demonstration / Presentation 提示
*(占总成绩的 10%，非报告内容但属于项目核心考核点)*
- **时间窗**：5月5日 - 5月15日。
- **要求**：不超过 15 分钟的演讲 + 15 分钟 Q&A。
- **行动项**：由于涉及硬件实物展示，若需在实验室（而非普通教室）进行，**必须在提交报告后尽早向导师申请确认场地**。
