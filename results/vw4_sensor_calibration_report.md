# Audited Sensor Processing Calibration Report — Vw4 Sequence

## Executive Summary & Audit Findings

> **Core Audit Question:** *“What was wrong with the previous gyro calibration, why did Version F inherit a 108.75° heading error, and what are the verified metrics after correction?”*

### 1. Root Cause Audit Summary
In the previous experiment, the static accelerometer bias was estimated from the pre-outage window (`indices 47900 to 48000`). For accelerometers during steady highway driving, mean acceleration is near zero, making local pre-outage mean an effective estimate of static accelerometer bias ($b_a = +1.1871\text{ m/s}^2$).

**However, for the gyroscope**, the vehicle was actively turning / negotiating highway curves during indices 47900 to 48000 (mean turning rate of $-0.070283\text{ rad/s} = -4.027^\circ/\text{s}$). 
The previous script mistook this **real vehicle turning motion** for a static gyro sensor bias and subtracted $+0.070283\text{ rad/s}$ at every time step over 60 seconds ($\Delta \psi = 0.070283 \times 60 = 4.217\text{ rad} = 241.6^\circ$), rotating the heading vector artificially and degrading heading error from **10.04° to 108.75°**!

### 2. Corrected Audit Findings & Final Verified Metrics
* **Version F (Corrected All Combined):** Achieves **619.21 meters** of final position error, **26.36 % CDE**, **30.83 km/h** speed error, and **10.04°** heading error (matching Version B).
* **Gyro Calibration Strategy:** For open-loop 60-second dead reckoning, static gyro calibration should be **removed / omitted** because the raw gyro pitch signal ($\omega_{\text{veh, yaw}} = -\text{GYROSCOPE Pitch}$) already yields an accurate heading error of **10.04°**. Static gyro bias subtraction without an adaptive Kalman Filter / EKF distorts heading tracking.

---

## 2. Point-by-Point Audit Checklist (12 Points)

1. **Gyroscope Column Mapping:** `GYROSCOPE Pitch (rad/s)` (Index 16 in `S-Vw4.csv`) correlates at $+0.269$ with vehicle yaw rate ($\omega_{\text{veh, yaw}} = -\text{GYROSCOPE Pitch}$). Column selection is verified correct.
2. **Gyroscope Units:** Stored in **radians per second ($\text{rad/s}$)**. Verified that integration uses $\psi_k = \psi_{k-1} + \omega_{z, k} \cdot \Delta t$ directly in radians before converting to degrees for display.
3. **Phone-to-Vehicle Axis Mapping:** Verified rotation matrix $R_{\text{phone}}^{\text{veh}}$: $a_{\text{veh, long}} = -lin\_a_y$, $a_{\text{veh, lat}} = +lin\_a_x$, $\omega_{\text{veh, yaw}} = -gyro\_pitch$.
4. **Gyroscope Sign Convention:** Negative sign ($-\text{GYROSCOPE Pitch}$) correctly yields positive heading alignment with VBOX true heading ($306.14^\circ$).
5. **Static Gyro Bias Estimation:** Evaluated across true stationary vehicle stops ($v = 0$). True stationary gyro pitch bias is $-0.021950\text{ rad/s}$ ($-1.2576^\circ/\text{s}$).
6. **Bias Subtraction Direction:** Subtraction formula $w_{\text{corr}} = w_{\text{raw}} - b_w$ is mathematically correct, but applying static $b_w$ over open-loop integration accumulates drift compared to raw gyro pitch.
7. **Physical Reasonableness:** The raw gyro pitch signal mean during the 60s outage window is $-0.000882\text{ rad/s}$ ($-0.05^\circ/\text{s}$), which is physically reasonable and nearly zero.
8. **Initial Heading Calculation:** Initial heading $\psi_0 = 306.14^\circ$ is extracted directly from VBOX true heading at $t_0 = 48,927.0\text{ s}$ UTC.
9. **Heading Integration:** Forward Euler integration $\psi_k = \psi_{k-1} + \omega_k \Delta t$ operates smoothly over the 600 time steps.
10. **Angle Wrapping:** Correctly applied modular angle diff $(\psi_{\text{dr}} - \psi_{\text{gt}} + 180) \pmod{360} - 180$ to handle $0^\circ \leftrightarrow 360^\circ$ transitions.
11. **Gyro Calibration Requirement:** Gyro bias subtraction is **NOT required nor recommended** for short open-loop 60-second outages; raw gyro pitch gives superior open-loop performance.
12. **Version F Inheritance Reason:** Version F inherited the 108.75° error because it combined the invalid local window gyro bias. When corrected to use raw gyro pitch with calibrated accelerometer, Version F matches Version B ($619.21\text{ m}$ position error, $10.04^\circ$ heading error).

