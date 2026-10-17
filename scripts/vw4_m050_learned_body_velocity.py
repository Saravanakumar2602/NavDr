import os
import sys
import time
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt

sys.path.append(os.getcwd())
from scripts.vw4_speednet_v2 import SpeedNetV2

torch.set_num_threads(4)
os.makedirs('models', exist_ok=True)
os.makedirs('results/m050', exist_ok=True)
os.makedirs('results/plots', exist_ok=True)

# ── 1. Data Loading & Preprocessing ─────────────────────────────────────────
s_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\S-Vw4.csv'
v_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\V-Vw4.csv'

df_s = pd.read_csv(s_path, encoding='latin1')
df_v = pd.read_csv(v_path, encoding='latin1')

df_s.columns = [c.strip() for c in df_s.columns]
df_v.columns = [c.strip() for c in df_v.columns]

# Timestamp Synchronization
t_s_utc = 44127.004 + (df_s['TIME SINCE START (ms)'] - df_s['TIME SINCE START (ms)'].iloc[0]) / 1000.0
t_v_utc = df_v['Time Since Start of Day (seconds)']

t_start = max(t_s_utc.iloc[0], t_v_utc.iloc[0])
t_end   = min(t_s_utc.iloc[-1], t_v_utc.iloc[-1])
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
w_yaw = -gyro_pitch

j_long_array = np.zeros(len(t_sync))
for k in range(1, len(t_sync)):
    j_long_array[k] = (a_long[k] - a_long[k-1]) / dt

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
idx_train_end = int(n_total * 0.70) # 88566
idx_val_end   = int(n_total * 0.85) # 107535
start_idx     = 108000              # Unseen test partition

train_mean = np.mean(X_raw_all[:idx_train_end], axis=0)
train_std  = np.std(X_raw_all[:idx_train_end], axis=0)
train_std[train_std == 0] = 1.0
X_norm_all = (X_raw_all - train_mean) / train_std

PRE_SAMPLES = 300

# Ground Truth Targets for Body Velocity Learning
x_smooth = savgol_filter(x_gt_all, 15, 3)
y_smooth = savgol_filter(y_gt_all, 15, 3)
vx_pos = np.gradient(x_smooth, dt)
vy_pos = np.gradient(y_smooth, dt)
psi_rad = np.radians(vbox_heading_deg)

v_fwd_gt = vbox_vel_ms # Direct forward speed target (m/s)
v_lat_gt = -vx_pos * np.cos(psi_rad) + vy_pos * np.sin(psi_rad) # Transverse lateral speed target (m/s)
v_lat_gt = np.clip(v_lat_gt, -3.0, 3.0) # Bounded physical lateral slip speed
speed_gt = np.sqrt(v_fwd_gt**2 + v_lat_gt**2)
stat_gt  = (vbox_vel_ms < 0.1).astype(np.float32)

a_fwd_gt = np.zeros_like(v_fwd_gt)
a_fwd_gt[10:] = v_fwd_gt[10:] - v_fwd_gt[:-10] # Short term delta-v target (over 1s)

# ── 2. Model Definitions ───────────────────────────────────────────────────

class SharedBackbone(nn.Module):
    def __init__(self, window_size=40, in_channels=6, hidden_dim=64):
        super(SharedBackbone, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(in_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU()
        )
        self.bilstm = nn.LSTM(64, hidden_dim, num_layers=1, batch_first=True, bidirectional=True)
        self.fc_shared = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64),
            nn.ReLU()
        )

    def forward(self, x):
        # x: [batch, window_size, 6]
        x_c = x.permute(0, 2, 1)
        feat_conv = self.conv(x_c).permute(0, 2, 1)
        out_lstm, _ = self.bilstm(feat_conv)
        feat_final = out_lstm[:, -1, :]
        return self.fc_shared(feat_final)

class VelocityNetF1(nn.Module):
    """Candidate F1: Body-Frame Velocity (v_forward, v_lateral)"""
    def __init__(self, window_size=40):
        super(VelocityNetF1, self).__init__()
        self.backbone = SharedBackbone(window_size=window_size)
        self.fc_fwd = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
        self.fc_lat = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
        self.fc_stat = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))

    def forward(self, x):
        feat = self.backbone(x)
        v_fwd = F.relu(self.fc_fwd(feat)).squeeze(-1)
        v_lat = self.fc_lat(feat).squeeze(-1)
        logit_stat = self.fc_stat(feat).squeeze(-1)
        return v_fwd, v_lat, logit_stat

class VelocityNetF2(nn.Module):
    """Candidate F2: Multi-Task Velocity + Speed"""
    def __init__(self, window_size=40):
        super(VelocityNetF2, self).__init__()
        self.backbone = SharedBackbone(window_size=window_size)
        self.fc_fwd = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
        self.fc_lat = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
        self.fc_speed = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
        self.fc_stat = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))

    def forward(self, x):
        feat = self.backbone(x)
        v_fwd = F.relu(self.fc_fwd(feat)).squeeze(-1)
        v_lat = self.fc_lat(feat).squeeze(-1)
        speed = F.relu(self.fc_speed(feat)).squeeze(-1)
        logit_stat = self.fc_stat(feat).squeeze(-1)
        return v_fwd, v_lat, speed, logit_stat

class VelocityNetF3(nn.Module):
    """Candidate F3: Multi-Task Velocity + Acceleration"""
    def __init__(self, window_size=40):
        super(VelocityNetF3, self).__init__()
        self.backbone = SharedBackbone(window_size=window_size)
        self.fc_fwd = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
        self.fc_lat = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
        self.fc_accel = nn.Sequential(nn.Linear(64, 16), nn.ReLU(), nn.Linear(16, 1))
        self.fc_stat = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))

    def forward(self, x):
        feat = self.backbone(x)
        v_fwd = F.relu(self.fc_fwd(feat)).squeeze(-1)
        v_lat = self.fc_lat(feat).squeeze(-1)
        a_fwd = self.fc_accel(feat).squeeze(-1)
        logit_stat = self.fc_stat(feat).squeeze(-1)
        return v_fwd, v_lat, a_fwd, logit_stat

