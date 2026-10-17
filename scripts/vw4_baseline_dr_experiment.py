import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# Create required output directories
os.makedirs('scripts', exist_ok=True)
os.makedirs('plots/vw4/baseline_experiment', exist_ok=True)
os.makedirs('results', exist_ok=True)

# Dataset paths
s_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\S-Vw4.csv'
v_path = r'C:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\IO-VNBD\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vw (Driver E)\Vw04\V-Vw4.csv'

print("Loading S-Vw4.csv and V-Vw4.csv datasets...")
df_s = pd.read_csv(s_path, encoding='latin1')
df_v = pd.read_csv(v_path, encoding='latin1')

df_s.columns = [c.strip() for c in df_s.columns]
df_v.columns = [c.strip() for c in df_v.columns]

# --- 1. Timestamp Synchronization ---
# Smartphone UTC start: 12:15:27.004 = 44127.004 s
# Vehicle UTC start:    12:15:26.700 = 44126.700 s
t_s_utc = 44127.004 + (df_s['TIME SINCE START (ms)'] - df_s['TIME SINCE START (ms)'].iloc[0]) / 1000.0
t_v_utc = df_v['Time Since Start of Day (seconds)']

t_start = max(t_s_utc.iloc[0], t_v_utc.iloc[0]) # 44127.004 s
t_end = min(t_s_utc.iloc[-1], t_v_utc.iloc[-1]) # 56779.300 s
dt = 0.1 # 10 Hz uniform sampling interval
t_sync = np.arange(t_start, t_end, dt)

print(f"Synchronized time grid: {len(t_sync)} samples at 10 Hz ({t_start:.3f} s to {t_end:.3f} s UTC)")

# --- 2. Extract & Resample Smartphone IMU Signals ---
raw_ax = interp1d(t_s_utc, df_s.iloc[:, 9], fill_value='extrapolate')(t_sync)
raw_ay = interp1d(t_s_utc, df_s.iloc[:, 10], fill_value='extrapolate')(t_sync)
raw_az = interp1d(t_s_utc, df_s.iloc[:, 11], fill_value='extrapolate')(t_sync)

grav_x = interp1d(t_s_utc, df_s.iloc[:, 12], fill_value='extrapolate')(t_sync)
grav_y = interp1d(t_s_utc, df_s.iloc[:, 13], fill_value='extrapolate')(t_sync)
grav_z = interp1d(t_s_utc, df_s.iloc[:, 14], fill_value='extrapolate')(t_sync)

gyro_pitch = interp1d(t_s_utc, df_s['GYROSCOPE Pitch (rad/s)'], fill_value='extrapolate')(t_sync)

# --- 3. Gravity Removal & Coordinate Frame Transformation ---
# Smartphone linear acceleration (Raw - Gravity)
lin_ax = raw_ax - grav_x
lin_ay = raw_ay - grav_y
lin_az = raw_az - grav_z

# Transform to vehicle body frame:
# - Forward longitudinal accel: a_long = -lin_ay
# - Vehicle yaw rate: w_yaw = -gyro_pitch
a_long = -lin_ay # m/s^2
w_yaw = -gyro_pitch # rad/s

# --- 4. Resample VBOX Reference Ground Truth Signals ---
vbox_lat = interp1d(t_v_utc, df_v['Latitude (degrees)'], fill_value='extrapolate')(t_sync)
vbox_lon = interp1d(t_v_utc, df_v['Longitude (degrees)'], fill_value='extrapolate')(t_sync)
vbox_vel_ms = interp1d(t_v_utc, df_v['Velocity (km/hr)'] / 3.6, fill_value='extrapolate')(t_sync)
vbox_heading_deg = interp1d(t_v_utc, df_v['Heading (degrees)'], fill_value='extrapolate')(t_sync)

# --- 5. Define Artificial GNSS Outage Windows ---
# Selecting representative continuous section:
# Start: t = 48,927.0 s UTC (t = 80.0 minutes from dataset start, active highway driving)
# Duration: 60 seconds (600 samples at 10 Hz)
start_idx = 48000
duration_sec = 60
n_samples = int(duration_sec / dt)
end_idx = start_idx + n_samples

