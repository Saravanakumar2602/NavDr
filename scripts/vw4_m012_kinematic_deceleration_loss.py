# -*- coding: utf-8 -*-
"""
vw4_m012_kinematic_deceleration_loss.py
=========================================
Milestone M012 — Kinematic Deceleration Loss Constraint & Zero-Speed Gated SpeedNet (SpeedNet v5)

Objective:
  Test whether adding a causal physical kinematic deceleration upper-bound loss penalty:
      L_kin = ReLU(v_hat_k - (v_hat_{k-1} + a_long_k * dt))^2
  directly into the training loss function reduces systematic positive speed overestimation
  during braking/deceleration without introducing temporal phase lag or degrading 300s navigation drift.

Variants Evaluated:
  F0: Control — SpeedNet v2 (W=40, lambda_kin = 0.0, baseline control)
  F1: SpeedNet v5 (W=40, lambda_kin = 0.01)
  F2: SpeedNet v5 (W=40, lambda_kin = 0.05)
  F3: SpeedNet v5 (W=40, lambda_kin = 0.20)
  F4: SpeedNet v5 (W=40, lambda_kin = 0.05 + Zero-Speed Gated Loss)

Protocol:
  1. Provenance Baseline Lock: F0 Control MUST reproduce 263.11 m @ 300s
  2. Validation Selection: Select optimal lambda_kin strictly via Val Speed MAE (88566:107535)
  3. Locked Evaluation: Test once on unseen test partition (start_idx = 108,000) for 60s, 120s, 300s
"""

import os, sys, io, time, json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
sys.path.append(os.getcwd())

torch.manual_seed(42)
np.random.seed(42)
torch.set_num_threads(8)

from scripts.vw4_speednet_v2 import SpeedNetV2
from scripts.vw4_speednet_v2_evaluate import (
    load_speednet_v2, predict_speednet_v2_full,
    t_sync, dt, n_total, idx_train_end, idx_val_end,
    ax_lin, ay_lin, az_lin, gx, gy, gz,
    raw_ax, raw_ay, grav_x, grav_y, gyro_pitch,
    a_long, w_yaw,
    vbox_lat, vbox_lon, vbox_vel_ms, vbox_heading_deg, vbox_yaw_rate_degs,
    x_gt_all, y_gt_all, vx_gt_all, vy_gt_all,
    X_raw_all, X_norm_all, lat0, lon0, R_earth
)

os.makedirs('models', exist_ok=True)
os.makedirs('plots/vw4/m012_kinematic_deceleration_loss', exist_ok=True)
os.makedirs('results', exist_ok=True)

v_gt = vbox_vel_ms
w_gt = np.radians(vbox_yaw_rate_degs)
stat_gt = (v_gt < 0.1).astype(np.float32)

delta_v_gt = np.zeros_like(v_gt)
delta_v_gt[10:] = v_gt[10:] - v_gt[:-10]

PRE_SAMPLES = 300
R_nhc_base  = 0.2**2
start_idx   = 108000

# ─────────────────────────────────────────────────────────────────────────────
# PRE-COMPUTE TENSORS FOR ULTRA-FAST BATCHING
# ─────────────────────────────────────────────────────────────────────────────
print("Pre-computing sliding windows (W=40)...", flush=True)
window_size = 40
sub_windows_all = np.lib.stride_tricks.sliding_window_view(X_norm_all, window_shape=(window_size, 6), axis=(0, 1)).squeeze(1)

train_indices = np.arange(window_size - 1, idx_train_end)
val_indices   = np.arange(idx_train_end, idx_val_end)

sub_tr_indices  = train_indices - (window_size - 1)
sub_val_indices = val_indices - (window_size - 1)

X_tr_tensor     = torch.tensor(sub_windows_all[sub_tr_indices], dtype=torch.float32)
v_tr_tensor     = torch.tensor(v_gt[train_indices], dtype=torch.float32)
w_tr_tensor     = torch.tensor(w_gt[train_indices], dtype=torch.float32)
stat_tr_tensor  = torch.tensor(stat_gt[train_indices], dtype=torch.float32)
delta_tr_tensor = torch.tensor(delta_v_gt[train_indices], dtype=torch.float32)
along_tr_tensor = torch.tensor(a_long[train_indices], dtype=torch.float32)

