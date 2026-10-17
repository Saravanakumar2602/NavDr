# Final Research Methodology — Intelligent Dead-Reckoning (IDR) Project

## 1. Mathematical System Formulation

The Intelligent Dead-Reckoning (IDR) system estimates 2D vehicle navigation states during long GNSS outages using smartphone 6-DOF IMU data, neural speed modeling, and post-inference physical Kalman filtering.

### State Vector Representation
The Error-State Extended Kalman Filter (EKF) maintains a 7-dimensional navigation state vector:

$$\mathbf{x}_k = \begin{bmatrix} p_x & p_y & v_x & v_y & \psi & b_a & b_w \end{bmatrix}^T$$

where:
- $p_x, p_y$: 2D position coordinates in the local East-North-Up (ENU) tangent frame (meters).
- $v_x, v_y$: 2D global-frame velocity components in ENU (m/s).
- $\psi$: Vehicle heading angle in ENU (radians, measured counter-clockwise from East).
- $b_a$: Causal longitudinal accelerometer bias estimate ($\text{m/s}^2$).
- $b_w$: Causal gyroscope yaw-rate bias estimate ($\text{rad/s}$).

---

## 2. Kinematic State Propagation (Process Model)

At time sample $k$ ($\Delta t = 0.1\text{ s}$ at 10 Hz), state propagation is driven by calibrated IMU measurements:

$$\hat{\omega}_{y,k} = \omega_{y,k} - b_{w,k}$$

$$\psi_{k+1} = \psi_k + \hat{\omega}_{y,k} \cdot \Delta t$$

$$\hat{a}_{\text{long},k} = a_{\text{long},k} - b_{a,k}$$

$$a_{x,k} = \hat{a}_{\text{long},k} \sin(\psi_{k+1})$$

$$a_{y,k} = \hat{a}_{\text{long},k} \cos(\psi_{k+1})$$

$$v_{x,k+1} = v_{x,k} + a_{x,k} \cdot \Delta t$$

$$v_{y,k+1} = v_{y,k} + a_{y,k} \cdot \Delta t$$

$$p_{x,k+1} = p_{x,k} + v_{x,k+1} \cdot \Delta t$$

$$p_{y,k+1} = p_{y,k} + v_{y,k+1} \cdot \Delta t$$

### Error Covariance Propagation
$$\mathbf{P}_{k+1|k} = \mathbf{F}_k \mathbf{P}_{k|k} \mathbf{F}_k^T + \mathbf{Q}_k$$

where $\mathbf{F}_k$ is the linearized error-state Jacobian matrix and $\mathbf{Q}_k = \text{diag}\left(10^{-3}, 10^{-3}, 10^{-2}, 10^{-2}, (0.05^\circ)^2, 10^{-5}, 10^{-6}\right)$ is the process noise covariance matrix.

---

## 3. Neural Speed Estimation (SpeedNet v2)

Forward scalar vehicle speed $\hat{v}_{\text{net}}$ is estimated at 10 Hz using **SpeedNet v2**, a 1D CNN + BiLSTM sequence model operating on a temporal sliding window $W=40$ ($4.0\text{ s}$ context):

$$\mathbf{X}_k = \begin{bmatrix} a_{x,\text{lin}} & a_{y,\text{lin}} & a_{z,\text{lin}} & \omega_x & \omega_y & \omega_z \end{bmatrix}_{k-W+1:k} \in \mathbb{R}^{40 \times 6}$$

- **Architecture:**
  - 1D Convolutional Layer: 64 filters, kernel size 3, ReLU activation.
  - Bidirectional LSTM Layer: 64 hidden units per direction (128 total).
  - Dense Output Heads:
    1. Forward Speed Head: Linear projection with non-negative ReLU clipping ($\hat{v}_{\text{net}} \ge 0$).
    2. Yaw Rate Head: Linear projection ($\hat{\omega}_{\text{net}}$).
    3. Stationary Classifier Head: Sigmoid projection producing stationary probability $P(\text{stat}) \in [0, 1]$.

---

## 4. Post-Inference Physical Correction Pipeline

### 4.1 M013 F4 Multi-Signal Confidence-Gated Hard Speed Constraint
To prevent SpeedNet from over-predicting speed during cruise, braking, and stationary regimes while avoiding bound corruption during turns:

