# SensorLab
> **Capture. Inspect. Export.**

A lightweight, standalone Android application designed for high-rate smartphone sensor telemetry recording, inspection, and dataset export. Built for personal research, robotics datasets, machine learning, inertial measurement, and navigation experimentation.

---

## 🌟 Overview

**SensorLab** turns any modern Android smartphone into a high-rate sensor telemetry recorder. It captures accelerometer, gyroscope, and GNSS location data in background callback threads, rendering smooth live UI telemetry while guaranteeing zero disk I/O latency or callback dropouts.

### Key Features
* **High-Rate IMU Capture:** Records Accelerometer + Gyroscope at maximum hardware speed (`SENSOR_DELAY_FASTEST`, up to ~200 Hz on supported hardware).
* **GNSS Telemetry:** Captures 1 Hz GNSS position, speed, bearing, and accuracy telemetry with explicit fix/permission status badges.
* **Non-Blocking Architecture:** Dedicated `HandlerThread` for sensor callbacks and single-threaded asynchronous disk writers prevent callback latency.
* **Live Telemetry Dashboard:** Smooth 6.6 Hz UI refresh displaying real-time 3-axis vectors, magnitudes, measured sampling rates, and session metrics.
* **Saved Sessions History:** View past recordings with duration, sample counts, file sizes, and completeness badges.
* **Session Details & Export:** Share complete session datasets directly as `.zip` archives containing `imu.csv`, `gnss.csv`, and `metadata.json`.
* **Data Inspector:** Asynchronously compute min/max/mean/std-dev statistics and visualize time-series line graphs for acceleration, angular velocity, and GNSS speed.
* **Downstream Tooling Compatibility:** Fully compatible with SIH 2026 Problem Statement 26168 preprocessing and dead-reckoning evaluation scripts.

---

## 📁 Data Format & Compatibility

Every recording session is stored in an independent folder named `SensorLab_YYYYMMDD_HHmmss`:

```text
SensorLab_20260914_143000/
  ├── imu.csv
  ├── gnss.csv
  └── metadata.json
```

### 1. `imu.csv`
Contains 6-axis inertial sensor telemetry recorded at ~200 Hz:
```csv
sensor_type,timestamp_ns,sensor_time_ns,val_x,val_y,val_z
ACCEL,1726305000000000,1726305000000100,0.12,9.81,0.45
GYRO,1726305000005000,1726305000005100,-0.001,0.002,0.0005
```

### 2. `gnss.csv`
Contains 1 Hz GNSS positioning and velocity telemetry:
```csv
timestamp_ns,elapsed_realtime_ns,latitude,longitude,altitude,speed_mps,bearing_deg,accuracy_m,bearing_accuracy_deg
1726305001000000,1726305001000050,13.0827,80.2707,15.2,4.5,180.0,3.2,1.5
```

### 3. `metadata.json`
Contains session parameters, device information, and sensor characteristics:
```json
{
  "app_name": "SensorLab",
  "app_version": "1.0.0",
  "device_model": "vivo V2355",
  "android_version": "14",
  "recording_start_time": "20260914_143000",
  "requested_imu_rate_hz": 200,
  "actual_imu_rate_hz": 198.4,
  "accel_sensor_name": "LSM6DSO Accelerometer",
  "gyro_sensor_name": "LSM6DSO Gyroscope",
  "orientation_convention": "X=Right, Y=Up/Forward, Z=Screen Normal"
}
```

---

## 🛠️ Architecture & Performance

```text
                 Smartphone IMU & GNSS
                           │
                           ▼
             HandlerThread ("SensorCallbackThread")
              SENSOR_DELAY_FASTEST (~200 Hz)
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
  UI Handler (6.6 Hz)         SingleThreadExecutor
  Volatile State Buffer       Asynchronous Disk FileWriter
             │                           │
             ▼                           ▼
   SensorLab Dashboard          imu.csv / gnss.csv / metadata.json
```

1. **Callback Thread Isolation:** `onSensorChanged` runs on a dedicated `HandlerThread`, completely decoupled from main thread layout measurement or animation frames.
2. **Asynchronous File I/O:** `FileWriter` calls are dispatched to a `SingleThreadExecutor` queue to prevent disk block latency from dropping sensor callbacks.
3. **Throttled UI Refresh:** Main thread polling at 150 ms intervals (6.6 Hz) ensures silky-smooth UI rendering without high CPU overhead.

---

## 🚀 Building & Installation

### Prerequisites
* JDK 17
* Android SDK 34 (Build-Tools 34.0.0)
* Android Device running Android 8.0+ (API 26+)

### Build Command
From the root or project directory, execute:
```bash
./gradlew assembleDebug
```

The compiled APK will be generated at:
`app/build/outputs/apk/debug/app-debug.apk`

---

## 🔐 Permissions & Privacy

* **Location Permissions (`ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`):** Required exclusively for GNSS telemetry recording (`gnss.csv`). If permission is denied or location services are disabled, IMU data collection continues operating at full rate without interruption.
* **High Sampling Rate (`HIGH_SAMPLING_RATE_SENSORS`):** Required on Android 12+ (API 31+) to access IMU rates above 200 Hz.
* **Zero Cloud Uploads:** All recorded telemetry files remain 100% local on-device unless explicitly exported by the user.

---

## 📄 License & Project Status
SensorLab is an open-source standalone research utility maintained under the SIH 2026 Dead Reckoning ecosystem.
