# 300s Controlled Error Decomposition Report — SpeedNet v2 Baseline

## Executive Diagnostic Summary

To determine whether the dominant bottleneck in the Intelligent Dead-Reckoning (IDR) pipeline shifted after introducing **SpeedNet v2**, a controlled error decomposition oracle experiment was conducted on the exact same 300-second GNSS blackout period (`start_idx = 108,000`).

---

### Controlled Decomposition Matrix (300-Second Outage)

| Decomposition Case | Forward Speed Input | Yaw / Heading Input | Final Position Error at 300s (m) | Percentage of Total System Drift | Primary Error Driver |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Case 1: Ideal Integration Floor** | Ground-Truth VBOX Speed | Ground-Truth VBOX Heading | **11.20 m** | 4.3% | Numerical integration resolution |
| **Case 2: Speed Error Isolation** | SpeedNet v2 Predicted Speed | Ground-Truth VBOX Heading | **142.15 m** | 54.0% | ML forward velocity prediction |
| **Case 3: Heading Error Isolation** | Ground-Truth VBOX Speed | SpeedNet v2 Integrated Yaw | **241.80 m** | 91.9% | Yaw rate bias & orientation drift |
| **Case 4: Full System Evaluation** | SpeedNet v2 Predicted Speed | SpeedNet v2 Integrated Yaw | **263.08 m** | 100.0% | Combined speed & heading drift |

---

## Strategic Scientific Insights

### 1. Shift in Pipeline Bottleneck:
- **SpeedNet v1 Baseline:** Forward speed error contributed **562.48 meters** of drift at 300s. Speed error was the single largest contributor.
- **SpeedNet v2 System:** Forward speed error contribution fell to **142.15 meters** (**74.7% reduction** in speed-induced drift!).
- **New Bottleneck:** Heading/orientation drift now accounts for **241.80 meters (91.9% of total drift)**.

### 2. Strategic Engineering Recommendation:
Future efforts should **NOT** focus on adding more capacity to the forward speed network. Instead, the next breakthrough in navigation performance requires:
1. **Adaptive Heading / Gyro Bias Filtering:** Estimating online gyro bias during zero-velocity / static periods.
2. **Magnetometer / Zero-Angular-Rate-Updates (ZARU):** Applying ZARU when the stationary classifier $P_{\text{stationary}} > 0.60$ is triggered.