X_val_tensor    = torch.tensor(sub_windows_all[sub_val_indices], dtype=torch.float32)
v_val_tensor    = torch.tensor(v_gt[val_indices], dtype=torch.float32)
w_val_tensor    = torch.tensor(w_gt[val_indices], dtype=torch.float32)
stat_val_tensor = torch.tensor(stat_gt[val_indices], dtype=torch.float32)
delta_val_tensor= torch.tensor(delta_v_gt[val_indices], dtype=torch.float32)
along_val_tensor= torch.tensor(a_long[val_indices], dtype=torch.float32)

X_full_tensor   = torch.tensor(sub_windows_all, dtype=torch.float32)

def get_batch_slice(tensors, batch_size=4096):
    n = len(tensors[0])
    for i in range(0, n, batch_size):
        yield tuple(t[i:i+batch_size] for t in tensors)

# ─────────────────────────────────────────────────────────────────────────────
# KINEMATIC DECELERATION LOSS FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
class KinematicDecelerationLoss(nn.Module):
    """
    Causal Kinematic Deceleration Upper-Bound Loss:
      v_max_k = v_hat_{k-1} + a_long_k * dt
      L_kin   = ReLU(v_hat_k - v_max_k)^2
    """
    def __init__(self, dt=0.1):
        super(KinematicDecelerationLoss, self).__init__()
        self.dt = dt

    def forward(self, v_pred, a_long_batch, stat_mask=None):
        if len(v_pred) < 2:
            return torch.tensor(0.0, device=v_pred.device)

        v_prev = v_pred[:-1]
        v_curr = v_pred[1:]
        a_curr = a_long_batch[1:]

        v_max_kin = v_prev + a_curr * self.dt
        violation = F.relu(v_curr - v_max_kin)

        if stat_mask is not None:
            stat_curr = stat_mask[1:]
            violation = violation * (1.0 - stat_curr)

        loss_kin = torch.mean(violation ** 2)
        return loss_kin

# ─────────────────────────────────────────────────────────────────────────────
# TRAINING DRIVER FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def train_m012_speednet_v5(lambda_kin=0.0, use_zero_gating=False, model_name='speednet_v5_control', num_epochs=15, batch_size=4096, lr=1e-3):
    ckpt_path = f'models/{model_name}.pth'
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    if lambda_kin == 0.0 and os.path.exists('models/speednet_v2_w40.pth') and model_name == 'speednet_v5_control':
        print(f"Loading existing baseline control from models/speednet_v2_w40.pth...", flush=True)
        model = SpeedNetV2(window_size=40).to(device)
        model.load_state_dict(torch.load('models/speednet_v2_w40.pth', map_location=device))
    else:
        print(f"\n--- Training {model_name} (W=40, lambda_kin={lambda_kin}, Gating={use_zero_gating}) ---", flush=True)

        model = SpeedNetV2(window_size=40).to(device)

        criterion_speed = nn.SmoothL1Loss()
        criterion_yaw   = nn.SmoothL1Loss()
        criterion_stat  = nn.BCEWithLogitsLoss()
        criterion_delta = nn.SmoothL1Loss()
        criterion_kin   = KinematicDecelerationLoss(dt=dt)

        optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)

        best_val_loss = float('inf')

        tr_tensors  = (X_tr_tensor, v_tr_tensor, w_tr_tensor, stat_tr_tensor, delta_tr_tensor, along_tr_tensor)
        val_tensors = (X_val_tensor, v_val_tensor, w_val_tensor, stat_val_tensor, delta_val_tensor, along_val_tensor)

        for epoch in range(1, num_epochs + 1):
            model.train()
            train_loss = 0.0
            for x_b, v_b, w_b, stat_b, delta_b, along_b in get_batch_slice(tr_tensors, batch_size=batch_size):
                x_b, v_b, w_b, stat_b, delta_b, along_b = x_b.to(device), v_b.to(device), w_b.to(device), stat_b.to(device), delta_b.to(device), along_b.to(device)
                optimizer.zero_grad()
                v_pred, w_pred, logit_stat, delta_pred = model(x_b)

                l_v     = criterion_speed(v_pred, v_b)
                l_w     = criterion_yaw(w_pred, w_b)
                l_stat  = criterion_stat(logit_stat, stat_b)
                l_delta = criterion_delta(delta_pred, delta_b)

                stat_mask = stat_b if use_zero_gating else None
                l_kin   = criterion_kin(v_pred, along_b, stat_mask=stat_mask)

                loss = 1.0 * l_v + 0.5 * l_w + 0.5 * l_stat + 0.2 * l_delta + lambda_kin * l_kin
                loss.backward()
                optimizer.step()
                train_loss += loss.item() * len(v_b)

            scheduler.step()
            train_loss /= len(X_tr_tensor)

            model.eval()
            val_loss = 0.0
            val_speed_err = 0.0
            with torch.no_grad():
                for x_b, v_b, w_b, stat_b, delta_b, along_b in get_batch_slice(val_tensors, batch_size=batch_size):
                    x_b, v_b, w_b, stat_b, delta_b, along_b = x_b.to(device), v_b.to(device), w_b.to(device), stat_b.to(device), delta_b.to(device), along_b.to(device)
                    v_pred, w_pred, logit_stat, delta_pred = model(x_b)

                    l_v     = criterion_speed(v_pred, v_b)
                    l_w     = criterion_yaw(w_pred, w_b)
                    l_stat  = criterion_stat(logit_stat, stat_b)
                    l_delta = criterion_delta(delta_pred, delta_b)
                    stat_mask = stat_b if use_zero_gating else None
                    l_kin   = criterion_kin(v_pred, along_b, stat_mask=stat_mask)

                    loss = 1.0 * l_v + 0.5 * l_w + 0.5 * l_stat + 0.2 * l_delta + lambda_kin * l_kin
                    val_loss += loss.item() * len(v_b)
                    val_speed_err += torch.sum(torch.abs(v_pred - v_b) * 3.6).item()

            val_loss /= len(X_val_tensor)
            val_mae = val_speed_err / len(X_val_tensor)
            print(f"  Epoch {epoch:02d}/{num_epochs:02d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Speed MAE: {val_mae:.2f} km/h", flush=True)

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(model.state_dict(), ckpt_path)

        model.load_state_dict(torch.load(ckpt_path, map_location=device))

    model.eval()
    v_preds_list, w_preds_list, stat_preds_list = [], [], []
    with torch.no_grad():
        for i in range(0, len(X_full_tensor), 4096):
            x_b = X_full_tensor[i:i+4096].to(device)
            vp, wp, logit_stat, _ = model(x_b)
            sp = torch.sigmoid(logit_stat)
            v_preds_list.append(vp.cpu().numpy())
            w_preds_list.append(wp.cpu().numpy())
            stat_preds_list.append(sp.cpu().numpy())

    v_preds_arr    = np.concatenate(v_preds_list)
    w_preds_arr    = np.concatenate(w_preds_list)
    stat_preds_arr = np.concatenate(stat_preds_list)

    v_ml_dict, w_ml_dict, prob_stat_dict = {}, {}, {}
    for i in range(len(v_preds_arr)):
        idx_original = i + 39
        v_ml_dict[idx_original]      = float(v_preds_arr[i])
        w_ml_dict[idx_original]      = float(w_preds_arr[i])
        prob_stat_dict[idx_original] = float(stat_preds_arr[i])

    param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return model, v_ml_dict, prob_stat_dict, param_count

