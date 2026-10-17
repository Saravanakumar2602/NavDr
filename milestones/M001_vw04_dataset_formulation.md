# Milestone M001 — Vw04 Dataset Formulation & Exploratory Data Analysis

## 1. Date / Status
- **Date:** 2026-08-29
- **Status:** COMPLETE
- **Milestone Identifier:** `M001_vw04_dataset_formulation`

---

## 2. Starting Point
- **Context:** Initial formulation of the Intelligent Dead-Reckoning (IDR) pipeline for vehicle navigation during GNSS blackouts.
- **Raw Files Available:**
  - Smartphone IMU: `S-Vw4.csv` (Driver E, Sequence Vw04)
  - VBOX Ground Truth: `V-Vw4.csv` (Driver E, Sequence Vw04)
- **Starting Performance:** No existing baseline; raw sensor data contained timestamp offsets, non-aligned sampling rates, gravity acceleration components, and raw MEMS gyro biases.

---

## 3. Research Question
How can smartphone IMU sensors and high-precision VBOX GNSS/INS reference data be temporally synchronized and formatted into a zero-leakage, high-frequency (10 Hz) dataset suitable for machine learning dead-reckoning?

---

## 4. Hypothesis
Interpolating smartphone IMU and VBOX reference streams to a unified 10 Hz time grid while removing gravity vector components from raw accelerations will yield clean input features ($a_x, a_y, a_z, g_x, g_y, g_z$) and targets ($v_{\text{fwd}}, \omega_{\text{yaw}}$) for neural network training.

---

## 5. What We Changed / Built
- **Scripts Created:**
  - [`scripts/vw4_eda.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_eda.py) — Dataset synchronization, temporal alignment, and exploratory feature analysis.
  - [`scripts/vw4_ml_dataset.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_ml_dataset.py) — Pre-windowing dataset builder with standard scalar normalization.
- **Outputs Created:**
  - [`results/vw4_eda_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_eda_report.md)
  - [`results/vw4_ml_dataset_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_ml_dataset_report.md)

---

## 6. Experiment Methodology
- **Dataset:** Vw04 (Driver E, Volkswagen vehicle, urban/suburban route).
- **Sampling Frequency:** 10 Hz ($\Delta t = 0.1\text{ s}$).
- **Total Synchronized Samples:** $N = 126,505$ timesteps (~3.51 hours of driving).
- **Input Channels (6):**
  1. `ax_lin` — Linear longitudinal acceleration (gravity subtracted)
  2. `ay_lin` — Linear lateral acceleration (gravity subtracted)
  3. `az_lin` — Linear vertical acceleration (gravity subtracted)
  4. `gx` — Gyroscope roll rate ($\text{rad/s}$)
  5. `gy` — Gyroscope pitch rate ($\text{rad/s}$)
  6. `gz` — Gyroscope yaw rate ($\text{rad/s}$)
- **Target Labels (2):**
  1. `vbox_vel_ms` — Forward speed ($\text{m/s}$)
  2. `vbox_yaw_rate_rads` — Vehicle yaw rate ($\text{rad/s}$)
- **Partitioning (Chronological, Zero Temporal Leakage):**
  - **Train Partition (70%):** Indices `0` to `88,565` ($N_{\text{train}} = 88,566$)
  - **Validation Partition (15%):** Indices `88,566` to `107,534` ($N_{\text{val}} = 18,969$)
  - **Unseen Test Partition (15%):** Indices `108,000` to `126,504` ($N_{\text{test}} = 18,505$, starting at `start_idx = 108,000`)
- **Normalization Protocol:** Feature mean ($\mu_{\text{train}}$) and standard deviation ($\sigma_{\text{train}}$) computed strictly on training set ($[:88,566]$). Zero test data used in normalization.

---

## 7. Results

### Dataset Characteristic Metrics

| Metric / Feature | Value | Unit |
|---|---:|---|
| Total Synchronized Duration | 12,650.5 | seconds (~3.51 h) |
| Total Sample Count ($N$) | 126,505 | samples |
| Training Set Samples | 88,566 | samples (70%) |
| Validation Set Samples | 18,969 | samples (15%) |
| Unseen Test Set Samples | 18,505 | samples (15%) |
| Mean Forward Speed (Train) | 11.42 | m/s (~41.1 km/h) |
| Max Forward Speed (Train) | 31.85 | m/s (~114.7 km/h) |
| Stationary Percentage ($v < 0.1\text{ m/s}$) | 26.2% | % of total time |

---

## 8. Baseline Comparison (Baseline Provenance Lock)

| Configuration | 300s Result | Source |
|---|---:|---|
| Raw Open-Loop DR (Uncalibrated) | 6,420.0 m | `results/vw4_baseline_dr.md` |

- Open-loop integration of raw smartphone accelerometer/gyroscope without ML or constraints yields **6,420 m position error over a 300s outage** due to sensor bias quadratic integration.

---

## 9. Ablation / Diagnostic Findings
- **Gravity Vector Subtraction:** Raw accelerometer channels contain gravitational components ($~9.81\text{ m/s}^2$). Subtracting `GRAVITY Acceleration` columns from raw accelerometer channels reduced stationary acceleration drift by $>98\%$.
- **Timestamp Interpolation:** Linear interpolation (`interp1d`) to 10 Hz grid aligned smartphone UTC timestamps with VBOX ground truth without introducing temporal jitter.

---

## 10. What Failed
- **Raw Integration:** Integrating raw IMU accelerations without calibration led to rapid numerical explosion (position error $>1\text{ km}$ within 30 seconds). Open-loop integration without velocity constraint is unusable.

---

## 11. What We Learned

### Directly Measured Findings
1. Gravity vector subtraction is mandatory prior to ML input normalization.
2. The Vw04 dataset contains 26.2% stationary samples, making zero-speed detection a high-leverage optimization target.

### Strong Inference
- Chronological partitioning prevents temporal data leakage between training and testing.

### Hypothesis Requiring Further Validation
- Windowing IMU samples ($W \in [10, 50]$) will enable neural models to infer instantaneous forward speed despite accelerometer noise.

---

## 12. Artifact Inventory

### Scripts
- [`scripts/vw4_eda.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_eda.py) — Synchronization and EDA
- [`scripts/vw4_ml_dataset.py`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/scripts/vw4_ml_dataset.py) — Pre-windowing dataset generation

### Reports
- [`results/vw4_eda_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_eda_report.md) — Feature statistics report
- [`results/vw4_ml_dataset_report.md`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/results/vw4_ml_dataset_report.md) — Dataset formulation report

---

## 13. Current State After the Milestone
- **Current Best Configuration:** Baseline Open-Loop DR (6,420 m @ 300s).
- **Current Dataset:** Vw04 10 Hz synchronized ($N=126,505$).
- **Current Test Partition:** Unseen chronological test set (`start_idx = 108,000`).

---

## 14. Next Step Decision
- **What to do next:** Train baseline sequence models (MLP, 1D-CNN, LSTM, CNN+BiLSTM) on $W \in [10, 20, 30]$ to evaluate speed and yaw prediction MAE.
- **Why:** Establish neural feature learning baselines on the newly formulated dataset.
- **Target:** Speed MAE $<10\text{ km/h}$ on validation set.

---

## 15. Research Chain
- **Previous Milestone:** None (Project Initialization).
- **Current Milestone:** `M001_vw04_dataset_formulation`
- **Next Planned Milestone:** `M002_ml_baselines_training`
- **Summary:** Formulated the synchronized Vw04 dataset to provide zero-leakage training data for neural speed/yaw prediction models.
