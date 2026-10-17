"""
SIH 2026 Problem Statement 26168 — Intelligent Dead Reckoning (IDR) System
M031 Dual-Mode Physical-Neural Heading Architecture Execution Script (run_m031.py)

Evaluates the M031 Dual-Mode Physical-Neural Heading Architecture:
- SpeedNet v2 (W=40, PyTorch checkpoint: models/speednet_v2_w40.pth) for Speed + ZUPT
- Dual-Mode Physical-Neural Heading Architecture:
  1. MEMS Gyro Integration for Primary Heading Propagation
  2. Vehicle Motion Mode Classification (STATIONARY, DYNAMIC_TURN, STRAIGHT_MOTION)
  3. Neural SpeedNet Yaw DISABLED during dynamic vehicle turns
  4. Motion-Gated Zero-Yaw Constraint during verified straight motion for Gyro Bias Calibration
"""

import os
import sys
import numpy as np
import pandas as pd
import torch
from scipy.interpolate import interp1d

# Ensure repository root is on Python path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from navigation.speednet import load_speednet_v2_model
from navigation.apm import APMModule
from navigation.m031_dual_mode_heading import EKF7StateM031

def run_m031_pipeline(df_imu, df_gnss, speednet_model_path, outage_start_s=265.0, outage_end_s=335.0, dt=0.1):
    """
    Runs the M031 Dual-Mode Physical-Neural Heading Dead Reckoning Pipeline.
    """
    t_imu = df_imu['timestamp_s'].values
    n_imu = len(t_imu)

    a_long = np.nan_to_num(df_imu['a_long'].values, nan=0.0)
    a_lat = np.nan_to_num(df_imu['a_lat'].values, nan=0.0)
    w_yaw = np.nan_to_num(df_imu['yaw_rate'].values, nan=0.0)
    j_long = np.nan_to_num(df_imu['jerk_long'].values, nan=0.0)

    # 1. Run SpeedNet v2 Inference for Speed & Stationary Probability
    X_raw = np.column_stack([
        df_imu['accel_x'].values, df_imu['accel_y'].values, df_imu['accel_z'].values,
        df_imu['gyro_x'].values, df_imu['gyro_y'].values, df_imu['gyro_z'].values
    ])
    X_raw_clean = np.nan_to_num(X_raw, nan=0.0)
    train_mean = np.mean(X_raw_clean, axis=0)
    train_std = np.std(X_raw_clean, axis=0)
    train_std[train_std == 0] = 1.0
    X_norm = (X_raw_clean - train_mean) / train_std

    model = load_speednet_v2_model(speednet_model_path, window_size=40)
    model.eval()

    window_size = 40
    needed_indices = np.arange(window_size - 1, n_imu)
    sub_windows = np.lib.stride_tricks.sliding_window_view(X_norm, window_shape=(window_size, 6), axis=(0, 1)).squeeze(1)
    sub_indices = needed_indices - (window_size - 1)
    sub_batch = sub_windows[sub_indices].astype(np.float32)

    v_ml_dict = {}
    w_ml_dict = {}
    prob_stat_dict = {}

    with torch.no_grad():
        v_p, w_p, logit_s, _ = model(torch.tensor(sub_batch, dtype=torch.float32))
        v_p = np.nan_to_num(v_p.numpy().flatten(), nan=0.0)
        w_p = np.nan_to_num(w_p.numpy().flatten(), nan=0.0)
        prob_s = np.nan_to_num(torch.sigmoid(logit_s).numpy().flatten(), nan=0.0)

    for j, idx in enumerate(needed_indices):
        v_ml_dict[idx] = max(0.0, float(v_p[j]))
        w_ml_dict[idx] = float(w_p[j])
        prob_stat_dict[idx] = float(prob_s[j])

    # 2. Alignment & Map GNSS Updates
    t_gnss = df_gnss['timestamp_s'].values
    east_gnss = df_gnss['east_m'].values
    north_gnss = df_gnss['north_m'].values
    speed_gnss = df_gnss['speed_mps'].values
    bearing_gnss = df_gnss['bearing_deg'].values

    gnss_update_map = {}
    for i, tg in enumerate(t_gnss):
        k_near = np.argmin(np.abs(t_imu - tg))
        gnss_update_map[k_near] = i

    idx_init = np.argmin(np.abs(t_imu - t_gnss[0]))
    x0 = df_gnss['east_m'].iloc[0]
    y0 = df_gnss['north_m'].iloc[0]
    v0 = df_gnss['speed_mps'].iloc[0]
    psi0 = np.radians(df_gnss['bearing_deg'].iloc[0])
    vx0 = v0 * np.sin(psi0)
    vy0 = v0 * np.cos(psi0)
    init_state = np.array([x0, y0, vx0, vy0, psi0, 0.0, 0.0])

    # 3. Execute M031 EKF Pipeline
    ekf_m031 = EKF7StateM031(init_state, dt=dt)
    apm_m031 = APMModule(jerk_threshold=-1.0, max_correction_mps=0.50)

    history = []
    v_est_hist = []

    for k in range(idx_init, n_imu):
        t_curr = t_imu[k]
        is_outage = (t_curr >= outage_start_s) and (t_curr < outage_end_s)

        a_m = a_long[k]
        w_m = w_yaw[k]
        a_l = a_lat[k]

        ekf_m031.predict(a_m, w_m)

        prob_stat = prob_stat_dict.get(k, 0.0)
        is_stat = (prob_stat > 0.70)
        v_snet = 0.0 if is_stat else max(0.0, v_ml_dict.get(k, 0.0))
        w_snet = w_ml_dict.get(k, 0.0)

        if not is_outage and (k in gnss_update_map):
            gnss_idx = gnss_update_map[k]
            psi_meas = np.radians(bearing_gnss[gnss_idx])
            z_gnss = np.array([
                east_gnss[gnss_idx], north_gnss[gnss_idx],
                speed_gnss[gnss_idx] * np.sin(psi_meas), speed_gnss[gnss_idx] * np.cos(psi_meas),
                psi_meas
            ])
            ekf_m031.update_gnss(z_gnss)
            mode, mode_action = 'GNSS_ACTIVE', 'GNSS_UPDATE'
        else:
            v_est_curr = np.sqrt(ekf_m031.x_state[2]**2 + ekf_m031.x_state[3]**2)
            mode, mode_action = ekf_m031.update_heading_mode(
                w_snet, w_m, a_l, v_est_curr, prob_stat
            )

            v_meas = v_snet
            if not is_stat and len(v_est_hist) >= 5:
                a_win = a_long[k-4:k+1]
                v_meas, _ = apm_m031.evaluate_correction(k, a_win, j_long[k], w_m, v_snet, v_est_hist)

            ekf_m031.update_speed(v_meas)
            ekf_m031.update_nhc()
            if is_stat:
                ekf_m031.update_zupt()

        st = ekf_m031.x_state.copy()
        v_est_curr = np.sqrt(st[2]**2 + st[3]**2)
        v_est_hist.append(v_est_curr)

        history.append({
            'timestamp_s': t_curr,
            'is_outage': is_outage,
            'east_m': st[0],
            'north_m': st[1],
            'speed_mps': v_est_curr,
            'heading_deg': np.degrees(st[4]) % 360.0,
            'gyro_bias_rads': st[6],
            'motion_mode': mode,
            'mode_action': mode_action
        })

    df_res = pd.DataFrame(history)
    return df_res, ekf_m031.mode_stats

if __name__ == '__main__':
    print("M031 Dual-Mode Physical-Neural Heading Architecture Module Loaded Successfully.")
