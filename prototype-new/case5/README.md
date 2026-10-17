# Case 05 — GNSS Jamming / Interference Simulated Navigation

## Safety & Presentation Disclaimer
> **IMPORTANT SAFETY NOTICE**: No physical RF hardware, radio transmission, or actual RF jamming is performed in this prototype. GNSS loss is simulated **entirely in software** by suppressing GNSS measurement inputs within the simulation engine.

## Overview
Case 05 demonstrates the **SIH 2026 Intelligent Dead-Reckoning (IDR)** system during a simulated GNSS interference / jamming event along an open expressway corridor.

## Environment & Location
- **Geographic Area**: Yamuna Expressway & Outer Ring Road Corridor, New Delhi NCR (`Lat ~28.550°N`, `Lon ~77.280°E`).
- **Map Data Source**: Esri World Imagery Satellite Tiles (`https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`) combined with CartoDB Dark & Reference Labels Overlay.
- **Route**: 3.2 km high-speed suburban express route with highway traffic bottleneck stop (t=120s–145s).

## GNSS Interference Event Model
The scenario models a 220-second software measurement denial event:
1. **0.0s – 20.0s**: `GNSS-AIDED` (Normal Open Expressway Driving, GNSS Online)
2. **20.0s – 35.0s**: `GNSS-DEGRADED` (Simulated RF Noise Warning, Measurement Jitter)
3. **35.0s – 255.0s**: `GNSS-DENIED` (Software Measurement Suppression, M028 Dead-Reckoning Active)
4. **255.0s – 270.0s**: `REACQUIRING` (Interference Event Ended, EKF Re-alignment)
5. **270.0s – 300.0s**: `GNSS-RESTORED` (Open Expressway Clearing)

## M028 Pipeline Integration (Unchanged Baseline)
- **Speed Estimator**: SpeedNet v2 ($W=40$, CNN+BiLSTM)
- **Kinematic Constraints**: Fixed 2D Non-Holonomic Constraint ($R_{\text{nhc}} = 0.04$)
- **Zero-Velocity Update**: M014 F3 ZUPT lock ($P_{\text{stat}} > 0.70$) active during highway bottleneck stop (t=120s–145s)
- **APM Jerk Gating**: M028 F2 Causal Jerk Gate ($j_{\text{long}} < -1.00\text{ m/s}^3$) for high-speed deceleration pseudo-measurements
- **Locked Benchmark Drift**: 27.35m @ 60s, 426.85m @ 120s, 218.93m @ 300s (vs 6,420m Raw Gyro Yaw Integration)

## Real vs. Simulated Components
- **Real Geographic Map Imagery**: Uses real satellite map tiles of the Yamuna Expressway corridor.
- **Simulated Measurement Denial**: GNSS measurement suppression is executed entirely in software.

## Launch Instructions
- Standalone HTTP Server: `python prototype-new/case5/server.py` (Port 8085)
- Direct File Browser: Open `prototype-new/case5/index.html`
- Master Switcher: Open `prototype-new/index.html` (Port 8080)
