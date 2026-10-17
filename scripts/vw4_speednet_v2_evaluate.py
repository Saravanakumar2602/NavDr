import os
import sys
import time
import json
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from scipy.interpolate import interp1d

sys.path.append(os.getcwd())
from scripts.vw4_speednet_v2 import SpeedNetV2

s_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\S-Vw4.csv'
v_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\V-Vw4.csv'

df_s = pd.read_csv(s_path, encoding='latin1')
df_v = pd.read_csv(v_path, encoding='latin1')

df_s.columns = [c.strip() for c in df_s.columns]
df_v.columns = [c.strip() for c in df_v.columns]

# --- Timestamp Synchronization ---
t_s_utc = 44127.004 + (df_s['TIME SINCE START (ms)'] - df_s['TIME SINCE START (ms)'].iloc[0]) / 1000.0
t_v_utc = df_v['Time Since Start of Day (seconds)']

t_start = max(t_s_utc.iloc[0], t_v_utc.iloc[0])
t_end = min(t_s_utc.iloc[-1], t_v_utc.iloc[-1])
dt = 0.1 # 10 Hz
t_sync = np.arange(t_start, t_end, dt)

ax_lin = interp1d(t_s_utc, df_s.iloc[:, 9] - df_s.iloc[:, 12], fill_value='extrapolate')(t_sync)
ay_lin = interp1d(t_s_utc, df_s.iloc[:, 10] - df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
az_lin = interp1d(t_s_utc, df_s.iloc[:, 11] - df_s.iloc[:, 14], fill_value='extrapolate')(t_sync)

gx = interp1d(t_s_utc, df_s['GYROSCOPE Roll (rad/s)'], fill_value='extrapolate')(t_sync)
gy = interp1d(t_s_utc, df_s['GYROSCOPE Pitch (rad/s)'], fill_value='extrapolate')(t_sync)
gz = interp1d(t_s_utc, df_s['GYROSCOPE Yaw (rad/s)'], fill_value='extrapolate')(t_sync)

X_raw_all = np.column_stack([ax_lin, ay_lin, az_lin, gx, gy, gz])

raw_ax = interp1d(t_s_utc, df_s.iloc[:, 9], fill_value='extrapolate')(t_sync)
raw_ay = interp1d(t_s_utc, df_s.iloc[:, 10], fill_value='extrapolate')(t_sync)
grav_x = interp1d(t_s_utc, df_s.iloc[:, 12], fill_value='extrapolate')(t_sync)
grav_y = interp1d(t_s_utc, df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
gyro_pitch = interp1d(t_s_utc, df_s['GYROSCOPE Pitch (rad/s)'], fill_value='extrapolate')(t_sync)

a_long = -(raw_ay - grav_y)
a_lat_tilt_comp = raw_ax - grav_x
w_yaw = -gyro_pitch

vbox_lat = interp1d(t_v_utc, df_v['Latitude (degrees)'], fill_value='extrapolate')(t_sync)
vbox_lon = interp1d(t_v_utc, df_v['Longitude (degrees)'], fill_value='extrapolate')(t_sync)
vbox_vel_ms = interp1d(t_v_utc, df_v['Velocity (km/hr)'] / 3.6, fill_value='extrapolate')(t_sync)
vbox_heading_deg = interp1d(t_v_utc, df_v['Heading (degrees)'], fill_value='extrapolate')(t_sync)
vbox_yaw_rate_degs = interp1d(t_v_utc, df_v['Yaw Rate (deg/sec)'], fill_value='extrapolate')(t_sync)

lat0, lon0 = vbox_lat[0], vbox_lon[0]
R_earth = 6378137.0
lat_rad_all = np.radians(vbox_lat)
lon_rad_all = np.radians(vbox_lon)
x_gt_all = (lon_rad_all - np.radians(lon0)) * R_earth * np.cos(np.radians(lat0))
y_gt_all = (lat_rad_all - np.radians(lat0)) * R_earth
vx_gt_all = vbox_vel_ms * np.sin(np.radians(vbox_heading_deg))
vy_gt_all = vbox_vel_ms * np.cos(np.radians(vbox_heading_deg))

n_total = len(t_sync)
idx_train_end = int(n_total * 0.70)
idx_val_end   = int(n_total * 0.85)

train_mean = np.mean(X_raw_all[:idx_train_end], axis=0)
train_std  = np.std(X_raw_all[:idx_train_end], axis=0)
train_std[train_std == 0] = 1.0

X_norm_all = (X_raw_all - train_mean) / train_std

def load_speednet_v2(window_size=30):
    device = torch.device('cpu')
    model = SpeedNetV2(window_size=window_size).to(device)
    model_path = f'models/speednet_v2_w{window_size}.pth'
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    return model

def predict_speednet_v2_full(model, window_size=30):
    device = torch.device('cpu')
    v_dict = {}; w_dict = {}; prob_stat_dict = {}
    
    needed_indices = np.arange(window_size - 1, n_total)
    sub_windows = np.lib.stride_tricks.sliding_window_view(X_norm_all, window_shape=(window_size, 6), axis=(0, 1)).squeeze(1)
    sub_indices = needed_indices - (window_size - 1)
    sub_batch = sub_windows[sub_indices].astype(np.float32)
    
    with torch.no_grad():
        v_p, w_p, logit_s, _ = model(torch.tensor(sub_batch, dtype=torch.float32).to(device))
        v_p = v_p.cpu().numpy()
        w_p = w_p.cpu().numpy()
        prob_s = torch.sigmoid(logit_s).cpu().numpy()
        
    for j, idx in enumerate(needed_indices):
        v_dict[idx] = max(0.0, float(v_p[j]))
        w_dict[idx] = float(w_p[j])
        prob_stat_dict[idx] = float(prob_s[j])
        
    return v_dict, w_dict, prob_stat_dict

def evaluate_pure_predictions(v_dict, w_dict, prob_stat_dict, start_eval=107535, end_eval=126505, p_thresh=0.5):
    test_indices = np.arange(start_eval, end_eval)
    v_pred = np.array([v_dict[i] for i in test_indices])
    w_pred = np.array([w_dict[i] for i in test_indices])
    prob_s = np.array([prob_stat_dict[i] for i in test_indices])
    
    v_gt_sub = vbox_vel_ms[test_indices]
    w_gt_sub = np.radians(vbox_yaw_rate_degs[test_indices])
    stat_gt_sub = (v_gt_sub < 0.1).astype(int)
    stat_pred = (prob_s > p_thresh).astype(int)
    
    speed_mae_kmh = float(np.mean(np.abs(v_pred - v_gt_sub)) * 3.6)
    speed_rmse_kmh = float(np.sqrt(np.mean((v_pred - v_gt_sub)**2)) * 3.6)
    yaw_mae_degs = float(np.degrees(np.mean(np.abs(w_pred - w_gt_sub))))
    yaw_rmse_degs = float(np.degrees(np.sqrt(np.mean((w_pred - w_gt_sub)**2))))
    
    tp = int(np.sum((stat_pred == 1) & (stat_gt_sub == 1)))
    fp = int(np.sum((stat_pred == 1) & (stat_gt_sub == 0)))
    fn = int(np.sum((stat_pred == 0) & (stat_gt_sub == 1)))
    tn = int(np.sum((stat_pred == 0) & (stat_gt_sub == 0)))
    
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    
    false_stationary_rate = float(fp / max(1, (fp + tn))) # Predicted stationary when moving
    false_motion_rate = float(fn / max(1, (tp + fn)))     # Predicted moving when stationary
    
    return {
        'speed_mae_kmh': round(speed_mae_kmh, 2),
        'speed_rmse_kmh': round(speed_rmse_kmh, 2),
        'yaw_mae_degs': round(yaw_mae_degs, 2),
        'yaw_rmse_degs': round(yaw_rmse_degs, 2),
        'stationary_precision': round(precision, 4),
        'stationary_recall': round(recall, 4),
        'stationary_f1': round(f1, 4),
        'false_stationary_rate': round(false_stationary_rate, 4),
        'false_motion_rate': round(false_motion_rate, 4)
    }
