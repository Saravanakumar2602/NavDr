"""
SIH 2026 Problem Statement 26168 — Intelligent Dead Reckoning (IDR) System
M030 Adaptive Confidence-Gated Yaw Fusion Architecture (m030_adaptive_yaw.py)

Extends the 7-State EKF with an Adaptive Innovation Gating and Covariance Weighting
mechanism for Neural SpeedNet Yaw-Rate Updates.

Concept:
"Use learned neural yaw information when it is trustworthy; fall back toward physical
 gyro propagation when the learned yaw disagrees with vehicle dynamics or exhibits
 high innovation residual."
"""

import numpy as np
from navigation.ekf import EKF7State

class AdaptiveYawGate:
    """
    Causal Innovation Residual & Covariance Inflation Engine for Neural Yaw Rate Updates.
    """
    def __init__(self, nis_soft_thresh=4.0, nis_hard_thresh=16.0, alpha=2.0):
        self.nis_soft_thresh = nis_soft_thresh  # 2-sigma boundary (NIS = 4.0)
        self.nis_hard_thresh = nis_hard_thresh  # 4-sigma outlier boundary (NIS = 16.0)
        self.alpha = alpha

    def evaluate(self, y_w, S_w_nominal, R_yaw_nominal):
        """
        Evaluates the innovation residual y_w against nominal variance S_w_nominal.
        
        Returns:
            is_accepted (bool): True if measurement should be fused into EKF
            R_yaw_adaptive (float): Adaptively inflated measurement covariance
            nis (float): Normalized Innovation Squared value
            status (str): 'ACCEPTED_FULL', 'ACCEPTED_INFLATED', or 'REJECTED_OUTLIER'
        """
        nis = float((y_w ** 2) / S_w_nominal)

        if nis > self.nis_hard_thresh or abs(y_w) > np.radians(3.0):
            # Hard Rejection: Neural yaw disagrees with gyro/kinematics -> Fallback to Gyro Propagation
            return False, R_yaw_nominal * 100.0, nis, 'REJECTED_OUTLIER'
        elif nis > self.nis_soft_thresh:
            # Soft Inflation: Moderate disagreement -> Inflate measurement covariance smoothly
            inflation_factor = 1.0 + self.alpha * (nis - self.nis_soft_thresh)
            R_yaw_adaptive = R_yaw_nominal * inflation_factor
            return True, R_yaw_adaptive, nis, 'ACCEPTED_INFLATED'
        else:
            # Full Acceptance: Excellent agreement -> Standard measurement covariance
            return True, R_yaw_nominal, nis, 'ACCEPTED_FULL'


class EKF7StateM030(EKF7State):
    """
    7-State EKF with Adaptive Confidence-Gated SpeedNet Yaw-Rate Fusion (M030).
    """
    def __init__(self, initial_state, dt=0.1, R_yaw_nominal=0.01**2, R_straight=0.005**2):
        super().__init__(initial_state, dt=dt)
        self.R_yaw_nominal = R_yaw_nominal
        self.R_straight = R_straight
        self.yaw_gate = AdaptiveYawGate(nis_soft_thresh=4.0, nis_hard_thresh=16.0, alpha=2.0)
        self.gate_stats = {
            'total_updates': 0,
            'accepted_full': 0,
            'accepted_inflated': 0,
            'rejected_outlier': 0
        }

    def update_yaw_rate(self, w_speednet, w_gyro_m):
        """
        Adaptive SpeedNet Neural Yaw Rate Fusion Update.
        """
        self.gate_stats['total_updates'] += 1
        bw = self.x_state[6]
        h_w = w_gyro_m - bw
        y_w = w_speednet - h_w

        H_w = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0]])
        S_w_nominal = float((H_w @ self.P @ H_w.T + self.R_yaw_nominal).item())

        is_accepted, R_yaw_adaptive, nis, status = self.yaw_gate.evaluate(y_w, S_w_nominal, self.R_yaw_nominal)

        if not is_accepted:
            self.gate_stats['rejected_outlier'] += 1
            # Fall back to pure gyro propagation (do not apply EKF update)
            return y_w, nis, 'REJECTED_OUTLIER'

        if status == 'ACCEPTED_INFLATED':
            self.gate_stats['accepted_inflated'] += 1
        else:
            self.gate_stats['accepted_full'] += 1

        S_w_adaptive = float((H_w @ self.P @ H_w.T + R_yaw_adaptive).item())
        K_w = (self.P @ H_w.T) / S_w_adaptive

        self.x_state = self.x_state + (K_w * y_w).flatten()
        self.P = (np.eye(7) - np.outer(K_w, H_w)) @ self.P
        return y_w, nis, status

    def update_zero_yaw_constraint(self, w_gyro_m):
        """Motion-Gated Zero-Yaw-Rate Straight Constraint Update."""
        bw = self.x_state[6]
        h_w = w_gyro_m - bw
        y_zero = 0.0 - h_w
        H_z = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0]])
        S_z = float((H_z @ self.P @ H_z.T + self.R_straight).item())
        K_z = (self.P @ H_z.T) / S_z
        self.x_state = self.x_state + (K_z * y_zero).flatten()
        self.P = (np.eye(7) - np.outer(K_z, H_z)) @ self.P
        return y_zero
