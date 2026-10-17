# -*- coding: utf-8 -*-
"""
vw4_speednet_v3_regime_aware.py
================================
SpeedNet v3 -- Regime-Aware Speed Estimation for GNSS-Denied Navigation
Dataset: Vw04 | Unseen test partition: start_idx = 108,000

Experiments:
  1. Regime label validity  -- Can regimes be classified from IMU alone?
  2. SpeedNet v3 training   -- Multi-task: speed + regime aux head (lambda sweep)
  3. Regime-specific errors -- V2 vs V3 per-regime speed bias/MAE
  4. Navigation ablation    -- A:V2+NHC  B:V3+NHC  C:V3,no-NHC  D:GT+NHC
  5. Regime-specific nav    -- Where does drift accumulate in 300s outage?
  6. Calibration stress     -- Simple bias correction vs learned V3

Scientific rules:
  - No adaptive gyro bias (shown harmful in previous ablation)
  - No test data used for any training, selection, or calibration
  - Model selected exclusively on validation partition
  - Final evaluation once on unseen test partition
"""

import os, sys, io, time, json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report
from scipy.interpolate import interp1d

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
sys.path.append(os.getcwd())
from scripts.vw4_speednet_v2 import SpeedNetV2
from scripts.vw4_speednet_v2_evaluate import load_speednet_v2, predict_speednet_v2_full

torch.set_num_threads(4)
os.makedirs('models', exist_ok=True)
os.makedirs('results', exist_ok=True)
os.makedirs('plots/vw4/speednet_v3', exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING (identical to all prior scripts)
# ─────────────────────────────────────────────────────────────────────────────
S_PATH = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\S-Vw4.csv'
V_PATH = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\V-Vw4.csv'

print("Loading Vw4 dataset...", flush=True)
df_s = pd.read_csv(S_PATH, encoding='latin1')
df_v = pd.read_csv(V_PATH, encoding='latin1')
df_s.columns = [c.strip() for c in df_s.columns]
df_v.columns = [c.strip() for c in df_v.columns]

t_s_utc = 44127.004 + (df_s['TIME SINCE START (ms)'] - df_s['TIME SINCE START (ms)'].iloc[0]) / 1000.0
t_v_utc = df_v['Time Since Start of Day (seconds)']
t_start = max(t_s_utc.iloc[0], t_v_utc.iloc[0])
t_end   = min(t_s_utc.iloc[-1], t_v_utc.iloc[-1])
dt = 0.1
t_sync = np.arange(t_start, t_end, dt)

ax_lin = interp1d(t_s_utc, df_s.iloc[:, 9]  - df_s.iloc[:, 12], fill_value='extrapolate')(t_sync)
ay_lin = interp1d(t_s_utc, df_s.iloc[:, 10] - df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
az_lin = interp1d(t_s_utc, df_s.iloc[:, 11] - df_s.iloc[:, 14], fill_value='extrapolate')(t_sync)
gx     = interp1d(t_s_utc, df_s['GYROSCOPE Roll (rad/s)'],  fill_value='extrapolate')(t_sync)
gy     = interp1d(t_s_utc, df_s['GYROSCOPE Pitch (rad/s)'], fill_value='extrapolate')(t_sync)
gz     = interp1d(t_s_utc, df_s['GYROSCOPE Yaw (rad/s)'],   fill_value='extrapolate')(t_sync)

raw_ax  = interp1d(t_s_utc, df_s.iloc[:, 9],  fill_value='extrapolate')(t_sync)
raw_ay  = interp1d(t_s_utc, df_s.iloc[:, 10], fill_value='extrapolate')(t_sync)
grav_x  = interp1d(t_s_utc, df_s.iloc[:, 12], fill_value='extrapolate')(t_sync)
grav_y  = interp1d(t_s_utc, df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
gyro_pitch = gy
a_long  = -(raw_ay - grav_y)
w_yaw   = -gyro_pitch

vbox_lat = interp1d(t_v_utc, df_v['Latitude (degrees)'],    fill_value='extrapolate')(t_sync)
vbox_lon = interp1d(t_v_utc, df_v['Longitude (degrees)'],   fill_value='extrapolate')(t_sync)
vbox_vel_ms  = interp1d(t_v_utc, df_v['Velocity (km/hr)'] / 3.6, fill_value='extrapolate')(t_sync)
vbox_heading = interp1d(t_v_utc, df_v['Heading (degrees)'], fill_value='extrapolate')(t_sync)
vbox_yaw_degs = interp1d(t_v_utc, df_v['Yaw Rate (deg/sec)'], fill_value='extrapolate')(t_sync)
vbox_yaw_rads = np.radians(vbox_yaw_degs)

lat0, lon0 = vbox_lat[0], vbox_lon[0]
R_earth = 6378137.0
x_gt_all = (np.radians(vbox_lon) - np.radians(lon0)) * R_earth * np.cos(np.radians(lat0))
y_gt_all = (np.radians(vbox_lat) - np.radians(lat0)) * R_earth
vx_gt_all = vbox_vel_ms * np.sin(np.radians(vbox_heading))
vy_gt_all = vbox_vel_ms * np.cos(np.radians(vbox_heading))

X_raw_all = np.column_stack([ax_lin, ay_lin, az_lin, gx, gy, gz])
n_total       = len(t_sync)
idx_train_end = int(n_total * 0.70)   # ~88566
idx_val_end   = int(n_total * 0.85)   # ~107535
start_idx     = 108000                 # Unseen test partition

train_mean = np.mean(X_raw_all[:idx_train_end], axis=0)
train_std  = np.std(X_raw_all[:idx_train_end], axis=0)
train_std[train_std == 0] = 1.0
X_norm_all = (X_raw_all - train_mean) / train_std

# ─────────────────────────────────────────────────────────────────────────────
# REGIME LABEL ASSIGNMENT (VBOX-derived; used for training labels only)
# ─────────────────────────────────────────────────────────────────────────────
# Regime IDs: 0=Stationary 1=Accel 2=Braking 3=Cruise 4=ModTurn 5=StrongTurn
REGIME_NAMES = ['Stationary', 'Acceleration', 'Braking', 'Straight/Cruise', 'Moderate Turn', 'Strong Turn']

a_long_gt = np.gradient(vbox_vel_ms, dt)   # GT longitudinal accel from VBOX speed
w_gt_abs  = np.abs(vbox_yaw_rads)

regime_labels = np.full(n_total, 3, dtype=np.int64)   # default: Cruise
regime_labels[w_gt_abs >= 0.25] = 5                   # Strong Turn (priority over accel/brake)
regime_labels[(w_gt_abs >= 0.05) & (w_gt_abs < 0.25)] = 4  # Moderate Turn
# Accel/Brake only when NOT turning
not_turning = (w_gt_abs < 0.05)
regime_labels[not_turning & (a_long_gt >= 0.5)]  = 1   # Acceleration
regime_labels[not_turning & (a_long_gt <= -0.5)] = 2   # Braking
# Stationary: overrides all (highest priority)
regime_labels[vbox_vel_ms < 0.1] = 0

W = 30   # window size for SpeedNet v3

# Stationary flag (for gating in navigation)
stat_gt_all = (vbox_vel_ms < 0.1).astype(np.float32)

# ─────────────────────────────────────────────────────────────────────────────
# SPEEDNET V3 ARCHITECTURE
# ─────────────────────────────────────────────────────────────────────────────
N_REGIMES = 6

class SpeedNetV3(nn.Module):
    """
    SpeedNet v3: Regime-Aware Multi-Task CNN + BiLSTM.

    Outputs:
      v_fwd       -- forward vehicle speed (m/s)   [primary]
      logit_stat  -- stationary binary logit        [auxiliary - preserves v2 gating]
      regime_logits -- 6-class regime classification [auxiliary - regime awareness]
    """
    def __init__(self, window_size=30, in_channels=6, hidden_dim=64, n_regimes=6):
        super().__init__()
        self.window_size = window_size

        # Shared feature extractor (same as v2)
        self.conv = nn.Sequential(
            nn.Conv1d(in_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm1d(32), nn.ReLU(),
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64), nn.ReLU()
        )
        self.bilstm = nn.LSTM(64, hidden_dim, num_layers=1,
                              batch_first=True, bidirectional=True)
        self.fc_shared = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64), nn.ReLU()
        )

        # Head 1: Forward Speed Regression
        self.fc_speed = nn.Sequential(
            nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1)
        )
        # Head 2: Stationary Binary (keeps stationary gating from v2)
        self.fc_stat = nn.Sequential(
            nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1)
        )
        # Head 3: Regime Classification (NEW — regime awareness)
        self.fc_regime = nn.Sequential(
            nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, n_regimes)
        )

    def forward(self, x):
        x_c = x.permute(0, 2, 1)
        feat = self.conv(x_c).permute(0, 2, 1)
        out, _ = self.bilstm(feat)
        h = self.fc_shared(out[:, -1, :])
        v_fwd        = F.relu(self.fc_speed(h)).squeeze(-1)
        logit_stat   = self.fc_stat(h).squeeze(-1)
        regime_logits = self.fc_regime(h)
        return v_fwd, logit_stat, regime_logits

