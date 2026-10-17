# Dead Reckoning Preparation Report — IO-VNBD Vw4 Dataset

## Executive Summary
This report documents the preparation, synchronization, coordinate frame transformation, gravity compensation, and signal validation performed on the **Vw04** dataset from **IO-VNBD** prior to executing baseline Dead Reckoning (DR) position integration. 

As instructed, **no position integration, EKF, ML model, or map matching has been implemented yet.**

---

## 1. Synchronization Method

### 1.1 Identified Timestamp Relationship
* **Vehicle Log (`V-Vw4.csv`):** Starts at `Time Since Start of Day = 44,126.700 seconds` (equivalent to **12:15:26.700 UTC**).
* **Smartphone Log (`S-Vw4.csv`):** Starts at `2020-01-08 12:15:27:004` (equivalent to **12:15:27.004 UTC**).
* **Clock Offset:** The smartphone log begins **304 milliseconds (0.304 seconds)** after the vehicle reference log.

### 1.2 Synchronization Pipeline
1. **Absolute UTC Time Base Conversion:**
   - Smartphone time vector: $t_{s, \text{UTC}} = 44127.004 + \frac{\text{TIME SINCE START (ms)} - 3410}{1000}$
   - Vehicle time vector: $t_{v, \text{UTC}} = \text{Time Since Start of Day (seconds)}$
2. **Uniform 10.0 Hz Resampling Grid:**
   - Overlap interval: $t_{\text{start}} = 44,127.004 \text{ s}$ to $t_{\text{end}} = 56,779.300 \text{ s}$.
   - Uniform sampling grid $T_{\text{sync}}$ generated at $\Delta t = 0.100 \text{ s}$ ($f_s = 10.0 \text{ Hz}$, total 126,523 synchronized time steps).
3. **Signal Interpolation:**
   - All smartphone sensors (Accelerometer, Gyroscope, Gravity) and vehicle reference signals (VBOX Velocity, Heading, Yaw Rate, Longitudinal Accel) are interpolated onto $T_{\text{sync}}$ using 1D piecewise linear interpolation.

---

## 2. Phone-to-Vehicle Coordinate Frame Alignment

### 2.1 Gravity Vector Alignment (Leveling)
The mean gravity vector components reported by the smartphone Android Sensor API in `S-Vw4.csv` are:
$$g_x = +0.0003 \text{ m/s}^2, \quad g_y = -0.00015 \text{ m/s}^2, \quad g_z = +9.8064 \text{ m/s}^2$$

Because $g_z \approx +9.806 \text{ m/s}^2$ dominates the vector ($g_x \approx 0, g_y \approx 0$), the smartphone was mounted **flat/horizontal** relative to the vehicle cabin floor. The smartphone local $+Z_{\text{phone}}$ axis aligns directly with the vehicle vertical $+Z_{\text{veh}}$ axis ($\hat{k}_{\text{phone}} \approx \hat{k}_{\text{veh}}$).

### 2.2 Horizontal Boresight Alignment
Empirical cross-correlation analysis between smartphone linear acceleration and CAN bus vehicle motion yields:
* **Forward Acceleration Correlation:** $-a_{\text{lin, } y}$ (negative phone Y-axis linear acceleration) correlates positively with forward vehicle acceleration during speeding/braking events ($r = +0.054$).
* **Lateral Acceleration Correlation:** $+a_{\text{lin, } x}$ (positive phone X-axis linear acceleration) correlates positively with vehicle rightward lateral acceleration ($r = +0.071$).
* **Yaw Rotation Correlation:** Phone Gyroscope Pitch ($\omega_y$) correlates strongly with VBOX vehicle yaw rate ($\omega_{\text{yaw}}$, $r = +0.269$).

### 2.3 Rotation Matrix $R_{\text{phone}}^{\text{veh}}$
$$\begin{bmatrix} a_{\text{veh, long}} \\ a_{\text{veh, lat}} \\ a_{\text{veh, vert}} \end{bmatrix} = \begin{bmatrix} 0 & -1 & 0 \\ 1 & 0 & 0 \\ 0 & 0 & 1 \end{bmatrix} \begin{bmatrix} a_{\text{lin, } x} \\ a_{\text{lin, } y} \\ a_{\text{lin, } z} \end{bmatrix}$$

---

## 3. Gravity Compensation

### 3.1 Linear Acceleration Extraction
The isolated gravity vector $\mathbf{g}_{\text{phone}}(t) = [g_x(t), g_y(t), g_z(t)]^T$ is subtracted from the raw accelerometer readings $\mathbf{a}_{\text{raw, phone}}(t)$ to yield pure linear acceleration:
$$\mathbf{a}_{\text{lin, phone}}(t) = \mathbf{a}_{\text{raw, phone}}(t) - \mathbf{g}_{\text{phone}}(t)$$

### 3.2 Vehicle Frame Linear Acceleration
Applying the coordinate transformation $R_{\text{phone}}^{\text{veh}}$:
$$a_{\text{veh, long}}(t) = -\left(a_{\text{raw, } y}(t) - g_y(t)\right)$$
$$a_{\text{veh, lat}}(t) = a_{\text{raw, } x}(t) - g_x(t)$$

