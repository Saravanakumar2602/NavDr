# Urban Canyon GNSS-Denied Scenario Documentation

## Purpose
Demonstrate the M028 Intelligent Dead-Reckoning (IDR) pipeline's ability to maintain high-accuracy vehicle positioning in high-density urban environments where GNSS signals suffer severe multipath degradation and satellite blockage from surrounding high-rise glass towers.

## Location & Map Source
- **Geographic Area**: DLF Cyber City Financial District & MG Road Corridor, Gurugram NCR (Lat ~28.495°N, Lon ~77.088°E).
- **Map Tile Provider**: Esri World Imagery Satellite Tiles (`https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}`) combined with CartoDB vector dark map and CartoDB reference labels overlay.

## Scenario Geometry & Visual Communication
- **Building Height**: 80m – 140m glass tower footprints flanking the street corridor.
- **Street Alignment**: 2.8 km urban avenue featuring 90-degree right and left street turns between skyscraper blocks.
- **Traffic Stop**: 25-second red light signal stop at urban intersection (t=120s–145s).

## GNSS Outage Model
The outage model transitions through 5 explicit states:
- `GNSS-AIDED` (0s – 20s): Open boulevard approach.
- `GNSS-DEGRADED` (20s – 40s): Skyscraper shadow entrance (multipath jitter).
- `GNSS-DENIED` (40s – 260s): Deep canyon blackout (M028 Dead-Reckoning).
- `REACQUIRING` (260s – 270s): Urban boundary exit (signal re-acquisition).
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
- **Real**: Geographic satellite map tiles, street geometry, and high-rise building footprints.
- **Simulated**: The satellite signal outage condition is simulated for demonstration purposes.

## Limitations
- Simulated multipath degradation; no claim is made that GNSS signals are physically lost on the public road in real life.