class VelocityNetF4(nn.Module):
    """Candidate F4: Multi-Task Velocity + Speed + Acceleration"""
    def __init__(self, window_size=40):
        super(VelocityNetF4, self).__init__()
        self.backbone = SharedBackbone(window_size=window_size)
        self.fc_fwd = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
        self.fc_lat = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
        self.fc_speed = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
        self.fc_accel = nn.Sequential(nn.Linear(64, 16), nn.ReLU(), nn.Linear(16, 1))
        self.fc_stat = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))

    def forward(self, x):
        feat = self.backbone(x)
        v_fwd = F.relu(self.fc_fwd(feat)).squeeze(-1)
        v_lat = self.fc_lat(feat).squeeze(-1)
        speed = F.relu(self.fc_speed(feat)).squeeze(-1)
        a_fwd = self.fc_accel(feat).squeeze(-1)
        logit_stat = self.fc_stat(feat).squeeze(-1)
        return v_fwd, v_lat, speed, a_fwd, logit_stat

# ── 3. Training Function for Candidate Models ─────────────────────────────

def train_candidate_model(cand_id, window_size=40, num_epochs=15, batch_size=1024, lr=1e-3):
    print(f"\n--- Training Candidate {cand_id} (W={window_size}, Epochs={num_epochs}) ---", flush=True)
    
    sub_windows = np.lib.stride_tricks.sliding_window_view(X_norm_all, window_shape=(window_size, 6), axis=(0, 1)).squeeze(1)
    
    train_indices = np.arange(window_size - 1, idx_train_end)
    val_indices   = np.arange(idx_train_end, idx_val_end)
    
    sub_tr_indices = train_indices - (window_size - 1)
    sub_val_indices = val_indices - (window_size - 1)
    
    X_tr_tensor = torch.tensor(sub_windows[sub_tr_indices], dtype=torch.float32)
    vfwd_tr_tensor = torch.tensor(v_fwd_gt[train_indices], dtype=torch.float32)
    vlat_tr_tensor = torch.tensor(v_lat_gt[train_indices], dtype=torch.float32)
    spd_tr_tensor  = torch.tensor(speed_gt[train_indices], dtype=torch.float32)
    afwd_tr_tensor = torch.tensor(a_fwd_gt[train_indices], dtype=torch.float32)
    stat_tr_tensor = torch.tensor(stat_gt[train_indices], dtype=torch.float32)
    
    X_val_tensor = torch.tensor(sub_windows[sub_val_indices], dtype=torch.float32)
    vfwd_val_tensor = torch.tensor(v_fwd_gt[val_indices], dtype=torch.float32)
    vlat_val_tensor = torch.tensor(v_lat_gt[val_indices], dtype=torch.float32)
    spd_val_tensor  = torch.tensor(speed_gt[val_indices], dtype=torch.float32)
    afwd_val_tensor = torch.tensor(a_fwd_gt[val_indices], dtype=torch.float32)
    stat_val_tensor = torch.tensor(stat_gt[val_indices], dtype=torch.float32)
    
    train_dataset = TensorDataset(X_tr_tensor, vfwd_tr_tensor, vlat_tr_tensor, spd_tr_tensor, afwd_tr_tensor, stat_tr_tensor)
    val_dataset   = TensorDataset(X_val_tensor, vfwd_val_tensor, vlat_val_tensor, spd_val_tensor, afwd_val_tensor, stat_val_tensor)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader   = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    if cand_id == 'F1':
        model = VelocityNetF1(window_size=window_size).to(device)
    elif cand_id == 'F2':
        model = VelocityNetF2(window_size=window_size).to(device)
    elif cand_id == 'F3':
        model = VelocityNetF3(window_size=window_size).to(device)
    elif cand_id == 'F4':
        model = VelocityNetF4(window_size=window_size).to(device)
    else:
        raise ValueError(f"Unknown cand_id: {cand_id}")
        
    crit_reg = nn.SmoothL1Loss()
    crit_stat = nn.BCEWithLogitsLoss()
    
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)
    
    best_val_loss = float('inf')
    best_model_path = f'models/vw4_m050_{cand_id.lower()}.pth'
    
    for epoch in range(1, num_epochs + 1):
        model.train()
        train_loss = 0.0
        for x_b, vfwd_b, vlat_b, spd_b, afwd_b, stat_b in train_loader:
            x_b = x_b.to(device)
            vfwd_b, vlat_b, spd_b, afwd_b, stat_b = vfwd_b.to(device), vlat_b.to(device), spd_b.to(device), afwd_b.to(device), stat_b.to(device)
            
            optimizer.zero_grad()
            
            if cand_id == 'F1':
                vfwd_p, vlat_p, logit_stat = model(x_b)
                loss = 1.0 * crit_reg(vfwd_p, vfwd_b) + 1.0 * crit_reg(vlat_p, vlat_b) + 0.5 * crit_stat(logit_stat, stat_b)
            elif cand_id == 'F2':
                vfwd_p, vlat_p, spd_p, logit_stat = model(x_b)
                loss = 1.0 * crit_reg(vfwd_p, vfwd_b) + 1.0 * crit_reg(vlat_p, vlat_b) + 0.5 * crit_reg(spd_p, spd_b) + 0.5 * crit_stat(logit_stat, stat_b)
            elif cand_id == 'F3':
                vfwd_p, vlat_p, afwd_p, logit_stat = model(x_b)
                loss = 1.0 * crit_reg(vfwd_p, vfwd_b) + 1.0 * crit_reg(vlat_p, vlat_b) + 0.2 * crit_reg(afwd_p, afwd_b) + 0.5 * crit_stat(logit_stat, stat_b)
            elif cand_id == 'F4':
                vfwd_p, vlat_p, spd_p, afwd_p, logit_stat = model(x_b)
                loss = 1.0 * crit_reg(vfwd_p, vfwd_b) + 1.0 * crit_reg(vlat_p, vlat_b) + 0.5 * crit_reg(spd_p, spd_b) + 0.2 * crit_reg(afwd_p, afwd_b) + 0.5 * crit_stat(logit_stat, stat_b)
                
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * len(vfwd_b)
            
        scheduler.step()
        train_loss /= len(train_dataset)
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_fwd_err = 0.0
        val_lat_err = 0.0
        with torch.no_grad():
            for x_b, vfwd_b, vlat_b, spd_b, afwd_b, stat_b in val_loader:
                x_b = x_b.to(device)
                vfwd_b, vlat_b, spd_b, afwd_b, stat_b = vfwd_b.to(device), vlat_b.to(device), spd_b.to(device), afwd_b.to(device), stat_b.to(device)
                
                if cand_id == 'F1':
                    vfwd_p, vlat_p, logit_stat = model(x_b)
                    loss = 1.0 * crit_reg(vfwd_p, vfwd_b) + 1.0 * crit_reg(vlat_p, vlat_b) + 0.5 * crit_stat(logit_stat, stat_b)
                elif cand_id == 'F2':
                    vfwd_p, vlat_p, spd_p, logit_stat = model(x_b)
                    loss = 1.0 * crit_reg(vfwd_p, vfwd_b) + 1.0 * crit_reg(vlat_p, vlat_b) + 0.5 * crit_reg(spd_p, spd_b) + 0.5 * crit_stat(logit_stat, stat_b)
                elif cand_id == 'F3':
                    vfwd_p, vlat_p, afwd_p, logit_stat = model(x_b)
                    loss = 1.0 * crit_reg(vfwd_p, vfwd_b) + 1.0 * crit_reg(vlat_p, vlat_b) + 0.2 * crit_reg(afwd_p, afwd_b) + 0.5 * crit_stat(logit_stat, stat_b)
                elif cand_id == 'F4':
                    vfwd_p, vlat_p, spd_p, afwd_p, logit_stat = model(x_b)
                    loss = 1.0 * crit_reg(vfwd_p, vfwd_b) + 1.0 * crit_reg(vlat_p, vlat_b) + 0.5 * crit_reg(spd_p, spd_b) + 0.2 * crit_reg(afwd_p, afwd_b) + 0.5 * crit_stat(logit_stat, stat_b)
                    
                val_loss += loss.item() * len(vfwd_b)
                val_fwd_err += torch.sum(torch.abs(vfwd_p - vfwd_b)).item()
                val_lat_err += torch.sum(torch.abs(vlat_p - vlat_b)).item()
                
        val_loss /= len(val_dataset)
        fwd_mae = val_fwd_err / len(val_dataset)
        lat_mae = val_lat_err / len(val_dataset)
        
        if epoch % 5 == 0 or epoch == num_epochs:
            print(f"Epoch {epoch:02d}/{num_epochs:02d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Fwd MAE: {fwd_mae:.3f} m/s | Lat MAE: {lat_mae:.3f} m/s", flush=True)
            
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), best_model_path)
            
    print(f"Saved best model checkpoint to {best_model_path}", flush=True)
    return best_model_path

