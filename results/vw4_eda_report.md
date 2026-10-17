# Exploratory Data Analysis (EDA) Report — IO-VNBD Vw4 Dataset

## Executive Summary
This report provides a detailed exploratory data analysis (EDA) of the **Vw04** dataset from the **IO-VNBD** (Inertial Odometry Vehicle Navigation Benchmark Dataset). The Vw04 dataset captures approximately **3.51 hours** (12,652.5 seconds) of driving data recorded simultaneously using a smartphone (`S-Vw4.csv`) and a research vehicle equipped with a VBOX reference navigation system and CAN bus loggers (`V-Vw4.csv`).

---

## 1. Basic Dataset Verification

### 1.1 Dataset Metadata & Verification Summary

| Metric | Smartphone Dataset (`S-Vw4.csv`) | Vehicle Reference Dataset (`V-Vw4.csv`) |
| :--- | :--- | :--- |
| **File Path** | `Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw04/S-Vw4.csv` | `Synchronised V abd S datasets/Categorised IOVNB Dataset/Vw (Driver E)/Vw04/V-Vw4.csv` |
| **File Size** | **23,607,418 bytes** (~23.61 MB) | **27,124,526 bytes** (~27.12 MB) |
| **Total Rows** | **126,526** | **126,527** |
| **Total Columns** | **24** | **29** |
| **Missing Values** | **0** (0.00%) | **0** (0.00%) |
| **Duplicate Rows** | **0** (0.00%) | **0** (0.00%) |
| **Start Time** | `2020-01-08 12:15:27:004` (`3410 ms` relative) | `44126.7 s` (Start of Day = `12:15:26.700 UTC`) |
| **End Time** | `2020-01-08 15:46:19:504` (`12655910 ms` relative) | `56779.3 s` (Start of Day = `15:46:19.300 UTC`) |
| **Total Duration** | **12,652.50 seconds** (~3.514 hours) | **12,652.60 seconds** (~3.515 hours) |
| **Mean Sampling Interval** | **100.00 ms** (std: 0.78 ms, range: 76 - 124 ms) | **100.00 ms** (std: 0.0056 ms, range: 99 - 101 ms) |
| **Approx. Sampling Frequency** | **10.0 Hz** | **10.0 Hz** |

---

### 1.2 Column Specifications & Data Types

#### Smartphone Dataset (`S-Vw4.csv` — 24 Columns)
1. `GPS LATITUDE (degrees)` (*float64*): 51.946430° to 52.390910°
2. `GPS LONGITUDE (degrees)` (*float64*): -2.253461° to -0.691026°
3. `GPS ALTITUDE (m)` (*float64*): 73.31 m to 244.25 m
4. `GPS SPEED (Kmh)` (*float64*): 0.00 to 35.81 km/h
5. `GPS ACCURACY (m)` (*int64*): 2 m to 8 m radius
6. `GPS ORIENTATION (°)` (*float64*): 0.54° to 359.97°
7. `GPS SATELLITES IN RANGE` (*object*): Format `"in_range / in_view"` (e.g. `"21 / 22"`, range 14 to 26 satellites)
8. `TIME SINCE START (ms)` (*int64*): 3,410 to 12,655,910 ms
9. `DATE (YYYY-MO-DD HH-MI-SS_SSS)` (*object*): ISO timestamp string
10. `ACCELEROMETER X (m/s²)` (*float64*): -31.9922 to +26.1168 m/s²
11. `ACCELEROMETER Y (m/s²)` (*float64*): -26.5225 to +18.6061 m/s²
12. `ACCELEROMETER Z (m/s²)` (*float64*): 0.1007 to +17.6865 m/s²
13. `GRAVITY X (m/s²)` (*float64*): -0.5899 to +0.3602 m/s²
14. `GRAVITY Y (m/s²)` (*float64*): -0.3086 to +0.3924 m/s²
15. `GRAVITY Z (m/s²)` (*float64*): 9.7869 to 9.8067 m/s²
16. `GYROSCOPE Yaw (rad/s)` (*float64*): -1.2511 to +1.0883 rad/s
17. `GYROSCOPE Pitch (rad/s)` (*float64*): -2.0775 to +3.5761 rad/s
18. `GYROSCOPE Roll (rad/s)` (*float64*): -1.7621 to +1.7031 rad/s
19. `MAGNETIC FIELD X (μT)` (*float64*): -40.06 to +33.69 μT
20. `MAGNETIC FIELD Y (μT)` (*float64*): -84.69 to +8.06 μT
21. `MAGNETIC FIELD Z (μT)` (*float64*): -30.50 to +54.75 μT
22. `ORIENTATION (Yaw) (°)` (*float64*): 0.00° to 360.00°
23. `ORIENTATION (Pitch) (°)` (*float64*): -89.85° to -74.79°
24. `ORIENTATION (Roll ) (°)` (*float64*): -180.00° to +180.00°