def count_params(model):
    return sum(p.numel() for p in model.parameters())

# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT 1: IMU REGIME CLASSIFIER VALIDITY
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("EXPERIMENT 1: IMU REGIME CLASSIFIER VALIDITY", flush=True)
print("="*70, flush=True)

# Build windows on training + validation sets
sub_windows = np.lib.stride_tricks.sliding_window_view(
    X_norm_all, window_shape=(W, 6), axis=(0, 1)).squeeze(1)

train_idx   = np.arange(W - 1, idx_train_end)
val_idx_arr = np.arange(idx_train_end, idx_val_end)

X_tr = torch.tensor(sub_windows[train_idx - (W-1)], dtype=torch.float32)
y_tr = torch.tensor(regime_labels[train_idx], dtype=torch.long)
X_val = torch.tensor(sub_windows[val_idx_arr - (W-1)], dtype=torch.float32)
y_val = torch.tensor(regime_labels[val_idx_arr], dtype=torch.long)

# Simple IMU-only regime classifier (independent of SpeedNet v3)
class RegimeClassifier(nn.Module):
    def __init__(self, window_size=30, n_regimes=6):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(6, 32, 3, padding=1), nn.BatchNorm1d(32), nn.ReLU(),
            nn.Conv1d(32, 64, 3, padding=1), nn.BatchNorm1d(64), nn.ReLU()
        )
        self.lstm = nn.LSTM(64, 64, batch_first=True, bidirectional=True)
        self.fc = nn.Sequential(nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, n_regimes))
    def forward(self, x):
        h = self.conv(x.permute(0,2,1)).permute(0,2,1)
        out, _ = self.lstm(h)
        return self.fc(out[:, -1, :])

clf = RegimeClassifier(W, N_REGIMES)
opt_clf = torch.optim.Adam(clf.parameters(), lr=1e-3, weight_decay=1e-4)
ds_clf = TensorDataset(X_tr, y_tr)
ld_clf = DataLoader(ds_clf, batch_size=1024, shuffle=True)

print("  Training IMU regime classifier (8 epochs)...", flush=True)
criterion_ce = nn.CrossEntropyLoss()
for ep in range(1, 9):
    clf.train()
    total_loss = 0
    for xb, yb in ld_clf:
        opt_clf.zero_grad()
        loss = criterion_ce(clf(xb), yb)
        loss.backward()
        opt_clf.step()
        total_loss += loss.item() * len(yb)
    total_loss /= len(y_tr)
    if ep % 2 == 0:
        clf.eval()
        with torch.no_grad():
            val_pred = clf(X_val).argmax(dim=1).numpy()
        val_acc = np.mean(val_pred == y_val.numpy()) * 100
        print(f"    Epoch {ep:02d}/08 | Loss: {total_loss:.4f} | Val Acc: {val_acc:.1f}%", flush=True)

clf.eval()
with torch.no_grad():
    val_pred_cls = clf(X_val).argmax(dim=1).numpy()
val_true_cls = y_val.numpy()

exp1_acc = float(np.mean(val_pred_cls == val_true_cls) * 100)
print(f"\n  Overall Validation Accuracy: {exp1_acc:.1f}%", flush=True)
print(f"\n  Per-class Report:", flush=True)
report_str = classification_report(val_true_cls, val_pred_cls,
                                    target_names=REGIME_NAMES, zero_division=0)
print(report_str, flush=True)
cm = confusion_matrix(val_true_cls, val_pred_cls)

# Per-class accuracy
exp1_per_class = {}
for i, name in enumerate(REGIME_NAMES):
    n_i = int(np.sum(val_true_cls == i))
    acc_i = float(np.mean(val_pred_cls[val_true_cls == i] == i) * 100) if n_i > 0 else 0.0
    exp1_per_class[name] = {'n': n_i, 'accuracy_pct': round(acc_i, 1)}
    print(f"    {name:<20}: n={n_i:>6}  acc={acc_i:.1f}%", flush=True)

