# Baseline Inertial Dead-Reckoning Experiment Report — Vw4 Sequence

## Executive Summary & Core Question Answer

> **Core Question:** *“How badly does basic smartphone IMU dead reckoning drift during a GNSS outage?”*

**Answer:** Without machine learning, EKF/UKF sensor fusion, zero-velocity updates, or map matching, **basic smartphone IMU dead reckoning drifts catastrophically within seconds**. 

During a simulated **60-second GNSS blackout** on active highway driving ($1.95\text{ km}$ distance traveled):
* **Position Error:** Reaches **1,590.43 meters** of error in just 60 seconds.
* **Drift Percentage (Cumulative Distance Error - CDE):** **83.10 %** mismatch in path length ($3,564.61\text{ m}$ estimated vs $1,946.84\text{ m}$ actual).
* **Final Position Error Ratio (FPER):** **81.69 %** displacement error relative to path length.
* **Velocity Drift:** Estimated speed explodes from $120.9\text{ km/h}$ to **345.8 km/h** (a velocity error of **224.89 km/h** / $62.47\text{ m/s}$).
* **Heading Drift:** Deviates by **10.04°** from the true VBOX heading.

---

## 1. Experiment Setup & Configuration

### 1.1 Outage Scenario & Window Selection
* **Selected Data Sequence:** `Vw04` (Driver E, Long Multi-City Motorway Route).
* **Outage Window:** Continuous 60-second segment starting at $t = 48,927.0\text{ s}$ UTC ($t = 80.0\text{ minutes}$ from dataset start).
* **Sampling Rate:** Uniform $10.0\text{ Hz}$ ($\Delta t = 0.100\text{ s}$, 600 synchronized samples).

### 1.2 Initial Conditions at Outage Start ($t_0$)
* **Initial Position $(\text{Lat}_0, \text{Lon}_0)$:** $52.047494^\circ\text{N}, -0.756153^\circ\text{E}$ (from VBOX ground truth immediately prior to outage).
* **Initial Velocity ($v_0$):** $120.90\text{ km/h} = 33.58\text{ m/s}$.
* **Initial Heading ($\psi_0$):** $306.14^\circ$ (relative to True North).

---

## 2. Methodology & Mathematical Integration

### 2.1 Orientation Estimation & Coordinate Alignment
1. **Gravity Removal (Leveling):** Isolates linear acceleration by subtracting the smartphone's isolated gravity vector:
   $$\mathbf{a}_{\text{lin, phone}}(t) = \mathbf{a}_{\text{raw, phone}}(t) - \mathbf{g}_{\text{phone}}(t)$$
2. **Phone-to-Vehicle Body Frame Rotation:**
   - Vehicle Forward Longitudinal Acceleration: $a_{\text{long}}(t) = -a_{\text{lin, } y}(t)$
   - Vehicle Lateral Acceleration: $a_{\text{lat}}(t) = a_{\text{lin, } x}(t)$
   - Vehicle Yaw Rate: $\omega_{\text{yaw}}(t) = -\text{GYROSCOPE Pitch}(t)$

### 2.2 Numerical Integration Equations (Forward Euler)
For discrete time step $k$ ($\Delta t = 0.1\text{ s}$):
1. **Heading Integration:**
   $$\psi_k = \psi_{k-1} + \omega_{\text{yaw}, k} \cdot \Delta t$$
2. **Velocity Integration:**
   $$v_k = \max\left(0, \: v_{k-1} + a_{\text{long}, k} \cdot \Delta t\right)$$
3. **Local Cartesian ENU Position Integration:**
   $$v_{\text{east}, k} = v_k \cdot \sin(\psi_k), \quad v_{\text{north}, k} = v_k \cdot \cos(\psi_k)$$
   $$x_k = x_{k-1} + v_{\text{east}, k} \cdot \Delta t$$
   $$y_k = y_{k-1} + v_{\text{north}, k} \cdot \Delta t$$

