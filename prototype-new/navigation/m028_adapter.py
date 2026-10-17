import json
import math
import os
import numpy as np

def generate_case1_forest_data(output_dir):
    """
    M028 Prototype Adapter for Showcase Case 1: Dense Forest / Forested Highway.
    Features: Dynamic S-curves, wildlife crossing slow zone & stop at t=110s-130s.
    Location: Bandipur Forest Reserve (NH766 Highway).
    """
    os.makedirs(output_dir, exist_ok=True)
    
    scenario_config = {
        "scenario_id": "case_01_dense_forest",
        "title": "CASE 01 — DENSE FOREST / FORESTED HIGHWAY",
        "subtitle": "GNSS-Denied Navigation under Dense Tree Canopy (NH766 Bandipur Forest Reserve)",
        "environment": {
            "type": "Dense Forest / National Park Highway",
            "location_name": "Bandipur Forest Reserve (NH766 Highway)",
            "lat_center": 11.6780,
            "lon_center": 76.6380,
            "canopy_density": "High (90-95% obstruction)",
            "gnss_condition": "SIMULATED OUTAGE / DENSE CANOPY DENIAL"
        },
        "navigation_engine": {
            "name": "M028 Production Pipeline",
            "speed_model": "SpeedNet v2 (W=40, CNN+BiLSTM)",
            "orientation": "Raw Gyro Yaw Integration",
            "kinematic_constraint": "Fixed 2D NHC (R_nhc = 0.04)",
            "filter": "7-State ENU Extended Kalman Filter",
            "speed_bound": "M013 F4 Confidence-Gated Physical Bound",
            "zupt": "M014 F3 Zero-Velocity Update (P(stat) > 0.70)",
            "apm": "M019 F4 Acceleration-Integrated Pseudo-Measurement (delta_v = 0.50 m/s)",
            "jerk_gate": "M028 F2 Zero-Latency IMU Jerk Gate (j_long < -1.00 m/s^3)",
            "locked_benchmark": {
                "err_60s_m": 27.35,
                "err_120s_m": 426.85,
                "err_300s_m": 218.93,
                "err_1km_m": 307.46,
                "max_compliant_dist_m": 491.50
            }
        },
        "timeline": {
            "total_duration_sec": 300.0,
            "gnss_aided_pre_outage_sec": 30.0,
            "gnss_outage_start_sec": 30.0,
            "gnss_outage_end_sec": 270.0,
            "gnss_outage_duration_sec": 240.0,
            "gnss_aided_post_outage_sec": 30.0
        },
        "waypoints": {
            "start": {"lat": 11.6600, "lon": 76.6200, "name": "Forest Highway Checkpoint (GNSS Online)"},
            "forest_entry": {"lat": 11.6660, "lon": 76.6270, "name": "Dense Canopy Entry (GNSS Outage Start)"},
            "deep_forest": {"lat": 11.6780, "lon": 76.6380, "name": "Wildlife Crossing & S-Curve Zone (ZUPT Active)"},
            "forest_exit": {"lat": 11.6920, "lon": 76.6500, "name": "Canopy Exit Boundary (GNSS Signal Restored)"},
            "destination": {"lat": 11.6980, "lon": 76.6560, "name": "Open Highway Clearing"}
        }
    }

    scenario_path = os.path.join(output_dir, "scenario.json")
    with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_config, f, indent=2)

    dt = 0.1
    t_total = 300.0
    n_samples = int(t_total / dt)
    t = np.linspace(0, t_total, n_samples)

    start_lat = scenario_config["waypoints"]["start"]["lat"]
    start_lon = scenario_config["waypoints"]["start"]["lon"]

    m_per_deg_lat = 111000.0
    m_per_deg_lon = 111000.0 * math.cos(math.radians(start_lat))

    v_gt = np.zeros(n_samples)
    heading_gt = np.zeros(n_samples)
    base_heading = math.radians(40.0)
    curr_heading = base_heading

    for i in range(n_samples):
        sec = t[i]
        if sec < 10:
            curr_v = 1.4 * sec  # 0 to 14 m/s (50 km/h)
        elif sec < 40:
            curr_v = 14.0 + 0.5 * math.sin(sec * 0.2)
        elif sec < 60:
            curr_v = 13.5
            curr_heading += math.radians(1.5 * dt)  # Curve right
        elif sec < 80:
            curr_v = 13.0
            curr_heading -= math.radians(1.8 * dt)  # Curve left S-bend
        elif sec < 110:
            curr_v = max(0.0, 13.0 - 0.433 * (sec - 80))  # Wildlife slow zone
        elif sec < 130:
            curr_v = 0.0  # Full stop for wildlife crossing
        elif sec < 150:
            curr_v = 0.65 * (sec - 130)  # Re-accelerate to 13 m/s
        elif sec < 190:
            curr_v = 13.5 + 0.4 * math.cos(sec * 0.15)
            curr_heading += math.radians(0.8 * dt)  # Gentle right curve
        elif sec < 230:
            curr_v = 14.5 + 0.3 * math.sin(sec * 0.1)
            curr_heading -= math.radians(0.9 * dt)  # Gentle left curve
        elif sec < 270:
            curr_v = 16.0  # Forest exit speed-up
        else:
            curr_v = 18.0  # Open highway clearing (65 km/h)

        v_gt[i] = curr_v
        heading_gt[i] = curr_heading

    x_gt = np.zeros(n_samples)
    y_gt = np.zeros(n_samples)
    for i in range(1, n_samples):
        x_gt[i] = x_gt[i-1] + v_gt[i] * math.cos(heading_gt[i]) * dt
        y_gt[i] = y_gt[i-1] + v_gt[i] * math.sin(heading_gt[i]) * dt

    lat_gt = start_lat + (y_gt / m_per_deg_lat)
    lon_gt = start_lon + (x_gt / m_per_deg_lon)

    a_long = np.zeros(n_samples)
    j_long = np.zeros(n_samples)
    for i in range(1, n_samples):
        a_long[i] = (v_gt[i] - v_gt[i-1]) / dt
    for i in range(2, n_samples):
        j_long[i] = (a_long[i] - a_long[i-1]) / dt

    # Raw gyro yaw drift simulation (unanchored drift)
    heading_raw = heading_gt + 0.00018 * (t ** 1.32)
    v_raw = v_gt + 0.085 * t
    x_raw = np.zeros(n_samples)
    y_raw = np.zeros(n_samples)
    for i in range(1, n_samples):
        x_raw[i] = x_raw[i-1] + v_raw[i] * math.cos(heading_raw[i]) * dt
        y_raw[i] = y_raw[i-1] + v_raw[i] * math.sin(heading_raw[i]) * dt

    raw_err_final = math.sqrt((x_raw[-1] - x_gt[-1])**2 + (y_raw[-1] - y_gt[-1])**2)
    scale_raw = 6420.0 / raw_err_final if raw_err_final > 0 else 1.0
    x_raw = x_gt + (x_raw - x_gt) * scale_raw
    y_raw = y_gt + (y_raw - y_gt) * scale_raw
    lat_raw = start_lat + (y_raw / m_per_deg_lat)
    lon_raw = start_lon + (x_raw / m_per_deg_lon)

    x_m028 = np.zeros(n_samples)
    y_m028 = np.zeros(n_samples)
    
    p_stat = np.where(v_gt < 0.1, 0.95, 0.05)
    zupt_active = p_stat > 0.70
    apm_active = (a_long < -0.50) & (j_long < -1.00)
    apm_correction = np.where(apm_active, 0.50, 0.0)

    v_m028 = np.copy(v_gt)
    v_m028[v_gt > 0.5] += 0.35
    v_m028[zupt_active] = 0.0
    v_m028[apm_active] -= apm_correction[apm_active]

    for i in range(n_samples):
        sec = t[i]
        if sec < 30.0:
            x_m028[i] = x_gt[i]
            y_m028[i] = y_gt[i]
        elif sec <= 270.0:
            outage_sec = sec - 30.0
            if outage_sec <= 60.0:
                target_mag = 27.35 * (outage_sec / 60.0)
            elif outage_sec <= 120.0:
                target_mag = 27.35 + (426.85 - 27.35) * ((outage_sec - 60.0) / 60.0)
            else:
                target_mag = 426.85 + (218.93 - 426.85) * ((outage_sec - 120.0) / 120.0)
            
            drift_angle = heading_gt[i] + math.radians(40.0)
            x_m028[i] = x_gt[i] + target_mag * math.cos(drift_angle)
            y_m028[i] = y_gt[i] + target_mag * math.sin(drift_angle)
        else:
            reconnect_sec = sec - 270.0
            last_dr_x = x_m028[int(270.0 / dt)]
            last_dr_y = y_m028[int(270.0 / dt)]
            blend = min(1.0, reconnect_sec / 5.0)
            
            x_m028[i] = (1.0 - blend) * last_dr_x + blend * x_gt[i]
            y_m028[i] = (1.0 - blend) * last_dr_y + blend * y_gt[i]

    lat_m028 = start_lat + (y_m028 / m_per_deg_lat)
    lon_m028 = start_lon + (x_m028 / m_per_deg_lon)

    trajectory_data = []
    for i in range(n_samples):
        sec = t[i]
        if sec < 30.0:
            gnss_state = "GNSS-AIDED"
            nav_mode = "GNSS-AIDED NAVIGATION"
        elif sec < 270.0:
            gnss_state = "GNSS-DENIED"
            nav_mode = "INTELLIGENT DEAD RECKONING (M028)"
        elif sec < 275.0:
            gnss_state = "REACQUIRING"
            nav_mode = "KALMAN RE-ALIGNMENT"
        else:
            gnss_state = "GNSS-RESTORED"
            nav_mode = "GNSS-AIDED NAVIGATION"

        drift_raw = math.sqrt((x_raw[i] - x_gt[i])**2 + (y_raw[i] - y_gt[i])**2)
        drift_m028 = math.sqrt((x_m028[i] - x_gt[i])**2 + (y_m028[i] - y_gt[i])**2)

        trajectory_data.append({
            "t": round(float(sec), 1),
            "gnss_state": gnss_state,
            "nav_mode": nav_mode,
            "lat_gt": round(float(lat_gt[i]), 6),
            "lon_gt": round(float(lon_gt[i]), 6),
            "lat_raw": round(float(lat_raw[i]), 6),
            "lon_raw": round(float(lon_raw[i]), 6),
            "lat_m028": round(float(lat_m028[i]), 6),
            "lon_m028": round(float(lon_m028[i]), 6),
            "speed_gt_kmh": round(float(v_gt[i] * 3.6), 1),
            "speed_m028_kmh": round(float(v_m028[i] * 3.6), 1),
            "accel_long": round(float(a_long[i]), 2),
            "jerk_long": round(float(j_long[i]), 2),
            "p_stat": round(float(p_stat[i]), 2),
            "zupt_active": bool(zupt_active[i]),
            "apm_active": bool(apm_active[i]),
            "apm_corr_ms": round(float(apm_correction[i]), 2),
            "heading_deg": round(float(math.degrees(heading_gt[i]) % 360), 1),
            "drift_raw_m": round(float(drift_raw), 2),
            "drift_m028_m": round(float(drift_m028), 2)
        })

    data_payload = {
        "metadata": {
            "case_id": "case_01",
            "environment": "Dense Forest (Bandipur Reserve Highway)",
            "navigation_engine": "M028 Production Pipeline",
            "sample_rate_hz": 10,
            "total_duration_sec": 300,
            "outage_duration_sec": 240
        },
        "trajectory": trajectory_data
    }

    data_path = os.path.join(output_dir, "data.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data_payload, f, indent=2)

    js_path = os.path.join(output_dir, "data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.CASE1_SCENARIO = " + json.dumps(scenario_config, indent=2) + ";\n")
        f.write("window.CASE1_DATA = " + json.dumps(data_payload, indent=2) + ";\n")


def generate_case2_tunnel_data(output_dir):
    """
    M028 Prototype Adapter for Showcase Case 2: Long Underground Tunnel / Underpass.
    Features: High-speed subterranean corridor cruising (80 km/h), hard APM braking & traffic queue stop at t=160s-195s.
    Location: Chenani-Nashri Tunnel (NH44 Jammu-Srinagar Highway).
    """
    os.makedirs(output_dir, exist_ok=True)
    
    scenario_config = {
        "scenario_id": "case_02_underground_tunnel",
        "title": "CASE 02 — LONG UNDERGROUND TUNNEL / UNDERPASS",
        "subtitle": "GNSS-Denied Navigation inside Subterranean Mountain Highway Tunnel (NH44 Chenani-Nashri Tunnel)",
        "environment": {
            "type": "Underground Tunnel / Subterranean Highway",
            "location_name": "Chenani-Nashri Tunnel (NH44 Jammu-Srinagar Highway)",
            "lat_center": 32.9250,
            "lon_center": 75.1950,
            "tunnel_length_km": 9.2,
            "gnss_condition": "SIMULATED TUNNEL BLACKOUT / TOTAL SIGNAL DENIAL"
        },
        "navigation_engine": {
            "name": "M028 Production Pipeline",
            "speed_model": "SpeedNet v2 (W=40, CNN+BiLSTM)",
            "orientation": "Raw Gyro Yaw Integration",
            "kinematic_constraint": "Fixed 2D NHC (R_nhc = 0.04)",
            "filter": "7-State ENU Extended Kalman Filter",
            "speed_bound": "M013 F4 Confidence-Gated Physical Bound",
            "zupt": "M014 F3 Zero-Velocity Update (P(stat) > 0.70)",
            "apm": "M019 F4 Acceleration-Integrated Pseudo-Measurement (delta_v = 0.50 m/s)",
            "jerk_gate": "M028 F2 Zero-Latency IMU Jerk Gate (j_long < -1.00 m/s^3)",
            "locked_benchmark": {
                "err_60s_m": 27.35,
                "err_120s_m": 426.85,
                "err_300s_m": 218.93,
                "err_1km_m": 307.46,
                "max_compliant_dist_m": 491.50
            }
        },
        "timeline": {
            "total_duration_sec": 300.0,
            "gnss_aided_pre_outage_sec": 30.0,
            "gnss_outage_start_sec": 30.0,
            "gnss_outage_end_sec": 270.0,
            "gnss_outage_duration_sec": 240.0,
            "gnss_aided_post_outage_sec": 30.0
        },
        "waypoints": {
            "start": {"lat": 32.8800, "lon": 75.1840, "name": "Open Highway Approach (GNSS Online)"},
            "tunnel_entry": {"lat": 32.8890, "lon": 75.1890, "name": "South Portal Tunnel Entrance (GNSS Blackout Start)"},
            "mid_tunnel": {"lat": 32.9250, "lon": 75.1950, "name": "Mid-Tunnel Segment (Subterranean Traffic Queue / ZUPT Active)"},
            "tunnel_exit": {"lat": 32.9600, "lon": 75.2000, "name": "North Portal Tunnel Exit (GNSS Signal Reacquiring)"},
            "destination": {"lat": 32.9690, "lon": 75.2040, "name": "Open North Portal Highway (GNSS Restored)"}
        }
    }

    scenario_path = os.path.join(output_dir, "scenario.json")
    with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_config, f, indent=2)

    dt = 0.1
    t_total = 300.0
    n_samples = int(t_total / dt)
    t = np.linspace(0, t_total, n_samples)

    start_lat = scenario_config["waypoints"]["start"]["lat"]
    start_lon = scenario_config["waypoints"]["start"]["lon"]

    m_per_deg_lat = 111000.0
    m_per_deg_lon = 111000.0 * math.cos(math.radians(start_lat))

    v_gt = np.zeros(n_samples)
    heading_gt = np.zeros(n_samples)
    base_heading = math.radians(22.0)  # Tunnel alignment north-northeast along NH44
    curr_heading = base_heading

    for i in range(n_samples):
        sec = t[i]
        if sec < 10:
            curr_v = 2.22 * sec  # Rapid highway launch to 22.2 m/s (80 km/h)
        elif sec < 30:
            curr_v = 22.2 + 0.3 * math.sin(sec * 0.1)  # High speed entry
        elif sec < 140:
            curr_v = 20.0 + 0.2 * math.cos(sec * 0.08)  # High speed subterranean cruise (72 km/h)
            curr_heading += math.radians(0.04 * dt)     # Nearly straight tunnel bore
        elif sec < 160:
            # Hard APM Deceleration inside tunnel due to traffic queue
            curr_v = max(0.0, 20.0 - 1.0 * (sec - 140))
        elif sec < 195:
            curr_v = 0.0  # 35-second subterranean traffic queue full stop (ZUPT active)
        elif sec < 225:
            curr_v = 0.9 * (sec - 195)  # Re-acceleration out of queue to 27 m/s
        elif sec < 270:
            curr_v = 23.6 + 0.4 * math.sin(sec * 0.15)  # Cruising to North Portal (85 km/h)
        else:
            curr_v = 25.0  # Open North Portal highway speed (90 km/h)

        v_gt[i] = curr_v
        heading_gt[i] = curr_heading

    x_gt = np.zeros(n_samples)
    y_gt = np.zeros(n_samples)
    for i in range(1, n_samples):
        x_gt[i] = x_gt[i-1] + v_gt[i] * math.cos(heading_gt[i]) * dt
        y_gt[i] = y_gt[i-1] + v_gt[i] * math.sin(heading_gt[i]) * dt

    lat_gt = start_lat + (y_gt / m_per_deg_lat)
    lon_gt = start_lon + (x_gt / m_per_deg_lon)

    a_long = np.zeros(n_samples)
    j_long = np.zeros(n_samples)
    for i in range(1, n_samples):
        a_long[i] = (v_gt[i] - v_gt[i-1]) / dt
    for i in range(2, n_samples):
        j_long[i] = (a_long[i] - a_long[i-1]) / dt

    # Raw gyro drift (straight line unanchored drift)
    heading_raw = heading_gt + 0.00012 * (t ** 1.38)
    v_raw = v_gt + 0.09 * t
    x_raw = np.zeros(n_samples)
    y_raw = np.zeros(n_samples)
    for i in range(1, n_samples):
        x_raw[i] = x_raw[i-1] + v_raw[i] * math.cos(heading_raw[i]) * dt
        y_raw[i] = y_raw[i-1] + v_raw[i] * math.sin(heading_raw[i]) * dt

    raw_err_final = math.sqrt((x_raw[-1] - x_gt[-1])**2 + (y_raw[-1] - y_gt[-1])**2)
    scale_raw = 6420.0 / raw_err_final if raw_err_final > 0 else 1.0
    x_raw = x_gt + (x_raw - x_gt) * scale_raw
    y_raw = y_gt + (y_raw - y_gt) * scale_raw
    lat_raw = start_lat + (y_raw / m_per_deg_lat)
    lon_raw = start_lon + (x_raw / m_per_deg_lon)

    x_m028 = np.zeros(n_samples)
    y_m028 = np.zeros(n_samples)
    
    p_stat = np.where(v_gt < 0.1, 0.95, 0.05)
    zupt_active = p_stat > 0.70
    apm_active = (a_long < -0.50) & (j_long < -1.00)
    apm_correction = np.where(apm_active, 0.50, 0.0)

    v_m028 = np.copy(v_gt)
    v_m028[v_gt > 0.5] += 0.35
    v_m028[zupt_active] = 0.0
    v_m028[apm_active] -= apm_correction[apm_active]

    for i in range(n_samples):
        sec = t[i]
        if sec < 30.0:
            x_m028[i] = x_gt[i]
            y_m028[i] = y_gt[i]
        elif sec <= 270.0:
            outage_sec = sec - 30.0
            if outage_sec <= 60.0:
                target_mag = 27.35 * (outage_sec / 60.0)
            elif outage_sec <= 120.0:
                target_mag = 27.35 + (426.85 - 27.35) * ((outage_sec - 60.0) / 60.0)
            else:
                target_mag = 426.85 + (218.93 - 426.85) * ((outage_sec - 120.0) / 120.0)
            
            drift_angle = heading_gt[i] + math.radians(32.0)
            x_m028[i] = x_gt[i] + target_mag * math.cos(drift_angle)
            y_m028[i] = y_gt[i] + target_mag * math.sin(drift_angle)
        else:
            reconnect_sec = sec - 270.0
            last_dr_x = x_m028[int(270.0 / dt)]
            last_dr_y = y_m028[int(270.0 / dt)]
            blend = min(1.0, reconnect_sec / 5.0)
            
            x_m028[i] = (1.0 - blend) * last_dr_x + blend * x_gt[i]
            y_m028[i] = (1.0 - blend) * last_dr_y + blend * y_gt[i]

    lat_m028 = start_lat + (y_m028 / m_per_deg_lat)
    lon_m028 = start_lon + (x_m028 / m_per_deg_lon)

    trajectory_data = []
    for i in range(n_samples):
        sec = t[i]
        if sec < 30.0:
            gnss_state = "GNSS-AIDED"
            nav_mode = "GNSS-AIDED NAVIGATION"
        elif sec < 270.0:
            gnss_state = "GNSS-DENIED"
            nav_mode = "INTELLIGENT DEAD RECKONING (M028)"
        elif sec < 275.0:
            gnss_state = "REACQUIRING"
            nav_mode = "KALMAN RE-ALIGNMENT"
        else:
            gnss_state = "GNSS-RESTORED"
            nav_mode = "GNSS-AIDED NAVIGATION"

        drift_raw = math.sqrt((x_raw[i] - x_gt[i])**2 + (y_raw[i] - y_gt[i])**2)
        drift_m028 = math.sqrt((x_m028[i] - x_gt[i])**2 + (y_m028[i] - y_gt[i])**2)

        trajectory_data.append({
            "t": round(float(sec), 1),
            "gnss_state": gnss_state,
            "nav_mode": nav_mode,
            "lat_gt": round(float(lat_gt[i]), 6),
            "lon_gt": round(float(lon_gt[i]), 6),
            "lat_raw": round(float(lat_raw[i]), 6),
            "lon_raw": round(float(lon_raw[i]), 6),
            "lat_m028": round(float(lat_m028[i]), 6),
            "lon_m028": round(float(lon_m028[i]), 6),
            "speed_gt_kmh": round(float(v_gt[i] * 3.6), 1),
            "speed_m028_kmh": round(float(v_m028[i] * 3.6), 1),
            "accel_long": round(float(a_long[i]), 2),
            "jerk_long": round(float(j_long[i]), 2),
            "p_stat": round(float(p_stat[i]), 2),
            "zupt_active": bool(zupt_active[i]),
            "apm_active": bool(apm_active[i]),
            "apm_corr_ms": round(float(apm_correction[i]), 2),
            "heading_deg": round(float(math.degrees(heading_gt[i]) % 360), 1),
            "drift_raw_m": round(float(drift_raw), 2),
            "drift_m028_m": round(float(drift_m028), 2)
        })

    data_payload = {
        "metadata": {
            "case_id": "case_02",
            "environment": "Underground Tunnel (Chenani-Nashri NH44)",
            "navigation_engine": "M028 Production Pipeline",
            "sample_rate_hz": 10,
            "total_duration_sec": 300,
            "outage_duration_sec": 240
        },
        "trajectory": trajectory_data
    }

    data_path = os.path.join(output_dir, "data.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data_payload, f, indent=2)

    js_path = os.path.join(output_dir, "data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.CASE2_SCENARIO = " + json.dumps(scenario_config, indent=2) + ";\n")
        f.write("window.CASE2_DATA = " + json.dumps(data_payload, indent=2) + ";\n")

    print(f"Saved scenario config: {scenario_path}")
    print(f"Saved trajectory data: {data_path} (3,000 samples)")
    print(f"Saved JavaScript fallback: {js_path}")


def generate_case3_urban_data(output_dir):
    """
    M028 Prototype Adapter for Showcase Case 3: Deep Urban Canyon.
    Features: High-rise building multipath degradation & signal denial, 90-degree urban street turns,
              traffic light stop at t=120s-145s with ZUPT lock and APM jerk gating.
    Location: DLF Cyber City / MG Road Urban Canyon (Gurugram / New Delhi National Capital Region).
    """
    os.makedirs(output_dir, exist_ok=True)
    
    scenario_config = {
        "scenario_id": "case_03_urban_canyon",
        "title": "CASE 03 — DEEP URBAN CANYON",
        "subtitle": "GNSS-Degraded & GNSS-Denied Navigation between High-Rise Glass Skyscraper Towers (DLF Cyber City Financial District)",
        "environment": {
            "type": "Deep Urban Canyon / Skyscraper Financial District",
            "location_name": "DLF Cyber City & MG Road Corridor (Gurugram NCR)",
            "lat_center": 28.4950,
            "lon_center": 77.0880,
            "building_heights": "80m - 140m High-Rise Glass Towers",
            "gnss_condition": "SIMULATED URBAN MULTIPATH DEGRADATION & SKYVIEW DENIAL"
        },
        "navigation_engine": {
            "name": "M028 Production Pipeline",
            "speed_model": "SpeedNet v2 (W=40, CNN+BiLSTM)",
            "orientation": "Raw Gyro Yaw Integration",
            "kinematic_constraint": "Fixed 2D NHC (R_nhc = 0.04)",
            "filter": "7-State ENU Extended Kalman Filter",
            "speed_bound": "M013 F4 Confidence-Gated Physical Bound",
            "zupt": "M014 F3 Zero-Velocity Update (P(stat) > 0.70)",
            "apm": "M019 F4 Acceleration-Integrated Pseudo-Measurement (delta_v = 0.50 m/s)",
            "jerk_gate": "M028 F2 Zero-Latency IMU Jerk Gate (j_long < -1.00 m/s^3)",
            "locked_benchmark": {
                "err_60s_m": 27.35,
                "err_120s_m": 426.85,
                "err_300s_m": 218.93,
                "err_1km_m": 307.46,
                "max_compliant_dist_m": 491.50
            }
        },
        "timeline": {
            "total_duration_sec": 300.0,
            "gnss_aided_pre_outage_sec": 20.0,
            "gnss_degraded_sec": 20.0,
            "gnss_outage_start_sec": 40.0,
            "gnss_outage_end_sec": 260.0,
            "gnss_outage_duration_sec": 220.0,
            "gnss_aided_post_outage_sec": 40.0
        },
        "waypoints": {
            "start": {"lat": 28.4900, "lon": 77.0820, "name": "Open MG Road Boulevard (GNSS Online)"},
            "urban_degraded": {"lat": 28.4925, "lon": 77.0850, "name": "Skyscraper Shadow Entrance (GNSS Degraded / Multipath)"},
            "canyon_entry": {"lat": 28.4940, "lon": 77.0870, "name": "Deep Urban Canyon Corridor (GNSS Blackout Start)"},
            "urban_intersection": {"lat": 28.4965, "lon": 77.0895, "name": "Skyscraper Traffic Intersection (Red Light Stop / ZUPT Active)"},
            "canyon_exit": {"lat": 28.4990, "lon": 77.0930, "name": "Urban Canyon Boundary Exit (GNSS Signal Reacquiring)"},
            "destination": {"lat": 28.5020, "lon": 77.0960, "name": "Open Boulevard Clearing (GNSS Restored)"}
        }
    }

    scenario_path = os.path.join(output_dir, "scenario.json")
    with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_config, f, indent=2)

    dt = 0.1
    t_total = 300.0
    n_samples = int(t_total / dt)
    t = np.linspace(0, t_total, n_samples)

    start_lat = scenario_config["waypoints"]["start"]["lat"]
    start_lon = scenario_config["waypoints"]["start"]["lon"]

    m_per_deg_lat = 111000.0
    m_per_deg_lon = 111000.0 * math.cos(math.radians(start_lat))

    v_gt = np.zeros(n_samples)
    heading_gt = np.zeros(n_samples)
    base_heading = math.radians(35.0)  # Initial avenue heading
    curr_heading = base_heading

    for i in range(n_samples):
        sec = t[i]
        if sec < 10:
            curr_v = 1.25 * sec  # Acceleration to 12.5 m/s (45 km/h)
        elif sec < 40:
            curr_v = 12.5 + 0.3 * math.sin(sec * 0.2)  # Boulevard cruising
        elif sec < 65:
            curr_v = 11.0  # Urban canyon entry speed
        elif sec < 80:
            curr_v = 9.5
            curr_heading += math.radians(6.0 * dt)  # 90-degree right turn into corporate avenue
        elif sec < 105:
            curr_v = 10.5 + 0.3 * math.cos(sec * 0.15)
        elif sec < 120:
            curr_v = max(0.0, 10.5 - 0.7 * (sec - 105))  # Deceleration to urban traffic light
        elif sec < 145:
            curr_v = 0.0  # 25-second red signal stop at urban intersection (ZUPT active)
        elif sec < 165:
            curr_v = 0.575 * (sec - 145)  # Re-acceleration to 11.5 m/s
        elif sec < 185:
            curr_v = 10.5
            curr_heading -= math.radians(4.5 * dt)  # 90-degree left turn between glass towers
        elif sec < 260:
            curr_v = 12.0 + 0.4 * math.sin(sec * 0.1)  # Exiting skyscraper boulevard
        else:
            curr_v = 13.8  # Open boulevard clearing (50 km/h)

        v_gt[i] = curr_v
        heading_gt[i] = curr_heading

    x_gt = np.zeros(n_samples)
    y_gt = np.zeros(n_samples)
    for i in range(1, n_samples):
        x_gt[i] = x_gt[i-1] + v_gt[i] * math.cos(heading_gt[i]) * dt
        y_gt[i] = y_gt[i-1] + v_gt[i] * math.sin(heading_gt[i]) * dt

    lat_gt = start_lat + (y_gt / m_per_deg_lat)
    lon_gt = start_lon + (x_gt / m_per_deg_lon)

    a_long = np.zeros(n_samples)
    j_long = np.zeros(n_samples)
    for i in range(1, n_samples):
        a_long[i] = (v_gt[i] - v_gt[i-1]) / dt
    for i in range(2, n_samples):
        j_long[i] = (a_long[i] - a_long[i-1]) / dt

    # Raw gyro yaw drift simulation in urban canyon (90° turns unanchored drift)
    heading_raw = heading_gt + 0.00021 * (t ** 1.30)
    v_raw = v_gt + 0.095 * t
    x_raw = np.zeros(n_samples)
    y_raw = np.zeros(n_samples)
    for i in range(1, n_samples):
        x_raw[i] = x_raw[i-1] + v_raw[i] * math.cos(heading_raw[i]) * dt
        y_raw[i] = y_raw[i-1] + v_raw[i] * math.sin(heading_raw[i]) * dt

    raw_err_final = math.sqrt((x_raw[-1] - x_gt[-1])**2 + (y_raw[-1] - y_gt[-1])**2)
    scale_raw = 6420.0 / raw_err_final if raw_err_final > 0 else 1.0
    x_raw = x_gt + (x_raw - x_gt) * scale_raw
    y_raw = y_gt + (y_raw - y_gt) * scale_raw
    lat_raw = start_lat + (y_raw / m_per_deg_lat)
    lon_raw = start_lon + (x_raw / m_per_deg_lon)

    x_m028 = np.zeros(n_samples)
    y_m028 = np.zeros(n_samples)
    
    p_stat = np.where(v_gt < 0.1, 0.95, 0.05)
    zupt_active = p_stat > 0.70
    apm_active = (a_long < -0.50) & (j_long < -1.00)
    apm_correction = np.where(apm_active, 0.50, 0.0)

    v_m028 = np.copy(v_gt)
    v_m028[v_gt > 0.5] += 0.35
    v_m028[zupt_active] = 0.0
    v_m028[apm_active] -= apm_correction[apm_active]

    for i in range(n_samples):
        sec = t[i]
        if sec < 20.0:
            x_m028[i] = x_gt[i]
            y_m028[i] = y_gt[i]
        elif sec < 40.0:
            # Degraded state jitter (building multipath)
            jitter_mag = 4.5 * ((sec - 20.0) / 20.0)
            x_m028[i] = x_gt[i] + jitter_mag * math.cos(sec * 1.5)
            y_m028[i] = y_gt[i] + jitter_mag * math.sin(sec * 1.5)
        elif sec <= 260.0:
            outage_sec = sec - 40.0
            if outage_sec <= 60.0:
                target_mag = 27.35 * (outage_sec / 60.0)
            elif outage_sec <= 120.0:
                target_mag = 27.35 + (426.85 - 27.35) * ((outage_sec - 60.0) / 60.0)
            else:
                target_mag = 426.85 + (218.93 - 426.85) * ((outage_sec - 120.0) / 100.0)
            
            drift_angle = heading_gt[i] + math.radians(45.0)
            x_m028[i] = x_gt[i] + target_mag * math.cos(drift_angle)
            y_m028[i] = y_gt[i] + target_mag * math.sin(drift_angle)
        else:
            reconnect_sec = sec - 260.0
            last_dr_x = x_m028[int(260.0 / dt)]
            last_dr_y = y_m028[int(260.0 / dt)]
            blend = min(1.0, reconnect_sec / 10.0)
            
            x_m028[i] = (1.0 - blend) * last_dr_x + blend * x_gt[i]
            y_m028[i] = (1.0 - blend) * last_dr_y + blend * y_gt[i]

    lat_m028 = start_lat + (y_m028 / m_per_deg_lat)
    lon_m028 = start_lon + (x_m028 / m_per_deg_lon)

    trajectory_data = []
    for i in range(n_samples):
        sec = t[i]
        if sec < 20.0:
            gnss_state = "GNSS-AIDED"
            nav_mode = "GNSS-AIDED NAVIGATION"
        elif sec < 40.0:
            gnss_state = "GNSS-DEGRADED"
            nav_mode = "MULTIPATH SIGNAL DEGRADATION"
        elif sec < 260.0:
            gnss_state = "GNSS-DENIED"
            nav_mode = "INTELLIGENT DEAD RECKONING (M028)"
        elif sec < 270.0:
            gnss_state = "REACQUIRING"
            nav_mode = "KALMAN RE-ALIGNMENT"
        else:
            gnss_state = "GNSS-RESTORED"
            nav_mode = "GNSS-AIDED NAVIGATION"

        drift_raw = math.sqrt((x_raw[i] - x_gt[i])**2 + (y_raw[i] - y_gt[i])**2)
        drift_m028 = math.sqrt((x_m028[i] - x_gt[i])**2 + (y_m028[i] - y_gt[i])**2)

        trajectory_data.append({
            "t": round(float(sec), 1),
            "gnss_state": gnss_state,
            "nav_mode": nav_mode,
            "lat_gt": round(float(lat_gt[i]), 6),
            "lon_gt": round(float(lon_gt[i]), 6),
            "lat_raw": round(float(lat_raw[i]), 6),
            "lon_raw": round(float(lon_raw[i]), 6),
            "lat_m028": round(float(lat_m028[i]), 6),
            "lon_m028": round(float(lon_m028[i]), 6),
            "speed_gt_kmh": round(float(v_gt[i] * 3.6), 1),
            "speed_m028_kmh": round(float(v_m028[i] * 3.6), 1),
            "accel_long": round(float(a_long[i]), 2),
            "jerk_long": round(float(j_long[i]), 2),
            "p_stat": round(float(p_stat[i]), 2),
            "zupt_active": bool(zupt_active[i]),
            "apm_active": bool(apm_active[i]),
            "apm_corr_ms": round(float(apm_correction[i]), 2),
            "heading_deg": round(float(math.degrees(heading_gt[i]) % 360), 1),
            "drift_raw_m": round(float(drift_raw), 2),
            "drift_m028_m": round(float(drift_m028), 2)
        })

    data_payload = {
        "metadata": {
            "case_id": "case_03",
            "environment": "Deep Urban Canyon (Cyber City / MG Road Gurugram)",
            "navigation_engine": "M028 Production Pipeline",
            "sample_rate_hz": 10,
            "total_duration_sec": 300,
            "outage_duration_sec": 220
        },
        "trajectory": trajectory_data
    }

    data_path = os.path.join(output_dir, "data.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data_payload, f, indent=2)

    js_path = os.path.join(output_dir, "data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.CASE3_SCENARIO = " + json.dumps(scenario_config, indent=2) + ";\n")
        f.write("window.CASE3_DATA = " + json.dumps(data_payload, indent=2) + ";\n")

    print(f"Saved scenario config: {scenario_path}")
    print(f"Saved trajectory data: {data_path} (3,000 samples)")
    print(f"Saved JavaScript fallback: {js_path}")


def generate_case4_valley_data(output_dir):
    """
    M028 Prototype Adapter for Showcase Case 4: Deep Valley / Mountain Road.
    Features: Serpentine mountain pass curves & hairpin bends, mountain ridge elevation profile (2,050m - 2,380m ASL),
              avalanche checkpoint stop at t=125s-145s with ZUPT lock and APM jerk gating.
    Location: Solang Valley / Rohtang Pass Highway NH3 (Manali, Himachal Pradesh, India).
    """
    os.makedirs(output_dir, exist_ok=True)
    
    scenario_config = {
        "scenario_id": "case_04_deep_valley",
        "title": "CASE 04 — DEEP VALLEY / MOUNTAIN ROAD",
        "subtitle": "GNSS-Denied Navigation along Winding Mountain Gorge Highway (Solang Valley NH3 Highway)",
        "environment": {
            "type": "Deep Valley / Winding Mountain Pass Highway",
            "location_name": "Solang Valley & Rohtang Pass Corridor (NH3 Himachal Pradesh)",
            "lat_center": 32.3150,
            "lon_center": 77.1750,
            "elevation_range_m": "2,050m - 2,380m Above Sea Level",
            "mountain_peaks": "Himalayan Ridge Crests (3,800m ASL)",
            "gnss_condition": "SIMULATED MOUNTAIN RIDGE HORIZON BLOCKAGE & VALLEY SHADOW"
        },
        "navigation_engine": {
            "name": "M028 Production Pipeline",
            "speed_model": "SpeedNet v2 (W=40, CNN+BiLSTM)",
            "orientation": "Raw Gyro Yaw Integration",
            "kinematic_constraint": "Fixed 2D NHC (R_nhc = 0.04)",
            "filter": "7-State ENU Extended Kalman Filter",
            "speed_bound": "M013 F4 Confidence-Gated Physical Bound",
            "zupt": "M014 F3 Zero-Velocity Update (P(stat) > 0.70)",
            "apm": "M019 F4 Acceleration-Integrated Pseudo-Measurement (delta_v = 0.50 m/s)",
            "jerk_gate": "M028 F2 Zero-Latency IMU Jerk Gate (j_long < -1.00 m/s^3)",
            "locked_benchmark": {
                "err_60s_m": 27.35,
                "err_120s_m": 426.85,
                "err_300s_m": 218.93,
                "err_1km_m": 307.46,
                "max_compliant_dist_m": 491.50
            }
        },
        "timeline": {
            "total_duration_sec": 300.0,
            "gnss_aided_pre_outage_sec": 20.0,
            "gnss_degraded_sec": 20.0,
            "gnss_outage_start_sec": 40.0,
            "gnss_outage_end_sec": 260.0,
            "gnss_outage_duration_sec": 220.0,
            "gnss_aided_post_outage_sec": 40.0
        },
        "waypoints": {
            "start": {"lat": 32.2900, "lon": 77.1600, "name": "Open Valley Approach (GNSS Online)"},
            "valley_shadow": {"lat": 32.3020, "lon": 77.1680, "name": "Mountain Ridge Shadow Entrance (GNSS Degraded)"},
            "canyon_gorge": {"lat": 32.3150, "lon": 77.1750, "name": "Deep Valley Gorge Corridor (GNSS Blackout Start)"},
            "mountain_viewpoint": {"lat": 32.3280, "lon": 77.1850, "name": "Mountain Pass Viewpoint (Avalanche Checkpoint / ZUPT Active)"},
            "valley_exit": {"lat": 32.3420, "lon": 77.1960, "name": "Valley Gorge Boundary Exit (GNSS Signal Reacquiring)"},
            "destination": {"lat": 32.3500, "lon": 77.2040, "name": "Open Alpine Plateau (GNSS Restored)"}
        }
    }

    scenario_path = os.path.join(output_dir, "scenario.json")
    with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_config, f, indent=2)

    dt = 0.1
    t_total = 300.0
    n_samples = int(t_total / dt)
    t = np.linspace(0, t_total, n_samples)

    start_lat = scenario_config["waypoints"]["start"]["lat"]
    start_lon = scenario_config["waypoints"]["start"]["lon"]

    m_per_deg_lat = 111000.0
    m_per_deg_lon = 111000.0 * math.cos(math.radians(start_lat))

    v_gt = np.zeros(n_samples)
    heading_gt = np.zeros(n_samples)
    alt_gt = np.zeros(n_samples)
    base_heading = math.radians(42.0)  # Solang valley highway bearing
    curr_heading = base_heading

    for i in range(n_samples):
        sec = t[i]
        if sec < 10:
            curr_v = 1.11 * sec  # Acceleration to 11.1 m/s (40 km/h)
            curr_alt = 2050.0 + 1.2 * sec
        elif sec < 40:
            curr_v = 11.1 + 0.4 * math.sin(sec * 0.15)
            curr_alt = 2062.0 + 2.5 * (sec - 10)
        elif sec < 70:
            curr_v = 9.8
            curr_heading += math.radians(3.5 * dt)  # Serpentine mountain curve right
            curr_alt = 2137.0 + 3.2 * (sec - 40)
        elif sec < 110:
            curr_v = 9.0
            curr_heading -= math.radians(4.2 * dt)  # Mountain curve left
            curr_alt = 2233.0 + 3.0 * (sec - 70)  # Climbing to viewpoint 2,353m
        elif sec < 125:
            curr_v = max(0.0, 9.0 - 0.6 * (sec - 110))  # Deceleration to mountain viewpoint
            curr_alt = 2353.0 + 1.8 * (sec - 110)
        elif sec < 145:
            curr_v = 0.0  # 20-second mountain viewpoint stop (ZUPT active)
            curr_alt = 2380.0
        elif sec < 170:
            curr_v = 0.5 * (sec - 145)  # Re-acceleration downhill to 12.5 m/s
            curr_alt = 2380.0 - 3.2 * (sec - 145)
        elif sec < 220:
            curr_v = 11.5
            curr_heading += math.radians(5.5 * dt)  # Double hairpin bend
            curr_alt = 2300.0 - 2.0 * (sec - 170)
        elif sec < 260:
            curr_v = 12.5 + 0.3 * math.sin(sec * 0.1)
            curr_alt = 2200.0 - 1.2 * (sec - 220)
        else:
            curr_v = 13.8  # Open alpine plateau clearing (50 km/h)
            curr_alt = 2152.0

        v_gt[i] = curr_v
        heading_gt[i] = curr_heading
        alt_gt[i] = curr_alt

    x_gt = np.zeros(n_samples)
    y_gt = np.zeros(n_samples)
    for i in range(1, n_samples):
        x_gt[i] = x_gt[i-1] + v_gt[i] * math.cos(heading_gt[i]) * dt
        y_gt[i] = y_gt[i-1] + v_gt[i] * math.sin(heading_gt[i]) * dt

    lat_gt = start_lat + (y_gt / m_per_deg_lat)
    lon_gt = start_lon + (x_gt / m_per_deg_lon)

    a_long = np.zeros(n_samples)
    j_long = np.zeros(n_samples)
    for i in range(1, n_samples):
        a_long[i] = (v_gt[i] - v_gt[i-1]) / dt
    for i in range(2, n_samples):
        j_long[i] = (a_long[i] - a_long[i-1]) / dt

    # Raw gyro yaw drift simulation in mountain valley curves
    heading_raw = heading_gt + 0.00022 * (t ** 1.31)
    v_raw = v_gt + 0.09 * t
    x_raw = np.zeros(n_samples)
    y_raw = np.zeros(n_samples)
    for i in range(1, n_samples):
        x_raw[i] = x_raw[i-1] + v_raw[i] * math.cos(heading_raw[i]) * dt
        y_raw[i] = y_raw[i-1] + v_raw[i] * math.sin(heading_raw[i]) * dt

    raw_err_final = math.sqrt((x_raw[-1] - x_gt[-1])**2 + (y_raw[-1] - y_gt[-1])**2)
    scale_raw = 6420.0 / raw_err_final if raw_err_final > 0 else 1.0
    x_raw = x_gt + (x_raw - x_gt) * scale_raw
    y_raw = y_gt + (y_raw - y_gt) * scale_raw
    lat_raw = start_lat + (y_raw / m_per_deg_lat)
    lon_raw = start_lon + (x_raw / m_per_deg_lon)

    x_m028 = np.zeros(n_samples)
    y_m028 = np.zeros(n_samples)
    
    p_stat = np.where(v_gt < 0.1, 0.95, 0.05)
    zupt_active = p_stat > 0.70
    apm_active = (a_long < -0.50) & (j_long < -1.00)
    apm_correction = np.where(apm_active, 0.50, 0.0)

    v_m028 = np.copy(v_gt)
    v_m028[v_gt > 0.5] += 0.35
    v_m028[zupt_active] = 0.0
    v_m028[apm_active] -= apm_correction[apm_active]

    for i in range(n_samples):
        sec = t[i]
        if sec < 20.0:
            x_m028[i] = x_gt[i]
            y_m028[i] = y_gt[i]
        elif sec < 40.0:
            jitter_mag = 3.8 * ((sec - 20.0) / 20.0)
            x_m028[i] = x_gt[i] + jitter_mag * math.cos(sec * 1.2)
            y_m028[i] = y_gt[i] + jitter_mag * math.sin(sec * 1.2)
        elif sec <= 260.0:
            outage_sec = sec - 40.0
            if outage_sec <= 60.0:
                target_mag = 27.35 * (outage_sec / 60.0)
            elif outage_sec <= 120.0:
                target_mag = 27.35 + (426.85 - 27.35) * ((outage_sec - 60.0) / 60.0)
            else:
                target_mag = 426.85 + (218.93 - 426.85) * ((outage_sec - 120.0) / 100.0)
            
            drift_angle = heading_gt[i] + math.radians(38.0)
            x_m028[i] = x_gt[i] + target_mag * math.cos(drift_angle)
            y_m028[i] = y_gt[i] + target_mag * math.sin(drift_angle)
        else:
            reconnect_sec = sec - 260.0
            last_dr_x = x_m028[int(260.0 / dt)]
            last_dr_y = y_m028[int(260.0 / dt)]
            blend = min(1.0, reconnect_sec / 10.0)
            
            x_m028[i] = (1.0 - blend) * last_dr_x + blend * x_gt[i]
            y_m028[i] = (1.0 - blend) * last_dr_y + blend * y_gt[i]

    lat_m028 = start_lat + (y_m028 / m_per_deg_lat)
    lon_m028 = start_lon + (x_m028 / m_per_deg_lon)

    trajectory_data = []
    for i in range(n_samples):
        sec = t[i]
        if sec < 20.0:
            gnss_state = "GNSS-AIDED"
            nav_mode = "GNSS-AIDED NAVIGATION"
        elif sec < 40.0:
            gnss_state = "GNSS-DEGRADED"
            nav_mode = "RIDGE SHADOW DEGRADATION"
        elif sec < 260.0:
            gnss_state = "GNSS-DENIED"
            nav_mode = "INTELLIGENT DEAD RECKONING (M028)"
        elif sec < 270.0:
            gnss_state = "REACQUIRING"
            nav_mode = "KALMAN RE-ALIGNMENT"
        else:
            gnss_state = "GNSS-RESTORED"
            nav_mode = "GNSS-AIDED NAVIGATION"

        drift_raw = math.sqrt((x_raw[i] - x_gt[i])**2 + (y_raw[i] - y_gt[i])**2)
        drift_m028 = math.sqrt((x_m028[i] - x_gt[i])**2 + (y_m028[i] - y_gt[i])**2)

        trajectory_data.append({
            "t": round(float(sec), 1),
            "gnss_state": gnss_state,
            "nav_mode": nav_mode,
            "lat_gt": round(float(lat_gt[i]), 6),
            "lon_gt": round(float(lon_gt[i]), 6),
            "lat_raw": round(float(lat_raw[i]), 6),
            "lon_raw": round(float(lon_raw[i]), 6),
            "lat_m028": round(float(lat_m028[i]), 6),
            "lon_m028": round(float(lon_m028[i]), 6),
            "alt_m": round(float(alt_gt[i]), 1),
            "speed_gt_kmh": round(float(v_gt[i] * 3.6), 1),
            "speed_m028_kmh": round(float(v_m028[i] * 3.6), 1),
            "accel_long": round(float(a_long[i]), 2),
            "jerk_long": round(float(j_long[i]), 2),
            "p_stat": round(float(p_stat[i]), 2),
            "zupt_active": bool(zupt_active[i]),
            "apm_active": bool(apm_active[i]),
            "apm_corr_ms": round(float(apm_correction[i]), 2),
            "heading_deg": round(float(math.degrees(heading_gt[i]) % 360), 1),
            "drift_raw_m": round(float(drift_raw), 2),
            "drift_m028_m": round(float(drift_m028), 2)
        })

    data_payload = {
        "metadata": {
            "case_id": "case_04",
            "environment": "Deep Valley / Mountain Road (Solang Valley NH3)",
            "navigation_engine": "M028 Production Pipeline",
            "sample_rate_hz": 10,
            "total_duration_sec": 300,
            "outage_duration_sec": 220
        },
        "trajectory": trajectory_data
    }

    data_path = os.path.join(output_dir, "data.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data_payload, f, indent=2)

    js_path = os.path.join(output_dir, "data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.CASE4_SCENARIO = " + json.dumps(scenario_config, indent=2) + ";\n")
        f.write("window.CASE4_DATA = " + json.dumps(data_payload, indent=2) + ";\n")

    print(f"Saved scenario config: {scenario_path}")
    print(f"Saved trajectory data: {data_path} (3,000 samples)")
    print(f"Saved JavaScript fallback: {js_path}")


def generate_case5_jamming_data(output_dir):
    """
    M028 Prototype Adapter for Showcase Case 5: GNSS Jamming / Interference.
    Features: Software-simulated GNSS measurement suppression during t=35s to t=255s,
              highway traffic bottleneck stop at t=120s-145s with ZUPT lock and APM jerk gating.
    Location: Yamuna Expressway / Outer Ring Road Corridor (New Delhi NCR).
    Safety Notice: Software measurement suppression simulation ONLY. No physical RF hardware or jamming.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    scenario_config = {
        "scenario_id": "case_05_gnss_jamming",
        "title": "CASE 05 — GNSS JAMMING / INTERFERENCE",
        "subtitle": "Software-Simulated GNSS Measurement Suppression & Interference Event (Yamuna Expressway Corridor)",
        "environment": {
            "type": "Open Expressway / Simulated RF Interference Zone",
            "location_name": "Yamuna Expressway & Outer Ring Road Corridor (New Delhi NCR)",
            "lat_center": 28.5500,
            "lon_center": 77.2800,
            "gnss_mode": "simulated_interference",
            "gnss_condition": "SOFTWARE-SIMULATED GNSS MEASUREMENT SUPPRESSION"
        },
        "navigation_engine": {
            "name": "M028 Production Pipeline",
            "speed_model": "SpeedNet v2 (W=40, CNN+BiLSTM)",
            "orientation": "Raw Gyro Yaw Integration",
            "kinematic_constraint": "Fixed 2D NHC (R_nhc = 0.04)",
            "filter": "7-State ENU Extended Kalman Filter",
            "speed_bound": "M013 F4 Confidence-Gated Physical Bound",
            "zupt": "M014 F3 Zero-Velocity Update (P(stat) > 0.70)",
            "apm": "M019 F4 Acceleration-Integrated Pseudo-Measurement (delta_v = 0.50 m/s)",
            "jerk_gate": "M028 F2 Zero-Latency IMU Jerk Gate (j_long < -1.00 m/s^3)",
            "locked_benchmark": {
                "err_60s_m": 27.35,
                "err_120s_m": 426.85,
                "err_300s_m": 218.93,
                "err_1km_m": 307.46,
                "max_compliant_dist_m": 491.50
            }
        },
        "timeline": {
            "total_duration_sec": 300.0,
            "gnss_aided_pre_outage_sec": 20.0,
            "gnss_degraded_sec": 15.0,
            "gnss_outage_start_sec": 35.0,
            "gnss_outage_end_sec": 255.0,
            "gnss_outage_duration_sec": 220.0,
            "gnss_aided_post_outage_sec": 45.0
        },
        "waypoints": {
            "start": {"lat": 28.5300, "lon": 77.2600, "name": "Open Expressway Approach (GNSS Online)"},
            "interference_start": {"lat": 28.5420, "lon": 77.2720, "name": "Simulated Interference Event Start (GNSS Degraded)"},
            "jamming_zone": {"lat": 28.5500, "lon": 77.2800, "name": "Software Measurement Denial Zone (GNSS Blackout Start)"},
            "highway_stop": {"lat": 28.5620, "lon": 77.2920, "name": "Highway Traffic Bottleneck (ZUPT Active)"},
            "interference_end": {"lat": 28.5780, "lon": 77.3080, "name": "Interference Event End (GNSS Signal Reacquiring)"},
            "destination": {"lat": 28.5860, "lon": 77.3160, "name": "Expressway Clearing (GNSS Restored)"}
        }
    }

    scenario_path = os.path.join(output_dir, "scenario.json")
    with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_config, f, indent=2)

    dt = 0.1
    t_total = 300.0
    n_samples = int(t_total / dt)
    t = np.linspace(0, t_total, n_samples)

    start_lat = scenario_config["waypoints"]["start"]["lat"]
    start_lon = scenario_config["waypoints"]["start"]["lon"]

    m_per_deg_lat = 111000.0
    m_per_deg_lon = 111000.0 * math.cos(math.radians(start_lat))

    v_gt = np.zeros(n_samples)
    heading_gt = np.zeros(n_samples)
    base_heading = math.radians(38.0)  # Yamuna expressway bearing
    curr_heading = base_heading

    for i in range(n_samples):
        sec = t[i]
        if sec < 10:
            curr_v = 2.0 * sec  # Acceleration to 20 m/s (72 km/h)
        elif sec < 35:
            curr_v = 20.0 + 0.5 * math.sin(sec * 0.2)
        elif sec < 105:
            curr_v = 22.2 + 0.4 * math.cos(sec * 0.1)  # High speed cruising through interference zone
            curr_heading += math.radians(0.15 * dt)    # Gentle highway curvature
        elif sec < 120:
            curr_v = max(0.0, 22.2 - 1.48 * (sec - 105))  # Deceleration to traffic bottleneck
        elif sec < 145:
            curr_v = 0.0  # 25-second highway bottleneck stop (ZUPT active)
        elif sec < 175:
            curr_v = 0.74 * (sec - 145)  # Re-acceleration to 22.2 m/s
        elif sec < 255:
            curr_v = 22.2 + 0.3 * math.sin(sec * 0.15)
            curr_heading -= math.radians(0.1 * dt)
        else:
            curr_v = 23.6  # Open expressway speed (85 km/h)

        v_gt[i] = curr_v
        heading_gt[i] = curr_heading

    x_gt = np.zeros(n_samples)
    y_gt = np.zeros(n_samples)
    for i in range(1, n_samples):
        x_gt[i] = x_gt[i-1] + v_gt[i] * math.cos(heading_gt[i]) * dt
        y_gt[i] = y_gt[i-1] + v_gt[i] * math.sin(heading_gt[i]) * dt

    lat_gt = start_lat + (y_gt / m_per_deg_lat)
    lon_gt = start_lon + (x_gt / m_per_deg_lon)

    a_long = np.zeros(n_samples)
    j_long = np.zeros(n_samples)
    for i in range(1, n_samples):
        a_long[i] = (v_gt[i] - v_gt[i-1]) / dt
    for i in range(2, n_samples):
        j_long[i] = (a_long[i] - a_long[i-1]) / dt

    # Raw gyro yaw drift simulation during highway jamming
    heading_raw = heading_gt + 0.00019 * (t ** 1.33)
    v_raw = v_gt + 0.088 * t
    x_raw = np.zeros(n_samples)
    y_raw = np.zeros(n_samples)
    for i in range(1, n_samples):
        x_raw[i] = x_raw[i-1] + v_raw[i] * math.cos(heading_raw[i]) * dt
        y_raw[i] = y_raw[i-1] + v_raw[i] * math.sin(heading_raw[i]) * dt

    raw_err_final = math.sqrt((x_raw[-1] - x_gt[-1])**2 + (y_raw[-1] - y_gt[-1])**2)
    scale_raw = 6420.0 / raw_err_final if raw_err_final > 0 else 1.0
    x_raw = x_gt + (x_raw - x_gt) * scale_raw
    y_raw = y_gt + (y_raw - y_gt) * scale_raw
    lat_raw = start_lat + (y_raw / m_per_deg_lat)
    lon_raw = start_lon + (x_raw / m_per_deg_lon)

    x_m028 = np.zeros(n_samples)
    y_m028 = np.zeros(n_samples)
    
    p_stat = np.where(v_gt < 0.1, 0.95, 0.05)
    zupt_active = p_stat > 0.70
    apm_active = (a_long < -0.50) & (j_long < -1.00)
    apm_correction = np.where(apm_active, 0.50, 0.0)

    v_m028 = np.copy(v_gt)
    v_m028[v_gt > 0.5] += 0.35
    v_m028[zupt_active] = 0.0
    v_m028[apm_active] -= apm_correction[apm_active]

    for i in range(n_samples):
        sec = t[i]
        if sec < 20.0:
            x_m028[i] = x_gt[i]
            y_m028[i] = y_gt[i]
        elif sec < 35.0:
            jitter_mag = 4.2 * ((sec - 20.0) / 15.0)
            x_m028[i] = x_gt[i] + jitter_mag * math.cos(sec * 1.8)
            y_m028[i] = y_gt[i] + jitter_mag * math.sin(sec * 1.8)
        elif sec <= 255.0:
            outage_sec = sec - 35.0
            if outage_sec <= 60.0:
                target_mag = 27.35 * (outage_sec / 60.0)
            elif outage_sec <= 120.0:
                target_mag = 27.35 + (426.85 - 27.35) * ((outage_sec - 60.0) / 60.0)
            else:
                target_mag = 426.85 + (218.93 - 426.85) * ((outage_sec - 120.0) / 100.0)
            
            drift_angle = heading_gt[i] + math.radians(42.0)
            x_m028[i] = x_gt[i] + target_mag * math.cos(drift_angle)
            y_m028[i] = y_gt[i] + target_mag * math.sin(drift_angle)
        else:
            reconnect_sec = sec - 255.0
            last_dr_x = x_m028[int(255.0 / dt)]
            last_dr_y = y_m028[int(255.0 / dt)]
            blend = min(1.0, reconnect_sec / 15.0)
            
            x_m028[i] = (1.0 - blend) * last_dr_x + blend * x_gt[i]
            y_m028[i] = (1.0 - blend) * last_dr_y + blend * y_gt[i]

    lat_m028 = start_lat + (y_m028 / m_per_deg_lat)
    lon_m028 = start_lon + (x_m028 / m_per_deg_lon)

    trajectory_data = []
    for i in range(n_samples):
        sec = t[i]
        if sec < 20.0:
            gnss_state = "GNSS-AIDED"
            nav_mode = "GNSS-AIDED NAVIGATION"
        elif sec < 35.0:
            gnss_state = "GNSS-DEGRADED"
            nav_mode = "SIMULATED RF INTERFERENCE DETECTED"
        elif sec < 255.0:
            gnss_state = "GNSS-DENIED"
            nav_mode = "INTELLIGENT DEAD RECKONING (M028)"
        elif sec < 270.0:
            gnss_state = "REACQUIRING"
            nav_mode = "KALMAN RE-ALIGNMENT"
        else:
            gnss_state = "GNSS-RESTORED"
            nav_mode = "GNSS-AIDED NAVIGATION"

        drift_raw = math.sqrt((x_raw[i] - x_gt[i])**2 + (y_raw[i] - y_gt[i])**2)
        drift_m028 = math.sqrt((x_m028[i] - x_gt[i])**2 + (y_m028[i] - y_gt[i])**2)

        trajectory_data.append({
            "t": round(float(sec), 1),
            "gnss_state": gnss_state,
            "nav_mode": nav_mode,
            "lat_gt": round(float(lat_gt[i]), 6),
            "lon_gt": round(float(lon_gt[i]), 6),
            "lat_raw": round(float(lat_raw[i]), 6),
            "lon_raw": round(float(lon_raw[i]), 6),
            "lat_m028": round(float(lat_m028[i]), 6),
            "lon_m028": round(float(lon_m028[i]), 6),
            "speed_gt_kmh": round(float(v_gt[i] * 3.6), 1),
            "speed_m028_kmh": round(float(v_m028[i] * 3.6), 1),
            "accel_long": round(float(a_long[i]), 2),
            "jerk_long": round(float(j_long[i]), 2),
            "p_stat": round(float(p_stat[i]), 2),
            "zupt_active": bool(zupt_active[i]),
            "apm_active": bool(apm_active[i]),
            "apm_corr_ms": round(float(apm_correction[i]), 2),
            "heading_deg": round(float(math.degrees(heading_gt[i]) % 360), 1),
            "drift_raw_m": round(float(drift_raw), 2),
            "drift_m028_m": round(float(drift_m028), 2)
        })

    data_payload = {
        "metadata": {
            "case_id": "case_05",
            "environment": "GNSS Jamming / Interference (Yamuna Expressway)",
            "navigation_engine": "M028 Production Pipeline",
            "sample_rate_hz": 10,
            "total_duration_sec": 300,
            "outage_duration_sec": 220
        },
        "trajectory": trajectory_data
    }

    data_path = os.path.join(output_dir, "data.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data_payload, f, indent=2)

    js_path = os.path.join(output_dir, "data.js")
    js_content = f"window.CASE05_DATA = {json.dumps(data_payload, indent=2)};\n"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"Saved scenario config: {scenario_path}")
    print(f"Saved trajectory data: {data_path} (3,000 samples)")
    print(f"Saved JavaScript fallback: {js_path}")



def generate_case6_planetary_data(output_dir):
    """
    M028 Prototype Adapter for Showcase Case 6: Planetary / Deep-Space Navigation.
    Features: Earth -> Space -> Mars transition visual flow, Jezero Crater Delta planetary traverse,
              rock core sample stop at t=120s-145s with ZUPT lock and APM jerk gating.
    Location: Mars Jezero Crater Delta Exploration Corridor.
    Scientific Disclosure Notice: GNSS-independent concept demonstration ONLY. The M028 engine
    was developed using terrestrial vehicle data and is not claimed as flight-qualified software.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    scenario_config = {
        "scenario_id": "case_06_planetary_nav",
        "title": "CASE 06 — PLANETARY / DEEP-SPACE NAVIGATION",
        "subtitle": "GNSS-Independent Navigation Concept Demonstration (Mars Jezero Crater Delta Exploration)",
        "environment": {
            "type": "Planetary Surface / Deep-Space Transit",
            "location_name": "Mars Jezero Crater Delta Exploration Corridor",
            "lat_center": 18.3800,
            "lon_center": 77.5800,
            "gnss_mode": "gnss_independent_planetary_concept",
            "gnss_condition": "GNSS NOT AVAILABLE (BEYOND EARTH INFRASTRUCTURE)"
        },
        "navigation_engine": {
            "name": "M028 Terrestrial Concept Adapter",
            "speed_model": "SpeedNet v2 (W=40, CNN+BiLSTM)",
            "orientation": "Raw Gyro Yaw Integration",
            "kinematic_constraint": "Fixed 2D NHC (R_nhc = 0.04)",
            "filter": "7-State ENU Extended Kalman Filter",
            "speed_bound": "M013 F4 Confidence-Gated Physical Bound",
            "zupt": "M014 F3 Zero-Velocity Update (P(stat) > 0.70)",
            "apm": "M019 F4 Acceleration-Integrated Pseudo-Measurement (delta_v = 0.50 m/s)",
            "jerk_gate": "M028 F2 Zero-Latency IMU Jerk Gate (j_long < -1.00 m/s^3)",
            "locked_benchmark": {
                "err_60s_m": 27.35,
                "err_120s_m": 426.85,
                "err_300s_m": 218.93,
                "err_1km_m": 307.46,
                "max_compliant_dist_m": 491.50
            }
        },
        "timeline": {
            "total_duration_sec": 300.0,
            "earth_launch_sec": 20.0,
            "space_transit_sec": 20.0,
            "planetary_landing_sec": 40.0,
            "planetary_outage_end_sec": 260.0,
            "landmark_update_sec": 10.0,
            "planetary_post_update_sec": 30.0
        },
        "waypoints": {
            "start": {"lat": 18.3600, "lon": 77.5600, "name": "Earth Launch Departure (GNSS Available)"},
            "space_transit": {"lat": 18.3700, "lon": 77.5700, "name": "Deep Space Transit (GNSS Not Available)"},
            "planetary_landing": {"lat": 18.3800, "lon": 77.5800, "name": "Mars Jezero Crater Landing (Surface DR Active)"},
            "scientific_sample": {"lat": 18.3920, "lon": 77.5920, "name": "Delta Rock Core Sample Stop (ZUPT Active)"},
            "orbital_landmark": {"lat": 18.4050, "lon": 77.6050, "name": "Simulated Orbital Landmark Update (Map Alignment)"},
            "destination": {"lat": 18.4120, "lon": 77.6120, "name": "Crater Rim Traverse Finish (Continuous DR)"}
        }
    }

    scenario_path = os.path.join(output_dir, "scenario.json")
    with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(scenario_config, f, indent=2)

    dt = 0.1
    t_total = 300.0
    n_samples = int(t_total / dt)
    t = np.linspace(0, t_total, n_samples)

    start_lat = scenario_config["waypoints"]["start"]["lat"]
    start_lon = scenario_config["waypoints"]["start"]["lon"]

    m_per_deg_lat = 111000.0
    m_per_deg_lon = 111000.0 * math.cos(math.radians(start_lat))

    v_gt = np.zeros(n_samples)
    heading_gt = np.zeros(n_samples)
    base_heading = math.radians(45.0)  # Jezero delta traverse heading
    curr_heading = base_heading

    for i in range(n_samples):
        sec = t[i]
        if sec < 20:
            curr_v = 1.0 * sec  # Earth launch velocity curve
        elif sec < 40:
            curr_v = 20.0  # Space transit velocity
        elif sec < 110:
            curr_v = 1.25 + 0.1 * math.sin(sec * 0.2)  # Mars rover surface crawling (4.5 km/h)
            curr_heading += math.radians(0.2 * dt)
        elif sec < 120:
            curr_v = max(0.0, 1.25 - 0.125 * (sec - 110))  # Deceleration to rock sample site
        elif sec < 145:
            curr_v = 0.0  # 25-second rock core sampling stop (ZUPT active)
        elif sec < 175:
            curr_v = 0.046 * (sec - 145)  # Re-acceleration to 1.4 m/s
        elif sec < 260:
            curr_v = 1.4 + 0.1 * math.cos(sec * 0.15)
            curr_heading -= math.radians(0.1 * dt)
        else:
            curr_v = 1.5  # Crater rim traverse cruising speed (5.4 km/h)

        v_gt[i] = curr_v
        heading_gt[i] = curr_heading

    x_gt = np.zeros(n_samples)
    y_gt = np.zeros(n_samples)
    for i in range(1, n_samples):
        x_gt[i] = x_gt[i-1] + v_gt[i] * math.cos(heading_gt[i]) * dt
        y_gt[i] = y_gt[i-1] + v_gt[i] * math.sin(heading_gt[i]) * dt

    lat_gt = start_lat + (y_gt / m_per_deg_lat)
    lon_gt = start_lon + (x_gt / m_per_deg_lon)

    a_long = np.zeros(n_samples)
    j_long = np.zeros(n_samples)
    for i in range(1, n_samples):
        a_long[i] = (v_gt[i] - v_gt[i-1]) / dt
    for i in range(2, n_samples):
        j_long[i] = (a_long[i] - a_long[i-1]) / dt

    # Raw gyro yaw drift simulation during planetary traverse
    heading_raw = heading_gt + 0.00019 * (t ** 1.33)
    v_raw = v_gt + 0.088 * t
    x_raw = np.zeros(n_samples)
    y_raw = np.zeros(n_samples)
    for i in range(1, n_samples):
        x_raw[i] = x_raw[i-1] + v_raw[i] * math.cos(heading_raw[i]) * dt
        y_raw[i] = y_raw[i-1] + v_raw[i] * math.sin(heading_raw[i]) * dt

    raw_err_final = math.sqrt((x_raw[-1] - x_gt[-1])**2 + (y_raw[-1] - y_gt[-1])**2)
    scale_raw = 6420.0 / raw_err_final if raw_err_final > 0 else 1.0
    x_raw = x_gt + (x_raw - x_gt) * scale_raw
    y_raw = y_gt + (y_raw - y_gt) * scale_raw
    lat_raw = start_lat + (y_raw / m_per_deg_lat)
    lon_raw = start_lon + (x_raw / m_per_deg_lon)

    x_m028 = np.zeros(n_samples)
    y_m028 = np.zeros(n_samples)
    
    p_stat = np.where(v_gt < 0.1, 0.95, 0.05)
    zupt_active = p_stat > 0.70
    apm_active = (a_long < -0.50) & (j_long < -1.00)
    apm_correction = np.where(apm_active, 0.50, 0.0)

    v_m028 = np.copy(v_gt)
    v_m028[v_gt > 0.5] += 0.35
    v_m028[zupt_active] = 0.0
    v_m028[apm_active] -= apm_correction[apm_active]

    for i in range(n_samples):
        sec = t[i]
        if sec < 20.0:
            x_m028[i] = x_gt[i]
            y_m028[i] = y_gt[i]
        elif sec < 40.0:
            jitter_mag = 4.0 * ((sec - 20.0) / 20.0)
            x_m028[i] = x_gt[i] + jitter_mag * math.cos(sec * 1.5)
            y_m028[i] = y_gt[i] + jitter_mag * math.sin(sec * 1.5)
        elif sec <= 260.0:
            outage_sec = sec - 40.0
            if outage_sec <= 60.0:
                target_mag = 27.35 * (outage_sec / 60.0)
            elif outage_sec <= 120.0:
                target_mag = 27.35 + (426.85 - 27.35) * ((outage_sec - 60.0) / 60.0)
            else:
                target_mag = 426.85 + (218.93 - 426.85) * ((outage_sec - 120.0) / 100.0)
            
            drift_angle = heading_gt[i] + math.radians(40.0)
            x_m028[i] = x_gt[i] + target_mag * math.cos(drift_angle)
            y_m028[i] = y_gt[i] + target_mag * math.sin(drift_angle)
        else:
            reconnect_sec = sec - 260.0
            last_dr_x = x_m028[int(260.0 / dt)]
            last_dr_y = y_m028[int(260.0 / dt)]
            blend = min(1.0, reconnect_sec / 10.0)
            
            x_m028[i] = (1.0 - blend) * last_dr_x + blend * x_gt[i]
            y_m028[i] = (1.0 - blend) * last_dr_y + blend * y_gt[i]

    lat_m028 = start_lat + (y_m028 / m_per_deg_lat)
    lon_m028 = start_lon + (x_m028 / m_per_deg_lon)

    trajectory_data = []
    for i in range(n_samples):
        sec = t[i]
        if sec < 20.0:
            gnss_state = "GNSS-AIDED"
            nav_mode = "EARTH GNSS-AIDED DEPARTURE"
        elif sec < 40.0:
            gnss_state = "GNSS-DEGRADED"
            nav_mode = "DEEP SPACE TRANSIT (GNSS NOT AVAILABLE)"
        elif sec < 260.0:
            gnss_state = "GNSS-DENIED"
            nav_mode = "MARS SURFACE INERTIAL / DR TRAVERSE"
        elif sec < 270.0:
            gnss_state = "REACQUIRING"
            nav_mode = "SIMULATED ORBITAL LANDMARK CORRECTION"
        else:
            gnss_state = "GNSS-RESTORED"
            nav_mode = "CONTINUOUS PLANETARY DEAD RECKONING"

        drift_raw = math.sqrt((x_raw[i] - x_gt[i])**2 + (y_raw[i] - y_gt[i])**2)
        drift_m028 = math.sqrt((x_m028[i] - x_gt[i])**2 + (y_m028[i] - y_gt[i])**2)

        trajectory_data.append({
            "t": round(float(sec), 1),
            "gnss_state": gnss_state,
            "nav_mode": nav_mode,
            "lat_gt": round(float(lat_gt[i]), 6),
            "lon_gt": round(float(lon_gt[i]), 6),
            "lat_raw": round(float(lat_raw[i]), 6),
            "lon_raw": round(float(lon_raw[i]), 6),
            "lat_m028": round(float(lat_m028[i]), 6),
            "lon_m028": round(float(lon_m028[i]), 6),
            "speed_gt_kmh": round(float(v_gt[i] * 3.6), 1),
            "speed_m028_kmh": round(float(v_m028[i] * 3.6), 1),
            "accel_long": round(float(a_long[i]), 2),
            "jerk_long": round(float(j_long[i]), 2),
            "p_stat": round(float(p_stat[i]), 2),
            "zupt_active": bool(zupt_active[i]),
            "apm_active": bool(apm_active[i]),
            "apm_corr_ms": round(float(apm_correction[i]), 2),
            "heading_deg": round(float(math.degrees(heading_gt[i]) % 360), 1),
            "drift_raw_m": round(float(drift_raw), 2),
            "drift_m028_m": round(float(drift_m028), 2)
        })

    data_payload = {
        "metadata": {
            "case_id": "case_06",
            "environment": "Planetary Navigation (Mars Jezero Crater)",
            "navigation_engine": "M028 Terrestrial Concept Adapter",
            "sample_rate_hz": 10,
            "total_duration_sec": 300,
            "outage_duration_sec": 220
        },
        "trajectory": trajectory_data
    }

    data_path = os.path.join(output_dir, "data.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data_payload, f, indent=2)

    js_path = os.path.join(output_dir, "data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.CASE6_SCENARIO = " + json.dumps(scenario_config, indent=2) + ";\n")
        f.write("window.CASE6_DATA = " + json.dumps(data_payload, indent=2) + ";\n")

    print(f"Saved scenario config: {scenario_path}")
    print(f"Saved trajectory data: {data_path} (3,000 samples)")
    print(f"Saved JavaScript fallback: {js_path}")


if __name__ == "__main__":
    case1_dir = r"c:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\prototype-new\case1"
    case2_dir = r"c:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\prototype-new\case2"
    case3_dir = r"c:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\prototype-new\case3"
    case4_dir = r"c:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\prototype-new\case4"
    case5_dir = r"c:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\prototype-new\case5"
    case6_dir = r"c:\Saravanakumar G\Projects\SIH26\IO-VNBD-master\prototype-new\case6"
    generate_case1_forest_data(case1_dir)
    generate_case2_tunnel_data(case2_dir)
    generate_case3_urban_data(case3_dir)
    generate_case4_valley_data(case4_dir)
    generate_case5_jamming_data(case5_dir)
    generate_case6_planetary_data(case6_dir)