#### Vehicle Reference Dataset (`V-Vw4.csv` — 29 Columns)
1. `No of GPS Satellites Available` (*float64*): 0.0 to 136.0 (VBOX satellite tracking metric)
2. `Time Since Start of Day (seconds)` (*float64*): 44,126.70 s to 56,779.30 s
3. `Latitude (degrees)` (*float64*): 51.946283° to 52.390910°
4. `Longitude (degrees)` (*float64*): -2.253547° to -0.691026°
5. `Velocity (km/hr)` (*float64*): 0.00 to 142.85 km/h (High accuracy VBOX GPS velocity)
6. `Heading (degrees)` (*float64*): 0.001° to 359.999°
7. `Height (km)` (*float64*): 20.19 m to 244.50 m (stored in meters despite label)
8. `Vertical velocity (km/hr)` (*float64*): -3.18 to +3.25 km/h
9. `Sample period (seconds)` (*float64*): 0.099 to 0.101 s
10. `Steering Angle (degrees)` (*float64*): 0.0° to 480.0°
11. `Wheel Speed Front Left (rad/sec)` (*float64*): 0.00 to 142.10 rad/s
12. `Wheel Speed Front Right (rad/sec)` (*float64*): 0.00 to 142.15 rad/s
13. `Wheel Speed Rear Left (rad/sec)` (*float64*): 0.00 to 142.05 rad/s
14. `Wheel Speed Rear Right (rad/sec)` (*float64*): 0.00 to 142.20 rad/s
15. `Yaw Rate (deg/sec)` (*float64*): -59.60 to +61.20 deg/s
16. `Indicated Vehicle Speed (km/hr)` (*float64*): 0.00 to 142.50 km/h (CAN bus speedometer)
17. `Indicated Longitudinal Acceleration (g)` (*float64*): -0.6599 to +0.4501 g
18. `Indicated Lateral Acceleration (g)` (*float64*): -0.6803 to +0.6750 g
19. `Handbrake (0 or 1)` (*float64*): Constantly `0.0`
20. `Gear Requested (Number fof gear employed 1-5)` (*float64*): 0.0 to 5.0
21. `Gear (Number fof gear employed 1-5)` (*float64*): 1.0 to 5.0
22. `Engine Speed (rev/min)` (*float64*): 787.0 to 4,850.0 RPM
23. `Coolant Temperature (degrees)` (*float64*): 81.0°C to 92.0°C
24. `Clutch Position (0 or 1)` (*float64*): Constantly `0.0`
25. `Brake Pressure (psi)` (*float64*): -1.44 to +150.0 psi
26. `Brake Position (0 or 1)` (*float64*): 0.0 or 1.0
27. `Battery Voltage (volts)` (*float64*): 12.60 to 14.40 V
28. `Air Temperature (degrees)` (*float64*): 9.0°C to 24.0°C
29. `Accelerator Pedal Position (0 or 1)` (*float64*): 0.0 to 100.0 %

---

## 2. Visualizations & Signal Explorations

All generated visualization artifacts are stored in `plots/vw4/`.

### 2.1 Smartphone Sensor Visualizations

