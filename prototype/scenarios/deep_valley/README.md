# Deep Valley / Mountain Road GNSS-Denied Scenario Documentation

## Purpose
Demonstrate the M028 Intelligent Dead-Reckoning (IDR) pipeline's operation along a winding mountain highway (Solang Valley NH3 Highway) where GNSS satellite signals are obscured by surrounding Himalayan mountain ridges and steep valley walls.

## Location & Map Source
- **Geographic Area**: Solang Valley & Rohtang Pass Highway NH3, Manali, Himachal Pradesh, India (`Lat ~32.315°N`, `Lon ~77.175°E`).
- **Elevation**: Real topographic altitude profile climbing from 2,050m ASL up to 2,380m ASL at the mountain pass viewpoint.
- **Map Tile Provider**: Esri World Imagery Satellite Tiles (`https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`) combined with CartoDB vector dark map and reference labels overlay.

## Scenario Geometry & Curved Motion
- **Road Geometry**: Serpentine mountain pass road with continuous curved segments and a 180° double hairpin bend.
- **Mountain Stop**: 20-second mountain viewpoint avalanche checkpoint stop (t=125s–145s).

## GNSS Outage Model
The outage model transitions through 5 explicit states:
- `GNSS-AIDED` (0s – 20s): Open valley plateau approach.
- `GNSS-DEGRADED` (20s – 40s): Mountain ridge shadow entrance (horizon blockage).
- `GNSS-DENIED` (40s – 260s): Deep valley gorge blackout (M028 Dead-Reckoning).
- `REACQUIRING` (260s – 270s): Gorge boundary exit (signal re-acquisition).
- `GNSS-RESTORED` (270s – 300s): Open alpine plateau clearing.

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
- **Real**: Geographic satellite map tiles, mountain pass road geometry, and altitude readings.
- **Simulated**: The satellite signal outage condition is simulated for demonstration purposes.

## Limitations
- Simulated horizon blockage; no claim is made that GNSS signals are physically lost on the public road in real life.
