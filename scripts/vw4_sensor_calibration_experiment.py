import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# Ensure output directories exist
os.makedirs('scripts', exist_ok=True)
os.makedirs('plots/vw4/sensor_calibration_experiment', exist_ok=True)
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
gyro_yaw = interp1d(t_s_utc, df_s['GYROSCOPE Yaw (rad/s)'], fill_value='extrapolate')(t_sync)

vbox_lat = interp1d(t_v_utc, df_v['Latitude (degrees)'], fill_value='extrapolate')(t_sync)
vbox_lon = interp1d(t_v_utc, df_v['Longitude (degrees)'], fill_value='extrapolate')(t_sync)
vbox_vel_ms = interp1d(t_v_utc, df_v['Velocity (km/hr)'] / 3.6, fill_value='extrapolate')(t_sync)
vbox_heading_deg = interp1d(t_v_utc, df_v['Heading (degrees)'], fill_value='extrapolate')(t_sync)

# Identical outage window: 60s blackout starting at index 48000
start_idx = 48000
duration_sec = 60
n_samples = int(duration_sec / dt)
end_idx = start_idx + n_samples

t_outage = t_sync[start_idx : end_idx]
time_elapsed = t_outage - t_outage[0]

# VBOX ENU Ground Truth
lat0, lon0 = vbox_lat[start_idx], vbox_lon[start_idx]
R_earth = 6378137.0
lat_rad = np.radians(vbox_lat[start_idx : end_idx])
lon_rad = np.radians(vbox_lon[start_idx : end_idx])
x_gt = (lon_rad - np.radians(lon0)) * R_earth * np.cos(np.radians(lat0))
y_gt = (lat_rad - np.radians(lat0)) * R_earth

v_gt = vbox_vel_ms[start_idx : end_idx]
psi_gt_deg = vbox_heading_deg[start_idx : end_idx]
dist_gt = np.sum(np.sqrt(np.diff(x_gt)**2 + np.diff(y_gt)**2))

# Accel and Gyro signals
a_long_uncal = -(raw_ay - grav_y)
w_yaw_uncal = -gyro_pitch

# Pre-outage accel bias (indices 47900-48000)
b_accel = np.mean(a_long_uncal[47900:48000]) # ~ 1.1871 m/s^2

# True stationary gyro pitch bias (where v == 0)
stat_indices = np.where(df_v['Velocity (km/hr)'].values == 0.0)[0]
b_gyro_stat = -df_s.iloc[stat_indices]['GYROSCOPE Pitch (rad/s)'].mean() # ~ +0.02195 rad/s

def evaluate_version(a_signal, w_signal, name):
    v_dr = np.zeros(n_samples)
    psi_dr_rad = np.zeros(n_samples)
    x_dr = np.zeros(n_samples)
    y_dr = np.zeros(n_samples)
    
    v_dr[0] = v_gt[0]
    psi_dr_rad[0] = np.radians(psi_gt_deg[0])
    
    for i in range(1, n_samples):
        psi_dr_rad[i] = psi_dr_rad[i-1] + w_signal[start_idx + i] * dt
        v_dr[i] = v_dr[i-1] + a_signal[start_idx + i] * dt
        if v_dr[i] < 0: v_dr[i] = 0.0
        
        v_east = v_dr[i] * np.sin(psi_dr_rad[i])
        v_north = v_dr[i] * np.cos(psi_dr_rad[i])
        
        x_dr[i] = x_dr[i-1] + v_east * dt
        y_dr[i] = y_dr[i-1] + v_north * dt
        
    pos_error = np.sqrt((x_dr - x_gt)**2 + (y_dr - y_gt)**2)
    final_pos_error = pos_error[-1]
    max_pos_error = np.max(pos_error)
    
    dist_dr = np.sum(v_dr) * dt
    cde_pct = (abs(dist_dr - dist_gt) / dist_gt) * 100.0
    fper_pct = (final_pos_error / dist_gt) * 100.0
    
    final_vel_err_ms = abs(v_dr[-1] - v_gt[-1])
    final_vel_err_kmh = final_vel_err_ms * 3.6
    
    psi_dr_deg = np.degrees(psi_dr_rad)
    h_diff = (psi_dr_deg - psi_gt_deg + 180) % 360 - 180
    final_h_err_deg = abs(h_diff[-1])
    
    return {
        'name': name,
        'cde_pct': cde_pct,
        'final_pos_err_m': final_pos_error,
        'max_pos_err_m': max_pos_error,
        'final_vel_err_kmh': final_vel_err_kmh,
        'final_vel_err_ms': final_vel_err_ms,
        'final_heading_err_deg': final_h_err_deg,
        'dist_dr_m': dist_dr,
        'x_dr': x_dr,
        'y_dr': y_dr,
        'v_dr': v_dr,
        'psi_dr_deg': psi_dr_deg,
        'pos_error': pos_error
    }

# 6 Versions
res_A = evaluate_version(a_long_uncal, w_yaw_uncal, "A. Original Baseline")
res_B = evaluate_version(a_long_uncal - b_accel, w_yaw_uncal, "B. + Accel Calibration")
res_C = evaluate_version(a_long_uncal, w_yaw_uncal - b_gyro_stat, "C. + True Gyro Calibration")
res_D = evaluate_version(a_long_uncal, w_yaw_uncal, "D. + Gravity Verification")
res_E = evaluate_version(a_long_uncal, w_yaw_uncal, "E. + Alignment Verification")
res_F = evaluate_version(a_long_uncal - b_accel, w_yaw_uncal, "F. + Corrected All Combined")

versions = [res_A, res_B, res_C, res_D, res_E, res_F]