# ── 4. Inference Helper for Candidate Models ──────────────────────────────

def get_candidate_predictions(cand_id, window_size=40):
    if cand_id == 'F0':
        # Control M028 SpeedNetV2
        device = torch.device('cpu')
        model = SpeedNetV2(window_size=window_size).to(device)
        model.load_state_dict(torch.load('models/speednet_v2_w40.pth', map_location=device))
        model.eval()
        
        needed_indices = np.arange(window_size - 1, n_total)
        sub_windows = np.lib.stride_tricks.sliding_window_view(X_norm_all, window_shape=(window_size, 6), axis=(0, 1)).squeeze(1)
        sub_indices = needed_indices - (window_size - 1)
        sub_batch = sub_windows[sub_indices].astype(np.float32)
        
        vfwd_dict = {}; vlat_dict = {}; speed_dict = {}; prob_stat_dict = {}
        with torch.no_grad():
            v_p, w_p, logit_s, _ = model(torch.tensor(sub_batch, dtype=torch.float32).to(device))
            v_p = v_p.cpu().numpy()
            prob_s = torch.sigmoid(logit_s).cpu().numpy()
            
        for j, idx in enumerate(needed_indices):
            vfwd_dict[idx] = max(0.0, float(v_p[j]))
            vlat_dict[idx] = 0.0
            speed_dict[idx] = max(0.0, float(v_p[j]))
            prob_stat_dict[idx] = float(prob_s[j])
            
        return vfwd_dict, vlat_dict, speed_dict, prob_stat_dict

    device = torch.device('cpu')
    model_path = f'models/vw4_m050_{cand_id.lower()}.pth'
    
    if cand_id == 'F1':
        model = VelocityNetF1(window_size=window_size).to(device)
    elif cand_id == 'F2':
        model = VelocityNetF2(window_size=window_size).to(device)
    elif cand_id == 'F3':
        model = VelocityNetF3(window_size=window_size).to(device)
    elif cand_id == 'F4':
        model = VelocityNetF4(window_size=window_size).to(device)
        
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    
    needed_indices = np.arange(window_size - 1, n_total)
    sub_windows = np.lib.stride_tricks.sliding_window_view(X_norm_all, window_shape=(window_size, 6), axis=(0, 1)).squeeze(1)
    sub_indices = needed_indices - (window_size - 1)
    sub_batch = sub_windows[sub_indices].astype(np.float32)
    
    vfwd_dict = {}; vlat_dict = {}; speed_dict = {}; prob_stat_dict = {}
    with torch.no_grad():
        if cand_id == 'F1':
            vfwd_p, vlat_p, logit_s = model(torch.tensor(sub_batch, dtype=torch.float32).to(device))
            spd_p = torch.sqrt(vfwd_p**2 + vlat_p**2)
        elif cand_id == 'F2':
            vfwd_p, vlat_p, spd_p, logit_s = model(torch.tensor(sub_batch, dtype=torch.float32).to(device))
        elif cand_id == 'F3':
            vfwd_p, vlat_p, _, logit_s = model(torch.tensor(sub_batch, dtype=torch.float32).to(device))
            spd_p = torch.sqrt(vfwd_p**2 + vlat_p**2)
        elif cand_id == 'F4':
            vfwd_p, vlat_p, spd_p, _, logit_s = model(torch.tensor(sub_batch, dtype=torch.float32).to(device))
            
        vfwd_p = vfwd_p.cpu().numpy()
        vlat_p = vlat_p.cpu().numpy()
        spd_p  = spd_p.cpu().numpy()
        prob_s = torch.sigmoid(logit_s).cpu().numpy()
        
    for j, idx in enumerate(needed_indices):
        vfwd_dict[idx] = max(0.0, float(vfwd_p[j]))
        vlat_dict[idx] = float(vlat_p[j])
        speed_dict[idx] = max(0.0, float(spd_p[j]))
        prob_stat_dict[idx] = float(prob_s[j])
        
    return vfwd_dict, vlat_dict, speed_dict, prob_stat_dict

