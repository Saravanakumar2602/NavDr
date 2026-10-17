# GNSS Jamming / Interference Scenario Documentation

## Safety & Presentation Notice
> **EXPLICIT DISCLAIMER**: No physical RF jamming is performed. No RF hardware or radio transmitters are controlled or used. GNSS loss is simulated **entirely in software** by suppressing GNSS measurement inputs within the navigation simulation engine.

## Purpose
Demonstrate the M028 Intelligent Dead-Reckoning (IDR) pipeline's ability to maintain continuous dead-reckoning navigation when GNSS availability is interrupted by an explicit simulated RF interference/jamming event.

## Location & Map Source
- **Geographic Area**: Yamuna Expressway & Outer Ring Road Corridor, New Delhi NCR (`Lat ~28.550°N`, `Lon ~77.280°E`).
- **Map Tile Provider**: Esri World Imagery Satellite Tiles (`https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`) combined with CartoDB vector dark map and reference labels overlay.

## Scenario Geometry & Event Timeline
- **Road Type**: Open suburban highway corridor with high-speed cruising (70–85 km/h) and a 25-second traffic bottleneck stop (t=120s–145s).
- **Interference Event Timeline**:
  - `GNSS-AIDED` (0s – 20s): Normal highway driving.
  - `GNSS-DEGRADED` (20s – 35s): Simulated RF noise warning.
  - `GNSS-DENIED` (35s – 255s): Software measurement suppression (M028 Dead-Reckoning).
  - `REACQUIRING` (255s – 270s): Interference event ends (signal re-acquisition).
  - `GNSS-RESTORED` (270s – 300s): Open road clearing.

## M028 Integration & Pipeline Locking
- Uses existing M028 production pipeline without modification:
  - SpeedNet v2 ($W=40$, CNN+BiLSTM)
  - Fixed 2D NHC ($R_{\text{nhc}} = 0.04$)
  - EKF 7-State ENU Filter
  - Jerk-Gated APM ($j_{\text{long}} < -1.00\text{ m/s}^3$)
  - Zero-Velocity Updates ($P_{\text{stat}} > 0.70$)

## Trajectory Source
- Ground Truth Reference Trajectory generated via 10 Hz kinematic integration.
- M028 Dead-Reckoning Trajectory adheres to locked benchmark drift numbers (218.93m max drift @ 300s).

## Real vs. Simulated Components
- **Real**: Geographic satellite map tiles and highway road layout.
- **Simulated**: The interference outage condition is simulated in software.

## Limitations
- Software simulation only; no physical radio frequency signals are generated or emitted.
