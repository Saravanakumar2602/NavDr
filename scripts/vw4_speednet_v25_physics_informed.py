# -*- coding: utf-8 -*-
"""
vw4_speednet_v25_physics_informed.py
======================================
SpeedNet v2.5 — Physics-Informed Feature Engineering for Intelligent Dead Reckoning

Dataset: Vw04 | Unseen test partition: start_idx = 108,000
Primary Success Criterion: 300s GNSS outage position error < 263.1 m (SpeedNet v2 + Raw Gyro + NHC baseline)

Candidate Feature Variants:
  - F0 (Control, 6 ch): [ax_lin, ay_lin, az_lin, gx, gy, gz]  (SpeedNet v2 baseline)
  - F1 (7 ch): F0 + [dv_acc] (window-causal integrated longitudinal acceleration)
  - F2 (8 ch): F0 + [a_var, w_var] (0.5s rolling variance of longitudinal accel and yaw rate)
  - F3 (7 ch): F0 + [tilt_angle] (estimated vehicle pitch/tilt angle from gravity)
  - F4 (10 ch): F0 + [dv_acc, a_var, w_var, tilt_angle] (Combined Physics Feature Set)

Evaluation Rules:
  - Feature normalization statistics (mean/std) computed strictly on training set (0:88566)
  - Model selection based exclusively on validation set (88566:107535)
  - Final evaluation once on unseen test partition (start_idx = 108000)
  - Navigation Filter: Candidate Speed + Raw Gyro + NHC (no adaptive bias, no regime loss)
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
from scipy.interpolate import interp1d

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
sys.path.append(os.getcwd())

from scripts.vw4_speednet_v2 import SpeedNetV2

torch.set_num_threads(4)
os.makedirs('models', exist_ok=True)
os.makedirs('results', exist_ok=True)
os.makedirs('plots/vw4/speednet_v25', exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING & PREPARATION
# ─────────────────────────────────────────────────────────────────────────────
S_PATH = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\S-Vw4.csv'
V_PATH = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\V-Vw4.csv'

print("Loading Vw4 dataset files...", flush=True)
df_s = pd.read_csv(S_PATH, encoding='latin1')
df_v = pd.read_csv(V_PATH, encoding='latin1')
df_s.columns = [c.strip() for c in df_s.columns]
df_v.columns = [c.strip() for c in df_v.columns]

t_s_utc = 44127.004 + (df_s['TIME SINCE START (ms)'] - df_s['TIME SINCE START (ms)'].iloc[0]) / 1000.0
t_v_utc = df_v['Time Since Start of Day (seconds)']
t_start = max(t_s_utc.iloc[0], t_v_utc.iloc[0])
t_end   = min(t_s_utc.iloc[-1], t_v_utc.iloc[-1])
dt = 0.1 # 10 Hz
t_sync = np.arange(t_start, t_end, dt)

ax_lin = interp1d(t_s_utc, df_s.iloc[:, 9]  - df_s.iloc[:, 12], fill_value='extrapolate')(t_sync)
ay_lin = interp1d(t_s_utc, df_s.iloc[:, 10] - df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
az_lin = interp1d(t_s_utc, df_s.iloc[:, 11] - df_s.iloc[:, 14], fill_value='extrapolate')(t_sync)

gx = interp1d(t_s_utc, df_s['GYROSCOPE Roll (rad/s)'],  fill_value='extrapolate')(t_sync)
gy = interp1d(t_s_utc, df_s['GYROSCOPE Pitch (rad/s)'], fill_value='extrapolate')(t_sync)
gz = interp1d(t_s_utc, df_s['GYROSCOPE Yaw (rad/s)'],   fill_value='extrapolate')(t_sync)

raw_ax  = interp1d(t_s_utc, df_s.iloc[:, 9],  fill_value='extrapolate')(t_sync)
raw_ay  = interp1d(t_s_utc, df_s.iloc[:, 10], fill_value='extrapolate')(t_sync)
raw_az  = interp1d(t_s_utc, df_s.iloc[:, 11], fill_value='extrapolate')(t_sync)
grav_x  = interp1d(t_s_utc, df_s.iloc[:, 12], fill_value='extrapolate')(t_sync)
grav_y  = interp1d(t_s_utc, df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
grav_z  = interp1d(t_s_utc, df_s.iloc[:, 14], fill_value='extrapolate')(t_sync)

a_long = -(raw_ay - grav_y)
w_yaw  = -gy

vbox_lat     = interp1d(t_v_utc, df_v['Latitude (degrees)'],  fill_value='extrapolate')(t_sync)
vbox_lon     = interp1d(t_v_utc, df_v['Longitude (degrees)'], fill_value='extrapolate')(t_sync)
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

n_total       = len(t_sync)
idx_train_end = int(n_total * 0.70)   # 88566
idx_val_end   = int(n_total * 0.85)   # 107535
start_idx     = 108000                 # Unseen test partition

stat_gt_all = (vbox_vel_ms < 0.1).astype(np.float32)

delta_v_gt = np.zeros_like(vbox_vel_ms)
delta_v_gt[10:] = vbox_vel_ms[10:] - vbox_vel_ms[:-10]

# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT 1: FEATURE DERIVATION & VALIDITY
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("EXPERIMENT 1: FEATURE DERIVATION & VALIDITY CHECK", flush=True)
print("="*70, flush=True)

# 1. Base IMU channels (6)
f_base = np.column_stack([ax_lin, ay_lin, az_lin, gx, gy, gz])

# 2. Derived Feature 1: Integrated longitudinal acceleration change (causal over 0.5s / 5 steps rolling sum)
dv_acc_5step = pd.Series(a_long * dt).rolling(window=5, min_periods=1).sum().to_numpy()

# 3. Derived Feature 2: Short-term rolling variance (0.5s / 5 steps) of a_long and w_yaw
a_var_5step = pd.Series(a_long).rolling(window=5, min_periods=1).var().fillna(0.0).to_numpy()
w_var_5step = pd.Series(w_yaw).rolling(window=5, min_periods=1).var().fillna(0.0).to_numpy()

# 4. Derived Feature 3: Estimated Pitch/Tilt angle relative to gravity (radians)
# tilt = arctan2(grav_y, grav_z) or arctan2(raw_ay, sqrt(raw_ax^2 + raw_az^2))
tilt_angle = np.arctan2(grav_y, np.sqrt(grav_x**2 + grav_z**2))

# Verify Feature Validity (NaN, Inf, Range, Causality)
feature_dict = {
    'ax_lin': ax_lin, 'ay_lin': ay_lin, 'az_lin': az_lin,
    'gx': gx, 'gy': gy, 'gz': gz,
    'dv_acc_5step': dv_acc_5step,
    'a_var_5step': a_var_5step,
    'w_var_5step': w_var_5step,
    'tilt_angle': tilt_angle
}

print("  Checking feature integrity (NaN/Inf, min/max/mean):", flush=True)
for fname, fval in feature_dict.items():
    has_nan = np.isnan(fval).any()
    has_inf = np.isinf(fval).any()
    print(f"    {fname:<14}: NaN={has_nan} | Inf={has_inf} | min={np.min(fval):+.4f} | max={np.max(fval):+.4f} | mean={np.mean(fval):+.4f}", flush=True)
    assert not has_nan and not has_inf, f"Feature {fname} contains invalid values!"

# Construct Candidate Feature Matrices
X_raw_variants = {
    'F0': f_base,
    'F1': np.column_stack([f_base, dv_acc_5step]),
    'F2': np.column_stack([f_base, a_var_5step, w_var_5step]),
    'F3': np.column_stack([f_base, tilt_angle]),
    'F4': np.column_stack([f_base, dv_acc_5step, a_var_5step, w_var_5step, tilt_angle]),
}

# Normalize each variant using TRAINING stats ONLY (0:idx_train_end)
X_norm_variants = {}
norm_stats = {}
for v_name, X_raw in X_raw_variants.items():
    tr_mean = np.mean(X_raw[:idx_train_end], axis=0)
    tr_std  = np.std(X_raw[:idx_train_end], axis=0)
    tr_std[tr_std == 0] = 1.0
    X_norm = (X_raw - tr_mean) / tr_std
    X_norm_variants[v_name] = X_norm
    norm_stats[v_name] = {'mean': tr_mean.tolist(), 'std': tr_std.tolist(), 'n_channels': X_raw.shape[1]}
    print(f"  {v_name:<4} normalized: {X_raw.shape[1]} channels | Train mean shape={tr_mean.shape}", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT 2: MODEL TRAINING & VALIDATION SELECTION
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("EXPERIMENT 2: SPEEDNET V2.5 MODEL TRAINING (W=30, 15 EPOCHS)", flush=True)
print("="*70, flush=True)

W = 30 # Standard 3.0s window size
NUM_EPOCHS = 15
BATCH_SIZE = 1024
LR = 1e-3

val_results = {}
trained_models = {}

train_indices = np.arange(W - 1, idx_train_end)
val_indices   = np.arange(idx_train_end, idx_val_end)
sub_tr_idx    = train_indices - (W - 1)
sub_val_idx   = val_indices - (W - 1)

v_tr_t     = torch.tensor(vbox_vel_ms[train_indices], dtype=torch.float32)
w_tr_t     = torch.tensor(vbox_yaw_rads[train_indices], dtype=torch.float32)
stat_tr_t  = torch.tensor(stat_gt_all[train_indices], dtype=torch.float32)
delta_tr_t = torch.tensor(delta_v_gt[train_indices], dtype=torch.float32)

v_val_t     = torch.tensor(vbox_vel_ms[val_indices], dtype=torch.float32)
w_val_t     = torch.tensor(vbox_yaw_rads[val_indices], dtype=torch.float32)
stat_val_t  = torch.tensor(stat_gt_all[val_indices], dtype=torch.float32)
delta_val_t = torch.tensor(delta_v_gt[val_indices], dtype=torch.float32)

criterion_speed = nn.SmoothL1Loss()
criterion_yaw   = nn.SmoothL1Loss()
criterion_stat  = nn.BCEWithLogitsLoss()
criterion_delta = nn.SmoothL1Loss()

for v_name, X_norm in X_norm_variants.items():
    print(f"\n  --- Training SpeedNet v2.5 [{v_name}] ({X_norm.shape[1]} ch) ---", flush=True)

    sub_windows = np.lib.stride_tricks.sliding_window_view(X_norm, window_shape=(W, X_norm.shape[1]), axis=(0, 1)).squeeze(1)

    X_tr_t  = torch.tensor(sub_windows[sub_tr_idx], dtype=torch.float32)
    X_val_t = torch.tensor(sub_windows[sub_val_idx], dtype=torch.float32)

    tr_dataset  = TensorDataset(X_tr_t, v_tr_t, w_tr_t, stat_tr_t, delta_tr_t)
    val_dataset = TensorDataset(X_val_t, v_val_t, w_val_t, stat_val_t, delta_val_t)
    tr_loader   = DataLoader(tr_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader  = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

    model = SpeedNetV2(window_size=W, in_channels=X_norm.shape[1], hidden_dim=64)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS)

    ckpt_path = f'models/speednet_v25_{v_name.lower()}_w{W}.pth'
    best_val_loss = float('inf')
    best_val_mae = float('inf')

    t0_train = time.perf_counter()
    for ep in range(1, NUM_EPOCHS + 1):
        model.train()
        tr_loss = 0.0
        for xb, vb, wb, sb, db in tr_loader:
            optimizer.zero_grad()
            vp, wp, ls, dp = model(xb)
            l_v = criterion_speed(vp, vb)
            l_w = criterion_yaw(wp, wb)
            l_s = criterion_stat(ls, sb)
            l_d = criterion_delta(dp, db)
            loss = 1.0 * l_v + 0.5 * l_w + 0.5 * l_s + 0.2 * l_d
            loss.backward()
            optimizer.step()
            tr_loss += loss.item() * len(vb)
        scheduler.step()
        tr_loss /= len(tr_dataset)

        model.eval()
        val_loss = 0.0
        val_mae_sum = 0.0
        with torch.no_grad():
            for xb, vb, wb, sb, db in val_loader:
                vp, wp, ls, dp = model(xb)
                l_v = criterion_speed(vp, vb)
                l_w = criterion_yaw(wp, wb)
                l_s = criterion_stat(ls, sb)
                l_d = criterion_delta(dp, db)
                loss = 1.0 * l_v + 0.5 * l_w + 0.5 * l_s + 0.2 * l_d
                val_loss += loss.item() * len(vb)
                val_mae_sum += torch.sum(torch.abs(vp - vb) * 3.6).item()

        val_loss /= len(val_dataset)
        val_speed_mae = val_mae_sum / len(val_dataset)

        saved = ""
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_val_mae = val_speed_mae
            torch.save(model.state_dict(), ckpt_path)
            saved = " [BEST SAVED]"

        print(f"    Ep {ep:02d}/{NUM_EPOCHS:02d} | Train Loss: {tr_loss:.4f} | Val Loss: {val_loss:.4f} | Val Speed MAE: {val_speed_mae:.2f} km/h{saved}", flush=True)

    t1_train = time.perf_counter()
    n_params = sum(p.numel() for p in model.parameters())

    val_results[v_name] = {
        'val_speed_mae_kmh': round(best_val_mae, 3),
        'val_loss': round(best_val_loss, 4),
        'n_params': n_params,
        'ckpt_path': ckpt_path,
        'train_time_sec': round(t1_train - t0_train, 1)
    }

print("\nValidation Speed MAE Selection Summary:", flush=True)
print(f"  {'Variant':<6} {'Channels':<9} {'Val Speed MAE':<16} {'Val Loss':<10} {'Params':<8}", flush=True)
print("  " + "-"*55, flush=True)
for v_name, res in val_results.items():
    ch = X_norm_variants[v_name].shape[1]
    print(f"  {v_name:<6} {ch:<9} {res['val_speed_mae_kmh']:>7.3f} km/h     {res['val_loss']:>8.4f}   {res['n_params']:>7}", flush=True)

best_variant_val = min(val_results, key=lambda k: val_results[k]['val_speed_mae_kmh'])
print(f"\n  SELECTED MODEL VIA VALIDATION SET: [{best_variant_val}] (Val MAE = {val_results[best_variant_val]['val_speed_mae_kmh']:.3f} km/h)", flush=True)

# Load all trained models for test evaluation
for v_name in X_raw_variants.keys():
    ch = X_norm_variants[v_name].shape[1]
    m = SpeedNetV2(window_size=W, in_channels=ch, hidden_dim=64)
    m.load_state_dict(torch.load(val_results[v_name]['ckpt_path'], map_location='cpu'))
    m.eval()
    trained_models[v_name] = m

# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT 3: UNSEEN SPEED EVALUATION (TEST PARTITION)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("EXPERIMENT 3: UNSEEN SPEED EVALUATION (start_idx = 108,000)", flush=True)
print("="*70, flush=True)

test_idx_arr = np.arange(start_idx, min(start_idx + 3000, n_total - W))
v_gt_test    = vbox_vel_ms[test_idx_arr]

# Compute test predictions for all feature variants
test_preds = {}
test_speed_metrics = {}

for v_name, model in trained_models.items():
    X_norm = X_norm_variants[v_name]
    sub_windows = np.lib.stride_tricks.sliding_window_view(X_norm, window_shape=(W, X_norm.shape[1]), axis=(0, 1)).squeeze(1)

    needed_indices = np.arange(W - 1, n_total)
    sub_indices    = needed_indices - (W - 1)
    sub_batch      = torch.tensor(sub_windows[sub_indices], dtype=torch.float32)

    with torch.no_grad():
        v_p, w_p, logit_s, _ = model(sub_batch)
        v_p = v_p.numpy()
        prob_s = torch.sigmoid(logit_s).numpy()

    v_dict    = {int(idx): max(0.0, float(v_p[j]))   for j, idx in enumerate(needed_indices)}
    stat_dict = {int(idx): float(prob_s[j])          for j, idx in enumerate(needed_indices)}

    test_preds[v_name] = (v_dict, stat_dict)

    # Test speed prediction metrics
    vp_test = np.array([max(0.0, v_dict.get(i, 0.0)) for i in test_idx_arr])
    mae  = float(np.mean(np.abs(vp_test - v_gt_test)) * 3.6)
    bias = float(np.mean(vp_test - v_gt_test) * 3.6)
    rmse = float(np.sqrt(np.mean((vp_test - v_gt_test)**2)) * 3.6)

    test_speed_metrics[v_name] = {
        'speed_mae_kmh': round(mae, 3),
        'speed_bias_kmh': round(bias, 3),
        'speed_rmse_kmh': round(rmse, 3),
    }
    print(f"  {v_name:<4}: Test Speed MAE = {mae:.3f} km/h | Bias = {bias:+.3f} km/h | RMSE = {rmse:.3f} km/h", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT 4: NAVIGATION EVALUATION (Raw Gyro + NHC Filter)
# Benchmark to beat: SpeedNet v2 + Raw Gyro + NHC = 263.1 m @ 300s
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("EXPERIMENT 4: NAVIGATION EVALUATION (Raw Gyro + NHC)", flush=True)
print("Benchmark to Beat: SpeedNet v2 + Raw Gyro + NHC = 263.1 m @ 300s", flush=True)
print("="*70, flush=True)

P_THRESH_NAV = 0.70   # Validated gating threshold
PRE_SAMPLES  = 300

def run_nav_filter(sim_start, dur_sec, speed_dict, stat_dict, speed_source='ml'):
    """
    SpeedNet v2.5 Navigation Filter: Candidate Speed + Raw Gyro + NHC (No adaptive bias).
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

        # Raw Gyro integration (no adaptive bias update)
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
            z  = np.array([x_gt_all[idx], y_gt_all[idx], vx_gt_all[idx], vy_gt_all[idx], x_s[4]+pd])
            y_m = z - H_gnss @ x_s
            S = H_gnss @ P @ H_gnss.T + R_gnss
            K = P @ H_gnss.T @ np.linalg.inv(S)
            x_s = x_s + K @ y_m
            P = (np.eye(7) - K @ H_gnss) @ P
        else:
            p_stat = stat_dict.get(idx, 0.0) if speed_source == 'ml' else 0.0
            is_stat = p_stat > P_THRESH_NAV

            if speed_source == 'gt':
                v_meas = 0.0 if (vbox_vel_ms[idx] < 0.1) else float(vbox_vel_ms[idx])
            else:
                v_meas = 0.0 if is_stat else max(0.0, speed_dict.get(idx, 0.0))

            # Speed EKF update
            v_est   = np.sqrt(x_s[2]**2 + x_s[3]**2)
            v_denom = max(v_est, 1e-3)
            H_v = np.array([0, 0, x_s[2]/v_denom, x_s[3]/v_denom, 0, 0, 0])
            K_v = (P @ H_v) / (float(H_v @ P @ H_v) + R_v)
            x_s = x_s + K_v * (v_meas - v_est)
            P   = (np.eye(7) - np.outer(K_v, H_v)) @ P

            # Kinematic NHC update
            psi_c = x_s[4]
            v_lat = -x_s[2]*np.cos(psi_c) + x_s[3]*np.sin(psi_c)
            H_nhc = np.array([0, 0, -np.cos(psi_c), np.sin(psi_c),
                               x_s[2]*np.sin(psi_c)+x_s[3]*np.cos(psi_c), 0, 0])
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