t_outage = t_sync[start_idx : end_idx]
time_elapsed = t_outage - t_outage[0]

# --- 6. Initial Conditions & VBOX Ground Truth ENU Conversion ---
lat0, lon0 = vbox_lat[start_idx], vbox_lon[start_idx]
R_earth = 6378137.0

# Convert VBOX WGS84 Lat/Lon to local Cartesian ENU coordinates
lat_rad = np.radians(vbox_lat[start_idx : end_idx])
lon_rad = np.radians(vbox_lon[start_idx : end_idx])
lat0_rad, lon0_rad = np.radians(lat0), np.radians(lon0)

x_gt = (lon_rad - lon0_rad) * R_earth * np.cos(lat0_rad) # East in meters
y_gt = (lat_rad - lat0_rad) * R_earth                  # North in meters

v_gt = vbox_vel_ms[start_idx : end_idx]               # Speed in m/s
psi_gt_deg = vbox_heading_deg[start_idx : end_idx]     # Heading in degrees (relative to North)

# --- 7. Inertial Dead Reckoning Numerical Integration ---
# System State Variables
v_dr = np.zeros(n_samples)
psi_dr_rad = np.zeros(n_samples)
x_dr = np.zeros(n_samples)
y_dr = np.zeros(n_samples)

# Initial conditions from VBOX immediately prior to outage start (t_0)
v_dr[0] = v_gt[0]
psi_dr_rad[0] = np.radians(psi_gt_deg[0])
x_dr[0] = 0.0
y_dr[0] = 0.0

for i in range(1, n_samples):
    # Step A: Heading integration from gyroscope yaw rate
    psi_dr_rad[i] = psi_dr_rad[i-1] + w_yaw[start_idx + i] * dt
    
    # Step B: Velocity integration from longitudinal acceleration
    v_dr[i] = v_dr[i-1] + a_long[start_idx + i] * dt
    if v_dr[i] < 0: # Non-negative speed physical constraint
        v_dr[i] = 0.0
        
    # Step C: Position integration in ENU frame (v_east = v*sin(psi), v_north = v*cos(psi))
    v_east = v_dr[i] * np.sin(psi_dr_rad[i])
    v_north = v_dr[i] * np.cos(psi_dr_rad[i])
    
    x_dr[i] = x_dr[i-1] + v_east * dt
    y_dr[i] = y_dr[i-1] + v_north * dt

# --- 8. Error & Performance Benchmark Calculations ---
pos_error = np.sqrt((x_dr - x_gt)**2 + (y_dr - y_gt)**2)
final_pos_error = pos_error[-1]

# Path distances
dist_gt = np.sum(np.sqrt(np.diff(x_gt)**2 + np.diff(y_gt)**2))
dist_dr = np.sum(v_dr) * dt

# Drift percentages
cde_pct = (abs(dist_dr - dist_gt) / dist_gt) * 100.0   # Cumulative Distance Mismatch Error %
fper_pct = (final_pos_error / dist_gt) * 100.0         # Final Position Displacement Error Ratio %
final_vel_error = abs(v_dr[-1] - v_gt[-1])

# Heading error in degrees
psi_dr_deg = np.degrees(psi_dr_rad)
heading_diff_deg = (psi_dr_deg - psi_gt_deg + 180) % 360 - 180
final_heading_error = abs(heading_diff_deg[-1])

print("\n" + "="*60)
print(f"BASELINE INERTIAL DEAD RECKONING RESULTS ({duration_sec}s OUTAGE)")
print("="*60)
print(f"Outage Window UTC Time:       {t_outage[0]:.1f} s to {t_outage[-1]:.1f} s")
print(f"Initial Velocity (v0):        {v_gt[0]*3.6:.2f} km/h ({v_gt[0]:.2f} m/s)")
print(f"Initial Heading (psi0):       {psi_gt_deg[0]:.2f}°")
print(f"Ground Truth Distance (D_gt): {dist_gt:.2f} m ({dist_gt/1000.0:.3f} km)")
print(f"Dead-Reckoned Distance:       {dist_dr:.2f} m ({dist_dr/1000.0:.3f} km)")
print(f"Final Position Error:         {final_pos_error:.2f} meters")
print(f"Cumulative Distance Error:    {cde_pct:.2f} %")
print(f"Final Pos Error Ratio (FPER): {fper_pct:.2f} %")
print(f"Final Velocity Error:         {final_vel_error:.2f} m/s ({final_vel_error*3.6:.2f} km/h)")
print(f"Final Heading Error:          {final_heading_error:.2f}°")
print("="*60)