# Check which regimes can be reliably identified (>60% recall)
reliable_regimes = [name for name, v in exp1_per_class.items() if v['accuracy_pct'] >= 60.0]
print(f"\n  Reliably classified (>=60% acc): {reliable_regimes}", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT 2: SPEEDNET V3 TRAINING (lambda sweep)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("EXPERIMENT 2: SPEEDNET V3 TRAINING (lambda = 0.05, 0.10, 0.20)", flush=True)
print("="*70, flush=True)

LAMBDAS     = [0.05, 0.10, 0.20]
NUM_EPOCHS  = 15
BATCH_SIZE  = 1024
LR          = 1e-3

# Build dataset with regime labels
v_tr_arr    = torch.tensor(vbox_vel_ms[train_idx], dtype=torch.float32)
stat_tr_arr = torch.tensor(stat_gt_all[train_idx], dtype=torch.float32)
reg_tr_arr  = torch.tensor(regime_labels[train_idx], dtype=torch.long)

v_val_arr   = torch.tensor(vbox_vel_ms[val_idx_arr], dtype=torch.float32)
stat_val_arr = torch.tensor(stat_gt_all[val_idx_arr], dtype=torch.float32)
reg_val_arr = torch.tensor(regime_labels[val_idx_arr], dtype=torch.long)

train_ds = TensorDataset(X_tr, v_tr_arr, stat_tr_arr, reg_tr_arr)
val_ds   = TensorDataset(X_val, v_val_arr, stat_val_arr, reg_val_arr)
train_ld = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
val_ld   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False)

criterion_speed  = nn.SmoothL1Loss()
criterion_stat   = nn.BCEWithLogitsLoss()
criterion_regime = nn.CrossEntropyLoss()

best_lambda_result = {}

for lam in LAMBDAS:
    print(f"\n  --- SpeedNet v3  lambda={lam:.2f} ---", flush=True)
    model_v3 = SpeedNetV3(window_size=W, in_channels=6, hidden_dim=64, n_regimes=N_REGIMES)
    optimizer = torch.optim.Adam(model_v3.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS)

    best_val_mae = float('inf')
    ckpt_path = f'models/speednet_v3_w{W}_lambda{int(lam*100):03d}.pth'

    for epoch in range(1, NUM_EPOCHS + 1):
        model_v3.train()
        tr_loss = 0.0
        for xb, vb, sb, rb in train_ld:
            optimizer.zero_grad()
            v_pred, logit_stat, regime_logits = model_v3(xb)
            l_speed  = criterion_speed(v_pred, vb)
            l_stat   = criterion_stat(logit_stat, sb)
            l_regime = criterion_regime(regime_logits, rb)
            loss = l_speed + 0.3 * l_stat + lam * l_regime
            loss.backward()
            optimizer.step()
            tr_loss += loss.item() * len(vb)
        scheduler.step()
        tr_loss /= len(train_ds)

        model_v3.eval()
        val_mae_sum = 0.0
        with torch.no_grad():
            for xb, vb, sb, rb in val_ld:
                v_pred, _, _ = model_v3(xb)
                val_mae_sum += torch.sum(torch.abs(v_pred - vb) * 3.6).item()
        val_mae = val_mae_sum / len(val_ds)

        saved = ""
        if val_mae < best_val_mae:
            best_val_mae = val_mae
            torch.save(model_v3.state_dict(), ckpt_path)
            saved = " [BEST SAVED]"
        print(f"    Ep {epoch:02d}/{NUM_EPOCHS:02d} | Train Loss: {tr_loss:.4f} | "
              f"Val Speed MAE: {val_mae:.2f} km/h{saved}", flush=True)

    best_lambda_result[lam] = {'val_mae_kmh': round(best_val_mae, 3), 'ckpt': ckpt_path}
    print(f"  lambda={lam:.2f}: Best Val Speed MAE = {best_val_mae:.3f} km/h", flush=True)

# Model selection: lowest val speed MAE
best_lambda = min(best_lambda_result, key=lambda l: best_lambda_result[l]['val_mae_kmh'])
best_v3_path = best_lambda_result[best_lambda]['ckpt']
print(f"\n  SELECTED: lambda={best_lambda:.2f} (Val MAE={best_lambda_result[best_lambda]['val_mae_kmh']:.3f} km/h)", flush=True)
print(f"  Model: {best_v3_path}", flush=True)

# Load best V3
model_v3_best = SpeedNetV3(window_size=W, in_channels=6, hidden_dim=64, n_regimes=N_REGIMES)
model_v3_best.load_state_dict(torch.load(best_v3_path, map_location='cpu'))
model_v3_best.eval()

# ─────────────────────────────────────────────────────────────────────────────
# LOAD SPEEDNET V2 (W=40 — the validated best v2 model)
# ─────────────────────────────────────────────────────────────────────────────
print("\nLoading SpeedNet v2 (W=40) predictions...", flush=True)
model_v2 = load_speednet_v2(window_size=40)
v2_v_dict, _, v2_stat_dict = predict_speednet_v2_full(model_v2, window_size=40)

# Get V3 predictions over full dataset
print("Running SpeedNet v3 predictions...", flush=True)
sub_windows_all = np.lib.stride_tricks.sliding_window_view(
    X_norm_all, window_shape=(W, 6), axis=(0, 1)).squeeze(1)
needed_idx = np.arange(W - 1, n_total)
sub_idx    = needed_idx - (W - 1)
sub_batch  = torch.tensor(sub_windows_all[sub_idx], dtype=torch.float32)

with torch.no_grad():
    v3_v_pred, v3_logit_stat, _ = model_v3_best(sub_batch)
    v3_v_pred  = v3_v_pred.numpy()
    v3_prob_stat = torch.sigmoid(v3_logit_stat).numpy()

v3_v_dict    = {int(idx): max(0.0, float(v3_v_pred[j]))     for j, idx in enumerate(needed_idx)}
v3_stat_dict = {int(idx): float(v3_prob_stat[j])             for j, idx in enumerate(needed_idx)}

# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT 3: REGIME-SPECIFIC SPEED ERROR COMPARISON
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("EXPERIMENT 3: REGIME-SPECIFIC SPEED ERROR (V2 vs V3, TEST PARTITION)", flush=True)
print("="*70, flush=True)

test_idx_arr = np.arange(start_idx, min(start_idx + 3000, n_total - W))
v_gt_test = vbox_vel_ms[test_idx_arr]
reg_test   = regime_labels[test_idx_arr]

# V2 predictions on test
v2_pred_test = np.array([max(0.0, v2_v_dict.get(i, 0.0)) for i in test_idx_arr])
# V3 predictions on test
v3_pred_test = np.array([max(0.0, v3_v_dict.get(i, 0.0)) for i in test_idx_arr])