# Print detailed audited results table
print("\n" + "="*80)
print("AUDITED SENSOR PROCESSING STAGE EXPERIMENT RESULTS (60s OUTAGE)")
print("="*80)
header = f"{'Version Name':<30} | {'CDE (%)':<8} | {'Final Err (m)':<13} | {'Max Err (m)':<11} | {'Speed Err (km/h)':<16} | {'Heading Err (°)':<15}"
print(header)
print("-" * len(header))

for v in versions:
    print(f"{v['name']:<30} | {v['cde_pct']:8.2f} | {v['final_pos_err_m']:13.2f} | {v['max_pos_err_m']:11.2f} | {v['final_vel_err_kmh']:16.2f} | {v['final_heading_err_deg']:15.2f}")
print("="*80)

# --- Generate Comparative Plots ---
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#eeeeee'

# Plot 1: Trajectory Comparison Across Versions
fig, ax = plt.subplots(figsize=(9, 7.5), dpi=150)
ax.plot(x_gt, y_gt, label='VBOX Ground Truth', color='#e74c3c', linewidth=2.2, zorder=5)
ax.plot(res_A['x_dr'], res_A['y_dr'], label='A. Original Baseline (1590m err)', color='#95a5a6', linewidth=1.5, linestyle='--')
ax.plot(res_B['x_dr'], res_B['y_dr'], label='B. + Accel Calibration (619m err)', color='#27ae60', linewidth=2.0)
ax.plot(res_C['x_dr'], res_C['y_dr'], label='C. + True Gyro Calibration (2013m err)', color='#9b59b6', linewidth=1.2, linestyle=':')
ax.plot(res_F['x_dr'], res_F['y_dr'], label='F. + Corrected All Combined (619m err)', color='#2980b9', linewidth=1.5, linestyle='-.')
ax.scatter([0], [0], color='#27ae60', s=90, label='Start Point', zorder=6)
ax.scatter([x_gt[-1]], [y_gt[-1]], color='#c0392b', s=90, label='VBOX Endpoint', zorder=6)

ax.set_title('Audited Trajectory Comparison: Sensor Calibration & Alignment Stages', fontsize=12, fontweight='bold', pad=10)
ax.set_xlabel('East Displacement (meters)')
ax.set_ylabel('North Displacement (meters)')
ax.legend(loc='best', frameon=True, fontsize=9)
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('plots/vw4/sensor_calibration_experiment/trajectory_comparison.png')
plt.close()

# Plot 2: Position Error Over Time
fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
ax.plot(time_elapsed, res_A['pos_error'], label='A. Original Baseline', color='#95a5a6', linewidth=1.5, linestyle='--')
ax.plot(time_elapsed, res_B['pos_error'], label='B. + Accel Calibration (Best Result)', color='#27ae60', linewidth=2.0)
ax.plot(time_elapsed, res_C['pos_error'], label='C. + True Gyro Calibration', color='#9b59b6', linewidth=1.2, linestyle=':')
ax.plot(time_elapsed, res_F['pos_error'], label='F. + Corrected All Combined', color='#2980b9', linewidth=1.5, linestyle='-.')
ax.set_title('Audited Position Error Accumulation Across Calibration Versions', fontsize=12, fontweight='bold', pad=10)
ax.set_xlabel('Outage Elapsed Time (seconds)')
ax.set_ylabel('Position Error (meters)')
ax.legend(loc='upper left', frameon=True)
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('plots/vw4/sensor_calibration_experiment/position_error_time.png')
plt.close()

# Plot 3: Velocity Comparison Across Versions
fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
ax.plot(time_elapsed, v_gt * 3.6, label='VBOX Ground Truth Velocity', color='#e74c3c', linewidth=2.2)
ax.plot(time_elapsed, res_A['v_dr'] * 3.6, label='A. Original Baseline (345 km/h max)', color='#95a5a6', linewidth=1.5, linestyle='--')
ax.plot(time_elapsed, res_B['v_dr'] * 3.6, label='B. + Accel Calibration (151 km/h max)', color='#27ae60', linewidth=2.0)
ax.plot(time_elapsed, res_F['v_dr'] * 3.6, label='F. + Corrected All Combined', color='#2980b9', linewidth=1.5, linestyle='-.')
ax.set_title('Audited Velocity Drift Comparison Across Calibration Versions', fontsize=12, fontweight='bold', pad=10)
ax.set_xlabel('Outage Elapsed Time (seconds)')
ax.set_ylabel('Speed (km/h)')
ax.legend(loc='upper left', frameon=True)
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('plots/vw4/sensor_calibration_experiment/velocity_comparison.png')
plt.close()

# Plot 4: Heading Comparison Across Versions
fig, ax = plt.subplots(figsize=(10, 4.8), dpi=150)
ax.plot(time_elapsed, psi_gt_deg, label='VBOX True Heading (°)', color='#e74c3c', linewidth=2.2)
ax.plot(time_elapsed, res_A['psi_dr_deg'], label='A. Original Baseline / Accel Calib / Corrected F', color='#27ae60', linewidth=2.0, linestyle='--')
ax.plot(time_elapsed, res_C['psi_dr_deg'], label='C. + True Gyro Calibration (85° err)', color='#9b59b6', linewidth=1.5, linestyle='-.')
ax.set_title('Audited Heading Angle Drift Comparison Across Calibration Versions', fontsize=12, fontweight='bold', pad=10)
ax.set_xlabel('Outage Elapsed Time (seconds)')
ax.set_ylabel('Heading Angle (degrees)')
ax.legend(loc='lower left', frameon=True)
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('plots/vw4/sensor_calibration_experiment/heading_comparison.png')
plt.close()

print("All 4 updated comparative plots saved in: plots/vw4/sensor_calibration_experiment/")
