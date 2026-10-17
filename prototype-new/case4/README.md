# Case 04 — Deep Valley / Mountain Road GNSS-Denied Navigation

## Overview
Case 04 demonstrates the **SIH 2026 Intelligent Dead-Reckoning (IDR)** system operating along a serpentine mountain pass highway surrounded by steep Himalayan mountain ridges (3,800m ASL peak crests) that block direct satellite horizon line-of-sight.

## Environment & Location
- **Geographic Area**: Solang Valley & Rohtang Pass Highway NH3, Manali, Himachal Pradesh, India (`Lat ~32.315°N`, `Lon ~77.175°E`).
- **Map Data Source**: Esri World Imagery Satellite Tiles (`https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`) combined with CartoDB Dark & Reference Labels Overlay.
- **Elevation Range**: Real topographic altitude profile climbing from 2,050m ASL up to 2,380m ASL at the mountain pass viewpoint, descending to 2,152m ASL.

## GNSS Outage & State Machine Model
The scenario models a 220-second simulated mountain ridge blackout:
1. **0.0s – 20.0s**: `GNSS-AIDED` (Open Solang Valley Approach, 100% Horizon Visibility)
2. **20.0s – 40.0s**: `GNSS-DEGRADED` (Mountain Ridge Shadow Entrance, Satellite Horizon Shadow)
3. **40.0s – 260.0s**: `GNSS-DENIED` (Deep Valley Gorge Blackout, M028 Dead-Reckoning Active)
4. **260.0s – 270.0s**: `REACQUIRING` (Gorge Boundary Exit, Satellite Re-acquisition & EKF Re-alignment)
5. **270.0s – 300.0s**: `GNSS-RESTORED` (Open Alpine Plateau Clearing)

## M028 Pipeline Integration (Unchanged Baseline)
- **Speed Estimator**: SpeedNet v2 ($W=40$, CNN+BiLSTM)
- **Kinematic Constraints**: Fixed 2D Non-Holonomic Constraint ($R_{\text{nhc}} = 0.04$)
- **Zero-Velocity Update**: M014 F3 ZUPT lock ($P_{\text{stat}} > 0.70$) active during mountain viewpoint stop (t=125s–145s)
- **APM Jerk Gating**: M028 F2 Causal Jerk Gate ($j_{\text{long}} < -1.00\text{ m/s}^3$) for steep descent braking pseudo-measurements
- **Locked Benchmark Drift**: 27.35m @ 60s, 426.85m @ 120s, 218.93m @ 300s (vs 6,420m Raw Gyro Yaw Integration)

## Real vs. Simulated Components
- **Real Geographic Coordinates & Altitude**: Uses real satellite map imagery of the Solang Valley highway and real altitude profile data.
- **Simulated Signal Denial**: Mountain ridge horizon blockage is simulated for demonstration without claiming physical satellite loss on public roads.

## Launch Instructions
- Standalone HTTP Server: `python prototype-new/case4/server.py` (Port 8084)
- Direct File Browser: Open `prototype-new/case4/index.html`
- Master Switcher: Open `prototype-new/index.html` (Port 8080)