# ── 5. Downstream EKF Navigation Engine ──────────────────────────────────

def run_navigation_m050(
    vfwd_dict, vlat_dict, speed_dict, prob_stat_dict,
    sim_start_idx=108000, duration_sec=300, jerk_thresh=-1.00
):
    n = int(duration_sec / dt)
    pre_samples = PRE_SAMPLES
    sim_start = sim_start_idx - pre_samples
    sim_end   = sim_start_idx + n

    x_state = np.zeros(7)
    x_state[0] = x_gt_all[sim_start]; x_state[1] = y_gt_all[sim_start]
    x_state[2] = vx_gt_all[sim_start]; x_state[3] = vy_gt_all[sim_start]
    x_state[4] = np.radians(vbox_heading_deg[sim_start])

    P = np.diag([1.0, 1.0, 0.5, 0.5, np.radians(2.0)**2, 0.1, np.radians(0.5)**2])
    Q = np.diag([0.001, 0.001, 0.01, 0.01, np.radians(0.05)**2, 1e-5, 1e-6])
    R_gnss = np.diag([2.0**2, 2.0**2, 0.2**2, 0.2**2, np.radians(1.0)**2])
    H_gnss = np.zeros((5, 7)); H_gnss[:5, :5] = np.eye(5)
    R_v   = 1.0**2
    R_nhc = 0.20**2

    H_zupt = np.zeros((2, 7))
    H_zupt[0, 2] = 1.0; H_zupt[1, 3] = 1.0
    R_z = (0.20**2) * np.eye(2)

    # M013 F4 Physical Speed Constraint Pre-computation for vfwd
    v_f4_dict = {}
    v_prev_f4 = 0.0
    var_thresh = np.percentile(rolling_var_a[:idx_val_end], 75)
    w_turn_thresh = np.radians(5.0)

    for idx in range(sim_start, sim_end):
        v_net = vfwd_dict.get(idx, 0.0)
        a_m = a_long[idx]
        if rolling_var_a[idx] <= var_thresh and np.abs(w_yaw[idx]) <= w_turn_thresh:
            v_phys_bound = max(0.0, v_prev_f4 + a_m * dt)
            v_corr = min(v_net, v_phys_bound)
        else:
            v_corr = v_net
        v_f4_dict[idx] = v_corr
        v_prev_f4 = v_corr

    x_hist = []
    v_est_history = []
    v_meas_history = []

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

        is_stat_pred = (prob_stat_dict.get(idx, 0.0) > 0.70)

        if not is_outage:
            psi_meas = np.radians(vbox_heading_deg[idx])
            psi_diff = (psi_meas - x_state[4] + np.pi) % (2 * np.pi) - np.pi
            z_gnss = np.array([x_gt_all[idx], y_gt_all[idx], vx_gt_all[idx], vy_gt_all[idx], x_state[4] + psi_diff])
            y_meas = z_gnss - H_gnss @ x_state
            S = H_gnss @ P @ H_gnss.T + R_gnss
            K = P @ H_gnss.T @ np.linalg.inv(S)
            x_state = x_state + K @ y_meas
            P = (np.eye(7) - K @ H_gnss) @ P
            v_est_curr = np.sqrt(x_state[2]**2 + x_state[3]**2)
            v_est_history.append(v_est_curr)
        else:
            v_speednet = 0.0 if is_stat_pred else max(0.0, v_f4_dict.get(idx, 0.0))
            v_meas = v_speednet

            # M028 Causal IMU Jerk APM Logic
            if (not is_stat_pred) and (len(v_est_history) >= 5):
                is_decel = (a_long[idx] < -0.5)
                is_turn_ok = (np.abs(w_yaw[idx]) <= np.radians(3.0))

                if is_decel and is_turn_ok:
                    j_val = j_long_array[idx]
                    if (jerk_thresh is None) or (j_val < jerk_thresh):
                        delta_v_imu = np.sum(a_long[idx-4:idx+1]) * dt
                        v_anchor = v_est_history[-5]
                        z_apm = max(0.0, v_anchor + delta_v_imu)

                        if v_speednet > z_apm:
                            raw_corr = v_speednet - z_apm
                            bounded_corr = min(raw_corr, 0.50) # Locked M019 bound
                            v_meas = v_speednet - bounded_corr

            v_meas_history.append(v_meas)

            v_est   = np.sqrt(x_state[2]**2 + x_state[3]**2)
            v_denom = max(v_est, 1e-3)
            H_v = np.array([0, 0, x_state[2]/v_denom, x_state[3]/v_denom, 0, 0, 0])
            y_v = v_meas - v_est
            S_v = float(H_v @ P @ H_v.T + R_v)
            K_v = (P @ H_v.T) / S_v
            x_state = x_state + K_v * y_v
            P = (np.eye(7) - np.outer(K_v, H_v)) @ P

            if is_stat_pred:
                z_z = np.array([0.0, 0.0])
                y_z = z_z - H_zupt @ x_state
                if np.linalg.norm(y_z) <= 5.0:
                    S_z = H_zupt @ P @ H_zupt.T + R_z
                    K_z = P @ H_zupt.T @ np.linalg.inv(S_z)
                    x_state = x_state + K_z @ y_z
                    P = (np.eye(7) - K_z @ H_zupt) @ P

            # Standard 2D NHC Update
            v_lat_meas = vlat_dict.get(idx, 0.0) if not is_stat_pred else 0.0
            psi_c = x_state[4]
            v_lat_est = -x_state[2] * np.cos(psi_c) + x_state[3] * np.sin(psi_c)
            H_nhc = np.array([0, 0, -np.cos(psi_c), np.sin(psi_c),
                               x_state[2]*np.sin(psi_c) + x_state[3]*np.cos(psi_c), 0, 0])
            y_nhc = v_lat_meas - v_lat_est
            S_nhc = float(H_nhc @ P @ H_nhc.T + R_nhc)
            K_nhc = (P @ H_nhc.T) / S_nhc
            x_state = x_state + K_nhc * y_nhc
            P = (np.eye(7) - np.outer(K_nhc, H_nhc)) @ P

            v_est_curr = np.sqrt(x_state[2]**2 + x_state[3]**2)
            v_est_history.append(v_est_curr)

        if idx >= sim_start_idx:
            x_hist.append(x_state.copy())

    arr = np.array(x_hist)
    x_t = arr[:, 0]
    y_t = arr[:, 1]
    return x_t, y_t, np.array(v_est_history[-n:]), np.array(v_meas_history), np.array([])

