"""
SIH 2026 Problem Statement 26168 — Intelligent Dead Reckoning (IDR) System
M031 Dual-Mode Physical-Neural Heading Architecture (m031_dual_mode_heading.py)

Architecture:
- Primary Heading Propagation: Smartphone MEMS Gyro Integration
- Neural SpeedNet Role: Forward Speed (v_snet) and Stationary Classification (P_stat) ONLY
- Vehicle Motion Mode Classifier:
    1. STATIONARY: (P_stat > 0.70) -> Execute ZUPT
    2. DYNAMIC_TURN: (|w_gyro| > 1.5 deg/s or |a_lat| > 0.5 m/s^2) -> Neural yaw DISABLED/IGNORED. 100% Gyro propagation!
    3. STRAIGHT_MOTION: Low angular (|w_gyro| < 0.5 deg/s) & lateral motion (|a_lat| < 0.2 m/s^2) with N>=10 hysteresis -> Gyro bias calibration.
    4. GENERAL_MOTION: Physical gyro propagation.
"""

import numpy as np
from navigation.ekf import EKF7State

class VehicleMotionModeClassifier:
    """
    Classifies vehicle motion state into STATIONARY, DYNAMIC_TURN, or STRAIGHT_MOTION
    using smartphone IMU and SpeedNet signals.
    """
    def __init__(self, gyro_turn_threshold_degs=1.5, alat_turn_threshold=0.5, speed_min_straight=1.0):
        self.w_turn_thresh = np.radians(gyro_turn_threshold_degs)  # 1.5 deg/s threshold
        self.alat_turn_thresh = alat_turn_threshold               # 0.5 m/s^2 lateral threshold
        self.v_min_straight = speed_min_straight                   # 1.0 m/s threshold
        
        self.w_strict_straight = np.radians(0.5)                   # 0.5 deg/s strict straight
        self.alat_strict_straight = 0.20                           # 0.2 m/s^2 strict lateral
        self.straight_counter = 0

    def classify(self, w_gyro_m, bw_est, a_lat, v_est, prob_stat):
        """
        Classifies current time-step vehicle motion mode.
        """
        if prob_stat > 0.70 or v_est < 0.2:
            self.straight_counter = 0
            return 'STATIONARY'

        w_corr = abs(w_gyro_m - bw_est)
        a_lat_abs = abs(a_lat)

        if w_corr > self.w_turn_thresh or a_lat_abs > self.alat_turn_thresh:
            self.straight_counter = 0
            return 'DYNAMIC_TURN'
        elif w_corr <= self.w_strict_straight and a_lat_abs <= self.alat_strict_straight and v_est >= self.v_min_straight:
            self.straight_counter += 1
            if self.straight_counter >= 10:
                return 'VERIFIED_STRAIGHT'
            return 'STRAIGHT_TRANSITION'
        else:
            self.straight_counter = 0
            return 'GENERAL_PROPAGATION'


class EKF7StateM031(EKF7State):
    """
    7-State EKF with Dual-Mode Physical-Neural Heading Architecture (M031).
    """
    def __init__(self, initial_state, dt=0.1, R_straight=0.005**2):
        super().__init__(initial_state, dt=dt)
        self.R_straight = R_straight
        self.classifier = VehicleMotionModeClassifier(
            gyro_turn_threshold_degs=1.5,
            alat_turn_threshold=0.5,
            speed_min_straight=1.0
        )
        self.mode_stats = {
            'total_steps': 0,
            'stationary': 0,
            'dynamic_turn': 0,
            'verified_straight': 0,
            'general_propagation': 0
        }

    def update_heading_mode(self, w_speednet, w_gyro_m, a_lat, v_est, prob_stat):
        """
        Dual-Mode Heading Update Execution:
        - DYNAMIC_TURN: Ignore SpeedNet yaw completely. Rely 100% on MEMS Gyro.
        - VERIFIED_STRAIGHT: Apply zero-yaw-rate constraint (N>=10 hysteresis) for clean gyro bias calibration.
        - GENERAL_PROPAGATION: 100% Gyro propagation.
        - STATIONARY: Handled by ZUPT.
        """
        self.mode_stats['total_steps'] += 1
        bw = self.x_state[6]
        mode = self.classifier.classify(w_gyro_m, bw, a_lat, v_est, prob_stat)

        if mode == 'STATIONARY':
            self.mode_stats['stationary'] += 1
            return mode, 'ZUPT_ACTIVE'

        elif mode == 'DYNAMIC_TURN':
            self.mode_stats['dynamic_turn'] += 1
            # NEURAL YAW DISABLED DURING TURNS! Rely purely on MEMS Gyro propagation in EKF predict step.
            return mode, 'NEURAL_YAW_DISABLED_GYRO_ONLY'

        elif mode == 'VERIFIED_STRAIGHT':
            self.mode_stats['verified_straight'] += 1
            # Apply motion-gated zero-yaw constraint (N>=10 hysteresis) to calibrate gyro bias bw cleanly
            h_w = w_gyro_m - bw
            y_zero = 0.0 - h_w
            H_z = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0]])
            S_z = float((H_z @ self.P @ H_z.T + self.R_straight).item())
            K_z = (self.P @ H_z.T) / S_z
            self.x_state = self.x_state + (K_z * y_zero).flatten()
            self.P = (np.eye(7) - np.outer(K_z, H_z)) @ self.P
            return mode, 'ZERO_YAW_BIAS_CALIBRATION'

        else:
            self.mode_stats['general_propagation'] += 1
            return mode, 'GYRO_PROPAGATION'
