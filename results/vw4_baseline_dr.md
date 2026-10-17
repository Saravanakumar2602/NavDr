# Baseline Dead Reckoning Experiment Report — IO-VNBD Vw4 Dataset

## Executive Summary
This report presents the empirical results of the **first physics-based Dead Reckoning (DR) baseline** evaluated on the **Vw04** dataset from **IO-VNBD**. 

The experiment simulates **60-second, 120-second, and 300-second GNSS outages** during active high-speed highway driving. During the outage, the dead-reckoning system relies **strictly and exclusively** on smartphone IMU sensors (Accelerometer and Gyroscope) without access to smartphone GPS, VBOX reference data, CAN bus wheel speeds, or AI/ML models. VBOX reference data is utilized solely for initial state setup ($t_0$) and post-hoc ground-truth evaluation.

---

## 1. Experiment Configuration

| Parameter | Value / Setting |
| :--- | :--- |
| **Outage Start Time** | `48,927.0 s` UTC ($t = 80.0$ minutes from dataset start) |
| **Outage Durations** | **60 seconds**, **120 seconds**, **300 seconds** |
| **Sampling Rate ($f_s$)** | **10.0 Hz** ($\Delta t = 0.100$ s uniform time step) |
| **Initial Position $(\text{Lat}_0, \text{Lon}_0)$** | $52.047494^\circ\text{N}, -0.756153^\circ\text{E}$ |
| **Initial Velocity ($v_0$)** | $117.07\text{ km/h} = 32.52\text{ m/s}$ |
| **Initial Heading ($\psi_0$)** | $269.96^\circ$ (relative to True North) |
| **Coordinate Frame** | Local East-North-Up (ENU) Cartesian frame ($x_0=0, y_0=0$) |
| **Heading Convention** | Navigation Heading ($\psi = 0^\circ$ North, $90^\circ$ East, $180^\circ$ South, $270^\circ$ West) |
| **Linear Accel Input** | $a_{\text{long}}(t) = -\left(a_{\text{raw, } y}(t) - g_y(t)\right)$ |
| **Gyro Yaw Rate Input** | $\omega_{\text{yaw}}(t) = -\text{GYROSCOPE Pitch}(t)$ |
| **Integration Algorithm** | Forward Euler Numerical Integration |

---

## 2. Experimental Results Summary Table

### 2.1 Pure Physics Baseline (Uncalibrated Raw IMU)

| Outage Duration | Ground Truth Distance ($D_{\text{gt}}$) | Estimated Distance ($D_{\text{est}}$) | Final Position Error ($e_{\text{final}}$) | Cumulative Distance Error (CDE %) | Final Pos Error Ratio (FPER %) | Final Velocity Error | Final Heading Error |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **60 s** | 1,946.84 m (1.95 km) | 3,564.61 m | **1,590.43 m** | **83.10 %** | 81.69 % | 224.89 km/h (62.47 m/s) | 10.04° |
| **120 s** | 3,659.81 m (3.66 km) | 10,766.47 m | **6,760.09 m** | **194.18 %** | 184.71 % | 456.69 km/h (126.86 m/s) | 5.30° |
| **300 s** | 9,002.14 m (9.00 km) | 55,255.15 m | **39,147.54 m** | **513.80 %** | 434.87 % | 1,118.47 km/h (310.69 m/s) | 55.21° |

---

### 2.2 Physics Baseline with Pre-Outage Static Bias Removal

| Outage Duration | Ground Truth Distance ($D_{\text{gt}}$) | Estimated Distance ($D_{\text{est}}$) | Final Position Error ($e_{\text{final}}$) | Cumulative Distance Error (CDE %) | Final Pos Error Ratio (FPER %) | Final Velocity Error | Final Heading Error |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **60 s** | 1,946.84 m (1.95 km) | 1,433.65 m | **2,135.60 m** | **26.36 %** | 109.70 % | 30.83 km/h (8.56 m/s) | 10.04° |
| **120 s** | 3,659.81 m (3.66 km) | 2,235.51 m | **3,532.08 m** | **38.92 %** | 96.51 % | 55.17 km/h (15.33 m/s) | 5.30° |
| **300 s** | 9,002.14 m (9.00 km) | 2,740.85 m | **9,073.45 m** | **69.55 %** | 100.79 % | 99.05 km/h (27.51 m/s) | 55.21° |

---

## 3. Visualizations Gallery

All experiment plots are stored in `plots/vw4/baseline_dr/`:

### 3.1 60-Second GNSS Outage

#### A. Trajectory Comparison (60s)
![Trajectory 60s](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/baseline_dr/outage_60s_trajectory.png)

#### B. Position Error Growth (60s)
![Position Error 60s](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/baseline_dr/outage_60s_position_error.png)

#### C. Velocity Comparison (60s)
![Velocity 60s](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/baseline_dr/outage_60s_velocity.png)