# ── Navigation Filter ───────────────────────────────────────────────────────
def run_navigation(v_ml_dict, prob_stat_dict, sim_start_idx=108000, duration_sec=300):
    n = int(duration_sec / dt)
    sim_start = sim_start_idx - PRE_SAMPLES
    sim_end   = sim_start_idx + n

    x_state = np.zeros(7)
    x_state[0] = x_gt_all[sim_start]; x_state[1] = y_gt_all[sim_start]
    x_state[2] = vx_gt_all[sim_start]; x_state[3] = vy_gt_all[sim_start]
    x_state[4] = np.radians(vbox_heading_deg[sim_start])

    P = np.diag([1.0, 1.0, 0.5, 0.5, np.radians(2.0)**2, 0.1, np.radians(0.5)**2])
    Q = np.diag([0.001, 0.001, 0.01, 0.01, np.radians(0.05)**2, 1e-5, 1e-6])
    R_gnss = np.diag([4.0, 4.0, 0.04, 0.04, np.radians(1.0)**2])
    H_gnss = np.zeros((5, 7)); H_gnss[:5, :5] = np.eye(5)
    R_v   = 1.0**2
    R_nhc = 0.2**2

    x_hist = []
    t0 = time.perf_counter()
    for idx in range(sim_start, sim_end):
        is_outage = (idx >= sim_start_idx)
        a_m = a_long[idx]; w_m = w_yaw[idx]
        x, y, vx, vy, psi, ba, bw = x_state

        w_hat   = w_m - bw
        psi_new = psi + w_hat * dt
        a_hat   = a_m - ba
        ax_enu  = a_hat * np.sin(psi_new)
        ay_enu  = a_hat * np.cos(psi_new)
        vx_new  = vx + ax_enu * dt
        vy_new  = vy + ay_enu * dt
        x_new   = x  + vx_new * dt
        y_new   = y  + vy_new * dt
        x_state = np.array([x_new, y_new, vx_new, vy_new, psi_new, ba, bw])

        F = np.eye(7)
        F[0, 2] = dt; F[1, 3] = dt
        F[2, 4] = a_hat * np.cos(psi_new) * dt; F[3, 4] = -a_hat * np.sin(psi_new) * dt
        F[2, 5] = -np.sin(psi_new) * dt; F[3, 5] = -np.cos(psi_new) * dt; F[4, 6] = -dt
        P = F @ P @ F.T + Q

        if not is_outage:
            psi_meas = np.radians(vbox_heading_deg[idx])
            psi_diff = (psi_meas - x_state[4] + np.pi) % (2 * np.pi) - np.pi
            z_gnss = np.array([x_gt_all[idx], y_gt_all[idx], vx_gt_all[idx], vy_gt_all[idx], x_state[4] + psi_diff])
            y_meas = z_gnss - H_gnss @ x_state
            S = H_gnss @ P @ H_gnss.T + R_gnss
            K = P @ H_gnss.T @ np.linalg.inv(S)
            x_state = x_state + K @ y_meas
            P = (np.eye(7) - K @ H_gnss) @ P
        else:
            p_stat = prob_stat_dict.get(idx, 0.0)
            is_stat = p_stat > 0.70
            v_meas = 0.0 if is_stat else max(0.0, v_ml_dict.get(idx, 0.0))

            v_est   = np.sqrt(x_state[2]**2 + x_state[3]**2)
            v_denom = max(v_est, 1e-3)
            H_v = np.array([0, 0, x_state[2]/v_denom, x_state[3]/v_denom, 0, 0, 0])
            y_v = v_meas - v_est
            S_v = float(H_v @ P @ H_v.T + R_v)
            K_v = (P @ H_v.T) / S_v
            x_state = x_state + K_v * y_v
            P = (np.eye(7) - np.outer(K_v, H_v)) @ P

            psi_c = x_state[4]
            v_lat = -x_state[2] * np.cos(psi_c) + x_state[3] * np.sin(psi_c)
            H_nhc = np.array([0, 0, -np.cos(psi_c), np.sin(psi_c),
                               x_state[2]*np.sin(psi_c) + x_state[3]*np.cos(psi_c), 0, 0])
            y_nhc = 0.0 - v_lat
            S_nhc = float(H_nhc @ P @ H_nhc.T + R_nhc)
            K_nhc = (P @ H_nhc.T) / S_nhc
            x_state = x_state + K_nhc * y_nhc
            P = (np.eye(7) - np.outer(K_nhc, H_nhc)) @ P

            x_hist.append(x_state.copy())

    t1 = time.perf_counter()
    arr  = np.array(x_hist)
    x_dr = arr[:, 0] - arr[0, 0]
    y_dr = arr[:, 1] - arr[0, 1]
    v_dr = np.sqrt(arr[:, 2]**2 + arr[:, 3]**2)
    psi_deg = np.degrees(arr[:, 4])
    lat_ms = ((t1 - t0) / (PRE_SAMPLES + n)) * 1000.0
    return x_dr, y_dr, v_dr, psi_deg, lat_ms

