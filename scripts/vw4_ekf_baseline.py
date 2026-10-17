import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# Ensure required output directories exist
os.makedirs('scripts', exist_ok=True)
os.makedirs('plots/vw4/ekf_baseline', exist_ok=True)
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

# Resample signals
raw_ax = interp1d(t_s_utc, df_s.iloc[:, 9], fill_value='extrapolate')(t_sync)
raw_ay = interp1d(t_s_utc, df_s.iloc[:, 10], fill_value='extrapolate')(t_sync)
raw_az = interp1d(t_s_utc, df_s.iloc[:, 11], fill_value='extrapolate')(t_sync)

grav_x = interp1d(t_s_utc, df_s.iloc[:, 12], fill_value='extrapolate')(t_sync)
grav_y = interp1d(t_s_utc, df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
grav_z = interp1d(t_s_utc, df_s.iloc[:, 14], fill_value='extrapolate')(t_sync)

gyro_pitch = interp1d(t_s_utc, df_s['GYROSCOPE Pitch (rad/s)'], fill_value='extrapolate')(t_sync)

vbox_lat = interp1d(t_v_utc, df_v['Latitude (degrees)'], fill_value='extrapolate')(t_sync)
vbox_lon = interp1d(t_v_utc, df_v['Longitude (degrees)'], fill_value='extrapolate')(t_sync)
vbox_vel_ms = interp1d(t_v_utc, df_v['Velocity (km/hr)'] / 3.6, fill_value='extrapolate')(t_sync)
vbox_heading_deg = interp1d(t_v_utc, df_v['Heading (degrees)'], fill_value='extrapolate')(t_sync)

a_long = -(raw_ay - grav_y) # m/s^2
w_yaw = -gyro_pitch         # rad/s

# Global ENU ground truth
lat0, lon0 = vbox_lat[0], vbox_lon[0]
R_earth = 6378137.0
lat_rad = np.radians(vbox_lat)
lon_rad = np.radians(vbox_lon)
x_gt_all = (lon_rad - np.radians(lon0)) * R_earth * np.cos(np.radians(lat0))
y_gt_all = (lat_rad - np.radians(lat0)) * R_earth
vx_gt_all = vbox_vel_ms * np.sin(np.radians(vbox_heading_deg))
vy_gt_all = vbox_vel_ms * np.cos(np.radians(vbox_heading_deg))

# --- Model 1: Raw Open-Loop DR ---
def run_raw_dr(start_idx, duration_sec):
    n = int(duration_sec / dt)
    v_dr = np.zeros(n)
    psi_dr = np.zeros(n)
    x_dr = np.zeros(n)
    y_dr = np.zeros(n)
    
    v_dr[0] = vbox_vel_ms[start_idx]
    psi_dr[0] = np.radians(vbox_heading_deg[start_idx])
    
    for i in range(1, n):
        psi_dr[i] = psi_dr[i-1] + w_yaw[start_idx + i] * dt
        v_dr[i] = v_dr[i-1] + a_long[start_idx + i] * dt
        if v_dr[i] < 0: v_dr[i] = 0.0
        
        x_dr[i] = x_dr[i-1] + v_dr[i] * np.sin(psi_dr[i]) * dt
        y_dr[i] = y_dr[i-1] + v_dr[i] * np.cos(psi_dr[i]) * dt
        
    return x_dr, y_dr, v_dr, np.degrees(psi_dr)

# --- Model 2: Calibrated Open-Loop DR ---
def run_calib_dr(start_idx, duration_sec):
    n = int(duration_sec / dt)
    b_accel_pre = np.mean(a_long[start_idx - 100 : start_idx]) # ~1.1871 m/s^2
    a_long_cal = a_long - b_accel_pre
    
    v_dr = np.zeros(n)
    psi_dr = np.zeros(n)
    x_dr = np.zeros(n)
    y_dr = np.zeros(n)
    
    v_dr[0] = vbox_vel_ms[start_idx]
    psi_dr[0] = np.radians(vbox_heading_deg[start_idx])
    
    for i in range(1, n):
        psi_dr[i] = psi_dr[i-1] + w_yaw[start_idx + i] * dt
        v_dr[i] = v_dr[i-1] + a_long_cal[start_idx + i] * dt
        if v_dr[i] < 0: v_dr[i] = 0.0
        
        x_dr[i] = x_dr[i-1] + v_dr[i] * np.sin(psi_dr[i]) * dt
        y_dr[i] = y_dr[i-1] + v_dr[i] * np.cos(psi_dr[i]) * dt
        
    return x_dr, y_dr, v_dr, np.degrees(psi_dr)

# --- Model 3: EKF/INS Sensor Fusion ---
def run_ekf(start_idx, duration_sec):
    n = int(duration_sec / dt)
    pre_samples = 300 # 30s GNSS aiding before outage
    sim_start = start_idx - pre_samples
    sim_end = start_idx + n
    
    # State x = [x, y, vx, vy, psi, ba, bw]^T
    x_state = np.zeros(7)
    x_state[0] = x_gt_all[sim_start]
    x_state[1] = y_gt_all[sim_start]
    x_state[2] = vx_gt_all[sim_start]
    x_state[3] = vy_gt_all[sim_start]
    x_state[4] = np.radians(vbox_heading_deg[sim_start])
    
    P = np.diag([1.0, 1.0, 0.5, 0.5, np.radians(2.0)**2, 0.1, np.radians(0.5)**2])
    Q = np.diag([0.001, 0.001, 0.01, 0.01, np.radians(0.05)**2, 1e-5, 1e-6])
    R_gnss = np.diag([2.0**2, 2.0**2, 0.2**2, 0.2**2, np.radians(1.0)**2])
    H = np.zeros((5, 7))
    for k_idx in range(5): H[k_idx, k_idx] = 1.0
    
    x_hist = []
    for idx in range(sim_start, sim_end):
        is_outage = (idx >= start_idx)
        
        a_m = a_long[idx]
        w_m = w_yaw[idx]
        x, y, vx, vy, psi, ba, bw = x_state
        
        a_hat = a_m - ba
        w_hat = w_m - bw
        
        psi_new = psi + w_hat * dt
        ax_enu = a_hat * np.sin(psi_new)
        ay_enu = a_hat * np.cos(psi_new)
        
        vx_new = vx + ax_enu * dt
        vy_new = vy + ay_enu * dt
        x_new = x + vx_new * dt
        y_new = y + vy_new * dt
        
        x_state = np.array([x_new, y_new, vx_new, vy_new, psi_new, ba, bw])
        
        F = np.eye(7)
        F[0, 2] = dt
        F[1, 3] = dt
        F[2, 4] = a_hat * np.cos(psi_new) * dt
        F[3, 4] = -a_hat * np.sin(psi_new) * dt
        F[2, 5] = -np.sin(psi_new) * dt
        F[3, 5] = -np.cos(psi_new) * dt
        F[4, 6] = -dt
        
        P = F @ P @ F.T + Q
        
        if not is_outage:
            psi_meas = np.radians(vbox_heading_deg[idx])
            psi_diff = (psi_meas - x_state[4] + np.pi) % (2 * np.pi) - np.pi
            psi_meas_unwrapped = x_state[4] + psi_diff
            
            z_gnss = np.array([x_gt_all[idx], y_gt_all[idx], vx_gt_all[idx], vy_gt_all[idx], psi_meas_unwrapped])
            y_meas = z_gnss - H @ x_state
            S = H @ P @ H.T + R_gnss
            K = P @ H.T @ np.linalg.inv(S)
            x_state = x_state + K @ y_meas
            P = (np.eye(7) - K @ H) @ P
            
        x_hist.append(x_state.copy())
        
    x_hist_arr = np.array(x_hist)[-n:]
    x_ekf = x_hist_arr[:, 0] - x_hist_arr[0, 0]
    y_ekf = x_hist_arr[:, 1] - x_hist_arr[0, 1]
    v_ekf = np.sqrt(x_hist_arr[:, 2]**2 + x_hist_arr[:, 3]**2)
    psi_ekf_deg = np.degrees(x_hist_arr[:, 4])
    return x_ekf, y_ekf, v_ekf, psi_ekf_deg

def evaluate_run(x_dr, y_dr, v_dr, psi_dr_deg, start_idx, duration_sec, model_name):
    n = int(duration_sec / dt)
    lat0, lon0 = vbox_lat[start_idx], vbox_lon[start_idx]
    lat_rad = np.radians(vbox_lat[start_idx : start_idx + n])
    lon_rad = np.radians(vbox_lon[start_idx : start_idx + n])
    x_gt = (lon_rad - np.radians(lon0)) * R_earth * np.cos(np.radians(lat0))
    y_gt = (lat_rad - np.radians(lat0)) * R_earth
    v_gt = vbox_vel_ms[start_idx : start_idx + n]
    psi_gt_deg = vbox_heading_deg[start_idx : start_idx + n]
    
    pos_err = np.sqrt((x_dr - x_gt)**2 + (y_dr - y_gt)**2)
    dist_gt = np.sum(np.sqrt(np.diff(x_gt)**2 + np.diff(y_gt)**2))
    dist_dr = np.sum(v_dr) * dt
    
    cde_pct = (abs(dist_dr - dist_gt) / dist_gt) * 100.0
    final_pos_err = pos_error = pos_err[-1]
    max_pos_err = np.max(pos_err)
    vel_err_kmh = abs(v_dr[-1] - v_gt[-1]) * 3.6
    h_err_deg = abs((psi_dr_deg[-1] - psi_gt_deg[-1] + 180) % 360 - 180)
    
    return {
        'duration_sec': duration_sec,
        'model_name': model_name,
        'dist_gt_m': dist_gt,
        'dist_dr_m': dist_dr,
        'cde_pct': cde_pct,
        'final_pos_err_m': final_pos_err,
        'max_pos_err_m': max_pos_err,
        'vel_err_kmh': vel_err_kmh,
        'h_err_deg': h_err_deg,
        'x_dr': x_dr,
        'y_dr': y_dr,
        'v_dr': v_dr,
        'psi_dr_deg': psi_dr_deg,
        'pos_err': pos_err,
        'x_gt': x_gt,
        'y_gt': y_gt,
        'v_gt': v_gt,
        'psi_gt_deg': psi_gt_deg
    }

# Run evaluations for 60s, 120s, 300s across 3 models
start_idx = 48000
all_results = []

for dur in [60, 120, 300]:
    # Model 1: Raw DR
    xr, yr, vr, psir = run_raw_dr(start_idx, dur)
    res_r = evaluate_run(xr, yr, vr, psir, start_idx, dur, "1. Raw Open-Loop DR")
    
    # Model 2: Calibrated DR
    xc, yc, vc, psic = run_calib_dr(start_idx, dur)
    res_c = evaluate_run(xc, yc, vc, psic, start_idx, dur, "2. Calibrated Open-Loop DR")
    
    # Model 3: EKF/INS
    xe, ye, ve, psie = run_ekf(start_idx, dur)
    res_e = evaluate_run(xe, ye, ve, psie, start_idx, dur, "3. EKF/INS Sensor Fusion")
    
    all_results.extend([res_r, res_c, res_e])

df_res = pd.DataFrame(all_results)[['duration_sec', 'model_name', 'dist_gt_m', 'cde_pct', 'final_pos_err_m', 'max_pos_err_m', 'vel_err_kmh', 'h_err_deg']]

print("\n" + "="*90)
print("CLASSICAL EKF/INS BASELINE VS OPEN-LOOP DR COMPARISON")
print("="*90)
print(df_res.to_string(index=False))
print("="*90)

# --- Plotting Visualizations for 60s, 120s, 300s ---
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#eeeeee'

for dur in [60, 120, 300]:
    r_r = [r for r in all_results if r['duration_sec'] == dur and 'Raw' in r['model_name']][0]
    r_c = [r for r in all_results if r['duration_sec'] == dur and 'Calibrated' in r['model_name']][0]
    r_e = [r for r in all_results if r['duration_sec'] == dur and 'EKF' in r['model_name']][0]
    
    t_rel = np.arange(int(dur/dt)) * dt
    
    # Plot 1: Trajectory
    fig, ax = plt.subplots(figsize=(8.5, 7), dpi=150)
    ax.plot(r_r['x_gt'], r_r['y_gt'], label='VBOX Ground Truth', color='#e74c3c', linewidth=2.2, zorder=5)
    ax.plot(r_r['x_dr'], r_r['y_dr'], label='1. Raw Open-Loop DR', color='#95a5a6', linewidth=1.5, linestyle='--')
    ax.plot(r_c['x_dr'], r_c['y_dr'], label='2. Calibrated Open-Loop DR', color='#f39c12', linewidth=1.8, linestyle='-.')
    ax.plot(r_e['x_dr'], r_e['y_dr'], label='3. EKF/INS Sensor Fusion', color='#27ae60', linewidth=2.0)
    ax.scatter([0], [0], color='#27ae60', s=90, label='Start Point', zorder=6)
    ax.scatter([r_r['x_gt'][-1]], [r_r['y_gt'][-1]], color='#c0392b', s=90, label='VBOX Endpoint', zorder=6)
    ax.set_title(f'Trajectory Comparison ({dur}s GNSS Outage)', fontsize=12, fontweight='bold', pad=10)
    ax.set_xlabel('East Displacement (meters)')
    ax.set_ylabel('North Displacement (meters)')
    ax.legend(loc='best', frameon=True, fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(f'plots/vw4/ekf_baseline/outage_{dur}s_trajectory.png')
    plt.close()

    # Plot 2: Position Error Over Time
    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
    ax.plot(t_rel, r_r['pos_err'], label='1. Raw Open-Loop DR', color='#95a5a6', linewidth=1.5, linestyle='--')
    ax.plot(t_rel, r_c['pos_err'], label='2. Calibrated Open-Loop DR', color='#f39c12', linewidth=1.8, linestyle='-.')
    ax.plot(t_rel, r_e['pos_err'], label='3. EKF/INS Sensor Fusion (Best)', color='#27ae60', linewidth=2.0)
    ax.set_title(f'Position Error Accumulation Over Time ({dur}s Outage)', fontsize=12, fontweight='bold', pad=10)
    ax.set_xlabel('Outage Elapsed Time (seconds)')
    ax.set_ylabel('Position Error (meters)')
    ax.legend(loc='upper left', frameon=True)
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(f'plots/vw4/ekf_baseline/outage_{dur}s_position_error.png')
    plt.close()

    # Plot 3: Velocity Comparison
    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
    ax.plot(t_rel, r_r['v_gt'] * 3.6, label='VBOX True Velocity', color='#e74c3c', linewidth=2.2)
    ax.plot(t_rel, r_r['v_dr'] * 3.6, label='1. Raw Open-Loop DR', color='#95a5a6', linewidth=1.5, linestyle='--')
    ax.plot(t_rel, r_c['v_dr'] * 3.6, label='2. Calibrated Open-Loop DR', color='#f39c12', linewidth=1.8, linestyle='-.')
    ax.plot(t_rel, r_e['v_dr'] * 3.6, label='3. EKF/INS Sensor Fusion', color='#27ae60', linewidth=2.0)
    ax.set_title(f'Velocity Drift Comparison ({dur}s Outage)', fontsize=12, fontweight='bold', pad=10)
    ax.set_xlabel('Outage Elapsed Time (seconds)')
    ax.set_ylabel('Speed (km/h)')
    ax.legend(loc='best', frameon=True)
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(f'plots/vw4/ekf_baseline/outage_{dur}s_velocity.png')
    plt.close()

    # Plot 4: Heading Comparison
    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
    ax.plot(t_rel, r_r['psi_gt_deg'], label='VBOX True Heading', color='#e74c3c', linewidth=2.2)
    ax.plot(t_rel, r_r['psi_dr_deg'], label='1 & 2. Open-Loop DR', color='#95a5a6', linewidth=1.8, linestyle='--')
    ax.plot(t_rel, r_e['psi_dr_deg'], label='3. EKF/INS Sensor Fusion', color='#27ae60', linewidth=2.0)
    ax.set_title(f'Heading Angle Comparison ({dur}s Outage)', fontsize=12, fontweight='bold', pad=10)
    ax.set_xlabel('Outage Elapsed Time (seconds)')
    ax.set_ylabel('Heading Angle (degrees)')
    ax.legend(loc='best', frameon=True)
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(f'plots/vw4/ekf_baseline/outage_{dur}s_heading.png')
    plt.close()

print("\nAll 12 EKF baseline plots saved in: plots/vw4/ekf_baseline/")
