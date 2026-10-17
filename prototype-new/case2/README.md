# SIH 2026 Intelligent Dead-Reckoning (IDR) — Showcase Case 02
## Long Underground Tunnel / Underpass GNSS-Denied Navigation

This directory contains **Showcase Case 02** of the modular prototype layer for the SIH 2026 Intelligent Dead-Reckoning (IDR) project.

---

## 🚇 1. Scenario Overview & Operational Purpose

- **Scenario Title:** CASE 02 — LONG UNDERGROUND TUNNEL / UNDERPASS
- **Environment:** Subterranean Mountain Highway Tunnel (NH44 Chenani-Nashri Tunnel, Jammu-Srinagar Highway)
- **GNSS Outage Model:** Simulated subterranean blackout representing total satellite signal loss upon crossing the south portal entrance.
- **Navigation Engine:** **M028 Production Pipeline** (Locked Production Baseline)
- **Primary Operational Goal:** Demonstrate the operational concept of dead-reckoning trajectory tracking inside a long subterranean tunnel where satellite signals are completely blocked, and smooth re-acquisition upon portal exit.

---

## 🔄 2. State Machine Flow

```
[ OPEN HIGHWAY APPROACH ] (t < 30s) — GNSS ONLINE
      ↓
[ SOUTH PORTAL TUNNEL ENTRANCE ] (t = 30s) — Subterranean Blackout Start
      ↓
[ DEAD RECKONING MODE ] (30s <= t <= 270s)
      ↳ M028 Navigation Engine Active
      ↳ SpeedNet v2 (W=40) Neural Speed Estimation
      ↳ Raw Gyro Yaw Integration + Fixed 2D NHC (R_nhc = 0.04)
      ↳ 7-State EKF Velocity & Position Fusion
      ↳ M013 F4 Confidence-Gated Speed Bound
      ↳ M014 ZUPT Velocity Update (during mid-tunnel traffic stop: P(stat) > 0.70)
      ↳ M019 APM Speed Damping (delta_v = 0.50 m/s)
      ↳ M028 Zero-Latency IMU Jerk Gate (j_long < -1.00 m/s³)
      ↓
[ NORTH PORTAL TUNNEL EXIT ] (t = 270s) — Signal Reacquiring
      ↓
[ KALMAN RE-ALIGNMENT BRIDGE ] (270s <= t <= 275s)
      ↓
[ GNSS-AIDED NAVIGATION ] (t > 275s)
```

---

## 🗺️ 3. Map & Trajectory Data Sources

- **Geographic Location:** Chenani-Nashri Tunnel (NH44 Highway, `33.0030° N, 75.2420° E`).
- **Map Base:** OpenStreetMap (OSM) / CartoDB Dark Matter tile layer via Leaflet.js.
- **Trajectory Sourcing:**
  - **Ground Truth (Cyan):** Synchronized 10 Hz reference trajectory through the highway tunnel.
  - **M028 Production DR (Emerald Green):** Exact locked production M028 benchmark trajectory error curve (**27.35 m @ 60s**, **426.85 m @ 120s**, **218.93 m @ 300s**).
  - **Raw Inertial (Red Exploding):** Unconstrained double-integration baseline (**6,420 m drift @ 300s**).
  - **GNSS Restoration (Gold):** Smooth Kalman re-alignment bridge upon exiting the tunnel north portal.

---

## 🔬 4. Scientific Transparency & Disclosure

### What is REAL:
- The navigation engine algorithm and parameters are **100% real and strictly locked to M028**.
- The mathematical error trajectory of the IDR pipeline matches the canonical M028 locked research benchmark (**218.93 m @ 300s**).
- The map geometry represents a real, publicly identifiable subterranean highway tunnel (NH44 Chenani-Nashri Tunnel).

### What is SIMULATED:
- The GNSS blackout boundary ($t=30\text{s}$ to $t=270\text{s}$) is a **simulated operational scenario**, representing subterranean signal loss inside the tunnel vault.

### What this Demo PROVES:
- Demonstrates that when GNSS signals are completely lost inside a tunnel, the M028 IDR engine maintains smooth 2D trajectory estimation using onboard IMU signals.
- Demonstrates the live interaction of M028 subsystem states (SpeedNet, NHC, ZUPT stop detection during traffic queues, APM braking damping, IMU jerk gating).

### What this Demo DOES NOT PROVE:
- Does NOT claim that the M028 300-second benchmark (**218.93 m**) was measured inside this specific physical tunnel. These numbers are project-wide benchmark results.

---

## 🚀 5. How to Launch Case 02

### Option A: Local Python Web Server (Recommended)
Run:
```bash
python prototype-new/case2/server.py
```
*Starts local server at `http://localhost:8082` and automatically opens your web browser.*

### Option B: Open directly in Browser
Open `prototype-new/case2/index.html` directly in Chrome, Edge, or Firefox.

---

## 🔒 6. Provenance & Research Integrity

- **Case 1 Intact?** **YES** (`prototype-new/case1/` fully functional and accessible via header switcher).
- **Research Milestones Changed?** **NONE** (`M028.md` through `M052.md` untouched).
- **M053 Created?** **NO**.
- **M028 Retrained or Modified?** **NO**. Codebase remains 100% locked at M028.
