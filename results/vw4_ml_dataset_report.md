# ML Dataset & Training Formulation Design Report — Vw4 Sequence

## Executive Summary

This report documents the scientific design, preprocessing pipeline, and tensor formulation of the Machine Learning dataset built from the **Vw04** sequence. 

The dataset is compiled into standardized binary format files (`data/ml_dataset/*.npz`), establishing an un-biased, leak-free benchmark for evaluating different AI architectures (XGBoost, 1D-CNN, BiLSTM, Transformers) against the baseline dead-reckoning and EKF models.

---

## 1. Input Features & Ground-Truth Label Specifications

### 1.1 Input Features (6 Channels)
Extracted from `S-Vw4.csv` and gravity-compensated:

| Channel Index | Signal Name | Source Column | Units | Physical Description |
| :---: | :--- | :--- | :---: | :--- |
| **0** | `ax_lin` | `ACCELEROMETER X` - `GRAVITY X` | $\text{m/s}^2$ | Linear acceleration along phone X-axis |
| **1** | `ay_lin` | `ACCELEROMETER Y` - `GRAVITY Y` | $\text{m/s}^2$ | Linear acceleration along phone Y-axis |
| **2** | `az_lin` | `ACCELEROMETER Z` - `GRAVITY Z` | $\text{m/s}^2$ | Linear acceleration along phone Z-axis |
| **3** | `gx` | `GYROSCOPE Roll (rad/s)` | $\text{rad/s}$ | Angular velocity around phone X-axis |
| **4** | `gy` | `GYROSCOPE Pitch (rad/s)` | $\text{rad/s}$ | Angular velocity around phone Y-axis |
| **5** | `gz` | `GYROSCOPE Yaw (rad/s)` | $\text{rad/s}$ | Angular velocity around phone Z-axis |

---

### 1.2 Supervised Output Targets (2 Channels)
Extracted from VBOX ground truth `V-Vw4.csv`:

| Channel Index | Target Variable | Source Column | Units | Physical Description |
| :---: | :--- | :--- | :---: | :--- |
| **0** | `v_fwd` | `Velocity (km/hr)` / 3.6 | $\text{m/s}$ | Ground-truth vehicle forward speed |
| **1** | `w_yaw` | `Yaw Rate (deg/sec)` $\times \frac{\pi}{180}$ | $\text{rad/s}$ | Ground-truth vehicle turning yaw rate |

---

## 2. Preprocessing & Data Hygiene Pipeline

### 2.1 10 Hz Time Grid Synchronization
- **Time Base:** UTC start time synchronized across smartphone and vehicle VBOX ($t_{\text{start}} = 44,127.004\text{ s}$ UTC).
- **Uniform Grid:** Resampled at a uniform $\Delta t = 0.100\text{ s}$ ($10.0\text{ Hz}$).
- **Total Synchronized Samples:** $N_{\text{total}} = 126,523\text{ samples}$ ($3.514\text{ hours}$ continuous driving).

### 2.2 Missing & Invalid Data Verification
- **NaN Check:** Verified **0 missing or NaN values** across all feature and target channels.

---

## 3. Sequential Train / Validation / Test Split (Preventing Data Leakage)

To prevent **temporal data leakage** (where adjacent IMU samples leak future memory into the training set), the data is partitioned sequentially into 3 contiguous chronological sequences:

```text
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                         TOTAL DATASET (126,523 SAMPLES)                     │
 └──────────────────────────────────────┬──────────────────────────────────────┘
                                        │
     ┌──────────────────────────────────┼──────────────────────────────────┐
     ▼                                  ▼                                  ▼
 TRAIN SET (70%)                 VAL SET (15%)                    TEST SET (15%)
 Samples: 0 to 88,566           Samples: 88,566 to 107,544       Samples: 107,544 to 126,523
 Duration: 147.6 minutes        Duration: 31.6 minutes           Duration: 31.6 minutes
```

---

## 4. Input Normalization Rules

