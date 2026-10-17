import os
import sys
import numpy as np
import pandas as pd
import torch
from scipy.interpolate import interp1d

sys.path.append(os.getcwd())
from scripts.vw4_speednet_v2 import SpeedNetV2
from scripts.vw4_speednet_v2_evaluate import load_speednet_v2, predict_speednet_v2_full

os.makedirs('data/ml_dataset', exist_ok=True)

s_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\S-Vw4.csv'
v_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\V-Vw4.csv'

print("Building HeadingNet dataset...", flush=True)
df_s = pd.read_csv(s_path, encoding='latin1')
df_v = pd.read_csv(v_path, encoding='latin1')

df_s.columns = [c.strip() for c in df_s.columns]
df_v.columns = [c.strip() for c in df_v.columns]

t_s_utc = 44127.004 + (df_s['TIME SINCE START (ms)'] - df_s['TIME SINCE START (ms)'].iloc[0]) / 1000.0
t_v_utc = df_v['Time Since Start of Day (seconds)']

t_start = max(t_s_utc.iloc[0], t_v_utc.iloc[0])
t_end = min(t_s_utc.iloc[-1], t_v_utc.iloc[-1])
dt = 0.1
t_sync = np.arange(t_start, t_end, dt)

ax_lin = interp1d(t_s_utc, df_s.iloc[:, 9] - df_s.iloc[:, 12], fill_value='extrapolate')(t_sync)
ay_lin = interp1d(t_s_utc, df_s.iloc[:, 10] - df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
az_lin = interp1d(t_s_utc, df_s.iloc[:, 11] - df_s.iloc[:, 14], fill_value='extrapolate')(t_sync)

gx = interp1d(t_s_utc, df_s['GYROSCOPE Roll (rad/s)'], fill_value='extrapolate')(t_sync)
gy = interp1d(t_s_utc, df_s['GYROSCOPE Pitch (rad/s)'], fill_value='extrapolate')(t_sync)
gz = interp1d(t_s_utc, df_s['GYROSCOPE Yaw (rad/s)'], fill_value='extrapolate')(t_sync)

gyro_pitch = gy
w_yaw_imu = -gyro_pitch

vbox_yaw_rate_degs = interp1d(t_v_utc, df_v['Yaw Rate (deg/sec)'], fill_value='extrapolate')(t_sync)
w_yaw_gt = np.radians(vbox_yaw_rate_degs)

# Primary target: yaw rate correction delta_w (rad/s)
delta_w_gt = w_yaw_gt - w_yaw_imu

# Get SpeedNet v2 predictions for 7-channel configuration
print("Loading frozen SpeedNet v2 model to extract v_ml feature...", flush=True)
speednet_m = load_speednet_v2(window_size=40)
v_ml_dict, _, _ = predict_speednet_v2_full(speednet_m, window_size=40)
v_ml_arr = np.array([v_ml_dict.get(i, 0.0) for i in range(len(t_sync))])

X_config_a = np.column_stack([ax_lin, ay_lin, az_lin, gx, gy, gz])
X_config_b = np.column_stack([ax_lin, ay_lin, az_lin, gx, gy, gz, v_ml_arr])

n_total = len(t_sync)
idx_train_end = int(n_total * 0.70)
idx_val_end   = int(n_total * 0.85)

# Calculate normalization stats ONLY from Training partition
mean_a = np.mean(X_config_a[:idx_train_end], axis=0)
std_a  = np.std(X_config_a[:idx_train_end], axis=0)
std_a[std_a == 0] = 1.0

mean_b = np.mean(X_config_b[:idx_train_end], axis=0)
std_b  = np.std(X_config_b[:idx_train_end], axis=0)
std_b[std_b == 0] = 1.0

X_norm_a = (X_config_a - mean_a) / std_a
X_norm_b = (X_config_b - mean_b) / std_b

out_path = 'data/ml_dataset/headingnet_dataset.npz'
np.savez(out_path,
         X_norm_a=X_norm_a,
         X_norm_b=X_norm_b,
         delta_w_gt=delta_w_gt,
         w_yaw_imu=w_yaw_imu,
         w_yaw_gt=w_yaw_gt,
         mean_a=mean_a, std_a=std_a,
         mean_b=mean_b, std_b=std_b,
         idx_train_end=idx_train_end,
         idx_val_end=idx_val_end,
         n_total=n_total)

print(f"HeadingNet dataset built and saved to {out_path}!", flush=True)
