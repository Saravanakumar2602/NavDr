# SIH 2026 Intelligent Dead-Reckoning (IDR) — Prototype Showcase Dashboard

This directory contains the interactive, web-based **Showcase Prototype Dashboard** for the SIH 2026 Intelligent Dead-Reckoning (IDR) project.

---

## 🌟 Key Features

1. **OpenStreetMap (OSM) Trajectory Visualization:**
   - Dark-mode map interface displaying real-time vehicle movement.
   - **Cyan Line:** Ground Truth GPS path.
   - **Red Line (Exploding):** Unconstrained Inertial Double-Integration baseline ($6,420\text{ m}$ drift @ 300s).
   - **Emerald Green Line:** Active Production Model (`M028/M040` - SpeedNet v2 + NHC + Hard Speed Bound + ZUPT + APM + Jerk Gate: $218.93\text{ m}$ drift @ 300s).
   - **Gold Vector:** Kalman smoothing re-correction bridge upon GNSS signal recovery.

2. **Interactive GNSS Outage Simulation Modes:**
   - **GNSS ONLINE:** Vehicle follows standard GNSS signal fix.
   - **GNSS LOST (OUTAGE MODE):** Simulates a tunnel or urban canyon GNSS blackout. The IDR Model takes over seamless 10 Hz trajectory generation.
   - **GNSS RESTORED (RE-CORRECTION):** Network signal arrives, demonstrating how the system smoothly re-corrects residual drift.

3. **Real-Time HUD Telemetry & Model Internal States:**
   - **Speedometer Gauge ($\text{km/h}$)**
   - **Outage Timer ($0\text{ s} - 300\text{ s}$)**
   - **Live Drift Meter Comparison** ($6,420\text{ m}$ vs $218.93\text{ m}$)
   - **IMU Jerk Gate LED Light ($j_{\text{long}} < -1.00\text{ m/s}^3$)**
   - **2D ZUPT Stop Detector Indicator ($P(\text{stat}) > 0.70$)**
   - **APM Speed Damping State Indicator ($\delta v = 0.50\text{ m/s}$)**

---

## 🚀 How to Launch the Showcase Dashboard

### Option A: Open directly in your Web Browser
Simply double-click [`prototype/index.html`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/prototype/index.html) or open it in any modern browser (Chrome, Edge, Firefox).

### Option B: Launch local server using Python
Run the included python server runner:
```bash
python prototype/server.py
```
This starts a local web server at `http://localhost:8080` and automatically opens your default browser!