def compute_metrics(x_dr, y_dr, v_dr, psi_deg, v_ml_dict, start, dur):
    n = int(dur / dt)
    ls, ln = vbox_lat[start], vbox_lon[start]
    xgt = (np.radians(vbox_lon[start:start+n]) - np.radians(ln)) * R_earth * np.cos(np.radians(ls))
    ygt = (np.radians(vbox_lat[start:start+n]) - np.radians(ls)) * R_earth
    vgt = vbox_vel_ms[start:start+n]
    hgt = vbox_heading_deg[start:start+n]
    pe  = np.sqrt((x_dr-xgt)**2 + (y_dr-ygt)**2)

    dist_gt = float(np.sum(np.sqrt(np.diff(xgt)**2+np.diff(ygt)**2)))
    dist_dr = float(np.sum(v_dr)*dt)
    cde = abs(dist_dr-dist_gt)/dist_gt*100
    he  = np.abs((psi_deg - hgt + 180) % 360 - 180)

    v_preds = np.array([v_ml_dict.get(i, 0.0) for i in range(start, start+n)])
    speed_mae  = float(np.mean(np.abs(v_preds - vgt)) * 3.6)
    speed_bias = float(np.mean(v_preds - vgt) * 3.6)
    speed_rmse = float(np.sqrt(np.mean((v_preds - vgt)**2)) * 3.6)

    return {
        'final_pos_m': round(float(pe[-1]), 2),
        'max_pos_m':   round(float(np.max(pe)), 2),
        'cde_pct':     round(float(cde), 2),
        'speed_mae_kmh': round(speed_mae, 2),
        'speed_bias_kmh': round(speed_bias, 2),
        'speed_rmse_kmh': round(speed_rmse, 2),
        'h_err_deg':   round(float(he[-1]), 2),
        'pos_err_arr': pe.tolist(),
        'v_preds_arr': (v_preds * 3.6).tolist(),
        'v_gt_arr':    (vgt * 3.6).tolist()
    }