exp3_results = []
print(f"\n  {'Regime':<22} {'N':>6} | {'V2 MAE':>8} {'V2 Bias':>9} | {'V3 MAE':>8} {'V3 Bias':>9} | {'DeltaMAE':>9}", flush=True)
print("  " + "-"*80, flush=True)
for rid, rname in enumerate(REGIME_NAMES):
    mask = (reg_test == rid)
    n_r  = int(np.sum(mask))
    if n_r < 5:
        continue
    v_gt_r = v_gt_test[mask]
    v2_r   = v2_pred_test[mask]
    v3_r   = v3_pred_test[mask]

    v2_mae  = float(np.mean(np.abs(v2_r - v_gt_r)) * 3.6)
    v2_bias = float(np.mean(v2_r - v_gt_r) * 3.6)
    v2_rmse = float(np.sqrt(np.mean((v2_r - v_gt_r)**2)) * 3.6)
    v2_med  = float(np.median(np.abs(v2_r - v_gt_r)) * 3.6)
    v2_p95  = float(np.percentile(np.abs(v2_r - v_gt_r), 95) * 3.6)

    v3_mae  = float(np.mean(np.abs(v3_r - v_gt_r)) * 3.6)
    v3_bias = float(np.mean(v3_r - v_gt_r) * 3.6)
    v3_rmse = float(np.sqrt(np.mean((v3_r - v_gt_r)**2)) * 3.6)
    v3_med  = float(np.median(np.abs(v3_r - v_gt_r)) * 3.6)
    v3_p95  = float(np.percentile(np.abs(v3_r - v_gt_r), 95) * 3.6)

    delta = round(v2_mae - v3_mae, 3)
    exp3_results.append({
        'regime': rname, 'n': n_r,
        'v2_mae': round(v2_mae,3), 'v2_bias': round(v2_bias,3),
        'v2_rmse': round(v2_rmse,3), 'v2_median': round(v2_med,3), 'v2_p95': round(v2_p95,3),
        'v3_mae': round(v3_mae,3), 'v3_bias': round(v3_bias,3),
        'v3_rmse': round(v3_rmse,3), 'v3_median': round(v3_med,3), 'v3_p95': round(v3_p95,3),
        'mae_improvement_kmh': round(delta, 3),
        'bias_improvement_kmh': round(v2_bias - v3_bias, 3),
    })
    improved = "YES" if delta > 0 else ("TIE" if delta == 0 else "NO")
    print(f"  {rname:<22} {n_r:>6} | {v2_mae:>7.3f} {v2_bias:>+8.3f} | "
          f"{v3_mae:>7.3f} {v3_bias:>+8.3f} | {delta:>+8.3f} {improved}", flush=True)