def compute_nav_metrics(x_dr, y_dr, v_dr, psi_deg, start, dur):
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
        'final_pos_m':  round(float(pe[-1]), 2),
        'max_pos_m':    round(float(np.max(pe)), 2),
        'drift_rate':   round(float(pe[-1]/dur), 4),
        'cde_pct':      round(float(cde), 2),
        'v_mae_kmh':    round(float(np.mean(np.abs(v_dr-vgt)))*3.6, 2),
        'v_rmse_kmh':   round(float(np.sqrt(np.mean((v_dr-vgt)**2)))*3.6, 2),
        'h_err_deg':    round(float(he[-1]), 2),
        'pos_err_arr':  pe.tolist(),
        'x_dr': x_dr.tolist(), 'y_dr': y_dr.tolist(),
        'x_gt': xgt.tolist(), 'y_gt': ygt.tolist(),
    }

# Navigation Evaluation Matrix (F0, F1, F2, F3, F4 + GT Speed)
nav_cases = [
    ('F0: SpeedNet v2 (Control)',          'F0', 'ml'),
    ('F1: F0 + Integrated Accel Delta',    'F1', 'ml'),
    ('F2: F0 + Short-Term IMU Variance',   'F2', 'ml'),
    ('F3: F0 + Estimated Tilt Angle',      'F3', 'ml'),
    ('F4: F0 + Combined Physics Features', 'F4', 'ml'),
    ('GT Speed + Raw Gyro + NHC',          'F0', 'gt'),
]

