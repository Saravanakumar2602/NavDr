# Case 03 — Deep Urban Canyon GNSS-Degraded & GNSS-Denied Navigation

## Overview
Case 03 demonstrates the **SIH 2026 Intelligent Dead-Reckoning (IDR)** system operating under simulated urban-canyon conditions. High-rise glass skyscrapers (80m–140m height) block direct line-of-sight satellite signals and induce severe multipath reflections.

## Environment & Location
- **Geographic Area**: DLF Cyber City & MG Road Financial District, Gurugram / New Delhi NCR (Lat ~28.495°N, Lon ~77.088°E).
- **Map Data Source**: Esri World Imagery Satellite Tiles (`https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`) combined with CartoDB Dark & Reference Labels Overlay.
- **Urban Corridor**: High-density skyscraper avenue flanked by 5 corporate glass tower blocks, urban traffic light intersections, and 90-degree street turns.

## GNSS Outage & State Machine Model
The scenario models a 220-second simulated GNSS blackout:
1. **0.0s – 20.0s**: `GNSS-AIDED` (Open MG Road Boulevard, 100% Sky Visibility)
2. **20.0s – 40.0s**: `GNSS-DEGRADED` (Skyscraper Shadow Entrance, High Multipath Jitter)
3. **40.0s – 260.0s**: `GNSS-DENIED` (Deep Urban Canyon Corridor Blackout, M028 Dead-Reckoning Active)
4. **260.0s – 270.0s**: `REACQUIRING` (Urban Boundary Exit, Satellite Re-acquisition & EKF Re-alignment)
5. **270.0s – 300.0s**: `GNSS-RESTORED` (Open Boulevard Clearing)

## M028 Pipeline Integration (Unchanged Baseline)
- **Speed Estimator**: SpeedNet v2 (W=40, CNN+BiLSTM)
- **Kinematic Constraints**: Fixed 2D Non-Holonomic Constraint ($R_{\text{nhc}} = 0.04$)
- **Zero-Velocity Update**: M014 F3 ZUPT lock ($P_{\text{stat}} > 0.70$) active during red signal traffic light stop (t=120s–145s)
- **APM Jerk Gating**: M028 F2 Causal Jerk Gate ($j_{\text{long}} < -1.00\text{ m/s}^3$) for urban braking pseudo-measurements
- **Locked Benchmark Drift**: 27.35m @ 60s, 426.85m @ 120s, 218.93m @ 300s (vs 6,420m Raw Gyro Yaw Integration)

## Real vs. Simulated Components
- **Real Geographic Coordinates & Imagery**: Uses real satellite map tiles of the Cyber City financial district.
- **Simulated Signal Denial**: Urban building blockage is simulated for demonstration without claiming physical satellite loss on public roads.

## Launch Instructions
- Standalone HTTP Server: `python prototype-new/case3/server.py` (Port 8083)
- Direct File Browser: Open `prototype-new/case3/index.html`
- Master Switcher: Open `prototype-new/index.html` (Port 8080)