$$\sigma_{a,5}^2(k) = \text{Var}\left(a_{\text{long}, k-4:k}\right)$$

If $\sigma_{a,5}^2(k) \le 3.72\text{ m}^2/\text{s}^4$ AND $|\omega_{y,k}| \le 5.0^\circ/\text{s}$:

$$v_{\text{bound},k} = \max\left(0, \hat{v}_{k-1} + a_{\text{long},k} \cdot \Delta t\right)$$

$$\hat{v}_{\text{m013},k} = \min\left(\hat{v}_{\text{net},k}, v_{\text{bound},k}\right)$$

Else: $\hat{v}_{\text{m013},k} = \hat{v}_{\text{net},k}$.

---

### 4.2 M014 ZUPT F3 Stationary Velocity Reset
When the stationary classifier predicts high probability ($P(\text{stat}) > 0.70$):
- Measurement vector: $\mathbf{z}_{\text{zupt}} = [0, 0]^T$
- Innovation vector: $\mathbf{y}_{\text{zupt}} = \mathbf{z}_{\text{zupt}} - [v_x, v_y]^T$
- Measurement noise covariance: $\mathbf{R}_{\text{zupt}} = (0.20\text{ m/s})^2 \cdot \mathbf{I}_2$
- State update performed if $\|\mathbf{y}_{\text{zupt}}\| \le 5.0\text{ m/s}$.

---

### 4.3 M019 APM Speed Damping & M028 Jerk Gating
To selectively damp SpeedNet's positive speed overestimation during braking without introducing temporal phase lag:

1. **Deceleration & Turn Exclusion Conditions:**
   - $a_{\text{long},k} < -0.50\text{ m/s}^2$
   - $|\omega_{y,k}| \le 3.0^\circ/\text{s}$

2. **M028 Causal Longitudinal Jerk Gate:**
   $$j_{\text{long},k} = \frac{a_{\text{long},k} - a_{\text{long},k-1}}{\Delta t}$$
   Active ONLY if $j_{\text{long},k} < -1.00\text{ m/s}^3$.

3. **APM Integration Anchor & Speed Correction:**
   $$v_{\text{anchor}} = v_{\text{est}, k-5}$$
   $$\delta v_{\text{imu}} = \sum_{i=k-4}^{k} a_{\text{long},i} \cdot \Delta t$$
   $$z_{\text{apm}} = \max\left(0, v_{\text{anchor}} + \delta v_{\text{imu}}\right)$$

   If $\hat{v}_{\text{m013},k} > z_{\text{apm}}$:
   $$\delta v_{\text{raw}} = \hat{v}_{\text{m013},k} - z_{\text{apm}}$$
   $$\delta v_{\text{bounded}} = \min\left(\delta v_{\text{raw}}, 0.50\text{ m/s}\right)$$
   $$v_{\text{meas},k} = \hat{v}_{\text{m013},k} - \delta v_{\text{bounded}}$$

---

### 4.4 Non-Holonomic Constraint (NHC) Velocity Update
To enforce zero lateral vehicle motion ($v_{\text{lateral}} \approx 0$):

$$v_{\text{lateral},k} = -v_{x,k} \cos(\psi_k) + v_{y,k} \sin(\psi_k)$$

$$\mathbf{H}_{\text{nhc}} = \begin{bmatrix} 0 & 0 & -\cos\psi & \sin\psi & (v_x \sin\psi + v_y \cos\psi) & 0 & 0 \end{bmatrix}$$

$$y_{\text{nhc}} = 0.0 - v_{\text{lateral},k}$$

$$R_{\text{nhc}} = (0.20\text{ m/s})^2 = 0.04\text{ m}^2/\text{s}^2$$

---

## 5. Chronological Partitioning Protocol

- **Dataset:** Synchronized 10 Hz Vw04 sequence ($N = 126,505$ samples).
- **Training Set:** Samples `0` to `88,565` (70% partition).
- **Validation Set:** Samples `88,566` to `107,535` (15% partition, $300\text{ s}$ duration).
- **Locked Unseen Test Set:** Samples `108,000` to `111,000` ($300\text{ s}$ duration, $3000$ samples).
- **Evaluation Rule:** All hyperparameter choices selected strictly on Validation (`88,566:107,535`). Locked Test evaluated exactly ONCE for validation winners.