#### D. Heading Comparison (60s)
![Heading 60s](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/baseline_dr/outage_60s_heading.png)

---

### 3.2 120-Second GNSS Outage

#### A. Trajectory Comparison (120s)
![Trajectory 120s](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/baseline_dr/outage_120s_trajectory.png)

#### B. Position Error Growth (120s)
![Position Error 120s](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/baseline_dr/outage_120s_position_error.png)

#### C. Velocity Comparison (120s)
![Velocity 120s](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/baseline_dr/outage_120s_velocity.png)

#### D. Heading Comparison (120s)
![Heading 120s](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/baseline_dr/outage_120s_heading.png)

---

### 3.3 300-Second GNSS Outage

#### A. Trajectory Comparison (300s)
![Trajectory 300s](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/baseline_dr/outage_300s_trajectory.png)

#### B. Position Error Growth (300s)
![Position Error 300s](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/baseline_dr/outage_300s_position_error.png)

#### C. Velocity Comparison (300s)
![Velocity 300s](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/baseline_dr/outage_300s_velocity.png)

#### D. Heading Comparison (300s)
![Heading 300s](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/baseline_dr/outage_300s_heading.png)

---

## 4. Answers to Critical Scientific Questions

### 1. How far did the vehicle travel during the outage?
* **60 s Outage:** 1,946.84 meters (~1.95 km)
* **120 s Outage:** 3,659.81 meters (~3.66 km)
* **300 s Outage:** 9,002.14 meters (~9.00 km)

### 2. How far was the dead-reckoned position from VBOX?
* **Pure Physics Baseline (Uncalibrated):**
  * 60 s Outage: **1,590.43 m**
  * 120 s Outage: **6,760.09 m**
  * 300 s Outage: **39,147.54 m**
* **Pre-calibrated Bias Baseline:**
  * 60 s Outage: **2,135.60 m**
  * 120 s Outage: **3,532.08 m**
  * 300 s Outage: **9,073.45 m**

### 3. What was the CDE?
* **Pure Physics Baseline:**
  * 60 s: **83.10 %**
  * 120 s: **194.18 %**
  * 300 s: **513.80 %**
* **Pre-calibrated Bias Baseline:**
  * 60 s: **26.36 %**
  * 120 s: **38.92 %**
  * 300 s: **69.55 %**
* *Metric Clarification:* **CDE (%)** measures path length distance mismatch relative to ground truth ($|D_{\text{est}} - D_{\text{gt}}| / D_{\text{gt}}$). **FPER (%)** measures final vector position error relative to path length ($e_{\text{final}} / D_{\text{gt}}$).

### 4. How quickly did the error grow?
* Error growth is **quadratically accelerated ($O(t^2)$)**. In the uncalibrated baseline, position error reaches 100 meters within 15 seconds, 1,000 meters by 45 seconds, and catastrophic kilometers-level divergence beyond 60 seconds.

### 5. How much did velocity drift?
* **Uncalibrated Baseline:** Velocity drifts by **224.89 km/h** at 60 s, **456.69 km/h** at 120 s, and **1,118.47 km/h** at 300 s.
* **Pre-calibrated Baseline:** Velocity drifts by **30.83 km/h** at 60 s, **55.17 km/h** at 120 s, and **99.05 km/h** at 300 s.

### 6. How much did heading drift?
* Heading drift accumulated to **10.04°** at 60 s, **5.30°** at 120 s, and **55.21°** at 300 s due to uncorrected gyroscope bias.

### 7. What is the dominant source of error?
* **Primary Factor:** Constant and dynamic **accelerometer sensor bias** ($b_a \approx 1.19 \text{ m/s}^2$). Integrating a non-zero bias yields linear velocity drift ($v_{\text{err}} = b_a t$) and quadratic position explosion ($x_{\text{err}} = \frac{1}{2} b_a t^2$).
* **Secondary Factor:** **Gyroscope bias drift** causing cumulative heading misalignment during vehicle turns.

### 8. Is the simple IMU-only baseline anywhere near the SIH target?
* **NO.** The SIH competition target requires sub-meter accuracy or CDE < 1-2% during GNSS outages. The pure physics baseline produces CDEs of **83.10% to 513.80%**, confirming that double numerical integration of raw consumer smartphone IMU signals fails completely without intelligent processing.

### 9. What specifically needs to be improved with AI/ML?
1. **Neural IMU Denoising & Bias Estimation:** Deep Neural Networks (CNN/LSTM/TCN) to learn and subtract non-stationary IMU bias and vehicle engine vibration noise.
2. **Direct Velocity Prediction (SpeedNet / RoNIN):** Deep learning models trained to infer instant 2D vehicle speed directly from 10 Hz IMU windows, bypassing acceleration double integration.
3. **Deep Orientation Tracking:** Neural gyro bias estimation to stabilize heading integration across long 300-second outages.