---

## 3. Quantitative Performance Results Table

| Parameter | VBOX Ground Truth | Dead-Reckoning Estimate | Error / Drift |
| :--- | :--- | :--- | :--- |
| **Outage Duration** | 60.0 seconds | 60.0 seconds | — |
| **Total Distance Traveled ($D$)** | **1,946.84 m** (1.947 km) | **3,564.61 m** (3.565 km) | **+1,617.77 m** mismatch |
| **Final Endpoint Position** | $(x_{\text{gt}}, y_{\text{gt}}) = (-1583.5, 1137.9)\text{ m}$ | $(x_{\text{dr}}, y_{\text{dr}}) = (-2899.7, 2049.2)\text{ m}$ | **1,590.43 m** displacement error |
| **Cumulative Distance Error (CDE %)** | — | — | **83.10 %** |
| **Final Pos Error Ratio (FPER %)** | — | — | **81.69 %** |
| **Final Velocity** | $120.90\text{ km/h}$ ($33.58\text{ m/s}$) | $345.79\text{ km/h}$ ($96.05\text{ m/s}$) | **224.89 km/h** ($62.47\text{ m/s}$) |
| **Final Heading** | $306.14^\circ$ | $316.18^\circ$ | **10.04°** |

---

## 4. Visualizations Gallery

All experiment plots are stored in `plots/vw4/baseline_experiment/`:

### 4.1 Trajectory Comparison (VBOX vs Dead Reckoning)
![Trajectory Comparison](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/baseline_experiment/trajectory_comparison.png)
*Figure 1: Comparison between true VBOX ground truth path (Red) and uncalibrated dead-reckoning path (Blue).*

### 4.2 Position Error Accumulation Over Time
![Position Error Time](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/baseline_experiment/position_error_time.png)
*Figure 2: Quadratic position error growth ($O(t^2)$) reaching 1,590 meters at 60 seconds.*

### 4.3 Velocity Drift Comparison
![Velocity Comparison](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/baseline_experiment/velocity_comparison.png)
*Figure 3: Velocity drift due to $+1.19\text{ m/s}^2$ uncalibrated accelerometer sensor bias.*

### 4.4 Heading Angle Comparison
![Heading Comparison](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/baseline_experiment/heading_comparison.png)
*Figure 4: Heading angle comparison showing 10.04° gyro drift over 60 seconds.*

---

## 5. Key Scientific Assumptions & Limitations

1. **Uncalibrated Sensor Bias:** The smartphone accelerometer contains an uncorrected constant bias of approximately $+1.19\text{ m/s}^2$. Integrating a non-zero acceleration bias results in linear velocity drift ($v_{\text{err}} = b_a t$) and quadratic position error explosion ($x_{\text{err}} = \frac{1}{2} b_a t^2$).
2. **2D Planar Motion Assumption:** Altitude changes and vehicle roll/pitch fluctuations are assumed small relative to horizontal motion.
3. **No Sensor Fusion / ZUPT / Map Matching:** No zero-velocity updates, Extended Kalman Filtering, or road network map constraints were applied, isolating pure open-loop inertial integration.

---

## 6. Conclusion & Roadmap

This baseline experiment empirically proves that **pure physics integration of consumer smartphone IMUs is completely unviable for navigation without intelligent filtering or AI models**.

### Next Engineering Steps for SIH / ISRO Project:
1. **AI SpeedNet (1D-CNN + BiLSTM):** Train a deep neural network to predict instant 2D vehicle velocity directly from 10 Hz IMU windows, bypassing double acceleration integration.
2. **Extended Kalman Filter (EKF):** Fuse AI velocity predictions with gyroscope heading updates to maintain sub-meter tracking accuracy.
3. **Map Matching (HMM + NHC):** Apply Non-Holonomic Constraints and OpenStreetMap road graphs to snap trajectories to the physical road grid.
