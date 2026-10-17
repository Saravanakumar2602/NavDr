"""
SIH 2026 Problem Statement 26168 — Intelligent Dead Reckoning (IDR) System
M032 Adaptive Hybrid Intelligent Dead Reckoning Engine (m032_adaptive_hybrid.py)

Core Design Principle:
- AI (SpeedNet v2): Learned Forward-Velocity & Stationary Constraint
- Physics (MEMS Gyro): Primary Heading Propagation & Kinematic Integration
- EKF (7-State ENU): Final Sensor Fusion & State Covariance Management
- Constraints: NHC (v_lat = 0), ZUPT (P_stat > 0.70), APM Jerk Bounding, Causal Pre-Outage GNSS Latch

State Vector: [x, y, vx, vy, psi, ba, bw]
"""

import numpy as np
from navigation.ekf import EKF7State

class MotionModeClassifierM032:
    """
    Vehicle Motion Mode Classifier for M032 Adaptive Hybrid Architecture.
    Categorizes motion into:
    - STATIONARY: (P_stat > 0.70 or v < 0.2 m/s) -> Execute ZUPT
    - DYNAMIC_MANEUVER: (|w_gyro| > 1.5 deg/s or |a_lat| > 0.5 m/s^2) -> Pure Gyro Heading Propagation
    - VERIFIED_STRAIGHT: Low angular/lateral motion with N>=10 hysteresis -> Gyro Bias Calibration
    - GENERAL_MOTION: Physical Gyro Propagation
    """
    def __init__(self, w_turn_deg=1.5, alat_turn=0.5, w_straight_deg=0.5, alat_straight=0.20):
        self.w_turn_thresh = np.radians(w_turn_deg)
        self.alat_turn_thresh = alat_turn
        self.w_straight_thresh = np.radians(w_straight_deg)
        self.alat_straight_thresh = alat_straight
        self.straight_counter = 0

    def classify(self, w_gyro_m, bw_est, a_lat, v_est, prob_stat):
        if prob_stat > 0.70 or v_est < 0.2:
            self.straight_counter = 0
            return 'STATIONARY'

        w_corr = abs(w_gyro_m - bw_est)
        a_lat_abs = abs(a_lat)

        if w_corr > self.w_turn_thresh or a_lat_abs > self.alat_turn_thresh:
            self.straight_counter = 0
            return 'DYNAMIC_MANEUVER'
        elif w_corr <= self.w_straight_thresh and a_lat_abs <= self.alat_straight_thresh and v_est >= 1.0:
            self.straight_counter += 1
            if self.straight_counter >= 10:
                return 'VERIFIED_STRAIGHT'
            return 'STRAIGHT_TRANSITION'
        else:
            self.straight_counter = 0
            return 'GENERAL_MOTION'


class EKF7StateM032(EKF7State):
    """
    7-State Extended Kalman Filter for M032 Adaptive Hybrid IDR Architecture.
    """
    def __init__(self, initial_state, dt=0.1, R_straight=0.005**2):
        super().__init__(initial_state, dt=dt)
        self.R_straight = R_straight
        self.classifier = MotionModeClassifierM032()
        self.stats = {
            'total_steps': 0,
            'gnss_updates': 0,
            'speednet_speed_updates': 0,
            'zupt_updates': 0,
            'bias_calibration_updates': 0,
            'gyro_propagations': 0
        }

    def process_step(self, a_long, w_gyro, a_lat, v_snet, prob_stat, is_outage, gnss_meas=None, apm_module=None, j_long=0.0, v_est_hist=None):
        """
        Processes a single 10 Hz navigation step using M032 Architecture.
        
        Exact Code Path Documented:
        SpeedNet forward speed (v_snet)
        -> EKF update_speed(v_meas)
        -> EKF velocity state [vx, vy]
        -> Position propagation [x, y]
        """
        self.stats['total_steps'] += 1
        
        # 1. EKF Kinematic Predict Step (IMU a_long, w_gyro)
        self.predict(a_long, w_gyro)

        is_stat = (prob_stat > 0.70)
        bw = float(self.x_state[6])
        v_est_curr = np.sqrt(self.x_state[2]**2 + self.x_state[3]**2)

        if not is_outage and gnss_meas is not None:
            # Full GNSS Measurement Update when GNSS is available
            self.update_gnss(gnss_meas)
            self.stats['gnss_updates'] += 1
            mode, action = 'GNSS_ACTIVE', 'GNSS_UPDATE'
        else:
            # GNSS Denied Outage Navigation
            mode = self.classifier.classify(w_gyro, bw, a_lat, v_est_curr, prob_stat)

            # Evaluate Speed Measurement (SpeedNet + APM)
            v_meas_snet = 0.0 if is_stat else max(0.0, v_snet)
            v_meas = v_meas_snet

            if not is_stat and apm_module is not None and v_est_hist is not None and len(v_est_hist) >= 5:
                a_win = np.array([a_long]*5)  # window approximation if scalar
                v_meas, _ = apm_module.evaluate_correction(self.stats['total_steps'], a_win, j_long, w_gyro, v_meas_snet, v_est_hist)

            # Perform Updates
            if mode == 'STATIONARY':
                self.update_zupt()
                self.stats['zupt_updates'] += 1
                action = 'ZUPT_UPDATE'
            else:
                self.update_speed(v_meas)
                self.stats['speednet_speed_updates'] += 1

                if mode == 'VERIFIED_STRAIGHT':
                    # Calibrate gyro bias bw without corrupting heading
                    h_w = w_gyro - bw
                    y_zero = 0.0 - h_w
                    H_z = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0]])
                    S_z = float((H_z @ self.P @ H_z.T + self.R_straight).item())
                    K_z = (self.P @ H_z.T) / S_z
                    self.x_state = self.x_state + (K_z * y_zero).flatten()
                    self.P = (np.eye(7) - np.outer(K_z, H_z)) @ self.P
                    self.stats['bias_calibration_updates'] += 1
                    action = 'SPEEDNET_SPEED_PLUS_BIAS_CALIB'
                else:
                    self.stats['gyro_propagations'] += 1
                    action = 'SPEEDNET_SPEED_PLUS_GYRO_PROP'

            # Always enforce Non-Holonomic Constraint (NHC)
            self.update_nhc()

        st = self.x_state.copy()
        v_est_final = np.sqrt(st[2]**2 + st[3]**2)

        return {
            'x': st[0], 'y': st[1],
            'east_m': st[0], 'north_m': st[1],
            'vx': st[2], 'vy': st[3],
            'speed_mps': v_est_final,
            'heading_deg': np.degrees(st[4]) % 360.0,
            'heading_rad': st[4],
            'b_accel': st[5],
            'b_gyro': st[6],
            'motion_mode': mode,
            'mode_action': action
        }