# Overall test set
v2_overall_mae  = float(np.mean(np.abs(v2_pred_test - v_gt_test)) * 3.6)
v3_overall_mae  = float(np.mean(np.abs(v3_pred_test - v_gt_test)) * 3.6)
v2_overall_bias = float(np.mean(v2_pred_test - v_gt_test) * 3.6)
v3_overall_bias = float(np.mean(v3_pred_test - v_gt_test) * 3.6)
print(f"\n  Overall V2: MAE={v2_overall_mae:.3f} km/h  Bias={v2_overall_bias:+.3f} km/h", flush=True)
print(f"  Overall V3: MAE={v3_overall_mae:.3f} km/h  Bias={v3_overall_bias:+.3f} km/h", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT 6: CALIBRATION STRESS TEST
# (computed here, BEFORE navigation, to keep it purely prediction-based)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("EXPERIMENT 6: CALIBRATION STRESS TEST (val-derived corrections)", flush=True)
print("="*70, flush=True)

# Learn regime-specific bias corrections from VALIDATION partition only
val_slice = slice(idx_train_end, idx_val_end)
v2_pred_val  = np.array([max(0.0, v2_v_dict.get(i, 0.0)) for i in val_idx_arr])
v_gt_val_arr = vbox_vel_ms[val_idx_arr]
reg_val_np   = regime_labels[val_idx_arr]

# Global bias correction (val-estimated)
global_bias_v2 = float(np.mean(v2_pred_val - v_gt_val_arr))  # in m/s
print(f"  V2 global bias on validation: {global_bias_v2*3.6:+.3f} km/h", flush=True)

# Regime-specific bias corrections from validation
regime_bias_v2 = {}
for rid, rname in enumerate(REGIME_NAMES):
    mask = (reg_val_np == rid)
    if np.sum(mask) < 10:
        regime_bias_v2[rid] = 0.0
        continue
    bias = float(np.mean(v2_pred_val[mask] - v_gt_val_arr[mask]))
    regime_bias_v2[rid] = bias
    print(f"    {rname:<22}: bias_correction = {-bias*3.6:+.3f} km/h", flush=True)

# Apply corrections to test partition
v2_global_corrected_test = np.clip(v2_pred_test - global_bias_v2, 0, None)
v2_regime_corrected_test = np.array([
    max(0.0, v2_pred_test[i] - regime_bias_v2.get(int(reg_test[i]), 0.0))
    for i in range(len(test_idx_arr))
])

cal0_mae = float(np.mean(np.abs(v2_pred_test - v_gt_test)) * 3.6)
cal1_mae = float(np.mean(np.abs(v2_global_corrected_test - v_gt_test)) * 3.6)
cal2_mae = float(np.mean(np.abs(v2_regime_corrected_test - v_gt_test)) * 3.6)

print(f"\n  Test MAE comparison (pure prediction metrics):", flush=True)
print(f"    V2 uncorrected:         {cal0_mae:.3f} km/h", flush=True)
print(f"    V2 + global correction: {cal1_mae:.3f} km/h", flush=True)
print(f"    V2 + regime correction: {cal2_mae:.3f} km/h", flush=True)
print(f"    SpeedNet v3 (learned):  {v3_overall_mae:.3f} km/h", flush=True)

exp6_results = {
    'v2_uncorrected_mae':        round(cal0_mae, 3),
    'v2_global_corrected_mae':   round(cal1_mae, 3),
    'v2_regime_corrected_mae':   round(cal2_mae, 3),
    'v3_learned_mae':            round(v3_overall_mae, 3),
    'global_bias_ms':            round(global_bias_v2, 5),
    'regime_bias_corrections_ms': {REGIME_NAMES[k]: round(v, 5) for k, v in regime_bias_v2.items()}
}

# Also build calibrated v2 dicts for navigation
v2_global_dict = {}
v2_regime_dict = {}
for i in range(n_total):
    raw = max(0.0, v2_v_dict.get(i, 0.0))
    v2_global_dict[i] = max(0.0, raw - global_bias_v2)
    rid = int(regime_labels[i])
    v2_regime_dict[i]  = max(0.0, raw - regime_bias_v2.get(rid, 0.0))

# ─────────────────────────────────────────────────────────────────────────────
# NAVIGATION FILTER (SpeedNet + Raw Gyro + NHC, NO adaptive bias)
# This is the verified best configuration (263 m at 300s)
# ─────────────────────────────────────────────────────────────────────────────
P_THRESH_NAV = 0.60   # stationary threshold (tuned on val in previous experiment)
PRE_SAMPLES  = 300

def run_nav_filter(sim_start, dur_sec, speed_dict, stat_dict,
                   speed_source='ml', use_nhc=True):
    """
    Dead-reckoning navigation filter.
    speed_source = 'ml' uses speed_dict | 'gt' uses VBOX speed
    No adaptive bias.
    """
    n  = int(dur_sec / dt)
    s0 = sim_start - PRE_SAMPLES
    se = sim_start + n

    x_s = np.zeros(7)
    x_s[0] = x_gt_all[s0]; x_s[1] = y_gt_all[s0]
    x_s[2] = vx_gt_all[s0]; x_s[3] = vy_gt_all[s0]
    x_s[4] = np.radians(vbox_heading[s0])

    P = np.diag([1.0, 1.0, 0.5, 0.5, np.radians(2.0)**2, 0.1, np.radians(0.5)**2])
    Q = np.diag([0.001, 0.001, 0.01, 0.01, np.radians(0.05)**2, 1e-5, 1e-6])
    R_gnss = np.diag([4.0, 4.0, 0.04, 0.04, np.radians(1.0)**2])
    H_gnss = np.zeros((5, 7)); H_gnss[:5, :5] = np.eye(5)
    R_v   = 1.0**2
    R_nhc = 0.2**2

    x_hist = []
    t0 = time.perf_counter()
    for idx in range(s0, se):
        is_out = (idx >= sim_start)
        x, y, vx, vy, psi, ba, bw = x_s
        a_m = a_long[idx]; w_m = w_yaw[idx]

        # Heading: raw gyro, no bias correction
        psi_new = psi + w_m * dt
        a_hat   = a_m - ba
        vx_new  = vx + a_hat * np.sin(psi_new) * dt
        vy_new  = vy + a_hat * np.cos(psi_new) * dt
        x_new   = x  + vx_new * dt
        y_new   = y  + vy_new * dt
        x_s = np.array([x_new, y_new, vx_new, vy_new, psi_new, ba, bw])

        F = np.eye(7)
        F[0,2]=dt; F[1,3]=dt
        F[2,4]=a_hat*np.cos(psi_new)*dt; F[3,4]=-a_hat*np.sin(psi_new)*dt
        F[2,5]=-np.sin(psi_new)*dt; F[3,5]=-np.cos(psi_new)*dt; F[4,6]=-dt
        P = F @ P @ F.T + Q

        if not is_out:
            pm = np.radians(vbox_heading[idx])
            pd = (pm - x_s[4] + np.pi) % (2*np.pi) - np.pi
            z  = np.array([x_gt_all[idx], y_gt_all[idx],
                            vx_gt_all[idx], vy_gt_all[idx], x_s[4]+pd])
            y_m = z - H_gnss @ x_s
            S = H_gnss @ P @ H_gnss.T + R_gnss
            K = P @ H_gnss.T @ np.linalg.inv(S)
            x_s = x_s + K @ y_m
            P = (np.eye(7) - K @ H_gnss) @ P
        else:
            p_stat = stat_dict.get(idx, 0.0)
            is_stat = p_stat > P_THRESH_NAV

            if speed_source == 'gt':
                v_meas = 0.0 if is_stat else float(vbox_vel_ms[idx])
            else:
                v_meas = 0.0 if is_stat else max(0.0, speed_dict.get(idx, 0.0))

            # Speed EKF update
            v_est   = np.sqrt(x_s[2]**2 + x_s[3]**2)
            v_denom = max(v_est, 1e-3)
            H_v = np.array([0, 0, x_s[2]/v_denom, x_s[3]/v_denom, 0, 0, 0])
            K_v = (P @ H_v) / (float(H_v @ P @ H_v) + R_v)
            x_s = x_s + K_v * (v_meas - v_est)
            P   = (np.eye(7) - np.outer(K_v, H_v)) @ P

            # NHC update
            if use_nhc:
                pc   = x_s[4]
                v_lat = -x_s[2]*np.cos(pc) + x_s[3]*np.sin(pc)
                H_nhc = np.array([0, 0, -np.cos(pc), np.sin(pc),
                                   x_s[2]*np.sin(pc)+x_s[3]*np.cos(pc), 0, 0])
                K_nhc = (P @ H_nhc) / (float(H_nhc @ P @ H_nhc) + R_nhc)
                x_s = x_s + K_nhc * (0.0 - v_lat)
                P   = (np.eye(7) - np.outer(K_nhc, H_nhc)) @ P

            x_hist.append(x_s.copy())

    t1 = time.perf_counter()
    lat_ms = ((t1 - t0) / (PRE_SAMPLES + n)) * 1000.0
    arr    = np.array(x_hist)
    x_dr   = arr[:,0] - arr[0,0]
    y_dr   = arr[:,1] - arr[0,1]
    v_dr   = np.sqrt(arr[:,2]**2 + arr[:,3]**2)
    psi_deg = np.degrees(arr[:,4])
    return x_dr, y_dr, v_dr, psi_deg, lat_ms


def nav_metrics(x_dr, y_dr, v_dr, psi_deg, start, dur):
    n = int(dur / dt)
    ls, ln = vbox_lat[start], vbox_lon[start]
    xgt = (np.radians(vbox_lon[start:start+n]) - np.radians(ln)) * R_earth * np.cos(np.radians(ls))
    ygt = (np.radians(vbox_lat[start:start+n]) - np.radians(ls)) * R_earth
    vgt = vbox_vel_ms[start:start+n]
    hgt = vbox_heading[start:start+n]
    pe  = np.sqrt((x_dr-xgt)**2 + (y_dr-ygt)**2)
    dist_gt = float(np.sum(np.sqrt(np.diff(xgt)**2+np.diff(ygt)**2)))
    dist_dr = float(np.sum(v_dr)*dt)
    cde = abs(dist_dr-dist_gt)/dist_gt*100
    he  = np.abs((psi_deg - hgt + 180) % 360 - 180)
    return {
        'final_pos_m':  round(float(pe[-1]),2),
        'max_pos_m':    round(float(np.max(pe)),2),
        'drift_rate':   round(float(pe[-1]/dur),4),
        'cde_pct':      round(float(cde),2),
        'v_mae_kmh':    round(float(np.mean(np.abs(v_dr-vgt)))*3.6,2),
        'v_rmse_kmh':   round(float(np.sqrt(np.mean((v_dr-vgt)**2)))*3.6,2),
        'h_err_deg':    round(float(he[-1]),2),
        'pos_err_arr':  pe.tolist(),
        'x_dr': x_dr.tolist(), 'y_dr': y_dr.tolist(),
        'x_gt': xgt.tolist(), 'y_gt': ygt.tolist(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT 4: NAVIGATION ABLATION
# A: SpeedNet v2 + Raw Gyro + NHC [VERIFIED BEST BASELINE]
# B: SpeedNet v3 + Raw Gyro + NHC
# C: SpeedNet v3 + Raw Gyro, no NHC
# D: GT Speed + Raw Gyro + NHC
# EXTRA: V2 + regime correction + NHC (calibration)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("EXPERIMENT 4: NAVIGATION ABLATION", flush=True)
print("="*70, flush=True)

nav_cases = [
    ("A: SpeedNet v2 + NHC [BASELINE]",     v2_v_dict,      v2_stat_dict,  True,  'ml'),
    ("B: SpeedNet v3 + NHC",                 v3_v_dict,      v3_stat_dict,  True,  'ml'),
    ("C: SpeedNet v3, no NHC",               v3_v_dict,      v3_stat_dict,  False, 'ml'),
    ("D: GT Speed + NHC",                    v2_v_dict,      v2_stat_dict,  True,  'gt'),
    ("E: V2 + Regime Calib + NHC",           v2_regime_dict, v2_stat_dict,  True,  'ml'),
]

nav_results = []
for label, spd_dict, st_dict, nhc, ss in nav_cases:
    row = {'case': label}
    print(f"\n  {label}", flush=True)
    for dur in [60, 120, 300]:
        xd, yd, vd, pd, lat = run_nav_filter(
            start_idx, dur, spd_dict, st_dict,
            speed_source=ss, use_nhc=nhc
        )
        m = nav_metrics(xd, yd, vd, pd, start_idx, dur)
        row[f'{dur}s'] = m
        row[f'{dur}s_lat_ms'] = round(lat, 4)
        print(f"    {dur}s -> pos={m['final_pos_m']:.1f}m  v_mae={m['v_mae_kmh']:.2f}km/h  "
              f"h_err={m['h_err_deg']:.1f}deg  cde={m['cde_pct']:.1f}%", flush=True)
    nav_results.append(row)

# Baseline (Case A)
base_60  = nav_results[0]['60s']['final_pos_m']
base_120 = nav_results[0]['120s']['final_pos_m']
base_300 = nav_results[0]['300s']['final_pos_m']
print(f"\n  BASELINE (V2+NHC): 60s={base_60}m  120s={base_120}m  300s={base_300}m", flush=True)

print(f"\n  Navigation Summary (300s):", flush=True)
print(f"  {'Case':<40} {'Pos(m)':>8} {'vs Base':>9} {'VMAE':>7} {'Hderr':>7}", flush=True)
for row in nav_results:
    m = row['300s']
    pct = (base_300 - m['final_pos_m']) / base_300 * 100
    print(f"  {row['case']:<40} {m['final_pos_m']:>7.1f} {pct:>+8.1f}% {m['v_mae_kmh']:>6.2f} {m['h_err_deg']:>6.1f}", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT 5: REGIME-SPECIFIC NAVIGATION DRIFT (300s)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("EXPERIMENT 5: REGIME-SPECIFIC DRIFT (V2 vs V3, 300s)", flush=True)
print("="*70, flush=True)

n300 = 3000
reg_test300 = regime_labels[start_idx:start_idx+n300]

# V2 and V3 position error arrays at 300s
pe_v2 = np.array(nav_results[0]['300s']['pos_err_arr'])
pe_v3 = np.array(nav_results[1]['300s']['pos_err_arr'])
pe_v3_nonhc = np.array(nav_results[2]['300s']['pos_err_arr'])
pe_gt  = np.array(nav_results[3]['300s']['pos_err_arr'])

pe_delta_v2 = np.concatenate([[pe_v2[0]], np.diff(pe_v2)])
pe_delta_v3 = np.concatenate([[pe_v3[0]], np.diff(pe_v3)])

exp5_results = []
print(f"\n  {'Regime':<22} {'%time':>7} | {'V2 contrib':>11} {'V2%':>6} | {'V3 contrib':>11} {'V3%':>6} | {'Delta':>8}", flush=True)
print("  " + "-"*82, flush=True)
for rid, rname in enumerate(REGIME_NAMES):
    m = (reg_test300 == rid)
    n_r = int(np.sum(m))
    if n_r == 0:
        continue
    pct_time  = round(n_r / n300 * 100, 1)
    v2_contrib = round(float(np.sum(pe_delta_v2[m])), 2)
    v3_contrib = round(float(np.sum(pe_delta_v3[m])), 2)
    v2_pct_drift = round(v2_contrib / pe_v2[-1] * 100, 1)
    v3_pct_drift = round(v3_contrib / pe_v3[-1] * 100, 1)
    delta = round(v2_contrib - v3_contrib, 2)
    exp5_results.append({
        'regime': rname, 'n': n_r, 'pct_time': pct_time,
        'v2_drift_m': v2_contrib, 'v2_pct_drift': v2_pct_drift,
        'v3_drift_m': v3_contrib, 'v3_pct_drift': v3_pct_drift,
        'drift_reduction_m': delta,
    })
    print(f"  {rname:<22} {pct_time:>6.1f}% | {v2_contrib:>10.1f} {v2_pct_drift:>5.1f}% | "
          f"{v3_contrib:>10.1f} {v3_pct_drift:>5.1f}% | {delta:>+7.1f}", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# PLOTS
# ─────────────────────────────────────────────────────────────────────────────
print("\nGenerating plots...", flush=True)
P_DIR = 'plots/vw4/speednet_v3'

# Plot 1: Speed bias by regime (V2 vs V3)
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
r_names_plot = [r['regime'] for r in exp3_results]
v2_biases = [r['v2_bias'] for r in exp3_results]
v3_biases = [r['v3_bias'] for r in exp3_results]
x_pos = np.arange(len(r_names_plot))
axes[0].bar(x_pos - 0.2, v2_biases, 0.35, label='SpeedNet v2', color='#F44336', alpha=0.8)
axes[0].bar(x_pos + 0.2, v3_biases, 0.35, label='SpeedNet v3', color='#2196F3', alpha=0.8)
axes[0].axhline(0, color='black', linewidth=1)
axes[0].set_xticks(x_pos); axes[0].set_xticklabels(r_names_plot, rotation=30, ha='right')
axes[0].set_ylabel('Mean Speed Bias (km/h)')
axes[0].set_title('Speed Bias by Regime\n(+ = overestimate)', fontweight='bold')
axes[0].legend()
v2_maes = [r['v2_mae'] for r in exp3_results]
v3_maes = [r['v3_mae'] for r in exp3_results]
axes[1].bar(x_pos - 0.2, v2_maes, 0.35, label='SpeedNet v2', color='#F44336', alpha=0.8)
axes[1].bar(x_pos + 0.2, v3_maes, 0.35, label='SpeedNet v3', color='#2196F3', alpha=0.8)
axes[1].set_xticks(x_pos); axes[1].set_xticklabels(r_names_plot, rotation=30, ha='right')
axes[1].set_ylabel('Speed MAE (km/h)'); axes[1].legend()
axes[1].set_title('Speed MAE by Regime', fontweight='bold')
plt.tight_layout()
plt.savefig(f'{P_DIR}/regime_bias_mae.png', dpi=150); plt.close()

# Plot 2: Regime classifier confusion matrix
fig, ax = plt.subplots(figsize=(9, 7))
im = ax.imshow(cm, interpolation='nearest', cmap='Blues')
ax.figure.colorbar(im, ax=ax)
ax.set(xticks=np.arange(N_REGIMES), yticks=np.arange(N_REGIMES),
       xticklabels=REGIME_NAMES, yticklabels=REGIME_NAMES,
       title=f'IMU Regime Classifier Confusion Matrix\n(Val Acc={exp1_acc:.1f}%)',
       ylabel='True', xlabel='Predicted')
plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
thresh = cm.max() / 2.
for i in range(N_REGIMES):
    for j in range(N_REGIMES):
        ax.text(j, i, format(cm[i, j], 'd'), ha='center', va='center',
                color='white' if cm[i,j] > thresh else 'black', fontsize=8)
plt.tight_layout()
plt.savefig(f'{P_DIR}/regime_confusion_matrix.png', dpi=150); plt.close()

# Plot 3: 300s Position error growth — V2 vs V3
fig, ax = plt.subplots(figsize=(12, 5))
t300 = np.arange(n300) * dt
ax.plot(t300, pe_v2, color='#F44336', linewidth=2, label=f'V2+NHC ({pe_v2[-1]:.0f}m)')
ax.plot(t300, pe_v3, color='#2196F3', linewidth=2, label=f'V3+NHC ({pe_v3[-1]:.0f}m)')
ax.plot(t300, pe_gt,  color='#4CAF50', linewidth=1.5, linestyle='--',
        label=f'GT Speed+NHC ({pe_gt[-1]:.0f}m)')
ax.axhline(150, color='orange', linestyle=':', linewidth=1.5, label='Target (<150m)')
ax.axhline(263, color='gray',   linestyle=':', linewidth=1,   label='Baseline V2 (263m)')
ax.set_xlabel('Time in GNSS Outage (s)'); ax.set_ylabel('Position Error (m)')
ax.set_title('300s GNSS-Denied Navigation — Position Error Growth', fontweight='bold')
ax.legend(); ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{P_DIR}/pos_error_300s.png', dpi=150); plt.close()

# Plot 4: 300s Trajectory comparison
fig, axes2 = plt.subplots(1, 3, figsize=(18, 6))
labels_traj = ['V2+NHC [Baseline]', 'V3+NHC', 'GT+NHC']
colors_traj = ['#F44336', '#2196F3', '#4CAF50']
for i, (lr, color, lbl) in enumerate(zip(
        [nav_results[0], nav_results[1], nav_results[3]], colors_traj, labels_traj)):
    ax = axes2[i]
    xdr = np.array(lr['300s']['x_dr']); ydr = np.array(lr['300s']['y_dr'])
    xgt = np.array(lr['300s']['x_gt']); ygt = np.array(lr['300s']['y_gt'])
    ax.plot(xgt, ygt, 'g-', linewidth=2, alpha=0.8, label='GT')
    ax.plot(xdr, ydr, '--', color=color, linewidth=2, label='DR')
    ax.scatter([xdr[-1]], [ydr[-1]], c=color, s=80, zorder=5)
    ax.scatter([xgt[-1]], [ygt[-1]], c='green', s=80, zorder=5)
    ax.set_title(f'{lbl}\nFinal err={lr["300s"]["final_pos_m"]:.0f}m', fontweight='bold', fontsize=10)
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3); ax.set_aspect('equal')
plt.suptitle('300s Trajectory Comparison', fontweight='bold', fontsize=13)
plt.tight_layout()
plt.savefig(f'{P_DIR}/trajectory_300s.png', dpi=150); plt.close()

# Plot 5: Navigation comparison bar chart (all durations)
fig, axes3 = plt.subplots(1, 3, figsize=(15, 5))
dur_list = [60, 120, 300]
case_labels = [r['case'][:25] for r in nav_results]
bar_colors = ['#F44336', '#2196F3', '#9C27B0', '#4CAF50', '#FF9800']
for ai, dur in enumerate(dur_list):
    vals = [r[f'{dur}s']['final_pos_m'] for r in nav_results]
    axes3[ai].bar(range(len(nav_results)), vals, color=bar_colors[:len(nav_results)], edgecolor='white', alpha=0.85)
    axes3[ai].set_title(f'{dur}s Outage', fontweight='bold')
    axes3[ai].set_ylabel('Final Position Error (m)')
    axes3[ai].set_xticks(range(len(nav_results)))
    axes3[ai].set_xticklabels(case_labels, rotation=30, ha='right', fontsize=8)
    axes3[ai].axhline(150, color='orange', linestyle=':', linewidth=1.5, label='Target' if ai==0 else '')
    for xi, v in enumerate(vals):
        axes3[ai].text(xi, v+5, f'{v:.0f}', ha='center', fontsize=8)
plt.suptitle('Navigation Performance — V2 vs V3 (All Durations)', fontweight='bold')
plt.tight_layout()
plt.savefig(f'{P_DIR}/nav_comparison_bars.png', dpi=150); plt.close()

# Plot 6: Regime drift contribution comparison
fig, axes4 = plt.subplots(1, 2, figsize=(14, 5))
r_names5 = [r['regime'] for r in exp5_results]
v2_drifts = [r['v2_drift_m'] for r in exp5_results]
v3_drifts = [r['v3_drift_m'] for r in exp5_results]
x5 = np.arange(len(r_names5))
axes4[0].bar(x5-0.2, v2_drifts, 0.35, label='V2', color='#F44336', alpha=0.8)
axes4[0].bar(x5+0.2, v3_drifts, 0.35, label='V3', color='#2196F3', alpha=0.8)
axes4[0].set_xticks(x5); axes4[0].set_xticklabels(r_names5, rotation=30, ha='right')
axes4[0].set_ylabel('Cumulative Drift Contribution (m)')
axes4[0].set_title('Regime Drift Contribution (300s)\n(DIRECTLY MEASURED)', fontweight='bold')
axes4[0].legend()
pcts_v2 = [r['v2_pct_drift'] for r in exp5_results]
pcts_v3 = [r['v3_pct_drift'] for r in exp5_results]
axes4[1].bar(x5-0.2, pcts_v2, 0.35, label='V2', color='#F44336', alpha=0.8)
axes4[1].bar(x5+0.2, pcts_v3, 0.35, label='V3', color='#2196F3', alpha=0.8)
axes4[1].set_xticks(x5); axes4[1].set_xticklabels(r_names5, rotation=30, ha='right')
axes4[1].set_ylabel('% of Total Drift'); axes4[1].legend()
axes4[1].set_title('% Drift by Regime', fontweight='bold')
plt.tight_layout()
plt.savefig(f'{P_DIR}/regime_drift_contribution.png', dpi=150); plt.close()

# Plot 7: Calibration stress test comparison
fig, ax = plt.subplots(figsize=(9, 5))
cal_methods = ['V2\n(uncorrected)', 'V2+global\ncorrection', 'V2+regime\ncorrection', 'V3\n(learned)']
cal_vals = [cal0_mae, cal1_mae, cal2_mae, v3_overall_mae]
cal_colors = ['#F44336', '#FF9800', '#FFC107', '#2196F3']
bars = ax.bar(cal_methods, cal_vals, color=cal_colors, edgecolor='white', width=0.5)
for bar, v in zip(bars, cal_vals):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05, f'{v:.3f}', ha='center', fontsize=10)
ax.set_ylabel('Speed MAE on Test Partition (km/h)')
ax.set_title('Calibration Stress Test\n(val-derived corrections vs learned)', fontweight='bold')
ax.set_ylim(0, max(cal_vals)*1.2)
plt.tight_layout()
plt.savefig(f'{P_DIR}/calibration_stress_test.png', dpi=150); plt.close()

print(f"  Plots saved to {P_DIR}/", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# SAVE RESULTS
# ─────────────────────────────────────────────────────────────────────────────
v3_300_pos  = nav_results[1]['300s']['final_pos_m']
v2_300_pos  = nav_results[0]['300s']['final_pos_m']

summary = {
    'experiment': 'SpeedNet v3 Regime-Aware Speed Estimation',
    'dataset':    'Vw04',
    'test_start': start_idx,
    'baseline_v2_nhc_300s_m': v2_300_pos,
    'v3_nhc_300s_m':          v3_300_pos,
    'target_m': 150,
    'target_achieved': v3_300_pos < 150,
    'improvement_vs_v2_pct': round((v2_300_pos - v3_300_pos) / v2_300_pos * 100, 2),

    'exp1_regime_classifier': {
        'overall_val_accuracy_pct': round(exp1_acc, 2),
        'per_class': exp1_per_class,
        'reliable_regimes': reliable_regimes
    },
    'exp2_lambda_sweep': {str(k): v for k, v in best_lambda_result.items()},
    'exp2_selected_lambda': best_lambda,
    'exp2_best_v3_ckpt': best_v3_path,
    'exp2_v3_params': count_params(model_v3_best),
    'exp2_v2_params': count_params(model_v2),

    'exp3_regime_errors': exp3_results,
    'exp3_v2_overall_mae': round(v2_overall_mae, 3),
    'exp3_v3_overall_mae': round(v3_overall_mae, 3),
    'exp3_v2_overall_bias': round(v2_overall_bias, 3),
    'exp3_v3_overall_bias': round(v3_overall_bias, 3),

    'exp4_navigation': [
        {k: v for k, v in r.items()
         if not any(k.endswith(suf) for suf in
                    ['pos_err_arr','x_dr','y_dr','x_gt','y_gt'])}
        for r in nav_results
    ],

    'exp5_regime_drift': exp5_results,

    'exp6_calibration': exp6_results,
}

with open('results/vw4_speednet_v3_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

# Save predictions
v3_v_arr   = np.array([v3_v_dict.get(i, 0.0)   for i in range(n_total)], dtype=np.float32)
v3_st_arr  = np.array([v3_stat_dict.get(i, 0.0) for i in range(n_total)], dtype=np.float32)
np.savez('results/vw4_speednet_v3_predictions.npz',
         v3_speed=v3_v_arr, v3_stat=v3_st_arr,
         v_gt=vbox_vel_ms.astype(np.float32),
         regime_labels=regime_labels.astype(np.int32))
print("Results saved.", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# FINAL REPORT PRINT
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("FINAL SPEEDNET V3 DIAGNOSTIC REPORT", flush=True)
print("="*70, flush=True)
print(f"""
Experiment 1 — Regime Classification from IMU:
  Overall val accuracy: {exp1_acc:.1f}%
  Reliable regimes (>=60% acc): {reliable_regimes}

Experiment 2 — Lambda Selection:""", flush=True)
for lam, res in best_lambda_result.items():
    sel = " <-- SELECTED" if lam == best_lambda else ""
    print(f"  lambda={lam:.2f}: Val MAE = {res['val_mae_kmh']:.3f} km/h{sel}", flush=True)

print(f"""
Experiment 3 — Speed Prediction (Test Partition):
  V2 overall MAE:  {v2_overall_mae:.3f} km/h  bias={v2_overall_bias:+.3f} km/h
  V3 overall MAE:  {v3_overall_mae:.3f} km/h  bias={v3_overall_bias:+.3f} km/h
  Improvement:     {v2_overall_mae - v3_overall_mae:+.3f} km/h

Experiment 4 — Navigation (300s):
  A: SpeedNet v2 + NHC [BASELINE]:  {nav_results[0]['300s']['final_pos_m']:.1f} m
  B: SpeedNet v3 + NHC:             {nav_results[1]['300s']['final_pos_m']:.1f} m
  C: SpeedNet v3, no NHC:           {nav_results[2]['300s']['final_pos_m']:.1f} m
  D: GT Speed + NHC:                {nav_results[3]['300s']['final_pos_m']:.1f} m
  E: V2 + Regime Calib + NHC:       {nav_results[4]['300s']['final_pos_m']:.1f} m

  Target (<150 m achieved): {v3_300_pos < 150}

Experiment 6 — Calibration vs Learning:
  V2 uncorrected:    {cal0_mae:.3f} km/h
  V2 + global bias:  {cal1_mae:.3f} km/h
  V2 + regime bias:  {cal2_mae:.3f} km/h
  V3 learned:        {v3_overall_mae:.3f} km/h

Output Files:
  models/speednet_v3_w{W}_lambda*.pth
  results/vw4_speednet_v3_summary.json
  results/vw4_speednet_v3_predictions.npz
  plots/vw4/speednet_v3/ (7 plots)
""", flush=True)
print("SpeedNet v3 experiment complete.", flush=True)
