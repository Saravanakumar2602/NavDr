# Final Research Package — Intelligent Dead-Reckoning (IDR) Project

## Overview

This directory (`final_report/`) contains the complete, formal, self-contained research report package for the SIH 2026 Intelligent Dead-Reckoning (IDR) project on the Vw04 dataset sequence (`M001` through `M040`).

---

## Directory Structure

```
final_report/
├── README.md                                  <- Directory overview and navigation guide
├── BUILD_MANIFEST.md                          <- Package build manifest, counts, and verification
├── FIGURE_INDEX.md                            <- Master index of all 196 copied research figures
├── FINAL_RESEARCH_REPORT.md                   <- Comprehensive 20-section primary technical research report
├── FINAL_METHODOLOGY.md                       <- Full mathematical and pipeline methodology documentation
├── FINAL_RESULTS.md                           <- Master results table, benchmark evolution, and ablation breakdown
├── FINAL_CONCLUSIONS.md                       <- Summary of scientific discoveries and closed research branches
├── figures/                                   <- Complete figure archive (M001 to M040)
│   ├── benchmark_evolution_master.png         <- Master line chart of 300s benchmark evolution
│   ├── M001/                                  <- M001 EDA & Dataset Formulation figures (36 files)
│   ├── M002/                                  <- M002 ML Baselines figures (20 files)
│   ├── ...                                    <- Figures for all intermediate milestones
│   └── M040/                                  <- M040 Final Counterfactual Audit figures (1 file)
└── tables/                                    <- Master numerical tables and data exports
```

---

## Core Benchmark Provenance

- **Final Locked Benchmark:** **`218.93 m` @ 300s** ($27.35\text{ m}$ @ 60s, $426.85\text{ m}$ @ 120s).
- **Final Production Pipeline:** SpeedNet v2 ($W=40$) + Raw Gyro + Fixed NHC ($R_{\text{nhc}} = 0.04$) + M013 F4 Confidence-Gated Hard Constraint + M014 ZUPT F3 + M019 APM Speed Damping ($\delta v_{\max} = 0.50\text{ m/s}$) + M028 Jerk Gate ($j_{\text{long}} < -1.00\text{ m/s}^3$).
- **Final Milestone:** `M040` (Counterfactual Navigation Consistency Audit).
- **Status:** **Research Sequence Complete. Pipeline Permanently Frozen.** No further experiments or benchmark modifications were performed.
