import os
import sys
import time
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from scipy.interpolate import interp1d

sys.path.append(os.getcwd())
from scripts.vw4_speednet_v2 import SpeedNetV2

torch.set_num_threads(4)
os.makedirs('models', exist_ok=True)

s_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\S-Vw4.csv'
v_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\V-Vw4.csv'

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

ax_lin = interp1d(t_s_utc, df_s.iloc[:, 9] - df_s.iloc[:, 12], fill_value='extrapolate')(t_sync)
ay_lin = interp1d(t_s_utc, df_s.iloc[:, 10] - df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
az_lin = interp1d(t_s_utc, df_s.iloc[:, 11] - df_s.iloc[:, 14], fill_value='extrapolate')(t_sync)

gx = interp1d(t_s_utc, df_s['GYROSCOPE Roll (rad/s)'], fill_value='extrapolate')(t_sync)
gy = interp1d(t_s_utc, df_s['GYROSCOPE Pitch (rad/s)'], fill_value='extrapolate')(t_sync)
gz = interp1d(t_s_utc, df_s['GYROSCOPE Yaw (rad/s)'], fill_value='extrapolate')(t_sync)

X_raw_all = np.column_stack([ax_lin, ay_lin, az_lin, gx, gy, gz])

v_gt = interp1d(t_v_utc, df_v['Velocity (km/hr)'] / 3.6, fill_value='extrapolate')(t_sync)
w_gt = np.radians(interp1d(t_v_utc, df_v['Yaw Rate (deg/sec)'], fill_value='extrapolate')(t_sync))
stat_gt = (v_gt < 0.1).astype(np.float32)

delta_v_gt = np.zeros_like(v_gt)
delta_v_gt[10:] = v_gt[10:] - v_gt[:-10]

n_total = len(t_sync)
idx_train_end = int(n_total * 0.70)  # 88566
idx_val_end   = int(n_total * 0.85)  # 107535

train_mean = np.mean(X_raw_all[:idx_train_end], axis=0)
train_std  = np.std(X_raw_all[:idx_train_end], axis=0)
train_std[train_std == 0] = 1.0

X_norm_all = (X_raw_all - train_mean) / train_std

def train_speednet_v2(window_size=30, num_epochs=15, batch_size=1024, lr=1e-3):
    print(f"\n--- Ultra-Fast Pre-Windowed Training SpeedNet v2 (W={window_size}) ---", flush=True)
    
    sub_windows = np.lib.stride_tricks.sliding_window_view(X_norm_all, window_shape=(window_size, 6), axis=(0, 1)).squeeze(1)
    
    train_indices = np.arange(window_size - 1, idx_train_end)
    val_indices   = np.arange(idx_train_end, idx_val_end)
    
    sub_tr_indices = train_indices - (window_size - 1)
    sub_val_indices = val_indices - (window_size - 1)
    
    X_tr_tensor = torch.tensor(sub_windows[sub_tr_indices], dtype=torch.float32)
    v_tr_tensor = torch.tensor(v_gt[train_indices], dtype=torch.float32)
    w_tr_tensor = torch.tensor(w_gt[train_indices], dtype=torch.float32)
    stat_tr_tensor = torch.tensor(stat_gt[train_indices], dtype=torch.float32)
    delta_tr_tensor = torch.tensor(delta_v_gt[train_indices], dtype=torch.float32)
    
    X_val_tensor = torch.tensor(sub_windows[sub_val_indices], dtype=torch.float32)
    v_val_tensor = torch.tensor(v_gt[val_indices], dtype=torch.float32)
    w_val_tensor = torch.tensor(w_gt[val_indices], dtype=torch.float32)
    stat_val_tensor = torch.tensor(stat_gt[val_indices], dtype=torch.float32)
    delta_val_tensor = torch.tensor(delta_v_gt[val_indices], dtype=torch.float32)
    
    train_dataset = TensorDataset(X_tr_tensor, v_tr_tensor, w_tr_tensor, stat_tr_tensor, delta_tr_tensor)
    val_dataset   = TensorDataset(X_val_tensor, v_val_tensor, w_val_tensor, stat_val_tensor, delta_val_tensor)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader   = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = SpeedNetV2(window_size=window_size).to(device)
    
    criterion_speed = nn.SmoothL1Loss()
    criterion_yaw   = nn.SmoothL1Loss()
    criterion_stat  = nn.BCEWithLogitsLoss()
    criterion_delta = nn.SmoothL1Loss()
    
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)
    
    best_val_loss = float('inf')
    best_model_path = f'models/speednet_v2_w{window_size}.pth'
    
    for epoch in range(1, num_epochs + 1):
        model.train()
        train_loss = 0.0
        for x_b, v_b, w_b, stat_b, delta_b in train_loader:
            x_b, v_b, w_b, stat_b, delta_b = x_b.to(device), v_b.to(device), w_b.to(device), stat_b.to(device), delta_b.to(device)
            optimizer.zero_grad()
            
            v_pred, w_pred, logit_stat, delta_pred = model(x_b)
            
            l_v = criterion_speed(v_pred, v_b)
            l_w = criterion_yaw(w_pred, w_b)
            l_stat = criterion_stat(logit_stat, stat_b)
            l_delta = criterion_delta(delta_pred, delta_b)
            
            loss = 1.0 * l_v + 0.5 * l_w + 0.5 * l_stat + 0.2 * l_delta
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * len(v_b)
            
        scheduler.step()
        train_loss /= len(train_dataset)
        
        # Validation Loop
        model.eval()
        val_loss = 0.0
        val_speed_err = 0.0
        with torch.no_grad():
            for x_b, v_b, w_b, stat_b, delta_b in val_loader:
                x_b, v_b, w_b, stat_b, delta_b = x_b.to(device), v_b.to(device), w_b.to(device), stat_b.to(device), delta_b.to(device)
                v_pred, w_pred, logit_stat, delta_pred = model(x_b)
                
                l_v = criterion_speed(v_pred, v_b)
                l_w = criterion_yaw(w_pred, w_b)
                l_stat = criterion_stat(logit_stat, stat_b)
                l_delta = criterion_delta(delta_pred, delta_b)
                
                loss = 1.0 * l_v + 0.5 * l_w + 0.5 * l_stat + 0.2 * l_delta
                val_loss += loss.item() * len(v_b)
                val_speed_err += torch.sum(torch.abs(v_pred - v_b) * 3.6).item()
                
        val_loss /= len(val_dataset)
        val_speed_mae_kmh = val_speed_err / len(val_dataset)
        
        print(f"Epoch {epoch:02d}/{num_epochs:02d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Speed MAE: {val_speed_mae_kmh:.2f} km/h", flush=True)
            
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), best_model_path)
                
    print(f"Saved best model checkpoint to {best_model_path}", flush=True)
    return best_val_loss

if __name__ == '__main__':
    for w in [20, 30, 40]:
        train_speednet_v2(window_size=w, num_epochs=15)