#### Accelerometer
![Smartphone Accelerometer](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/accelerometer.png)
*Figure 1: Smartphone Accelerometer signals (X, Y, Z) showing dynamic shocks, vehicle accelerations, and gravity offset along the Z-axis (~9.81 m/s²).*

#### Gyroscope
![Smartphone Gyroscope](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/gyroscope.png)
*Figure 2: Smartphone Gyroscope angular velocities (Yaw, Pitch, Roll rad/s).*

#### Gravity
![Smartphone Gravity](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/gravity.png)
*Figure 3: Smartphone isolated Gravity vector showing near-constant Z gravity acceleration (~9.806 m/s²).*

#### Magnetometer
![Smartphone Magnetometer](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/magnetometer.png)
*Figure 4: Smartphone Magnetometer field strength (X, Y, Z μT) subject to vehicle body magnetic interference.*

#### Orientation
![Smartphone Orientation](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/orientation.png)
*Figure 5: Smartphone Orientation angles (Yaw, Pitch, Roll in degrees).*

#### Smartphone GPS Signals & Trajectory
![Smartphone GPS](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/smartphone_gps.png)
*Figure 6: Smartphone GPS Speed, Accuracy radius, Satellite count, and 2D Spatial Trajectory.*

---

### 2.2 Vehicle Reference & CAN Bus Visualizations

#### Vehicle Speeds (VBOX Velocity vs Indicated Speed)
![Vehicle Speed](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/vehicle_speed.png)
*Figure 7: VBOX High-precision reference velocity vs CAN Bus indicated speedometer speed.*

#### Vehicle Yaw Rate & Heading
![Vehicle Yaw Rate and Heading](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/vehicle_yaw_rate.png)
*Figure 8: Vehicle Yaw Rate (deg/s) and VBOX Heading angle (degrees).*

#### Wheel Speeds (4-Wheel CAN Bus Odometry)
![Wheel Speeds](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/wheel_speeds.png)
*Figure 9: Individual wheel speeds (Front-Left, Front-Right, Rear-Left, Rear-Right in rad/s).*

#### Vehicle Accelerations
![Vehicle Acceleration](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/vehicle_acceleration.png)
*Figure 10: CAN bus Longitudinal and Lateral Acceleration (in g).*

---

### 2.3 Exploratory Signal Comparisons

#### Speed Comparison: Smartphone GPS Speed vs VBOX Reference Velocity
![Speed Comparison](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/speed_comparison.png)
*Figure 11: Smartphone GPS speed compared against VBOX ground-truth velocity.*

> [!WARNING]
> **Exploratory Comparison Notice:** Note that Smartphone GPS speed is reported capped/quantized around 35.8 km/h or exhibits sampling lag compared to VBOX 142.8 km/h actual vehicle speeds.

#### Acceleration Comparison: Smartphone Accelerometer vs Vehicle Longitudinal Acceleration
![Acceleration Comparison](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/acceleration_comparison.png)
*Figure 12: Smartphone Accelerometer axes vs Vehicle CAN bus longitudinal acceleration.*

> [!NOTE]
> Smartphone axes are in phone-body frame and require coordinate transformation to align with vehicle longitudinal/lateral chassis frame.

#### Trajectory Comparison: Smartphone GPS Trajectory vs VBOX Ground-Truth Trajectory
![Trajectory Comparison](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/plots/vw4/trajectory_comparison.png)
*Figure 13: 2D Spatial Trajectory comparison between Smartphone GPS and VBOX.*

---

## 3. Synchronization Check

1. **Physical Start Time:**
   - **Vehicle (`V-Vw4.csv`):** `44,126.70 s` from start of day (equivalent to **12:15:26.700 UTC**).
   - **Smartphone (`S-Vw4.csv`):** `2020-01-08 12:15:27:004` (equivalent to **12:15:27.004 UTC**).
   - **Time Offset:** The smartphone dataset starts **304 milliseconds (0.304 s)** after the vehicle reference dataset.