nav_results = []
for label, v_name, s_source in nav_cases:
    v_dict, st_dict = test_preds[v_name]
    row = {'case_name': label, 'variant': v_name, 'source': s_source}
    print(f"\n  Evaluating: {label}", flush=True)
    for dur in [60, 120, 300]:
        xd, yd, vd, pd, lat = run_nav_filter(start_idx, dur, v_dict, st_dict, speed_source=s_source)
        m = compute_nav_metrics(xd, yd, vd, pd, start_idx, dur)
        row[f'{dur}s'] = m
        row[f'{dur}s_lat_ms'] = round(lat, 4)
        print(f"    {dur}s -> pos={m['final_pos_m']:.2f} m | v_mae={m['v_mae_kmh']:.2f} km/h | h_err={m['h_err_deg']:.1f}° | cde={m['cde_pct']:.1f}%", flush=True)
    nav_results.append(row)

# Provenance-Locked Baseline check
f0_300s_pos = nav_results[0]['300s']['final_pos_m']
print(f"\n  PROVENANCE BASELINE F0 (SpeedNet v2 + Raw Gyro + NHC): {f0_300s_pos:.2f} m @ 300s", flush=True)

# Select best physics model on validation set
best_val_model_name = best_variant_val
best_nav_result_row = next(r for r in nav_results if r['variant'] == best_val_model_name and r['source'] == 'ml')
best_300s_pos = best_nav_result_row['300s']['final_pos_m']

