# SIH 2026 Intelligent Dead-Reckoning (IDR) — Showcase Case 01
## Dense Forest / Forested Highway GNSS-Denied Navigation

This directory contains **Showcase Case 01** of the modular prototype layer for the SIH 2026 Intelligent Dead-Reckoning (IDR) project.

---

## 🌲 1. Scenario Overview & Operational Purpose

- **Scenario Title:** CASE 01 — DENSE FOREST / FORESTED HIGHWAY
- **Environment:** Dense Forest Canopy / National Park Reserve Highway (Bandipur National Park Highway NH766)
- **GNSS Outage Model:** Simulated GNSS-denied zone representing vehicle operation under dense tree canopy and severe satellite signal degradation.
- **Navigation Engine:** **M028 Production Pipeline** (Locked Production Baseline)
- **Primary Operational Goal:** Demonstrate the operational concept of seamless dead-reckoning navigation takeover during GNSS blackouts and smooth recovery when satellite signals return.

---

## 🔄 2. State Machine Flow

```
[ GNSS ONLINE ] (t < 30s)
      ↓
[ FOREST ENTRY ] (t = 30s) — GNSS Blackout Simulated Outage Triggered
      ↓
[ DEAD RECKONING MODE ] (30s <= t <= 270s)
      ↳ M028 Navigation Engine Pipeline Active
      ↳ SpeedNet v2 (W=40) Neural Speed Estimation
      ↳ Raw Gyro Yaw Integration + Fixed 2D NHC (R_nhc = 0.04)
      ↳ 7-State EKF Velocity & Position Fusion
      ↳ M013 F4 Confidence-Gated Physical Bound
      ↳ M014 ZUPT Velocity Update (during wildlife stop: P(stat) > 0.70)
      ↳ M019 APM Speed Damping (delta_v = 0.50 m/s)
      ↳ M028 Zero-Latency IMU Jerk Gate (j_long < -1.00 m/s³)
      ↓
[ FOREST EXIT ] (t = 270s) — GNSS Signal Restored
      ↓
[ KALMAN RE-ALIGNMENT BRIDGE ] (270s <= t <= 275s)
      ↓
[ GNSS-AIDED NAVIGATION ] (t > 275s)
```

---

## 🗺️ 3. Map & Trajectory Data Sources

- **Geographic Location:** Bandipur National Park Forest Reserve, Karnataka-Tamil Nadu Border Highway (NH766, `11.6750° N, 76.6350° E`).
- **Map Base:** OpenStreetMap (OSM) / CartoDB Dark Matter tile layer via Leaflet.js.
- **Trajectory Sourcing:**
  - **Ground Truth (Cyan):** Synchronized 10 Hz vehicle trajectory along NH766 highway.
  - **M028 Production DR (Emerald Green):** Exact locked production M028 benchmark trajectory error curve (**27.35 m @ 60s**, **426.85 m @ 120s**, **218.93 m @ 300s**).
  - **Raw Inertial (Red Exploding):** Unconstrained double-integration baseline (**6,420 m drift @ 300s**).
  - **GNSS Restoration (Gold):** Smooth Kalman re-alignment bridge upon exiting forest canopy.

---

## 🔬 4. Scientific Transparency & Disclosure

### What is REAL:
- The navigation engine algorithm and parameters are **100% real and strictly locked to M028**.
- The mathematical error trajectory of the IDR pipeline matches the canonical M028 locked research benchmark (**218.93 m @ 300s**).
- The map geometry represents a real, publicly accessible forested highway (NH766).

### What is SIMULATED:
- The GNSS outage boundary ($t=30\text{s}$ to $t=270\text{s}$) is a **simulated operational scenario**, representing dense canopy signal loss. It does NOT claim that the forest itself physically blocks 100% of GNSS signals under all real-world conditions.

### What this Demo PROVES:
- Demonstrates that when GNSS signals are lost, the M028 IDR engine seamlessly maintains 2D vehicle trajectory estimation using smartphone IMU sensors.
- Demonstrates how multi-signal physical constraints (NHC, ZUPT, APM, Jerk Gate) bound integrated position drift compared to unconstrained inertial integration.

### What this Demo DOES NOT PROVE:
- Does NOT claim that M028 solves 100% of the long-horizon SIH accuracy target (<10% FPER across 1 km). Outages beyond 491.50 m remain non-compliant under M028.

---

## 🚀 5. How to Launch Case 01

### Option A: Local Python Web Server (Recommended)
Run:
```bash
python prototype-new/case1/server.py
```
This automatically starts a local HTTP server at `http://localhost:8081` and opens your web browser.

### Option B: Open directly in Browser
Open `prototype-new/case1/index.html` directly in Chrome, Edge, or Firefox.

---

## 🔒 6. Provenance & Research Integrity

- **Research Milestones Changed?** **NONE** (`M028.md` through `M052.md` untouched).
- **M053 Created?** **NO**.
- **M028 Retrained or Modified?** **NO**. Codebase remains 100% locked at M028.
