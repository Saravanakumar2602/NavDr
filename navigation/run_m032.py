"""
SIH 2026 Problem Statement 26168 — Intelligent Dead Reckoning (IDR) System
M032 Production Navigation Pipeline Execution Script (run_m032.py)

Pipeline Architecture:
- SpeedNet v2 (W=40, PyTorch checkpoint: models/speednet_v2_w40.pth)
- 7-State EKF with 2D NHC, ZUPT, and Jerk-Gated APM
- M032 Adaptive Hybrid Heading Strategy:
  * Primary Heading = MEMS Gyro Propagation
  * SpeedNet Forward Speed = EKF Velocity Measurement Anchor
  * Verified Straight Gyro Bias Calibration
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
from navigation.m032_adaptive_hybrid import EKF7StateM032

def run_m032_pipeline(df_imu, df_gnss, speednet_model_path, outage_start_s=265.0, outage_end_s=335.0, dt=0.1):
    """
    Executes M032 Navigation Pipeline over a given dataset.
    """
    t_imu = df_imu['timestamp_s'].values
    n_imu = len(t_imu)

    a_long = np.nan_to_num(df_imu['a_long'].values, nan=0.0)
    a_lat = np.nan_to_num(df_imu['a_lat'].values, nan=0.0)
    w_yaw = np.nan_to_num(df_imu['yaw_rate'].values, nan=0.0)
    j_long = np.nan_to_num(df_imu['jerk_long'].values, nan=0.0)

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

    v_ml_dict, w_ml_dict, prob_stat_dict = {}, {}, {}
    with torch.no_grad():
        v_p, w_p, logit_s, _ = model(torch.tensor(sub_batch, dtype=torch.float32))
        v_p = np.nan_to_num(v_p.numpy().flatten(), nan=0.0)
        w_p = np.nan_to_num(w_p.numpy().flatten(), nan=0.0)
        prob_s = np.nan_to_num(torch.sigmoid(logit_s).numpy().flatten(), nan=0.0)

    for j, idx in enumerate(needed_indices):
        v_ml_dict[idx] = max(0.0, float(v_p[j]))
        w_ml_dict[idx] = float(w_p[j])
        prob_stat_dict[idx] = float(prob_s[j])

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

    ekf_m032 = EKF7StateM032(init_state, dt=dt)
    apm_m032 = APMModule(jerk_threshold=-1.0, max_correction_mps=0.50)

    history = []
    v_est_hist = []

    for k in range(idx_init, n_imu):
        t_curr = t_imu[k]
        is_outage = (t_curr >= outage_start_s) and (t_curr < outage_end_s)

        a_m = a_long[k]
        w_m = w_yaw[k]
        a_l = a_lat[k]
        j_m = j_long[k]

        prob_stat = prob_stat_dict.get(k, 0.0)
        v_snet = v_ml_dict.get(k, 0.0)

        if not is_outage and (k in gnss_update_map):
            gnss_idx = gnss_update_map[k]
            psi_meas = np.radians(bearing_gnss[gnss_idx])
            z_gnss = np.array([
                east_gnss[gnss_idx], north_gnss[gnss_idx],
                speed_gnss[gnss_idx] * np.sin(psi_meas), speed_gnss[gnss_idx] * np.cos(psi_meas),
                psi_meas
            ])
        else:
            z_gnss = None

        step_res = ekf_m032.process_step(
            a_long=a_m, w_gyro=w_m, a_lat=a_l, v_snet=v_snet, prob_stat=prob_stat,
            is_outage=is_outage, gnss_meas=z_gnss, apm_module=apm_m032, j_long=j_m, v_est_hist=v_est_hist
        )

        v_est_hist.append(step_res['speed_mps'])
        step_res['timestamp_s'] = t_curr
        step_res['is_outage'] = is_outage
        history.append(step_res)

    df_res = pd.DataFrame(history)
    return df_res, ekf_m032.stats

if __name__ == '__main__':
    print("M032 Production Navigation Runner Loaded Successfully.")