2. **Sample Count Difference:**
   - `V-Vw4.csv`: 126,527 rows.
   - `S-Vw4.csv`: 126,526 rows (differs by exactly 1 row).
3. **Sampling Rate Consistency:**
   - Both datasets average exactly **100.0 ms** per sample (10.0 Hz).
4. **Direct Alignment Feasibility:**
   - Datasets **cannot be directly aligned row-by-row** without applying a 304 ms time-shift interpolation and trimming/padding the 1-sample mismatch.

---

## 4. Data-Quality & Anomaly Report

1. **Constant / Stuck Values:**
   - `Handbrake (0 or 1)` in `V-Vw4.csv` is constantly `0.0`.
   - `Clutch Position (0 or 1)` in `V-Vw4.csv` is constantly `0.0` (automatic transmission / sensor unequipped).
2. **Smartphone GPS Speed Discrepancy:**
   - Smartphone `GPS SPEED (Kmh)` is capped/quantized around ~35.8 km/h, while VBOX true velocity reaches 142.8 km/h. This indicates a smartphone Android API reporting limitation or satellite speed filter cap.
3. **Sensor Shocks / Spikes:**
   - `ACCELEROMETER X` exhibits transient extreme spikes up to -31.99 m/s² and +26.11 m/s² due to road bumps and engine vibrations.
   - `GYROSCOPE Pitch` spikes up to +3.57 rad/s during vehicle turns/bumps.
4. **Orientation Wrapping Discontinuities:**
   - `ORIENTATION (Yaw)` and VBOX `Heading` exhibit 0° <-> 360° phase wrapping jumps.
5. **Baseline Sensor Noise:**
   - `Brake Pressure (psi)` shows minor negative baseline noise (-1.44 psi when unpressed).

---

## 5. Final Summary Answers

### 1. What signals do we have?
* **Smartphone (`S-Vw4`):** 3-axis Accelerometer, 3-axis Gyroscope, 3-axis Gravity vector, 3-axis Magnetometer, 3-axis Orientation angles, Smartphone GPS (Latitude, Longitude, Altitude, Speed, Accuracy, Satellites).
* **Vehicle (`V-Vw4`):** VBOX Reference Navigation (Latitude, Longitude, High-accuracy Velocity, Heading, Height, Vertical velocity, Yaw Rate), 4 Wheel Speeds (FL, FR, RL, RR), Indicated Speedometer Speed, Longitudinal Accel, Lateral Accel, Engine RPM, Steering Angle, Brake Pressure, Gear, Accelerator Position.

### 2. What is their actual sampling rate?
* Both datasets operate at a stable nominal sampling frequency of **10.0 Hz** (100.0 ms mean sample interval).

### 3. Are the smartphone and vehicle datasets synchronized?
* **Nearly synchronized, but not identical row-for-row.** The smartphone dataset starts **304 ms** after the vehicle dataset, and the vehicle dataset has 1 additional row (126,527 vs 126,526).

### 4. What obvious data-quality problems exist?
* Smartphone GPS speed is artificially capped at ~35.8 km/h.
* Smartphone accelerometers contain transient road vibration spikes (up to 3g).
* Phone coordinate frame is unaligned with vehicle chassis body frame.
* Two constant sensor channels (`Handbrake`, `Clutch Position`).

### 5. Which signals are useful for our future dead-reckoning system?
* **For Inputs / Prediction:** Smartphone 3-axis Accelerometer, 3-axis Gyroscope, and 4 Wheel Speeds (wheel odometry).
* **For State Estimation / Alignment:** Smartphone Gravity vector (for tilt compensation) and Yaw Rate.
* **For Ground Truth / Validation:** VBOX Latitude, Longitude, High-accuracy Velocity, and Heading.

### 6. What should we do next?
* Perform timestamp alignment (interpolate by 304 ms offset).
* Implement phone-to-vehicle body frame rotation calibration using the gravity vector and vehicle motion.
* Proceed to loading and preprocessing Vw4 data for Dead Reckoning trajectory reconstruction.
