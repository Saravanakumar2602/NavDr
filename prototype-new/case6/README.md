# Showcase Case 06 — Planetary & Deep-Space Navigation (GNSS-Independent Concept Demonstration)

## 1. Purpose
Showcase Case 06 demonstrates the **core concept of GNSS-independent dead-reckoning navigation** in a planetary environment (Mars Jezero Crater) where terrestrial GNSS infrastructure is physically absent (`GNSS NOT AVAILABLE`).

The visual story follows the mission progression:
```
EARTH (GNSS Available) ➔ SPACECRAFT DEPARTURE ➔ DEEP SPACE TRANSIT ➔ MARS JEZERO ARRIVAL ➔ PLANETARY ROVER TRAVERSE
```

Key Scientific Message:
> *"Navigation does not fundamentally depend on GNSS. When GNSS is unavailable in deep space or on planetary bodies, autonomous inertial/dead-reckoning navigation can continue using onboard IMU measurements and motion models."*

---

## 2. Planetary Target & Environment
- **Target Body**: Mars (`Jezero Crater Delta Exploration Corridor`, 18.3800° N, 77.5800° E).
- **Environment**: Terrestrial GNSS is physically non-existent (`GNSS NOT AVAILABLE`).
- **Surface Dynamics**: Rover traverse across crater floor, delta deposits, and boulder fields with rock core sample extraction stop at $t = 120\text{s} - 145\text{s}$.

---

## 3. Data Sources & Scientific Framing
- **Surface Context**: Illustrative topographic surface layout based on NASA Jezero Crater orbital mapping data.
- **Reference Trajectory**: Simulated rover exploration mission trajectory across Jezero Delta.
- **Scientific Disclosure**:
  - The M028 production model was developed and validated strictly using **terrestrial vehicle datasets**.
  - M028 is used here as a **concept adapter** to demonstrate autonomous dead-reckoning principles.
  - **No claim is made that M028 is flight-qualified, spacecraft-ready, or experimentally validated on space/planetary flight data.**

---

## 4. Navigation Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    CASE 06 SCENARIO                     │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  M028 CONCEPT ADAPTER                   │
│   (Onboard IMU 100 Hz + Rover Kinematic NHC Dynamics)  │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│         AUTONOMOUS DEAD-RECKONING ESTIMATION            │
│       (Pos Drift: 0.82 m @ 300s vs 6,420 m Raw IMU)     │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│       OPTIONAL SIMULATED LANDMARK UPDATE (t=180s)       │
│  (Belva Crater Rim Optical Feature Check Bounded Reset) │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Summary of Real vs. Simulated Components
| Component | Real / Production | Simulated / Concept | Notes |
| :--- | :--- | :--- | :--- |
| **Dead-Reckoning Engine** | M028 Pipeline | Concept Adapter Layer | Production M028 code unchanged |
| **GNSS Status** | `GNSS NOT AVAILABLE` | Surface Environment | Differentiates planetary from outage |
| **Landmark Correction** | None (Raw DR) | Simulated @ t=180s | Clearly labelled simulated update |
| **Rover Kinematics** | Wheel NHC Model | Mars Gravity Adaptor | Plausible rover motion profile |

---

## 6. How to Run
```bash
python prototype-new/case6/server.py
```
Then open `http://localhost:8086` in any web browser.
