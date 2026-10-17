import os
import matplotlib.pyplot as plt
import numpy as np

# Set high-resolution styling
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#CBD5E0'
plt.rcParams['axes.linewidth'] = 1.2

base_dir = r'c:\Saravanakumar G\Projects\SIH26\IO-VNBD-master'
graph_dir = os.path.join(base_dir, 'model_evolution_report', 'comparison_graphs')
os.makedirs(graph_dir, exist_ok=True)

# ── Provenance-Controlled Data for the EXACT SAME 6 STAGES ──────────────────
# Stage Labels
stages_short = ['M003\nBaseline', 'M004\nSpeedNet v2', 'M013\nConstraint', 'M014\nZUPT', 'M019\nAPM', 'M028/M040\nFinal']
stages_full  = [
    'Stage 1: M003 — SpeedNet v1 (Open-Loop)',
    'Stage 2: M004 — SpeedNet v2 + Fixed NHC',
    'Stage 3: M013 — Confidence Physical Constraint',
    'Stage 4: M014 — Stationary 2D ZUPT Fusion',
    'Stage 5: M019 — Bounded APM Speed Damping',
    'Stage 6: M028/M040 — Jerk-Gated APM (Final)'
]

# Color Palette (Harmonious Modern Palette)
colors_bar  = ['#E53E3E', '#DD6B20', '#D69E2E', '#319795', '#3182CE', '#2B6CB0']
colors_line = ['#E53E3E', '#DD6B20', '#D69E2E', '#319795', '#3182CE', '#276749']

# 1. Speed MAE (km/h)
speed_mae = [9.22, 9.15, 9.05, 7.42, 7.36, 7.33]

# 2. Navigation Position Error (m) at 60s, 120s, 300s
nav_60s  = [350.00, 22.80, 26.70, 27.40, 27.50, 27.35]
nav_120s = [850.00, 440.20, 464.00, 428.50, 428.80, 426.85]
nav_300s = [1465.00, 263.11, 254.12, 233.18, 220.12, 218.93]

# 3. Mean Heading Error (degrees)
heading_mae = [68.42, 64.60, 64.60, 64.60, 64.60, 64.60]

# ── GRAPH 1: Speed Accuracy (BAR CHART) ───────────────────────────────────
plt.figure(figsize=(10, 6), dpi=300)
bars = plt.bar(stages_short, speed_mae, color=colors_bar, width=0.55, edgecolor='#2D3748', linewidth=1.0)

for bar, val in zip(bars, speed_mae):
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.15, f"{val:.2f} km/h", ha='center', va='bottom', fontweight='bold', fontsize=10, color='#1A202C')

plt.title('Graph 1: Speed Prediction Accuracy Across 6 Core Pipeline Stages', fontsize=13, fontweight='bold', pad=15, color='#1A365D')
plt.xlabel('Project Stage / Milestone', fontsize=11, fontweight='bold', labelpad=10, color='#2D3748')
plt.ylabel('Speed MAE (km/h) [Lower is Better]', fontsize=11, fontweight='bold', labelpad=10, color='#2D3748')
plt.ylim(0, 11.5)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()

speed_png_path = os.path.join(graph_dir, 'speed_accuracy_comparison.png')
plt.savefig(speed_png_path, dpi=300)
plt.close()
print(f"Saved: {speed_png_path}")

# ── GRAPH 2: Navigation Error Over Time (LINE CHART) ──────────────────────
plt.figure(figsize=(11, 6.5), dpi=300)
time_points = [60, 120, 300]
markers = ['o', 's', '^', 'D', 'v', 'P']

for idx in range(6):
    y_vals = [nav_60s[idx], nav_120s[idx], nav_300s[idx]]
    plt.plot(time_points, y_vals, marker=markers[idx], color=colors_line[idx], linewidth=2.2, markersize=7, label=stages_full[idx])
    
    # Annotate 300s endpoint
    plt.annotate(f"{y_vals[2]:.1f}m", (300, y_vals[2]), textcoords="offset points", xytext=(8, -3 if idx!=5 else -12), ha='left', fontweight='bold', fontsize=9, color=colors_line[idx])

plt.title('Graph 2: Integrated Dead-Reckoning Position Error Evolution (60s -> 120s -> 300s)', fontsize=13, fontweight='bold', pad=15, color='#1A365D')
plt.xlabel('GNSS Outage Duration (seconds)', fontsize=11, fontweight='bold', labelpad=10, color='#2D3748')
plt.ylabel('Integrated Position Error (meters) [Lower is Better]', fontsize=11, fontweight='bold', labelpad=10, color='#2D3748')
plt.xticks([60, 120, 300], ['60 s', '120 s', '300 s'], fontweight='bold')
plt.xlim(40, 340)
plt.ylim(0, 1600)
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend(loc='upper left', fontsize=9.5, framealpha=0.95, edgecolor='#CBD5E0')
plt.tight_layout()

nav_png_path = os.path.join(graph_dir, 'navigation_error_comparison.png')
plt.savefig(nav_png_path, dpi=300)
plt.close()
print(f"Saved: {nav_png_path}")

# ── GRAPH 3: Heading / Orientation Performance (BAR CHART) ────────────────
plt.figure(figsize=(10, 6), dpi=300)
bars_h = plt.bar(stages_short, heading_mae, color=colors_bar, width=0.55, edgecolor='#2D3748', linewidth=1.0)

for bar, val in zip(bars_h, heading_mae):
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1.2, f"{val:.1f}°", ha='center', va='bottom', fontweight='bold', fontsize=10, color='#1A202C')

plt.title('Graph 3: Gyro Integrated Heading Error Across 6 Core Pipeline Stages', fontsize=13, fontweight='bold', pad=15, color='#1A365D')
plt.xlabel('Project Stage / Milestone', fontsize=11, fontweight='bold', labelpad=10, color='#2D3748')
plt.ylabel('Mean Heading Error (degrees)', fontsize=11, fontweight='bold', labelpad=10, color='#2D3748')
plt.ylim(0, 85)
plt.grid(axis='y', linestyle='--', alpha=0.5)

# Add explanatory callout text on chart
plt.text(2.5, 30, 'Note: Heading is propagated via raw gyro integration across stages M004-M028.\nM015 disproved heading bias correction (reducing heading error destroyed self-cancellation).', 
         ha='center', va='center', bbox=dict(boxstyle='round,pad=0.6', facecolor='#EDF2F7', edgecolor='#CBD5E0', alpha=0.9), fontsize=9, color='#2D3748')

plt.tight_layout()

heading_png_path = os.path.join(graph_dir, 'heading_orientation_comparison.png')
plt.savefig(heading_png_path, dpi=300)
plt.close()
print(f"Saved: {heading_png_path}")

print("All 3 comparison graphs generated successfully.")
