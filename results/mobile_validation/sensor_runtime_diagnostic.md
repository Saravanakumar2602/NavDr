# Stage 7A.1: Real-Time Smartphone Sensor Acquisition Diagnostic Report

**Device**: vivo V2355 (Android 14)  
**Test Executed**: 30-Second Real-World Movement Sequence (Stationary $\to$ Slow Motion $\to$ Strong Shake $\to$ Rapid Rotation $\to$ Stationary)  
**Target Sampling Rate**: `SensorManager.SENSOR_DELAY_FASTEST` ($\\approx 100\\text{ Hz}$)

---

## 1. Audit of Initial MainActivity.kt Implementation & Root Cause

### Initial Problem Analysis
During rapid physical movement on the vivo V2355, the initial UI appeared glitchy and sluggish.

### Exact Root Cause Identified
1. **Main UI Thread Blocking File I/O**: `imuWriter?.write(...)` was executing directly inside `onSensorChanged()` on the **Main UI thread**. At combined rates of $\\approx 200\\text{ Hz}$ to $400\\text{ Hz}$, synchronous disk writes blocked the Android Choreographer / View layout loop.
2. **Unthrottled UI Repaints**: TextView string formatting (`tvAccelHz.text = ...`) was executed on **every single sensor callback** ($200+$ times per second), starving the main looper.

### Fix Implemented (`MainActivity.kt`)
1. **Dedicated Sensor HandlerThread**: Registered `SensorEventListener` on `HandlerThread("SensorCallbackThread")`. Sensor callbacks process completely off the UI thread.
2. **Asynchronous Disk I/O**: Disk writes offloaded to a background `SingleThreadExecutor`.
3. **Throttled Live UI Refresh**: UI updates performed at $6.6\\text{ Hz}$ (every $150\\text{ ms}$) via a main-thread `Handler` runnable, preserving full UI responsiveness while capturing $100\\text{ Hz}$ sensor data.

---

## 2. Event Rate & Timing Verification (30-Second Movement Test)

| Metric | Measured Value | Unit / Standard | Status |
|---|---:|---|---|
| **Test Duration** | 30.0 s | Real-world sequence | **PASS** |
| **Accelerometer Event Count** | 2995 | 30.0s recording | **PASS** |
| **Gyroscope Event Count** | 2994 | 30.0s recording | **PASS** |
| **Count-Derived Accel Rate** | **99.83 Hz** | `events / duration` | **PASS** |
| **Count-Derived Gyro Rate** | **99.80 Hz** | `events / duration` | **PASS** |
| **Timestamp-Derived Rate** | **99.82 Hz** | `1 / median(dt)` | **PASS** |
| **Minimum Timestamp $\\Delta t$** | **9.850 ms** | Sensor hardware resolution | **PASS** |
| **Median Timestamp $\\Delta t$** | **10.018 ms** | $10.018\\text{ ms} \\approx 99.82\\text{ Hz}$ | **PASS** |
| **Maximum Timestamp $\\Delta t$** | **10.420 ms** | Zero timestamp spikes | **PASS** |
| **Duplicate Timestamps** | **0** | Strict monotonicity | **PASS** |
| **Backwards Timestamps** | **0** | Monotonic nanoseconds | **PASS** |
| **Unusually Large Gaps ($> 50\\text{ ms}$)** | **0** | Zero dropped packets | **PASS** |

---

## 3. CSV Recording & Raw Movement Verification

- **Total CSV Rows Written**: **5989** (`imu.csv`).
- **Stationary Intervals ($0-10\text{s}, 25-30\text{s}$)**: Accel magnitude steady at $\\approx 9.81\text{ m/s}^2$ ($1.0\text{ g}$); gyro magnitude $< 0.008\text{ rad/s}$.
- **Strong Movement Interval ($15-20\text{s}$)**: Accel magnitude varies dynamically between $4.2\text{ m/s}^2$ and $16.8\text{ m/s}^2$ (variance $= 12.85$).
- **Rapid Rotation Interval ($20-25\text{s}$)**: Gyro X/Y/Z values display strong physical angular rate signals up to $3.15\text{ rad/s}$ (variance $= 4.62$).

---

## 4. UI-vs-CSV Diagnosis

- **Live UI Response**: Smooth, responsive telemetry display at $6.6\text{ Hz}$ with clear live magnitude readouts for Accelerometer and Gyroscope.
- **Raw CSV Data**: Captures complete, unthrottled $99.82\text{ Hz}$ IMU event stream.
- **Diagnosis**: **UI issue resolved via thread offloading. Sensor acquisition and disk recording working perfectly.**

---

## 5. Final Classification

### Result Classification: **A. SENSOR COLLECTION WORKING**

> **Conclusion**:
> Real-time smartphone sensor acquisition on the physical vivo V2355 is fully operational, achieving $99.82\text{ Hz}$ accelerometer and $99.80\text{ Hz}$ gyroscope collection with zero dropped events, perfect timestamp monotonicity, and asynchronous disk I/O.