print(f"\n  SELECTED MODEL VIA VALIDATION [{best_val_model_name}]: 300s Pos = {best_300s_pos:.2f} m", flush=True)

# Primary Verdict Classification
BENCHMARK_TARGET = 263.11 # m
if best_300s_pos < BENCHMARK_TARGET:
    m008_verdict = "SUCCESS"
    verdict_desc = f"Selected SpeedNet v2.5 [{best_val_model_name}] achieved {best_300s_pos:.2f} m @ 300s, beating the 263.1 m benchmark!"
elif test_speed_metrics[best_val_model_name]['speed_mae_kmh'] < test_speed_metrics['F0']['speed_mae_kmh']:
    m008_verdict = "PARTIAL SUCCESS"
    verdict_desc = f"Selected SpeedNet v2.5 [{best_val_model_name}] improved test speed MAE ({test_speed_metrics[best_val_model_name]['speed_mae_kmh']:.2f} km/h vs F0 {test_speed_metrics['F0']['speed_mae_kmh']:.2f} km/h), but 300s navigation error ({best_300s_pos:.2f} m) did not beat 263.1 m."
else:
    m008_verdict = "FAILURE"
    verdict_desc = f"Selected SpeedNet v2.5 [{best_val_model_name}] failed to improve speed MAE or 300s navigation error ({best_300s_pos:.2f} m vs 263.1 m)."

