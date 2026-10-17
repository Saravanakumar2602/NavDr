# Adaptive Orientation Anchor Filter — Design & Architecture Report

## Executive Summary & System Context

This document specifies the technical design, mathematical formulation, coordinate transformation conventions, and filter architecture for the **Adaptive Orientation Anchor Filter (ZARU + Adaptive Gyro Bias + Kinematic NHC)** integrated with **SpeedNet v2** on the Vw04 dataset.

Our previous 300-second controlled oracle error decomposition established that while SpeedNet v2 reduced speed prediction error contribution down to **142.15 meters**, heading/orientation drift accounts for **241.80 meters (91.9% of total remaining navigation drift)**.

---

## 1. Verified Coordinate Conventions & Signal Mapping

From inspection of the Vw04 dataset files (`S-Vw4.csv`, `V-Vw4.csv`):
- **Sampling Frequency:** $f_s = 10\text{ Hz}$ ($\Delta t = 0.1\text{ s}$).
- **IMU Axes Mapping:**
  - `raw_ax`: Channel 9 (Lateral acceleration, m/s^2)
  - `raw_ay`: Channel 10 (Longitudinal acceleration, m/s^2)
  - `grav_x`: Channel 12 (Gravity component, x-axis)
  - `grav_y`: Channel 13 (Gravity component, y-axis)
  - `gyro_pitch`: Channel 15 (Smartphone Gyroscope Pitch rate, rad/s)
- **Signal Transformations:**
  - Tilt-Compensated Longitudinal Acceleration: $a_{\text{long}} = -(\text{raw\_ay} - \text{grav\_y})$
  - Smartphone Gyro Yaw Signal: $\omega_{\text{yaw}} = -\text{gyro\_pitch}$ (rad/s)
- **Ground Truth Reference (VBOX GNSS/INS):**
  - Position: ENU local Cartesian coordinates derived from Latitude & Longitude using spherical Earth model ($R_{\text{earth}} = 6378137.0\text{ m}$).
  - Heading: True azimuth heading $\psi_{\text{GT}}$ in degrees ($0^\circ = \text{North}, 90^\circ = \text{East}$).

---

## 2. 7-State EKF Formulation & State Vector

The system maintains a 7-dimensional continuous-discrete Extended Kalman Filter state:

$$\mathbf{x}_k = \begin{bmatrix} x_k \\ y_k \\ v_{x,k} \\ v_{y,k} \\ \psi_k \\ b_{a,k} \\ b_{g,k} \end{bmatrix}$$

where:
- $(x_k, y_k)$: Vehicle East and North position (meters)
- $(v_{x,k}, v_{y,k})$: Vehicle East and North velocity (m/s)
- $\psi_k$: Vehicle ENU heading angle (radians)
- $b_{a,k}$: Longitudinal accelerometer bias estimate ($\text{m/s}^2$)
- $b_{g,k}$: Gyroscope yaw rate bias estimate ($\text{rad/s}$)

### Process Model Kinematics
$$\psi_k = \psi_{k-1} + (\omega_{\text{m},k} - b_{g,k-1}) \cdot \Delta t$$
$$a_{\text{hat},k} = a_{\text{long},k} - b_{a,k-1}$$
$$v_{x,k} = v_{x,k-1} + a_{\text{hat},k} \sin(\psi_k) \cdot \Delta t$$
$$v_{y,k} = v_{y,k-1} + a_{\text{hat},k} \cos(\psi_k) \cdot \Delta t$$
$$x_k = x_{k-1} + v_{x,k} \cdot \Delta t$$
$$y_k = y_{k-1} + v_{y,k} \cdot \Delta t$$

---

## 3. Adaptive Zero Angular Rate Update (ZARU) & Bias Adaptation

During GNSS-denied operation, gyro bias $b_g$ is updated when SpeedNet v2 outputs strong stationary confidence ($P_{\text{stationary}} > P_{\text{thresh}}$):

### Robust Stationary Bias Extractor
When a stationary interval $T_{\text{stat}}$ is triggered, the raw stationary gyro samples $\{\omega_m(\tau)\}_{\tau \in T_{\text{stat}}}$ are collected, and a robust median estimator extracts the mean stationary bias:
$$\hat{b}_{\text{stat}} = \text{median}\left(\{\omega_m(\tau)\}_{\tau \in T_{\text{stat}}}\right)$$

### Adaptive Bias Updating Rule
Rather than abruptly changing $b_g$, a smooth exponential moving average (EMA) update is applied:
$$b_{g, \text{new}} = (1 - \alpha) \cdot b_{g, \text{old}} + \alpha \cdot \hat{b}_{\text{stat}}$$

- Sensitivity grid search on Validation set: $P_{\text{thresh}} \in \{0.50, 0.60, 0.70, 0.80, 0.90\}$, $\alpha \in \{0.01, 0.05, 0.10, 0.20\}$.

---

## 4. Kinematic Non-Holonomic Constraint (NHC) Pseudo-Measurement

Vehicle lateral velocity in the body frame is constrained to zero:
$$z_{\text{nhc}} = 0 \approx h_{\text{nhc}}(\mathbf{x}) = -v_x \cos\psi + v_y \sin\psi$$

Measurement Jacobian:
$$\mathbf{H}_{\text{nhc}} = \begin{bmatrix} 0 & 0 & -\cos\psi & \sin\psi & (v_x \sin\psi + v_y \cos\psi) & 0 & 0 \end{bmatrix}$$

Observation Noise Covariance: $R_{\text{nhc}} = (0.2\text{ m/s})^2$.

---

## 5. Gravity Tilt Safety Verification

During stationary events ($P_{\text{stationary}} > P_{\text{thresh}}$), linear acceleration components $(a_x, a_y)$ are used strictly to verify local roll/pitch tilt alignment:
$$\phi_{\text{roll}} = \arctan2(\text{grav}_y, \text{grav}_z), \quad \theta_{\text{pitch}} = \arctan2(-\text{grav}_x, \sqrt{\text{grav}_y^2 + \text{grav}_z^2})$$

> **Scientific Boundary:** Accelerometers provide gravity vectors which only constrain roll and pitch. Gravity does NOT provide heading azimuth $\psi$. Therefore, no false "gravity heading corrections" are applied.