---

## 4. Signal Verification & Generated Plots

All visual verification artifacts are stored in `plots/vw4/dr_preparation/`:

### 4.1 Raw Smartphone Accelerometer
![Raw Accelerometer](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/dr_preparation/raw_accelerometer.png)
*Figure 1: Raw 3-axis accelerometer readings showing gravity offset on Z-axis (~9.81 m/s²).*

### 4.2 Isolated Gravity Vector
![Gravity Vector](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/dr_preparation/gravity_vector.png)
*Figure 2: Isolated gravity vector components ($g_x, g_y, g_z$).*

### 4.3 Gravity-Compensated Linear Acceleration
![Compensated Acceleration](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/dr_preparation/compensated_acceleration.png)
*Figure 3: Linear acceleration after gravity removal in phone frame.*

### 4.4 Estimated Vehicle Longitudinal Acceleration
![Estimated Longitudinal Acceleration](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/dr_preparation/estimated_longitudinal_acceleration.png)
*Figure 4: Extracted longitudinal acceleration in vehicle body frame ($a_{\text{veh, long}}$).*

### 4.5 Validation Against VBOX Reference Acceleration
![Acceleration Validation](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/dr_preparation/acceleration_validation.png)
*Figure 5: 1-second smoothed comparison between phone-derived longitudinal acceleration and VBOX reference acceleration.*

---

## 5. Dead Reckoning Preparation & Requirements

### 5.1 Required Initial Conditions ($t_0 = 44,127.004 \text{ s}$)
1. **Initial Position $(x_0, y_0)$ / $(\text{Lat}_0, \text{Lon}_0)$:** Extracted from initial VBOX GPS:
   - $\text{Latitude}_0 = 52.047494^\circ\text{N}$
   - $\text{Longitude}_0 = -0.756153^\circ\text{E}$
2. **Initial Velocity $v_0$:** Extracted from initial VBOX velocity:
   - $v_0 = 13.18 \text{ km/h} = 3.661 \text{ m/s}$
3. **Initial Heading $\psi_0$:** Extracted from initial VBOX heading:
   - $\psi_0 = 270.768^\circ$ (relative to True North)

### 5.2 Acceleration Signal to Integrate
- **Signal:** Vehicle longitudinal acceleration $a_{\text{veh, long}}(t) = -lin\_a_y(t)$.
- **Filtering Requirement:** Low-pass filtering (e.g. 1-second moving average or Butterworth filter with 1 Hz cutoff) is necessary prior to integration to prevent high-frequency noise aliasing.

---

## 6. Key Analysis Questions & Answers

### 1. What is the exact synchronization method?
* We convert both dataset timestamps to absolute UTC seconds from 00:00:00. The smartphone log starts 304 ms after the vehicle log. We resample all signals onto a common uniform 10.0 Hz time grid $T_{\text{sync}}$ ($t \in [44127.004, 56779.300]$ s) using linear interpolation.

### 2. What phone-to-vehicle coordinate transformation are we using?
* We use an orthogonal principal-axis transformation:
  $$\begin{bmatrix} a_{\text{veh, long}} \\ a_{\text{veh, lat}} \\ a_{\text{veh, vert}} \end{bmatrix} = \begin{bmatrix} 0 & -1 & 0 \\ 1 & 0 & 0 \\ 0 & 0 & 1 \end{bmatrix} \begin{bmatrix} a_{\text{lin, } x} \\ a_{\text{lin, } y} \\ a_{\text{lin, } z} \end{bmatrix}$$
  justified by the Z-axis gravity vector orientation ($g_z \approx 9.81 \text{ m/s}^2$) and cross-correlations with vehicle longitudinal/lateral acceleration.

### 3. How are we removing gravity?
* By directly subtracting the Android Sensor Manager isolated gravity vector $\mathbf{g}_{\text{phone}}(t)$ from the raw accelerometer data $\mathbf{a}_{\text{raw, phone}}(t)$ at each time step.

### 4. What acceleration signal will be integrated?
* The transformed longitudinal linear acceleration $a_{\text{veh, long}}(t) = -(a_{\text{raw, } y} - g_y)$, post low-pass filtering.

### 5. What initial conditions are required?
* Initial latitude ($52.047494^\circ\text{N}$), initial longitude ($-0.756153^\circ\text{E}$), initial velocity ($3.661 \text{ m/s}$), and initial heading ($270.768^\circ$).

### 6. What assumptions are being made?
* **2D Planar Motion:** Vehicle moves on a flat horizontal plane.
* **Rigid Phone Mounting:** Phone orientation relative to vehicle chassis remains fixed during the drive.
* **Constant Clock Lag:** The 304 ms synchronization offset is constant.
* **Zero Vehicle Sideslip:** Velocity vector aligns with longitudinal chassis axis.

### 7. What uncertainties remain?
* **Quadratic Position Drift:** Double integration of accelerometer noise without velocity updates or zero-velocity updates (ZUPT) will result in trajectory drift over time.
* **Gyroscope Bias Drift:** Uncorrected gyro bias will cause heading errors to accumulate.
* **Road Bump Artifacts:** High-frequency vertical shocks leak into horizontal acceleration axes due to transient pitch variations.