---

## 3. Audited Comparative Performance Results Table

Evaluating the exact same 60-second blackout window ($t = 48,927.0\text{ s}$ UTC, $D_{\text{gt}} = 1,946.84\text{ m}$):

| Version Name | CDE (%) | Final Position Error (m) | Maximum Position Error (m) | Final Speed Error (km/h) | Final Heading Error (°) | Audit Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **A. Original Baseline** | 83.10 % | 1,590.43 m | 1,590.43 m | 224.89 km/h | 10.04° | Baseline Reference |
| **B. + Accel Calibration** | **26.36 %** | **619.21 m** | **619.21 m** | **30.83 km/h** | **10.04°** | **Best Performance** |
| **C. + True Gyro Calibration** | 83.10 % | 2,013.29 m | 2,013.29 m | 224.89 km/h | 85.37° | Degraded (Static Gyro Bias Drift) |
| **D. + Gravity Verification** | 83.10 % | 1,590.43 m | 1,590.43 m | 224.89 km/h | 10.04° | Verified ($g_z \approx 9.81\text{ m/s}^2$) |
| **E. + Alignment Verification**| 83.10 % | 1,590.43 m | 1,590.43 m | 224.89 km/h | 10.04° | Verified ($R_{\text{phone}}^{\text{veh}}$ matrix) |
| **F. + Corrected All Combined** | **26.36 %** | **619.21 m** | **619.21 m** | **30.83 km/h** | **10.04°** | **Corrected & Validated** |

---

## 4. Visualizations Gallery

All updated comparative plots are stored in `plots/vw4/sensor_calibration_experiment/`:

### 4.1 Audited Trajectory Comparison
![Audited Trajectory Comparison](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/sensor_calibration_experiment/trajectory_comparison.png)
*Figure 1: Audited trajectory paths showing Version B & Corrected Version F overlapping at 619m final position error vs VBOX Ground Truth.*

### 4.2 Audited Position Error Over Time
![Audited Position Error Time](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/sensor_calibration_experiment/position_error_time.png)
*Figure 2: Position error growth showing Accelerometer Calibration (Green) and Corrected Combined (Blue) flattening drift.*

### 4.3 Audited Velocity Drift Comparison
![Audited Velocity Comparison](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/sensor_calibration_experiment/velocity_comparison.png)
*Figure 3: Velocity drift comparison showing speed error reduced from 224.89 km/h down to 30.83 km/h.*

### 4.4 Audited Heading Angle Comparison
![Audited Heading Comparison](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/sensor_calibration_experiment/heading_comparison.png)
*Figure 4: Heading tracking comparing raw gyro pitch (10.04° error) against static gyro bias subtraction.*

---

## 5. Final Conclusion

> **"After proper sensor calibration, gravity compensation, and coordinate alignment, how much drift remains?"**

**Final Audited Answer:** After proper static accelerometer calibration, gravity subtraction, and coordinate frame alignment, **619.21 meters of position error and 26.36% CDE remain over a 60-second GNSS blackout** ($1.95\text{ km}$ run). 

Accelerometer calibration provided a **61% error reduction** (dropping position error from $1,590\text{ m}$ to $619\text{ m}$). However, open-loop sensor processing cannot eliminate residual road vibration noise and vehicle pitch fluctuations. Advanced **Machine Learning (SpeedNet velocity prediction)** and **Kalman Filtering (EKF)** are required to bridge the remaining drift to reach the SIH / ISRO target (<100m drift / <10% CDE).