# --- 9. Plotting Visualizations ---
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#eeeeee'

# Plot A: Trajectory Comparison (VBOX Ground Truth vs Dead Reckoning)
fig, ax = plt.subplots(figsize=(8, 7), dpi=150)
ax.plot(x_gt, y_gt, label='VBOX Ground Truth Trajectory', color='#e74c3c', linewidth=2)
ax.plot(x_dr, y_dr, label='Dead-Reckoned Trajectory (Uncalibrated Physics)', color='#2980b9', linewidth=1.8, linestyle='--')
ax.scatter([0], [0], color='#27ae60', s=90, label='Outage Start Point', zorder=5)
ax.scatter([x_gt[-1]], [y_gt[-1]], color='#c0392b', s=90, label='VBOX True Endpoint', zorder=5)
ax.scatter([x_dr[-1]], [y_dr[-1]], color='#2980b9', s=90, label='DR Predicted Endpoint', zorder=5)
ax.set_title(f'Vw4 Trajectory Comparison ({duration_sec}s GNSS Outage)', fontsize=12, fontweight='bold', pad=10)
ax.set_xlabel('East Displacement (meters)')
ax.set_ylabel('North Displacement (meters)')
ax.legend(loc='best', frameon=True)
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('plots/vw4/baseline_experiment/trajectory_comparison.png')
plt.close()

# Plot B: Position Error over Time
fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
ax.plot(time_elapsed, pos_error, color='#c0392b', linewidth=1.8, label='Position Error (m)')
ax.set_title(f'Position Error Accumulation Over Time ({duration_sec}s Outage)', fontsize=12, fontweight='bold', pad=10)
ax.set_xlabel('Outage Elapsed Time (seconds)')
ax.set_ylabel('Position Error (meters)')
ax.legend(loc='upper left', frameon=True)
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('plots/vw4/baseline_experiment/position_error_time.png')
plt.close()

# Plot C: Velocity Comparison
fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
ax.plot(time_elapsed, v_gt * 3.6, label='VBOX True Velocity (km/h)', color='#e74c3c', linewidth=1.8)
ax.plot(time_elapsed, v_dr * 3.6, label='Dead-Reckoned Speed (km/h)', color='#2980b9', linewidth=1.5, linestyle='--')
ax.set_title(f'Velocity Drift Comparison ({duration_sec}s Outage)', fontsize=12, fontweight='bold', pad=10)
ax.set_xlabel('Outage Elapsed Time (seconds)')
ax.set_ylabel('Speed (km/h)')
ax.legend(loc='best', frameon=True)
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('plots/vw4/baseline_experiment/velocity_comparison.png')
plt.close()

# Plot D: Heading Angle Comparison
fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
ax.plot(time_elapsed, psi_gt_deg, label='VBOX True Heading (°)', color='#e74c3c', linewidth=1.8)
ax.plot(time_elapsed, psi_dr_deg, label='Dead-Reckoned Heading (°)', color='#2980b9', linewidth=1.5, linestyle='--')
ax.set_title(f'Heading Angle Comparison ({duration_sec}s Outage)', fontsize=12, fontweight='bold', pad=10)
ax.set_xlabel('Outage Elapsed Time (seconds)')
ax.set_ylabel('Heading Angle (degrees)')
ax.legend(loc='best', frameon=True)
ax.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig('plots/vw4/baseline_experiment/heading_comparison.png')
plt.close()

print("\nAll 4 baseline experiment plots saved in: plots/vw4/baseline_experiment/")