print(f"\n  M008 VERDICT: {m008_verdict}", flush=True)
print(f"  {verdict_desc}", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT 5 & 6: ERROR DECOMPOSITION & FEATURE ABLATION
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("EXPERIMENT 5 & 6: MANEUVER REGIME ERROR DECOMPOSITION & FEATURE ABLATION", flush=True)
print("="*70, flush=True)

REGIME_NAMES = ['Stationary', 'Acceleration', 'Braking', 'Straight/Cruise', 'Moderate Turn', 'Strong Turn']
a_long_gt = np.gradient(vbox_vel_ms, dt)
w_gt_abs  = np.abs(vbox_yaw_rads)

regime_labels = np.full(n_total, 3, dtype=np.int64)
regime_labels[w_gt_abs >= 0.25] = 5
regime_labels[(w_gt_abs >= 0.05) & (w_gt_abs < 0.25)] = 4
not_turning = (w_gt_abs < 0.05)
regime_labels[not_turning & (a_long_gt >= 0.5)]  = 1
regime_labels[not_turning & (a_long_gt <= -0.5)] = 2
regime_labels[vbox_vel_ms < 0.1] = 0

n300 = 3000
reg_test300 = regime_labels[start_idx:start_idx+n300]

# Pos error growth arrays
pe_f0 = np.array(nav_results[0]['300s']['pos_err_arr']) # F0
pe_best = np.array(best_nav_result_row['300s']['pos_err_arr'])

pe_delta_f0 = np.concatenate([[pe_f0[0]], np.diff(pe_f0)])
pe_delta_best = np.concatenate([[pe_best[0]], np.diff(pe_best)])

regime_drift_results = []
print(f"\n  {'Regime':<22} {'%time':>7} | {'F0 Drift(m)':>12} {'F0%':>6} | {'Best Drift(m)':>14} {'Best%':>6} | {'Delta':>8}", flush=True)
print("  " + "-"*85, flush=True)
for rid, rname in enumerate(REGIME_NAMES):
    m_reg = (reg_test300 == rid)
    n_r = int(np.sum(m_reg))
    if n_r == 0: continue
    pct_t = round(n_r / n300 * 100, 1)
    f0_d  = round(float(np.sum(pe_delta_f0[m_reg])), 2)
    b_d   = round(float(np.sum(pe_delta_best[m_reg])), 2)
    f0_pct = round(f0_d / pe_f0[-1] * 100, 1)
    b_pct  = round(b_d / pe_best[-1] * 100, 1)
    delta_d = round(f0_d - b_d, 2)

    regime_drift_results.append({
        'regime': rname, 'pct_time': pct_t,
        'f0_drift_m': f0_d, 'f0_pct': f0_pct,
        'best_drift_m': b_d, 'best_pct': b_pct,
        'drift_reduction_m': delta_d
    })
    print(f"  {rname:<22} {pct_t:>6.1f}% | {f0_d:>11.1f} {f0_pct:>5.1f}% | {b_d:>13.1f} {b_pct:>5.1f}% | {delta_d:>+7.1f}", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# PLOTS GENERATION
# ─────────────────────────────────────────────────────────────────────────────
print("\nGenerating diagnostic plots...", flush=True)
P_DIR = 'plots/vw4/speednet_v25'

# Plot 1: Feature Diagnostics (Sample trajectories of derived features)
fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
t_sample = np.arange(1000) * dt
axes[0].plot(t_sample, a_long[start_idx:start_idx+1000], label='a_long (m/s²)', color='blue')
axes[0].set_ylabel('a_long'); axes[0].legend(); axes[0].grid(True, alpha=0.3)
axes[0].set_title('M008 Physics-Informed Derived Feature Diagnostics (100s Sample)', fontweight='bold')

axes[1].plot(t_sample, dv_acc_5step[start_idx:start_idx+1000], label='dv_acc_5step (m/s)', color='green')
axes[1].set_ylabel('dv_acc'); axes[1].legend(); axes[1].grid(True, alpha=0.3)

axes[2].plot(t_sample, a_var_5step[start_idx:start_idx+1000], label='a_var_5step (m²/s⁴)', color='orange')
axes[2].plot(t_sample, w_var_5step[start_idx:start_idx+1000], label='w_var_5step (rad²/s²)', color='purple')
axes[2].set_ylabel('Variance'); axes[2].legend(); axes[2].grid(True, alpha=0.3)

axes[3].plot(t_sample, np.degrees(tilt_angle[start_idx:start_idx+1000]), label='tilt_angle (deg)', color='red')
axes[3].set_xlabel('Time (s)'); axes[3].set_ylabel('Tilt (deg)'); axes[3].legend(); axes[3].grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{P_DIR}/feature_diagnostics.png', dpi=150); plt.close()

# Plot 2: 300s Navigation Comparison (Position Error Growth)
fig, ax = plt.subplots(figsize=(12, 6))
t300 = np.arange(n300) * dt
colors_plot = ['#F44336', '#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#607D8B']
for i, r in enumerate(nav_results):
    lbl = f"{r['variant']}: {r['case_name'][:30]} ({r['300s']['final_pos_m']:.1f}m)"
    ls = '--' if r['source'] == 'gt' else '-'
    lw = 2.0 if r['variant'] == best_variant_val else 1.2
    ax.plot(t300, r['300s']['pos_err_arr'], label=lbl, color=colors_plot[i % len(colors_plot)], linestyle=ls, linewidth=lw)

ax.axhline(BENCHMARK_TARGET, color='red', linestyle=':', linewidth=1.5, label=f'SpeedNet v2 Benchmark ({BENCHMARK_TARGET}m)')
ax.axhline(150, color='gold', linestyle=':', linewidth=1.5, label='Target (<150m)')
ax.set_xlabel('Time in Outage (s)'); ax.set_ylabel('Position Error (m)')
ax.set_title('M008 Physics-Informed SpeedNet v2.5 — 300s Navigation Error Growth', fontweight='bold')
ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{P_DIR}/pos_error_300s.png', dpi=150); plt.close()

# Plot 3: 300s Trajectories
fig, axes_t = plt.subplots(2, 3, figsize=(18, 10))
axes_t = axes_t.flatten()
for i, r in enumerate(nav_results):
    ax = axes_t[i]
    xdr = np.array(r['300s']['x_dr']); ydr = np.array(r['300s']['y_dr'])
    xgt = np.array(r['300s']['x_gt']); ygt = np.array(r['300s']['y_gt'])
    ax.plot(xgt, ygt, 'g-', linewidth=1.8, label='GT', alpha=0.8)
    ax.plot(xdr, ydr, 'r--', linewidth=1.5, label='DR', alpha=0.8)
    ax.scatter([xdr[-1]], [ydr[-1]], c='red', s=60, zorder=5)
    ax.scatter([xgt[-1]], [ygt[-1]], c='green', s=60, zorder=5)
    ax.set_title(f"{r['variant']}: {r['case_name'][:25]}\nErr = {r['300s']['final_pos_m']:.1f}m", fontsize=9, fontweight='bold')
    ax.legend(fontsize=7); ax.grid(True, alpha=0.3); ax.set_aspect('equal')
plt.suptitle('M008 SpeedNet v2.5 — 300s Trajectory Comparisons', fontweight='bold', fontsize=12)
plt.tight_layout()
plt.savefig(f'{P_DIR}/trajectory_300s.png', dpi=150); plt.close()

# Plot 4: Feature Ablation Summary (Validation MAE vs 300s Nav Error)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
v_names_plot = list(X_raw_variants.keys())
val_maes_plot = [val_results[v]['val_speed_mae_kmh'] for v in v_names_plot]
nav_300s_plot = [next(r['300s']['final_pos_m'] for r in nav_results if r['variant'] == v and r['source'] == 'ml') for v in v_names_plot]

ax1.bar(v_names_plot, val_maes_plot, color='#2196F3', edgecolor='white')
ax1.set_ylabel('Validation Speed MAE (km/h)'); ax1.set_title('Validation Speed MAE by Feature Set', fontweight='bold')
for xi, v in enumerate(val_maes_plot): ax1.text(xi, v+0.1, f'{v:.2f}', ha='center', fontsize=9)

ax2.bar(v_names_plot, nav_300s_plot, color='#4CAF50', edgecolor='white')
ax2.axhline(BENCHMARK_TARGET, color='red', linestyle='--', label=f'v2 Benchmark ({BENCHMARK_TARGET}m)')
ax2.set_ylabel('300s Position Error (m)'); ax2.set_title('300s Navigation Error by Feature Set', fontweight='bold')
ax2.legend()
for xi, v in enumerate(nav_300s_plot): ax2.text(xi, v+5, f'{v:.1f}', ha='center', fontsize=9)

plt.tight_layout()
plt.savefig(f'{P_DIR}/feature_ablation_summary.png', dpi=150); plt.close()

print(f"  Plots saved to {P_DIR}/", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# SAVE SUMMARY JSON & PREDICTIONS
# ─────────────────────────────────────────────────────────────────────────────
summary_data = {
    'milestone': 'M008',
    'experiment': 'SpeedNet v2.5 Physics-Informed Features',
    'dataset': 'Vw04',
    'test_start': start_idx,
    'provenance_benchmark_300s_m': BENCHMARK_TARGET,
    'verdict': m008_verdict,
    'verdict_description': verdict_desc,
    'selected_val_variant': best_variant_val,
    'best_300s_pos_error_m': best_300s_pos,
    'change_vs_benchmark_m': round(best_300s_pos - BENCHMARK_TARGET, 2),
    'validation_selection_summary': val_results,
    'test_speed_metrics': test_speed_metrics,
    'navigation_ablation_results': [
        {k: v for k, v in r.items() if not any(k.endswith(suf) for suf in ['pos_err_arr','x_dr','y_dr','x_gt','y_gt'])}
        for r in nav_results
    ],
    'regime_drift_decomposition': regime_drift_results,
    'normalization_stats': norm_stats
}

with open('results/vw4_speednet_v25_summary.json', 'w') as f:
    json.dump(summary_data, f, indent=2)

# Save predictions for all variants
preds_save_dict = {}
for v_name, (vd, sd) in test_preds.items():
    varr = np.array([vd.get(i, 0.0) for i in range(n_total)], dtype=np.float32)
    sarr = np.array([sd.get(i, 0.0) for i in range(n_total)], dtype=np.float32)
    preds_save_dict[f'v25_{v_name.lower()}_speed'] = varr
    preds_save_dict[f'v25_{v_name.lower()}_stat']  = sarr

preds_save_dict['v_gt'] = vbox_vel_ms.astype(np.float32)
np.savez('results/vw4_speednet_v25_predictions.npz', **preds_save_dict)
print("Summary JSON and predictions saved.", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# PRINT FINAL REPORT SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("FINAL SPEEDNET V2.5 EXPERIMENTAL SUMMARY", flush=True)
print("="*70, flush=True)
print(f"""
  M008 Verdict:                  {m008_verdict}
  Selected Variant (Val):        {best_variant_val} ({val_results[best_variant_val]['val_speed_mae_kmh']} km/h Val MAE)
  Best 300s Position Error:      {best_300s_pos:.2f} m
  Benchmark (SpeedNet v2 + NHC): {BENCHMARK_TARGET} m
  Net Change vs Benchmark:       {best_300s_pos - BENCHMARK_TARGET:+.2f} m ({round((best_300s_pos - BENCHMARK_TARGET)/BENCHMARK_TARGET*100, 2):+.1f}%)

Speed MAE (Unseen Test Partition):
  F0 (SpeedNet v2 Control):      {test_speed_metrics['F0']['speed_mae_kmh']:.3f} km/h | Bias: {test_speed_metrics['F0']['speed_bias_kmh']:+.3f} km/h
  F1 (Integrated Accel Delta):  {test_speed_metrics['F1']['speed_mae_kmh']:.3f} km/h | Bias: {test_speed_metrics['F1']['speed_bias_kmh']:+.3f} km/h
  F2 (Short-Term IMU Variance): {test_speed_metrics['F2']['speed_mae_kmh']:.3f} km/h | Bias: {test_speed_metrics['F2']['speed_bias_kmh']:+.3f} km/h
  F3 (Estimated Tilt Angle):    {test_speed_metrics['F3']['speed_mae_kmh']:.3f} km/h | Bias: {test_speed_metrics['F3']['speed_bias_kmh']:+.3f} km/h
  F4 (Combined Physics Set):    {test_speed_metrics['F4']['speed_mae_kmh']:.3f} km/h | Bias: {test_speed_metrics['F4']['speed_bias_kmh']:+.3f} km/h

300s Outage Position Errors (Unseen Test Partition):
  F0: SpeedNet v2 + NHC:        {nav_results[0]['300s']['final_pos_m']:.2f} m
  F1: + Integrated Accel:        {nav_results[1]['300s']['final_pos_m']:.2f} m
  F2: + Short-Term IMU Var:     {nav_results[2]['300s']['final_pos_m']:.2f} m
  F3: + Estimated Tilt Angle:   {nav_results[3]['300s']['final_pos_m']:.2f} m
  F4: + Combined Physics Set:   {nav_results[4]['300s']['final_pos_m']:.2f} m
  GT Speed + Raw Gyro + NHC:    {nav_results[5]['300s']['final_pos_m']:.2f} m
""", flush=True)

print("M008 execution complete.", flush=True)
