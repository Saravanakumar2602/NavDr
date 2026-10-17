"""
Causal IMU Jerk-Gated Adaptive Position/Velocity Correction Mechanism (APM).
Gate threshold: j_long < -1.0 m/s^3
"""

import numpy as np

class APMModule:
    """
    Causal Jerk-Gated APM Module (M028 Canonical Baseline).
    """
    def __init__(self, jerk_threshold=-1.0, max_correction_mps=0.50, dt=0.1):
        self.jerk_threshold = jerk_threshold
        self.max_correction_mps = max_correction_mps
        self.dt = dt

    def evaluate_correction(self, idx, a_long_window, j_long_val, w_yaw_val, v_speednet, v_est_history):
        """
        Evaluates whether an APM speed correction should be applied.
        
        Parameters:
        - idx: current timestep index
        - a_long_window: longitudinal acceleration over recent samples [idx-4:idx+1]
        - j_long_val: causal longitudinal jerk value at timestep idx (m/s^3)
        - w_yaw_val: vehicle yaw rate at timestep idx (rad/s)
        - v_speednet: forward speed predicted by SpeedNet v2 (m/s)
        - v_est_history: list of recent EKF estimated speeds
        
        Returns:
        - v_meas: corrected speed measurement to update EKF with (m/s)
        - is_active: boolean flag indicating if APM triggered
        """
        if len(v_est_history) < 5:
            return v_speednet, False

        a_current = a_long_window[-1]
        is_decel = (a_current < -0.5)
        is_turn_ok = (abs(w_yaw_val) <= np.radians(3.0))

        if is_decel and is_turn_ok:
            is_jerk_ok = (j_long_val < self.jerk_threshold)
            if is_jerk_ok:
                delta_v_imu = np.sum(a_long_window) * self.dt
                v_anchor = v_est_history[-5]
                z_apm = max(0.0, v_anchor + delta_v_imu)

                if v_speednet > z_apm:
                    raw_corr = v_speednet - z_apm
                    bounded_corr = min(raw_corr, self.max_correction_mps)
                    v_meas = v_speednet - bounded_corr
                    return v_meas, True

        return v_speednet, False
