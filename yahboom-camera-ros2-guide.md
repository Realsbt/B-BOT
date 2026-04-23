# Yahboom ESP32 摄像头 + micro-ROS 快速参考

> 来源：Yahboom 官方教程。Vibe coding 速查用。

---

## 第一步：配置摄像头模块（XCOM 串口发送）

在 XCOM 串口工具中依次发送以下指令，将摄像头模块连接到 WiFi 并告知主机 IP：

```text
sta_ssid:你的WiFi名称       # 设置要连接的 WiFi 名
sta_pd:你的WiFi密码          # 设置 WiFi 密码
ros_ip:主机IP地址            # 告知 ROS 主机的 IP（如 192.168.1.100）
sta_ip                       # 查询模块是否获得 IP（确认连接成功）
```

---

## 第二步：启动 micro-ROS Agent（主机终端）

建立主机与摄像头模块的通信连接。

```bash
# 方式一：Yahboom 提供的脚本（推荐）
sh start_Camera_computer.sh

# 方式二：Docker
docker run -it --rm -v /dev:/dev -v /dev/shm:/dev/shm \
  --privileged --net=host \
  microros/micro-ros-agent:humble udp4 --port 9999 -v4
```

> 出现连接成功的日志后，**保持此终端运行，不要关闭**。

---

## 第三步：查看摄像头画面（新开终端）

两种方式选其一：

```bash
# 方式一：直接显示（推荐，更简单）
ros2 run yahboom_esp32_camera sub_img

# 方式二：用 RViz2 查看
rviz2
# 然后手动添加 Image 话题，Fixed Frame 设为 /esp32_img
```

---

## 第四步：使用 MediaPipe 功能（新开终端）

关闭第三步的节点后，运行以下任意一个 MediaPipe 节点：

```bash
ros2 run yahboom_esp32_mediapipe 01_HandDetector       # 手部检测
ros2 run yahboom_esp32_mediapipe 11_GestureRecognition # 手势识别
ros2 run yahboom_esp32_mediapipe 02_PoseDetector       # 姿态估计
ros2 run yahboom_esp32_mediapipe 07_FaceDetection      # 人脸检测
ros2 run yahboom_esp32_mediapipe 05_FaceEyeDetection   # 人脸+眼睛检测
```

> **注意**：第二步的 Agent 必须始终保持运行；MediaPipe 节点运行时不需要同时开 RViz2。

---

## 快速检查清单

| 步骤 | 状态 | 说明 |
|------|------|------|
| WiFi 配置 | `sta_ip` 返回 IP | 摄像头模块已连上网 |
| Agent 运行 | 终端显示连接日志 | 通信链路就绪 |
| 摄像头画面 | `/espRos/esp32camera` 有 `CompressedImage`，`sub_img` 弹出窗口 | 图像流正常 |
| MediaPipe | 窗口显示检测结果 | AI 推理正常 |