# ─────────────────────────────────────────────────────────────────────────────
# M012 EXPERIMENTAL CANDIDATES SWEEP
# ─────────────────────────────────────────────────────────────────────────────
candidates = [
    ("F0: SpeedNet v2 Control (lambda_kin=0.0)",  0.00, False, "speednet_v5_control"),
    ("F1: SpeedNet v5 (lambda_kin=0.01)",         0.01, False, "speednet_v5_kin_001"),
    ("F2: SpeedNet v5 (lambda_kin=0.05)",         0.05, False, "speednet_v5_kin_005"),
    ("F3: SpeedNet v5 (lambda_kin=0.20)",         0.20, False, "speednet_v5_kin_020"),
    ("F4: SpeedNet v5 (lambda=0.05 + Zero-Gating)", 0.05, True,  "speednet_v5_kin_gated"),
]

print("\n" + "="*70, flush=True)
print("TRAINING & VALIDATION SELECTION OF M012 KINEMATIC CANDIDATES", flush=True)
print("="*70, flush=True)

candidate_results = []
best_val_mae = float('inf')
selected_candidate_idx = 0

val_slice = slice(idx_train_end, idx_val_end)
val_gt_speed_kmh = v_gt[val_slice] * 3.6

for idx, (label, l_kin, gating, mname) in enumerate(candidates):
    model, v_ml_dict, prob_stat_dict, num_params = train_m012_speednet_v5(lambda_kin=l_kin, use_zero_gating=gating, model_name=mname, num_epochs=15, batch_size=4096)

    val_preds_kmh = np.array([v_ml_dict.get(i, 0.0) for i in range(idx_train_end, idx_val_end)]) * 3.6
    val_mae = float(np.mean(np.abs(val_preds_kmh - val_gt_speed_kmh)))
    val_bias = float(np.mean(val_preds_kmh - val_gt_speed_kmh))

    if val_mae < best_val_mae and idx > 0:
        best_val_mae = val_mae
        selected_candidate_idx = idx

    candidate_results.append({
        'label': label, 'lambda_kin': l_kin, 'gating': gating, 'mname': mname,
        'model': model, 'v_ml_dict': v_ml_dict, 'prob_stat_dict': prob_stat_dict,
        'params': num_params, 'val_speed_mae_kmh': round(val_mae, 3), 'val_speed_bias_kmh': round(val_bias, 3)
    })
    print(f"  {label:<45} | Params: {num_params:>7} | Val Speed MAE: {val_mae:>6.2f} km/h | Val Bias: {val_bias:>+6.2f} km/h", flush=True)

candidate_results[selected_candidate_idx]['is_selected'] = True
selected_label = candidate_results[selected_candidate_idx]['label']
selected_mname = candidate_results[selected_candidate_idx]['mname']
print(f"\n  SELECTED MODEL VIA VALIDATION: {selected_label} (Val MAE = {candidate_results[selected_candidate_idx]['val_speed_mae_kmh']:.2f} km/h)", flush=True)

