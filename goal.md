M028 baseline → reduce drift → real smartphone data → real-time Android/edge prototype → external software integration → robustness testing → final benchmark

① Get M029 working in the prototype
↓
② Make the Android app clean and real-time
↓
③ Export SpeedNet for on-device inference
↓
④ Add offline OSM map database
↓
⑤ Add map matching + kinematic constraints
↓
⑥ Bus test with real smartphone data
↓
⑦ Validate GNSS → IDR → GNSS transition
↓
⑧ Package the same core as an external-IMU edge engine





PHASE 1 — MAP
 ├─ 1A Real MapLibre                     ✅
 ├─ 1B Good cartographic style            🔄
 ├─ 1C Light/Dark                         ✅
 ├─ 1D Map controls                       🔄
 ├─ 1E Map style switcher                 ⏳
 └─ 1F Satellite                          ⏳

PHASE 2 — LOCATION
 ├─ 2A Real GNSS fix
 ├─ 2B Location update reliability
 ├─ 2C GPS jitter
 ├─ 2D Speed
 └─ 2E Heading

PHASE 3 — NAVIGATION UX
 ├─ 3A Smooth marker
 ├─ 3B Camera follow
 ├─ 3C Recenter
 ├─ 3D Route
 └─ 3E Navigation trajectory

PHASE 4 — NavDR
 ├─ 4A GNSS outage
 ├─ 4B M032 live
 ├─ 4C DR trajectory
 ├─ 4D Map matching
 └─ 4E Offline maps