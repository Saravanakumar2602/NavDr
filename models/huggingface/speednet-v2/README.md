# SpeedNet v2: Multi-Task Neural Network for Inertial Dead Reckoning

## 1. Model Name
**SpeedNet v2** (`speednet-v2`)

## 2. Purpose
SpeedNet v2 is a lightweight multi-task neural network designed for vehicle forward-speed and yaw-rate estimation from noisy 6-DOF IMU sensor data. It operates during GNSS outage windows in Intelligent Dead Reckoning (IDR) navigation systems, providing real-time speed, yaw-rate, stationary state logits, and short-term velocity change estimates to bound inertial drift without cloud connectivity.

## 3. Architecture
- **Input Representation:** 4-second temporal window ($W = 40$ samples at 10 Hz sampling rate, 6 IMU channels: `accel_x`, `accel_y`, `accel_z`, `gyro_x`, `gyro_y`, `gyro_z`).
- **Feature Extractor:**
  - 1D Convolutional Layer: 32 channels, kernel size 3, padding 1, BatchNorm1d, ReLU.
  - 1D Convolutional Layer: 64 channels, kernel size 3, padding 1, BatchNorm1d, ReLU.
  - Bidirectional LSTM (BiLSTM): 1 layer, input size 64, hidden size 64 (bidirectional output dimensionality = 128).
- **Shared Dense Bottleneck:** Linear(128, 64) + ReLU.
- **Multi-Task Heads:**
  - Forward Speed Regression ($v_{\text{fwd}}$): Linear(64, 32) + ReLU + Linear(32, 1) + ReLU (enforces non-negativity).
  - Yaw Rate Regression ($\omega_{\text{yaw}}$): Linear(64, 32) + ReLU + Linear(32, 1).
  - Stationary Logit ($\text{logit}_{\text{stat}}$): Linear(64, 32) + ReLU + Linear(32, 1).
  - Auxiliary Velocity Change ($\Delta v$): Linear(64, 16) + ReLU + Linear(16, 1).

## 4. Outputs
1. **`v_fwd`**: Estimated vehicle forward speed ($m/s$).
2. **`w_yaw`**: Estimated vehicle yaw rate ($rad/s$).
3. **`logit_stat`**: Logit output for binary zero-speed / stationary classification.
4. **`delta_v`**: Auxiliary short-term longitudinal velocity change ($m/s$).

## 5. Deployment
- **Formats Included:**
  - **ONNX (`speednet_v2_w40.onnx` & `speednet_v2_w40.onnx.data`)**: Opset 14, constant-folded, dynamic batch dimension.
  - **TorchScript Lite (`speednet_v2_w40.ptl`)**: Traced for PyTorch Mobile / Native Android execution.
- **Target Platform:** On-device smartphone and embedded edge runtimes (ONNX Runtime Mobile / PyTorch Mobile).
- **Cloud Dependency:** None. Designed for 100% offline, real-time edge execution during GNSS loss.

## 6. Dataset
Trained and evaluated on the **IO-VNBD** (Inertial Outdoor Vehicle Navigation & Benchmark Dataset), featuring aligned high-frequency smartphone IMU telemetry paired with high-precision RTK GNSS ground truth across diverse driving trajectories.

## 7. Benchmarks
- **Offline Trajectory Benchmark (M028 / M029 EKF System):** $218.93\text{ m}$ position error after a 300-second complete GNSS outage.
- **On-Device Edge Latency:** Not yet benchmarked
- **On-Device Energy Consumption:** Not yet benchmarked
- **Quantized Edge Throughput:** Not yet benchmarked

## 8. Note on M028 / M029 Benchmark Configurations
The M028 and M029 benchmark configurations utilize the **exact same SpeedNet v2 neural model weights** (`speednet_v2_w40.pth`). The performance improvements observed in M029 over previous milestones stem entirely from enhancements to the navigation, jerk-gating, and heading filter integration architecture, rather than retraining or modifying the underlying neural network checkpoint.

## 9. Limitations
- **Sensor Orientation & Calibration:** Model predictions rely on consistent IMU axis mapping and pre-calibrated accelerometer/gyroscope bias offsets.
- **Smartphone Domain Shift:** Variations in vehicle mounting, vibration spectrums, and smartphone sensor noise characteristics across different hardware models may impact speed accuracy.
- **Target Hardware Latency:** Edge inference latency must be validated on the specific mobile processor target.
- **Navigation Accuracy Scope:** The published neural model artifacts alone do not guarantee full navigation accuracy; system performance depends on integration with an Extended Kalman Filter (EKF) or Dead Reckoning engine.
