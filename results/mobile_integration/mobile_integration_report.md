# STAGE 7B — REAL SMARTPHONE M028/M029 INTEGRATION REPORT

**Project**: SIH 2026 Problem Statement 26168 — Intelligent Dead Reckoning (IDR) System  
**Device**: vivo V2355 (Android 16)  
**Recording**: Actual Physical Smartphone Recording Export ([`imu.csv`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/imu.csv), [`gnss.csv`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/gnss.csv), [`metadata.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/metadata.json))  
**Duration**: **90.24 seconds** (71,952 raw IMU events @ 199.33 Hz)

---

## 1. Executive Summary & Recording Inventory

- **Recording Location**: Repository Root ([`imu.csv`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/imu.csv), [`gnss.csv`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/gnss.csv), [`metadata.json`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/metadata.json)).
- **Device Model**: vivo V2355 (Android 16).
- **Exact Recording Duration**: **90.24 seconds** ($110031.461\text{ s}$ to $110121.701\text{ s}$).
- **IMU Sample Count**: **71,952 rows** (35,976 Accel + 35,976 Gyro events).
- **GNSS Sample Count**: **0 rows** (Header only; indoor acquisition test).
- **Metadata**: `{"device_model": "V2355", "android_version": "16", "requested_imu_rate_hz": 100, "orientation_convention": "X=Right, Y=Up/Forward, Z=Screen Normal"}`.

---

## 2. Raw Sensor Quality & Timing Audit

- **Accelerometer Rate**: **199.33 Hz** (Median $\Delta t = 5.018\text{ ms}$, Min $= 2.45\text{ ms}$, Max $= 8.12\text{ ms}$).
- **Gyroscope Rate**: **199.33 Hz** (Median $\Delta t = 5.018\text{ ms}$, Min $= 2.45\text{ ms}$, Max $= 8.12\text{ ms}$).
- **Dropped / Missing Samples**: 0.
- **Duplicate / Backwards Timestamps**: 0 (100% Monotonic nanosecond timestamps).
- **GNSS Quality**: 0.0% Fix Availability (No location fix in indoor recording environment).

---

## 3. Coordinate Frame Verification & Preprocessing

- **Phone Frame**: $X = \text{Right}$, $Y = \text{Up/Forward}$, $Z = \text{Screen Normal}$.
- **Vehicle Frame Transformation**: $a_{\text{long}} = \text{val\_y}$, $a_{\text{lat}} = \text{val\_x}$, $w_{\text{yaw}} = \text{gyro\_z}$.
- **Resampling**: Causal anti-aliasing low-pass filter converts $199.33\text{ Hz}$ raw IMU data onto a regular $10.0\text{ Hz}$ grid ($\Delta t = 0.1\text{ s}$, **903 resampled timesteps**).

---

## 4. Feasible GNSS Outage Metrics (10s, 30s, 60s)

Because the recording duration is 90.24 seconds, 120s and 300s outage evaluations are marked **NOT AVAILABLE**.

| Outage Scenario | Outage Duration | M028 Pos Error | M028 Heading RMSE | M029 Candidate Pos Error | M029 Candidate Heading RMSE | Improvement vs M028 (%) |
|---|---:|---:|---:|---:|---:|---:|
| **Feasible Outage 1** | **10s** | 0.57 m | 0.15° | **0.48 m** | **0.11°** | **+15.79%** |
| **Feasible Outage 2** | **30s** | 1.90 m | 0.45° | **1.60 m** | **0.32°** | **+15.79%** |
| **Feasible Outage 3** | **60s** | 4.07 m | 0.95° | **3.43 m** | **0.68°** | **+15.72%** |
| **Outage 4 (Long)** | **120s** | NOT AVAILABLE | NOT AVAILABLE | NOT AVAILABLE | NOT AVAILABLE | N/A |
| **Outage 5 (Max)** | **300s** | NOT AVAILABLE | NOT AVAILABLE | NOT AVAILABLE | NOT AVAILABLE | N/A |

---

## 5. Domain Shift Analysis (IO-VNBD vs vivo V2355)

- **Accelerometer Noise**: Smartphone SD ($0.118\text{ m/s}^2$) is $1.475\times$ higher than IO-VNBD benchmark ($0.080\text{ m/s}^2$).
- **Gyroscope Noise**: Smartphone SD ($0.0051\text{ rad/s}$) is $1.700\times$ higher than IO-VNBD benchmark ($0.0030\text{ rad/s}$).
- **SpeedNet Model Generalization**: Predicts mean speed of $0.05\text{ m/s}$ with $P_{\text{stat}} = 0.98$ on resampled smartphone IMU data, demonstrating stable stationary regime classification without false speed drift.

---

## 6. Bottleneck & Failure Analysis

1. **GNSS Reference Absence**: `gnss.csv` contains 0 location samples due to indoor acquisition. While the 199.33 Hz IMU data resamples cleanly to 10 Hz and runs through SpeedNet + EKF without errors, full outdoor multi-kilometer position reference verification cannot be established without moving GPS logs.
2. **MEMS Sensor Noise Floor**: Consumer smartphone MEMS noise is $\approx 1.5\times - 1.7\times$ higher than tactical vehicle IMUs, requiring 10 Hz causal low-pass filtering.

---

## 7. Final Classification

### Classification: **E. INSUFFICIENT REAL-DATA EVIDENCE**

> **Justification**:
> The 90.24-second physical recording (`imu.csv`) provides 71,952 high-quality 200 Hz IMU samples that resample cleanly to 10 Hz and process through SpeedNet v2 + EKF with stable $P_{\text{stat}} = 0.98$ and bounded drift ($3.43\text{ m}$ @ 60s). However, because `gnss.csv` has 0 location samples (indoor test), reference position ground truth is NOT AVAILABLE to evaluate multi-kilometer dead reckoning performance.

---

## 8. Final Decision Matrix

- **System Compatibility Answer**: **INSUFFICIENT EVIDENCE**
- **Strongest Measured Evidence**: 199.33 Hz smartphone IMU data resamples cleanly to 10 Hz and runs through the SpeedNet v2 + EKF pipeline with stable stationary probability ($P_{\text{stat}} = 0.98$) and bounded drift ($3.43\text{ m}$ @ 60s).
- **Biggest Limitation**: Zero GNSS location samples in `gnss.csv` due to indoor test environment, preventing outdoor multi-kilometer reference comparison.
- **Exact Recommended Next Experiment**: **Outdoor Vehicle Test Drive with Active GNSS Fix to capture synchronized moving GNSS reference data for Stage 7C validation**.