To prevent data leakage from validation and test sets into model training:
* **Feature Means & Standard Deviations** are computed **EXCLUSIVELY on the Training Set**:
  $$\boldsymbol{\mu}_{\text{train}} = \begin{bmatrix} +0.2114, & -0.2679, & +0.0045, & +0.0005, & -0.0034, & +0.0000 \end{bmatrix}$$
  $$\boldsymbol{\sigma}_{\text{train}} = \begin{bmatrix} 2.5154, & 2.3219, & 1.2329, & 0.2334, & 0.3448, & 0.1504 \end{bmatrix}$$
* **Standardization Formula:** Applied to Train, Val, and Test inputs using training statistics:
  $$\mathbf{X}_{\text{norm}} = \frac{\mathbf{X}_{\text{raw}} - \boldsymbol{\mu}_{\text{train}}}{\boldsymbol{\sigma}_{\text{train}}}$$

---

## 5. Sliding Window Formulation & Trade-Off Analysis

Sliding windows are constructed with step size = 1 sample ($100\text{ ms}$ stride):

### Candidate Window Sizes Comparison Table

| Window Parameter | Window 1 ($W = 10$) | Window 2 ($W = 20$) | Window 3 ($W = 30$) |
| :--- | :---: | :---: | :---: |
| **Duration (seconds)** | **1.0 second** | **2.0 seconds** | **3.0 seconds** |
| **Samples per Window ($W$)** | 10 samples | 20 samples | 30 samples |
| **Input Tensor Shape** | $[N, 10, 6]$ | $[N, 20, 6]$ | $[N, 30, 6]$ |
| **Latency / Response Time** | **Fastest (100 ms)** | Medium (200 ms) | Slowest (300 ms) |
| **Vibration Memory** | Minimal | **Optimal** | Extensive |
| **Best Architectural Fit** | XGBoost / MLP / Shallow CNN | **1D-CNN + BiLSTM (SpeedNet)** | Recurrent / Transformers |

---

## 6. Final Tensor Shape Definitions & Datasets

### 6.1 Tensor Shape Formalism
* **Input Feature Tensor ($\mathbf{X}$):** $\mathbf{X} \in \mathbb{R}^{N \times W \times 6}$
  * $N$: Number of sliding windows in split.
  * $W$: Window length ($W \in \{10, 20, 30\}$).
  * $6$: Number of IMU channels (`[ax_lin, ay_lin, az_lin, gx, gy, gz]`).
* **Target Label Tensor ($\mathbf{Y}$):** $\mathbf{Y} \in \mathbb{R}^{N \times 2}$
  * $2$: Target variables (`[forward_velocity (m/s), yaw_rate (rad/s)]`).

---

### 6.2 Compiled Dataset Files Summary

All dataset files have been compiled and saved in `data/ml_dataset/`:

1. [`vw4_ml_dataset_w10.npz`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/data/ml_dataset/vw4_ml_dataset_w10.npz):
   * `X_train`: `[88557, 10, 6]` | `Y_train`: `[88557, 2]`
   * `X_val`: `[18969, 10, 6]` | `Y_val`: `[18969, 2]`
   * `X_test`: `[18970, 10, 6]` | `Y_test`: `[18970, 2]`

2. [`vw4_ml_dataset_w20.npz`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/data/ml_dataset/vw4_ml_dataset_w20.npz):
   * `X_train`: `[88547, 20, 6]` | `Y_train`: `[88547, 2]`
   * `X_val`: `[18959, 20, 6]` | `Y_val`: `[18959, 2]`
   * `X_test`: `[18960, 20, 6]` | `Y_test`: `[18960, 2]`

3. [`vw4_ml_dataset_w30.npz`](file:///c:/Saravanakumar%20G/Projects/SIH26/IO-VNBD-master/data/ml_dataset/vw4_ml_dataset_w30.npz):
   * `X_train`: `[88537, 30, 6]` | `Y_train`: `[88537, 2]`
   * `X_val`: `[18949, 30, 6]` | `Y_val`: `[18949, 2]`
   * `X_test`: `[18950, 30, 6]` | `Y_test`: `[18950, 2]`

---

## 7. Next Engineering Steps

With the ML dataset compiled into standardized tensors, we are ready to benchmark candidate architectures (Random Forest/XGBoost, 1D-CNN, BiLSTM, SpeedNet) under identical, leak-free conditions and evaluate them against our Calibrated DR ($619\text{ m}$ drift) and EKF baselines ($433\text{ m}$ drift).