# Pre-compute rolling IMU variance for physical constraint
rolling_var_a = np.zeros(n_total)
for i in range(5, n_total):
    rolling_var_a[i] = np.var(a_long[i-5:i])

# ── 6. Main Experiment Execution ─────────────────────────────────────────

if __name__ == '__main__':
    print("======================================================================", flush=True)
    print("M050 — LEARNED BODY-FRAME VELOCITY REPRESENTATION EXPERIMENT", flush=True)
    print("======================================================================", flush=True)
    
    # Step 1: Baseline Reproduction Check (F0 Control)
    print("\n--- Step 1: Baseline Reproduction Check (M028 Control F0) ---", flush=True)
    f0_fwd, f0_lat, f0_spd, f0_stat = get_candidate_predictions('F0')
    x_f0, y_f0, v_f0, _, head_err_f0 = run_navigation_m050(f0_fwd, f0_lat, f0_spd, f0_stat, sim_start_idx=108000, duration_sec=300)
    
    # Calculate baseline metrics at 60s, 120s, 300s, 1000m
    ref_x = x_gt_all[start_idx:start_idx+3000]
    ref_y = y_gt_all[start_idx:start_idx+3000]
    ref_dist = np.cumsum(np.sqrt(np.diff(ref_x, prepend=ref_x[0])**2 + np.diff(ref_y, prepend=ref_y[0])**2))
    
    pos_err_f0 = np.sqrt((x_f0 - ref_x)**2 + (y_f0 - ref_y)**2)
    
    e60_f0  = pos_err_f0[599]
    e120_f0 = pos_err_f0[1199]
    e300_f0 = pos_err_f0[2999]
    
    idx_1km = np.searchsorted(ref_dist, 1000.0)
    if idx_1km >= len(pos_err_f0): idx_1km = len(pos_err_f0) - 1
    e1km_f0 = pos_err_f0[idx_1km]
    
    fper_f0 = pos_err_f0 / np.maximum(ref_dist, 1e-3) * 100.0
    compliant_mask_f0 = (fper_f0 <= 10.0)
    max_comp_f0 = ref_dist[np.where(compliant_mask_f0)[0][-1]] if np.any(compliant_mask_f0) else 0.0
    
    print(f"M028 Baseline Test: 60s={e60_f0:.2f}m | 120s={e120_f0:.2f}m | 300s={e300_f0:.2f}m | 1km={e1km_f0:.2f}m | Max Compliant={max_comp_f0:.2f}m", flush=True)
    
    # Step 2: Train Candidate Models (F1 - F4)
    print("\n--- Step 2: Training Candidate Models (F1, F2, F3, F4) ---", flush=True)
    candidates = ['F1', 'F2', 'F3', 'F4']
    for cand in candidates:
        train_candidate_model(cand, window_size=40, num_epochs=15)
        
    # Step 3: Validation Partition Evaluation (88566:107535)
    print("\n======================================================================", flush=True)
    print("STEP 3: VALIDATION EVALUATION & CANDIDATE SELECTION (Partition 88566:107535)", flush=True)
    print("======================================================================", flush=True)
    
    val_start_k = 88566
    dur_val = int((107535 - 88566) * dt) # ~1896 seconds
    
    val_results = {}
    cand_preds = {'F0': (f0_fwd, f0_lat, f0_spd, f0_stat)}
    
    for cand in ['F0'] + candidates:
        if cand != 'F0':
            cand_preds[cand] = get_candidate_predictions(cand)
            
        vfwd_d, vlat_d, spd_d, stat_d = cand_preds[cand]
        
        # Calculate Validation Velocity MAEs
        val_indices = np.arange(idx_train_end, idx_val_end)
        pred_fwd = np.array([vfwd_d.get(k, 0.0) for k in val_indices])
        pred_lat = np.array([vlat_d.get(k, 0.0) for k in val_indices])
        pred_spd = np.array([spd_d.get(k, 0.0) for k in val_indices])
        
        gt_fwd = v_fwd_gt[val_indices]
        gt_lat = v_lat_gt[val_indices]
        gt_spd = speed_gt[val_indices]
        
        mae_fwd = float(np.mean(np.abs(pred_fwd - gt_fwd)))
        mae_lat = float(np.mean(np.abs(pred_lat - gt_lat)))
        mae_spd = float(np.mean(np.abs(pred_spd - gt_spd)))
        mae_vec = float(np.mean(np.sqrt((pred_fwd - gt_fwd)**2 + (pred_lat - gt_lat)**2)))
        
        # Run Validation Navigation Filter
        x_val, y_val, _, _, _ = run_navigation_m050(vfwd_d, vlat_d, spd_d, stat_d, sim_start_idx=val_start_k, duration_sec=300)
        ref_val_x = x_gt_all[val_start_k:val_start_k+3000]
        ref_val_y = y_gt_all[val_start_k:val_start_k+3000]
        ref_val_dist = np.cumsum(np.sqrt(np.diff(ref_val_x, prepend=ref_val_x[0])**2 + np.diff(ref_val_y, prepend=ref_val_y[0])**2))
        
        val_pos_err = np.sqrt((x_val - ref_val_x)**2 + (y_val - ref_val_y)**2)
        val_60s  = float(val_pos_err[599])
        val_120s = float(val_pos_err[1199])
        val_300s = float(val_pos_err[2999])
        
        idx_val_1km = np.searchsorted(ref_val_dist, 1000.0)
        val_1km  = float(val_pos_err[idx_val_1km if idx_val_1km < len(val_pos_err) else -1])
        
        val_results[cand] = {
            'mae_fwd_ms': mae_fwd,
            'mae_lat_ms': mae_lat,
            'mae_spd_ms': mae_spd,
            'mae_vec_ms': mae_vec,
            'val_60s_m': val_60s,
            'val_120s_m': val_120s,
            'val_300s_m': val_300s,
            'val_1km_m': val_1km
        }
        
        print(f"Cand {cand:2s} | Fwd MAE: {mae_fwd:.3f} m/s | Lat MAE: {mae_lat:.3f} m/s | Val 60s: {val_60s:.2f}m | Val 120s: {val_120s:.2f}m | Val 300s: {val_300s:.2f}m | Val 1km: {val_1km:.2f}m", flush=True)

    # Validation Winner Selection (Lowest Val 300s Navigation Error)
    best_cand = min(val_results.keys(), key=lambda c: val_results[c]['val_300s_m'])
    print(f"\n--> SELECTION: Best Validation Candidate is '{best_cand}' with Val 300s Error = {val_results[best_cand]['val_300s_m']:.2f} m", flush=True)

    # Step 4: Locked Test Evaluation (start_idx = 108000)
    print("\n======================================================================", flush=True)
    print(f"STEP 4: LOCKED UNSEEN TEST EVALUATION (start_idx = 108,000)")
    print("======================================================================", flush=True)
    
    test_results = {}
    test_histories = {}
    
    for cand in ['F0'] + candidates:
        vfwd_d, vlat_d, spd_d, stat_d = cand_preds[cand]
        x_t, y_t, v_est_t, v_meas_t, head_err_t = run_navigation_m050(vfwd_d, vlat_d, spd_d, stat_d, sim_start_idx=108000, duration_sec=300)
        
        pos_err_t = np.sqrt((x_t - ref_x)**2 + (y_t - ref_y)**2)
        
        e60  = float(pos_err_t[599])
        e120 = float(pos_err_t[1199])
        e300 = float(pos_err_t[2999])
        e1km = float(pos_err_t[idx_1km])
        
        fper_t = pos_err_t / np.maximum(ref_dist, 1e-3) * 100.0
        compliant_t = (fper_t <= 10.0)
        max_comp_t = float(ref_dist[np.where(compliant_t)[0][-1]]) if np.any(compliant_t) else 0.0
        
        # Test Velocity MAEs
        test_indices = np.arange(108000, 108000 + 3000)
        t_fwd_p = np.array([vfwd_d.get(k, 0.0) for k in test_indices])
        t_lat_p = np.array([vlat_d.get(k, 0.0) for k in test_indices])
        t_spd_p = np.array([spd_d.get(k, 0.0) for k in test_indices])
        
        t_fwd_gt = v_fwd_gt[test_indices]
        t_lat_gt = v_lat_gt[test_indices]
        t_spd_gt = speed_gt[test_indices]
        
        t_mae_fwd = float(np.mean(np.abs(t_fwd_p - t_fwd_gt)))
        t_mae_lat = float(np.mean(np.abs(t_lat_p - t_lat_gt)))
        t_mae_spd = float(np.mean(np.abs(t_spd_p - t_spd_gt)))
        
        test_results[cand] = {
            't_mae_fwd_ms': t_mae_fwd,
            't_mae_lat_ms': t_mae_lat,
            't_mae_spd_ms': t_mae_spd,
            'e60_m': e60,
            'fper60': float(fper_t[599]),
            'e120_m': e120,
            'fper120': float(fper_t[1199]),
            'e300_m': e300,
            'fper300': float(fper_t[2999]),
            'e1km_m': e1km,
            'fper1km': float(fper_t[idx_1km]),
            'max_compliant_dist_m': max_comp_t
        }
        
        test_histories[cand] = {
            'x': x_t, 'y': y_t, 'pos_err': pos_err_t, 'fper': fper_t, 'head_err': head_err_t
        }
        
        print(f"Cand {cand:2s} | Fwd MAE: {t_mae_fwd:.3f} m/s | 60s: {e60:.2f}m ({fper_t[599]:.2f}%) | 120s: {e120:.2f}m ({fper_t[1199]:.2f}%) | 300s: {e300:.2f}m ({fper_t[2999]:.2f}%) | 1km: {e1km:.2f}m ({fper_t[idx_1km]:.2f}%) | Max Comp: {max_comp_t:.2f}m", flush=True)

    # Step 5: Turn-Regime & Braking Analysis
    print("\n--- Step 5: Turn-Regime & Braking Error Decomposition ---", flush=True)
    test_indices = np.arange(108000, 108000 + 3000)
    w_yaw_test = np.abs(w_yaw[test_indices])
    a_long_test = a_long[test_indices]
    
    mask_straight = (w_yaw_test <= np.radians(5.0))
    mask_mod_turn = (w_yaw_test > np.radians(5.0)) & (w_yaw_test <= np.radians(10.0))
    mask_str_turn = (w_yaw_test > np.radians(10.0))
    mask_braking  = (a_long_test < -0.5)
    
    turn_analysis = {}
    for cand in ['F0'] + candidates:
        vfwd_d, vlat_d, spd_d, _ = cand_preds[cand]
        t_fwd_p = np.array([vfwd_d.get(k, 0.0) for k in test_indices])
        t_lat_p = np.array([vlat_d.get(k, 0.0) for k in test_indices])
        
        t_fwd_gt = v_fwd_gt[test_indices]
        t_lat_gt = v_lat_gt[test_indices]
        
        err_fwd = np.abs(t_fwd_p - t_fwd_gt)
        err_lat = np.abs(t_lat_p - t_lat_gt)
        
        turn_analysis[cand] = {
            'straight_fwd_mae': float(np.mean(err_fwd[mask_straight])),
            'mod_turn_fwd_mae': float(np.mean(err_fwd[mask_mod_turn])),
            'str_turn_fwd_mae': float(np.mean(err_fwd[mask_str_turn])),
            'braking_fwd_mae':  float(np.mean(err_fwd[mask_braking])),
            'straight_lat_mae': float(np.mean(err_lat[mask_straight])),
            'mod_turn_lat_mae': float(np.mean(err_lat[mask_mod_turn])),
            'str_turn_lat_mae': float(np.mean(err_lat[mask_str_turn])),
            'braking_lat_mae':  float(np.mean(err_lat[mask_braking]))
        }
        
    # Step 6: Final Verdict Determination
    e300_win = test_results[best_cand]['e300_m']
    e300_f0  = test_results['F0']['e300_m']
    
    if e300_win < e300_f0:
        verdict = "ACCEPTED"
        prod_changed = True
    elif val_results[best_cand]['val_300s_m'] < val_results['F0']['val_300s_m'] and e300_win >= e300_f0:
        verdict = "GENERALIZATION FAILURE"
        prod_changed = False
    else:
        verdict = "REJECTED"
        prod_changed = False
        
    print("\n======================================================================", flush=True)
    print(f"FINAL VERDICT: M050 is {verdict}")
    print(f"Production Baseline Changed: {prod_changed}")
    print(f"Selected Candidate: {best_cand}")
    print(f"300s Error: M028 = {e300_f0:.2f} m | {best_cand} = {e300_win:.2f} m (Diff: {e300_win - e300_f0:+.2f} m)")
    print("======================================================================", flush=True)

    # Save Results JSON
    m050_summary = {
        'verdict': verdict,
        'production_changed': prod_changed,
        'selected_candidate': best_cand,
        'val_results': val_results,
        'test_results': test_results,
        'turn_analysis': turn_analysis
    }
    
    with open('results/m050/m050_results.json', 'w') as f:
        json.dump(m050_summary, f, indent=4)

    # Step 7: Plot Generation (12 Plots)
    print("\n--- Step 7: Generating Diagnostic Plots ---", flush=True)
    
    t_sec = np.arange(3000) * dt
    
    # 1. m050_speed_prediction_comparison.png
    plt.figure(figsize=(10, 5))
    plt.plot(t_sec, v_fwd_gt[test_indices] * 3.6, 'k--', label='VBOX GT Speed', alpha=0.8)
    plt.plot(t_sec, np.array([cand_preds['F0'][0].get(k, 0) for k in test_indices]) * 3.6, label='F0 (SpeedNet v2)', alpha=0.7)
    plt.plot(t_sec, np.array([cand_preds[best_cand][0].get(k, 0) for k in test_indices]) * 3.6, label=f'{best_cand} Predicted Fwd Speed', alpha=0.7)
    plt.xlabel('Time (s)'); plt.ylabel('Speed (km/h)'); plt.title('M050: Speed Prediction Comparison on Test Set')
    plt.grid(True, linestyle='--', alpha=0.5); plt.legend()
    plt.savefig('results/plots/m050_speed_prediction_comparison.png', dpi=300)
    plt.close()

    # 2. m050_forward_velocity_prediction.png
    plt.figure(figsize=(10, 5))
    plt.plot(t_sec, v_fwd_gt[test_indices], 'k--', label='GT Forward Velocity (m/s)')
    for cand in candidates:
        plt.plot(t_sec, np.array([cand_preds[cand][0].get(k, 0) for k in test_indices]), label=f'{cand} Fwd Vel', alpha=0.7)
    plt.xlabel('Time (s)'); plt.ylabel('Forward Velocity (m/s)'); plt.title('M050: Forward Velocity Predictions Across Candidates')
    plt.grid(True, linestyle='--', alpha=0.5); plt.legend()
    plt.savefig('results/plots/m050_forward_velocity_prediction.png', dpi=300)
    plt.close()

    # 3. m050_lateral_velocity_prediction.png
    plt.figure(figsize=(10, 5))
    plt.plot(t_sec, v_lat_gt[test_indices], 'k--', label='GT Lateral Velocity (m/s)')
    for cand in candidates:
        plt.plot(t_sec, np.array([cand_preds[cand][1].get(k, 0) for k in test_indices]), label=f'{cand} Lat Vel', alpha=0.7)
    plt.xlabel('Time (s)'); plt.ylabel('Lateral Velocity (m/s)'); plt.title('M050: Lateral Velocity Predictions Across Candidates')
    plt.grid(True, linestyle='--', alpha=0.5); plt.legend()
    plt.savefig('results/plots/m050_lateral_velocity_prediction.png', dpi=300)
    plt.close()

    # 4. m050_velocity_vector_error.png
    plt.figure(figsize=(10, 5))
    for cand in ['F0'] + candidates:
        fwd_p = np.array([cand_preds[cand][0].get(k, 0) for k in test_indices])
        lat_p = np.array([cand_preds[cand][1].get(k, 0) for k in test_indices])
        vec_err = np.sqrt((fwd_p - v_fwd_gt[test_indices])**2 + (lat_p - v_lat_gt[test_indices])**2)
        plt.plot(t_sec, vec_err, label=f'{cand} Vector Error', alpha=0.7)
    plt.xlabel('Time (s)'); plt.ylabel('Velocity Vector Error (m/s)'); plt.title('M050: Velocity Vector Absolute Error')
    plt.grid(True, linestyle='--', alpha=0.5); plt.legend()
    plt.savefig('results/plots/m050_velocity_vector_error.png', dpi=300)
    plt.close()

    # 5. m050_braking_region_comparison.png
    plt.figure(figsize=(10, 5))
    plt.plot(t_sec[mask_braking], v_fwd_gt[test_indices][mask_braking], 'k.', label='GT Braking Speed')
    for cand in ['F0', best_cand]:
        fwd_p = np.array([cand_preds[cand][0].get(k, 0) for k in test_indices])
        plt.plot(t_sec[mask_braking], fwd_p[mask_braking], '.', label=f'{cand} Braking Speed')
    plt.xlabel('Time (s)'); plt.ylabel('Speed (m/s)'); plt.title('M050: Speed Estimation During Braking Events')
    plt.grid(True, linestyle='--', alpha=0.5); plt.legend()
    plt.savefig('results/plots/m050_braking_region_comparison.png', dpi=300)
    plt.close()

    # 6. m050_turn_region_comparison.png
    plt.figure(figsize=(10, 5))
    plt.plot(t_sec[mask_str_turn], np.abs(v_lat_gt[test_indices][mask_str_turn]), 'k.', label='GT Lateral Speed (Strong Turn)')
    for cand in candidates:
        lat_p = np.array([cand_preds[cand][1].get(k, 0) for k in test_indices])
        plt.plot(t_sec[mask_str_turn], np.abs(lat_p[mask_str_turn]), '.', label=f'{cand} Lat Speed', alpha=0.7)
    plt.xlabel('Time (s)'); plt.ylabel('Lateral Speed (m/s)'); plt.title('M050: Lateral Speed During Strong Turning (>10 deg/s)')
    plt.grid(True, linestyle='--', alpha=0.5); plt.legend()
    plt.savefig('results/plots/m050_turn_region_comparison.png', dpi=300)
    plt.close()

    # 7. m050_val_nav_error_vs_candidate.png
    plt.figure(figsize=(8, 5))
    cands_all = ['F0'] + candidates
    val_300s_errs = [val_results[c]['val_300s_m'] for c in cands_all]
    plt.bar(cands_all, val_300s_errs, color=['navy', 'teal', 'tab:orange', 'tab:green', 'crimson'])
    plt.axhline(val_results['F0']['val_300s_m'], color='r', linestyle='--', label='F0 Control')
    plt.xlabel('Candidate'); plt.ylabel('Validation 300s Navigation Error (m)'); plt.title('M050: Validation 300s Navigation Performance')
    plt.grid(True, linestyle='--', alpha=0.5); plt.legend()
    plt.savefig('results/plots/m050_val_nav_error_vs_candidate.png', dpi=300)
    plt.close()

    # 8. m050_locked_nav_trajectory.png
    plt.figure(figsize=(9, 8))
    plt.plot(ref_x, ref_y, 'k-', linewidth=2, label='VBOX Ground Truth')
    plt.plot(test_histories['F0']['x'], test_histories['F0']['y'], 'r--', label='F0 Control (M028)')
    plt.plot(test_histories[best_cand]['x'], test_histories[best_cand]['y'], 'b-', label=f'{best_cand} Candidate (Best Val)')
    plt.xlabel('East Position (m)'); plt.ylabel('North Position (m)'); plt.title('M050: Locked Test Navigation Trajectories (300s)')
    plt.axis('equal'); plt.grid(True, linestyle='--', alpha=0.5); plt.legend()
    plt.savefig('results/plots/m050_locked_nav_trajectory.png', dpi=300)
    plt.close()

    # 9. m050_position_error_vs_distance.png
    plt.figure(figsize=(10, 5))
    for cand in ['F0'] + candidates:
        plt.plot(ref_dist, test_histories[cand]['pos_err'], label=f'{cand} Pos Err')
    plt.xlabel('Reference Distance (m)'); plt.ylabel('Position Error (m)'); plt.title('M050: Position Drift vs Distance Travelled')
    plt.grid(True, linestyle='--', alpha=0.5); plt.legend()
    plt.savefig('results/plots/m050_position_error_vs_distance.png', dpi=300)
    plt.close()

    # 10. m050_sih_fper_vs_distance.png
    plt.figure(figsize=(10, 5))
    for cand in ['F0'] + candidates:
        plt.plot(ref_dist, test_histories[cand]['fper'], label=f'{cand} FPER (%)')
    plt.axhline(10.0, color='r', linestyle='--', label='SIH 10% Threshold')
    plt.xlabel('Reference Distance (m)'); plt.ylabel('FPER (%)'); plt.title('M050: SIH Distance-Normalized Error FPER (%)')
    plt.ylim(0, 60); plt.grid(True, linestyle='--', alpha=0.5); plt.legend()
    plt.savefig('results/plots/m050_sih_fper_vs_distance.png', dpi=300)
    plt.close()

    # 11. m050_checkpoints_comparison.png
    plt.figure(figsize=(9, 5))
    x_indices = np.arange(len(cands_all))
    w_bar = 0.25
    plt.bar(x_indices - w_bar, [test_results[c]['e60_m'] for c in cands_all], width=w_bar, label='60s Error')
    plt.bar(x_indices, [test_results[c]['e120_m'] for c in cands_all], width=w_bar, label='120s Error')
    plt.bar(x_indices + w_bar, [test_results[c]['e300_m'] for c in cands_all], width=w_bar, label='300s Error')
    plt.xticks(x_indices, cands_all); plt.ylabel('Position Error (m)'); plt.title('M050: Position Error at Standard Checkpoints')
    plt.grid(True, linestyle='--', alpha=0.5); plt.legend()
    plt.savefig('results/plots/m050_checkpoints_comparison.png', dpi=300)
    plt.close()

    # 12. m050_1km_comparison.png
    plt.figure(figsize=(8, 5))
    e1kms = [test_results[c]['e1km_m'] for c in cands_all]
    plt.bar(cands_all, e1kms, color='purple', alpha=0.7)
    plt.axhline(test_results['F0']['e1km_m'], color='r', linestyle='--', label='F0 Control (1km)')
    plt.xlabel('Candidate'); plt.ylabel('1 km Position Error (m)'); plt.title('M050: 1 km Integrated Position Drift Comparison')
    plt.grid(True, linestyle='--', alpha=0.5); plt.legend()
    plt.savefig('results/plots/m050_1km_comparison.png', dpi=300)
    plt.close()

    print("All 12 diagnostic plots successfully generated in results/plots/", flush=True)