torch.save(candidate_results[selected_candidate_idx]['model'].state_dict(), 'models/speednet_v5_m012_selected.pth')
print("  Saved selected candidate checkpoint to models/speednet_v5_m012_selected.pth", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# LOCKED TEST EVALUATION (UNSEEN TEST PARTITION start_idx = 108,000)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("LOCKED EVALUATION ON UNSEEN TEST PARTITION (start_idx = 108,000)", flush=True)
print("Provenance Benchmark (SpeedNet v2 W=40): 263.11 m @ 300s", flush=True)
print("="*70, flush=True)

eval_summary_table = []
print(f"  {'Variant Name':<45} {'Val MAE':>8} {'Test MAE':>9} {'60s (m)':>8} {'120s (m)':>9} {'300s (m)':>9} {'vs Base':>10}", flush=True)
print("  " + "-"*105, flush=True)

benchmark_300s = 0.0

for idx, c in enumerate(candidate_results):
    row = {'label': c['label'], 'lambda_kin': c['lambda_kin'], 'gating': c['gating'], 'mname': c['mname'], 'val_mae': c['val_speed_mae_kmh'], 'is_selected': c.get('is_selected', False)}

    for dur in [60, 120, 300]:
        xd, yd, vd, psi_d, lat = run_navigation(c['v_ml_dict'], c['prob_stat_dict'], sim_start_idx=start_idx, duration_sec=dur)
        m = compute_metrics(xd, yd, vd, psi_d, c['v_ml_dict'], start_idx, dur)
        row[f'{dur}s'] = m

    p60  = row['60s']['final_pos_m']
    p120 = row['120s']['final_pos_m']
    p300 = row['300s']['final_pos_m']
    test_mae = row['300s']['speed_mae_kmh']

    if idx == 0:
        benchmark_300s = p300
        delta_str = "BENCHMARK"
    else:
        diff = p300 - benchmark_300s
        pct  = (diff / benchmark_300s) * 100
        delta_str = f"{diff:>+6.1f}m ({pct:>+5.1f}%)"

    row['change_vs_benchmark_m'] = round(p300 - benchmark_300s, 2)
    eval_summary_table.append(row)
    print(f"  {c['label']:<45} {c['val_speed_mae_kmh']:>7.2f}k {test_mae:>8.2f}k {p60:>8.1f} {p120:>9.1f} {p300:>9.1f} {delta_str:>10}", flush=True)

print(f"\n  REPRODUCED PROVENANCE BASELINE (F0 Control): {benchmark_300s:.2f} m @ 300s (Target = 263.11 m)", flush=True)
assert abs(benchmark_300s - 263.11) < 2.0, f"Baseline reproduction error! Expected ~263.11m, got {benchmark_300s:.2f}m"

selected_300s_pos = eval_summary_table[selected_candidate_idx]['300s']['final_pos_m']
print(f"  SELECTED MODEL TEST RESULT ({selected_label}): {selected_300s_pos:.2f} m @ 300s", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# BRAKING & REGIME SPEED ACCURACY DIAGNOSTIC
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*70, flush=True)
print("BRAKING & REGIME SPEED BIAS DIAGNOSTIC (Unseen Test Partition)", flush=True)
print("="*70, flush=True)

REGIME_NAMES = ['Stationary', 'Acceleration', 'Braking', 'Straight/Cruise', 'Moderate Turn', 'Strong Turn']
a_long_gt_all = np.gradient(vbox_vel_ms, dt)
w_gt_abs_all  = np.abs(vbox_yaw_rate_degs)

regime_labels = np.full(n_total, 3, dtype=np.int64)
regime_labels[w_gt_abs_all >= 14.3] = 5
regime_labels[(w_gt_abs_all >= 2.87) & (w_gt_abs_all < 14.3)] = 4
not_turning = (w_gt_abs_all < 2.87)
regime_labels[not_turning & (a_long_gt_all >= 0.5)]  = 1
regime_labels[not_turning & (a_long_gt_all <= -0.5)] = 2
regime_labels[vbox_vel_ms < 0.1] = 0

n300 = 3000
test_regimes = regime_labels[start_idx:start_idx+n300]
test_vgt_kmh = vbox_vel_ms[start_idx:start_idx+n300] * 3.6

regime_speed_report = []
print(f"  {'Regime':<18} | {'F0 Control Bias':>16} | {'Selected F1 Bias':>17} | {'F2 (0.05) Bias':>16}", flush=True)
print("  " + "-"*75, flush=True)

f0_preds = np.array(eval_summary_table[0]['300s']['v_preds_arr'])
f1_preds = np.array(eval_summary_table[1]['300s']['v_preds_arr'])
f2_preds = np.array(eval_summary_table[2]['300s']['v_preds_arr'])

for rid, rname in enumerate(REGIME_NAMES):
    mask = (test_regimes == rid)
    if np.sum(mask) == 0: continue
    b0 = round(float(np.mean(f0_preds[mask] - test_vgt_kmh[mask])), 2)
    b1 = round(float(np.mean(f1_preds[mask] - test_vgt_kmh[mask])), 2)
    b2 = round(float(np.mean(f2_preds[mask] - test_vgt_kmh[mask])), 2)
    regime_speed_report.append({'regime': rname, 'f0_bias': b0, 'f1_bias': b1, 'f2_bias': b2})
    print(f"  {rname:<18} | {b0:>+15.2f}k | {b1:>+16.2f}k | {b2:>+15.2f}k", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# M012 VERDICT & SCIENTIFIC DECISION
# ─────────────────────────────────────────────────────────────────────────────
BENCHMARK_TARGET = 263.11

if selected_300s_pos < BENCHMARK_TARGET - 2.0:
    m012_verdict = "ACCEPTED"
    verdict_desc = f"Selected {selected_label} [{selected_300s_pos:.2f} m] beat the 263.11 m benchmark by {BENCHMARK_TARGET - selected_300s_pos:.2f} m!"
elif abs(selected_300s_pos - BENCHMARK_TARGET) <= 2.0:
    m012_verdict = "NO MEANINGFUL CHANGE"
    verdict_desc = f"Selected {selected_label} [{selected_300s_pos:.2f} m] performed identically to the 263.11 m benchmark."
else:
    m012_verdict = "REJECTED"
    verdict_desc = f"Selected {selected_label} [{selected_300s_pos:.2f} m] degraded 300s navigation compared to the 263.11 m benchmark (+{selected_300s_pos - BENCHMARK_TARGET:.2f} m)."

print(f"\n" + "="*70, flush=True)
print(f"M012 VERDICT: {m012_verdict}", flush=True)
print(f"  {verdict_desc}", flush=True)
print("="*70, flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# PLOTS GENERATION
# ─────────────────────────────────────────────────────────────────────────────
print("\nGenerating M012 diagnostic plots...", flush=True)
P_DIR = 'plots/vw4/m012_kinematic_deceleration_loss'
t300  = np.arange(n300) * dt

fig, ax = plt.subplots(figsize=(8, 5))
l_vals   = [r['lambda_kin'] for r in eval_summary_table]
val_maes = [r['val_mae'] for r in eval_summary_table]
test_maes= [r['300s']['speed_mae_kmh'] for r in eval_summary_table]
labels_p1= [r['label'][:25] for r in eval_summary_table]
x_p1 = np.arange(len(l_vals))

ax.plot(x_p1, val_maes, 'o-', color='#2196F3', label='Validation Speed MAE (km/h)', linewidth=2)
ax.plot(x_p1, test_maes, 's--', color='#FF9800', label='Unseen Test Speed MAE (km/h)', linewidth=2)
ax.set_xticks(x_p1); ax.set_xticklabels(labels_p1, rotation=25, ha='right', fontsize=8)
ax.set_ylabel('Speed Prediction MAE (km/h)')
ax.set_title('M012 — Kinematic Penalty Weight vs Speed Estimation MAE', fontweight='bold')
ax.legend(); ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{P_DIR}/penalty_weight_vs_speed_mae.png', dpi=150); plt.close()

braking_mask = (test_regimes == 2)
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(t300[braking_mask], test_vgt_kmh[braking_mask], 'k.', label='Ground Truth Speed (km/h)', alpha=0.6)
ax.plot(t300[braking_mask], f0_preds[braking_mask], 'r.', label='F0 Control (lambda=0.0)', alpha=0.5)
ax.plot(t300[braking_mask], f1_preds[braking_mask], 'b.', label='F1 (lambda=0.01)', alpha=0.5)
ax.plot(t300[braking_mask], f2_preds[braking_mask], 'g.', label='F2 (lambda=0.05)', alpha=0.5)
ax.set_xlabel('Time in Outage (s)'); ax.set_ylabel('Speed (km/h)')
ax.set_title('M012 — Speed Estimation Comparison During Braking Regimes', fontweight='bold')
ax.legend(); ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{P_DIR}/braking_speed_prediction.png', dpi=150); plt.close()

fig, ax = plt.subplots(figsize=(10, 5))
r_labels3 = [r['regime'] for r in regime_speed_report]
b0_vals   = [r['f0_bias'] for r in regime_speed_report]
b1_vals   = [r['f1_bias'] for r in regime_speed_report]
b2_vals   = [r['f2_bias'] for r in regime_speed_report]
x3 = np.arange(len(r_labels3))
w3 = 0.25
ax.bar(x3 - w3, b0_vals, w3, label='F0 Control', color='#4CAF50')
ax.bar(x3, b1_vals, w3, label='F1 (lambda=0.01)', color='#2196F3')
ax.bar(x3 + w3, b2_vals, w3, label='F2 (lambda=0.05)', color='#9C27B0')
ax.set_xticks(x3); ax.set_xticklabels(r_labels3, rotation=30, ha='right')
ax.axhline(0, color='black', linewidth=1)
ax.set_ylabel('Speed Bias (km/h)'); ax.set_title('M012 — Speed Prediction Bias Across Maneuver Regimes', fontweight='bold')
ax.legend(); ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{P_DIR}/speed_bias_by_regime.png', dpi=150); plt.close()

fig, ax = plt.subplots(figsize=(12, 6))
colors_p4 = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#E91E63']
for i, r in enumerate(eval_summary_table):
    lbl = f"{r['label'][:30]} ({r['300s']['final_pos_m']:.1f}m)"
    lw = 2.2 if i in [0, selected_candidate_idx] else 1.2
    ax.plot(t300, r['300s']['pos_err_arr'], label=lbl, color=colors_p4[i], linewidth=lw)

ax.axhline(BENCHMARK_TARGET, color='red', linestyle=':', label=f'Benchmark ({BENCHMARK_TARGET}m)')
ax.set_xlabel('Time in Outage (s)'); ax.set_ylabel('Position Error (m)')
ax.set_title('M012 — 300s Dead-Reckoning Position Error Growth (Kinematic Loss)', fontweight='bold')
ax.legend(); ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{P_DIR}/pos_error_vs_time.png', dpi=150); plt.close()

fig, ax = plt.subplots(figsize=(10, 5))
c_labels5 = [r['label'][:25] for r in eval_summary_table]
p60_vals5  = [r['60s']['final_pos_m'] for r in eval_summary_table]
p120_vals5 = [r['120s']['final_pos_m'] for r in eval_summary_table]
p300_vals5 = [r['300s']['final_pos_m'] for r in eval_summary_table]
x5 = np.arange(len(c_labels5))
w5 = 0.25
ax.bar(x5 - w5, p60_vals5, w5, label='60s Error (m)', color='#4CAF50')
ax.bar(x5, p120_vals5, w5, label='120s Error (m)', color='#2196F3')
ax.bar(x5 + w5, p300_vals5, w5, label='300s Error (m)', color='#F44336')
ax.set_xticks(x5); ax.set_xticklabels(c_labels5, rotation=30, ha='right', fontsize=8)
ax.axhline(BENCHMARK_TARGET, color='black', linestyle=':', label=f'Benchmark ({BENCHMARK_TARGET}m)')
ax.set_ylabel('Position Error (m)'); ax.set_title('M012 — Navigation Position Error Matrix Across Outage Horizons', fontweight='bold')
ax.legend(); ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{P_DIR}/multi_horizon_comparison.png', dpi=150); plt.close()

fig, ax = plt.subplots(figsize=(8, 6))
for r in eval_summary_table:
    s_mae = r['300s']['speed_mae_kmh']
    p_err = r['300s']['final_pos_m']
    ax.scatter(s_mae, p_err, s=120, label=r['label'][:25])
    ax.annotate(f"{r['label'][:15]}\n({p_err:.1f}m)", (s_mae, p_err), xytext=(5, 5), textcoords='offset points', fontsize=8)

ax.set_xlabel('Unseen Test Speed MAE (km/h)')
ax.set_ylabel('300s Navigation Position Error (m)')
ax.set_title('M012 — Scientific Check: Speed Prediction MAE vs Integrated Navigation Error', fontweight='bold')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{P_DIR}/speed_mae_vs_nav_error.png', dpi=150); plt.close()

print(f"  M012 diagnostic plots saved to {P_DIR}/", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# SAVE SUMMARY JSON & PREDICTIONS
# ─────────────────────────────────────────────────────────────────────────────
summary_data = {
    'milestone': 'M012',
    'experiment': 'Kinematic Deceleration Loss Constraint & Zero-Speed Gated SpeedNet (SpeedNet v5)',
    'dataset': 'Vw04',
    'test_start': start_idx,
    'provenance_benchmark_300s_m': BENCHMARK_TARGET,
    'verdict': m012_verdict,
    'verdict_description': verdict_desc,
    'selected_candidate': selected_label,
    'selected_300s_pos_m': selected_300s_pos,
    'change_vs_benchmark_m': round(selected_300s_pos - BENCHMARK_TARGET, 2),
    'eval_summary_table': eval_summary_table,
    'regime_speed_report': regime_speed_report
}

with open('results/vw4_m012_kinematic_deceleration_loss_summary.json', 'w') as f:
    json.dump(summary_data, f, indent=2)

np.savez('results/vw4_m012_kinematic_deceleration_loss_predictions.npz',
         f0_preds=f0_preds, f1_preds=f1_preds, f2_preds=f2_preds,
         test_vgt_kmh=test_vgt_kmh, test_regimes=test_regimes)

print("M012 summary JSON and predictions NPZ saved.", flush=True)
print("M012 execution complete.", flush=True)
