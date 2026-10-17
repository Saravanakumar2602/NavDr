import os
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

# Ensure output directories exist
os.makedirs('scripts', exist_ok=True)
os.makedirs('data/ml_dataset', exist_ok=True)
os.makedirs('results', exist_ok=True)

s_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\S-Vw4.csv'
v_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\V-Vw4.csv'

print("Loading S-Vw4.csv and V-Vw4.csv datasets...")
df_s = pd.read_csv(s_path, encoding='latin1')
df_v = pd.read_csv(v_path, encoding='latin1')

df_s.columns = [c.strip() for c in df_s.columns]
df_v.columns = [c.strip() for c in df_v.columns]

# --- 1. Timestamp Synchronization ---
t_s_utc = 44127.004 + (df_s['TIME SINCE START (ms)'] - df_s['TIME SINCE START (ms)'].iloc[0]) / 1000.0
t_v_utc = df_v['Time Since Start of Day (seconds)']

t_start = max(t_s_utc.iloc[0], t_v_utc.iloc[0])
t_end = min(t_s_utc.iloc[-1], t_v_utc.iloc[-1])
dt = 0.1 # 10 Hz
t_sync = np.arange(t_start, t_end, dt)

# Extract 6-Channel IMU Inputs:
# 1. ax_lin (m/s^2)
# 2. ay_lin (m/s^2)
# 3. az_lin (m/s^2)
# 4. gx (rad/s) - Gyroscope Roll
# 5. gy (rad/s) - Gyroscope Pitch
# 6. gz (rad/s) - Gyroscope Yaw

ax_lin = interp1d(t_s_utc, df_s.iloc[:, 9] - df_s.iloc[:, 12], fill_value='extrapolate')(t_sync)
ay_lin = interp1d(t_s_utc, df_s.iloc[:, 10] - df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
az_lin = interp1d(t_s_utc, df_s.iloc[:, 11] - df_s.iloc[:, 14], fill_value='extrapolate')(t_sync)

gx = interp1d(t_s_utc, df_s['GYROSCOPE Roll (rad/s)'], fill_value='extrapolate')(t_sync)
gy = interp1d(t_s_utc, df_s['GYROSCOPE Pitch (rad/s)'], fill_value='extrapolate')(t_sync)
gz = interp1d(t_s_utc, df_s['GYROSCOPE Yaw (rad/s)'], fill_value='extrapolate')(t_sync)

X_raw = np.column_stack([ax_lin, ay_lin, az_lin, gx, gy, gz])

# Extract Supervised Ground-Truth Labels:
# 1. Forward velocity v_fwd (m/s)
# 2. Vehicle Yaw Rate w_yaw (rad/s)
v_fwd = interp1d(t_v_utc, df_v['Velocity (km/hr)'] / 3.6, fill_value='extrapolate')(t_sync)
w_yaw = interp1d(t_v_utc, np.radians(df_v['Yaw Rate (deg/sec)']), fill_value='extrapolate')(t_sync)

Y_raw = np.column_stack([v_fwd, w_yaw])

print(f"Synchronized 10 Hz Raw Features Shape: {X_raw.shape}")
print(f"Synchronized 10 Hz Raw Targets Shape:  {Y_raw.shape}")

# --- 2. Sequential Train/Val/Test Split (Preventing Temporal Leakage) ---
n_total = len(t_sync)
idx_train_end = int(n_total * 0.70)
idx_val_end = int(n_total * 0.85)

X_train_raw = X_raw[:idx_train_end]
Y_train_raw = Y_raw[:idx_train_end]

X_val_raw = X_raw[idx_train_end:idx_val_end]
Y_val_raw = Y_raw[idx_train_end:idx_val_end]

X_test_raw = X_raw[idx_val_end:]
Y_test_raw = Y_raw[idx_val_end:]

# --- 3. Normalization (Statistics Computed ONLY on Training Set) ---
train_mean = np.mean(X_train_raw, axis=0)
train_std = np.std(X_train_raw, axis=0)
train_std[train_std == 0] = 1.0

X_train_norm = (X_train_raw - train_mean) / train_std
X_val_norm = (X_val_raw - train_mean) / train_std
X_test_norm = (X_test_raw - train_mean) / train_std

def create_sliding_windows(X_data, Y_data, window_size, step_size=1):
    X_windows = []
    Y_targets = []
    
    n_samples = len(X_data)
    for start_i in range(0, n_samples - window_size + 1, step_size):
        end_i = start_i + window_size
        X_win = X_data[start_i:end_i]
        Y_target = Y_data[end_i - 1]
        
        X_windows.append(X_win)
        Y_targets.append(Y_target)
        
    return np.array(X_windows, dtype=np.float32), np.array(Y_targets, dtype=np.float32)

# Generate ML Datasets for 3 Window Sizes (W = 10, 20, 30)
for w_size in [10, 20, 30]:
    X_tr_win, Y_tr_win = create_sliding_windows(X_train_norm, Y_train_raw, window_size=w_size)
    X_val_win, Y_val_win = create_sliding_windows(X_val_norm, Y_val_raw, window_size=w_size)
    X_te_win, Y_te_win = create_sliding_windows(X_test_norm, Y_test_raw, window_size=w_size)
    
    output_npz_path = f'data/ml_dataset/vw4_ml_dataset_w{w_size}.npz'
    np.savez_compressed(
        output_npz_path,
        X_train=X_tr_win, Y_train=Y_tr_win,
        X_val=X_val_win, Y_val=Y_val_win,
        X_test=X_te_win, Y_test=Y_te_win,
        feature_means=train_mean,
        feature_stds=train_std,
        window_size=w_size,
        sampling_freq=10.0
    )
    print(f"Generated W={w_size} dataset: X_train shape {X_tr_win.shape}, Y_train shape {Y_tr_win.shape} -> Saved to {output_npz_path}")

print("All ML dataset files successfully generated in data/ml_dataset/")
