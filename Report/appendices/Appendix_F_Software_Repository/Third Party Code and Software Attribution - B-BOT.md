# Third-Party Code and Software Attribution

This table identifies external code, libraries, frameworks and generated code used by B-BOT. The report cites the relevant documentation or papers in the references section where these tools support a technical claim.

| Item | Project use | Repository / location in B-BOT | Attribution status |
| --- | --- | --- | --- |
| Yahboom ESP32 wheel-legged robot base project and hardware platform | Starting point for the robot platform, motor/leg hardware context and vendor examples | Original vendor material; modified project now stored in this repository | Must be acknowledged as third-party/vendor basis where relevant |
| Yahboom / ROS 2 WiFi camera module | Provides compressed image topic used by the host ROS 2 vision bridge | External camera module; host-side evidence uses `/espRos/esp32camera` | Must be described as an external camera module, not original robot-control code |
| NimBLE-Arduino | ESP32 BLE support used for Xbox controller input | `lib/NimBLE-Arduino/` | Apache License 2.0; local copy includes `LICENSE` and `library.properties` |
| Xbox controller support headers | Xbox controller BLE parsing and HID report support | `include/XboxSeriesXControllerESP32_asukiaaa.hpp`, `include/XboxSeriesXHIDReportBuilder_asukiaaa.hpp`, `include/XboxControllerNotificationParser.h` | Requires final acknowledgement of original source/adaptation status |
| ESP32 Arduino framework | Embedded firmware framework for the ESP32 target | PlatformIO dependency through `platformio.ini` | Cite ESP32 Arduino / PlatformIO in final references |
| FreeRTOS | Task scheduling and timing model used by ESP32 firmware | Provided through ESP32 Arduino environment | Cite where discussing real-time task structure |
| electroniccats MPU6050 library | IMU/DMP support for attitude sensing | PlatformIO `lib_deps` entry | Cite or acknowledge library in software appendix |
| Adafruit ADS1X15 library | ADS1115/ADC voltage sensing support | PlatformIO `lib_deps` entry | Cite or acknowledge library in software appendix |
| ROS 2 Humble | Host robot software framework, launch system and message transport | Host environment for `host/ros2_ws/src/wheeleg_vision_bridge/` | Cite ROS 2 documentation/paper in final references |
| micro-ROS Agent / Micro XRCE-DDS | Image transport between ROS 2 WiFi camera module and host ROS 2 graph | Started through `host/scripts/camera_quickstart.sh` | Cite micro-ROS and XRCE-DDS references where discussing architecture |
| OpenCV | Image conversion and processing support for the host vision bridge | Host Python dependency | Cite or acknowledge in software appendix |
| MediaPipe | Hand/pose/face perception for vision teleoperation | Host Python dependency used by `mediapipe_runner.py` | Cite MediaPipe references in final report |
| NumPy | Numeric support for host-side perception and data scripts | Host Python dependency | Acknowledge as standard scientific Python dependency |
| MATLAB-generated code | Generated leg kinematics, VMC conversion and LQR support code | `src/matlab_code/`, `include/matlab_code/` | Identify as generated support code and explain source model/derivation in Methods if needed |
| Matplotlib / Python data scripts | Plot generation for experiment evidence | `Report/appendices/E_data/*/*.py`, `Report/appendices/E_data/make_provisional_plots.py` | Used for analysis/figures; cite only if required by report policy |

## Attribution Checks

Submission checklist:

- Verify each external item has an accurate license/source statement.
- Replace generic placeholder license metadata in ROS package files if the package is submitted publicly.
- Ensure the final report references separate original work, generated code, vendor examples and third-party libraries.
- Avoid claiming the ROS 2 WiFi camera module firmware or vendor robot base as original project code.
