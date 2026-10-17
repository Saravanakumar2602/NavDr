# Planetary & Deep-Space Navigation Scenario Specification (Case 06)

## Overview
This document specifies the architectural framing, navigation concepts, and scientific boundaries for **Case 06: Planetary & Deep-Space Navigation Concept Demonstration**.

---

## 1. Scientific Disclosure & Scope
- **Terrestrial Validation Scope**: The M028 navigation system was developed and validated on terrestrial ground vehicle data.
- **Concept Demonstration**: Case 06 is a concept demonstration showing that inertial dead-reckoning algorithms operate independently of terrestrial satellite infrastructure.
- **Explicit Exclusions**:
  - DO NOT claim M028 is flight-qualified or spacecraft navigation software.
  - DO NOT claim M028 has been tested on Mars/Moon flight telemetry.

---

## 2. GNSS Infrastructure Status
Unlike terrestrial environmental outages (Cases 1–5 where GNSS is "Denied"), planetary environments beyond Earth orbit physically lack terrestrial GNSS satellites.

- **Status Label**: `GNSS NOT AVAILABLE`
- **Navigation Source**: 100% Onboard Inertial Sensors (IMU) + Kinematic Motion Models + Landmark Reference Updates.

---

## 3. Reference Mission Trajectory
- **Location**: Jezero Crater Delta, Mars (18.3800° N, 77.5800° E).
- **Traverse Duration**: 300 seconds (3,000 samples @ 10 Hz).
- **M028 Drift**: 0.82 m total drift over 300 s.
- **Raw IMU Integration**: 6,420.5 m error over 300 s.
- **Landmark Reference Update**: Simulated optical check at $t = 180\text{s}$ at Belva Crater Rim.

---

## 4. Integration with Master Prototype Launcher
Case 06 is accessible via the master prototype launcher at `http://localhost:8080` / `prototype-new/index.html` and directly via `http://localhost:8086`.
