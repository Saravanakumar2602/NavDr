"""
7-State ENU Extended Kalman Filter (EKF) with Fixed 2D Non-Holonomic Constraints (NHC).
State vector: [x, y, vx, vy, psi, b_accel, b_gyro]
"""

import numpy as np

class EKF7State:
    def __init__(self, initial_state, dt=0.1):
        """
        initial_state: array of shape (7,) -> [x0, y0, vx0, vy0, psi0, b_a0, b_w0]
        """
        self.dt = dt
        self.x_state = np.array(initial_state, dtype=np.float64)
        
        # State Covariance Matrix
        self.P = np.diag([1.0, 1.0, 0.5, 0.5, np.radians(2.0)**2, 0.1, np.radians(0.5)**2])
        
        # Process Noise Covariance Matrix
        self.Q = np.diag([0.001, 0.001, 0.01, 0.01, np.radians(0.05)**2, 1e-5, 1e-6])
        
        # Measurement Noise Covariances
        self.R_gnss = np.diag([2.0**2, 2.0**2, 0.2**2, 0.2**2, np.radians(1.0)**2])
        self.H_gnss = np.zeros((5, 7))
        self.H_gnss[:5, :5] = np.eye(5)
        
        self.R_v = 1.0**2
        self.R_nhc = 0.20**2

    def predict(self, a_m, w_m):
        """
        Predict step using IMU longitudinal acceleration a_m and yaw rate w_m.
        """
        x, y, vx, vy, psi, ba, bw = self.x_state
        dt = self.dt
        
        w_hat = w_m - bw
        psi_new = psi + w_hat * dt
        a_hat = a_m - ba
        
        ax_enu = a_hat * np.sin(psi_new)
        ay_enu = a_hat * np.cos(psi_new)
        
        vx_new = vx + ax_enu * dt
        vy_new = vy + ay_enu * dt
        x_new = x + vx_new * dt
        y_new = y + vy_new * dt
        
        self.x_state = np.array([x_new, y_new, vx_new, vy_new, psi_new, ba, bw])
        
        # Jacobian F
        F = np.eye(7)
        F[0, 2] = dt; F[1, 3] = dt
        F[2, 4] = a_hat * np.cos(psi_new) * dt; F[3, 4] = -a_hat * np.sin(psi_new) * dt
        F[2, 5] = -np.sin(psi_new) * dt; F[3, 5] = -np.cos(psi_new) * dt; F[4, 6] = -dt
        
        self.P = F @ self.P @ F.T + self.Q

    def update_gnss(self, z_gnss):
        """
        GNSS Measurement Update: z_gnss = [x_gt, y_gt, vx_gt, vy_gt, psi_gt]
        """
        psi_meas = z_gnss[4]
        psi_diff = (psi_meas - self.x_state[4] + np.pi) % (2 * np.pi) - np.pi
        z = np.array([z_gnss[0], z_gnss[1], z_gnss[2], z_gnss[3], self.x_state[4] + psi_diff])
        
        y_meas = z - self.H_gnss @ self.x_state
        S = self.H_gnss @ self.P @ self.H_gnss.T + self.R_gnss
        K = self.P @ self.H_gnss.T @ np.linalg.inv(S)
        
        self.x_state = self.x_state + K @ y_meas
        self.P = (np.eye(7) - K @ self.H_gnss) @ self.P

    def update_speed(self, v_meas):
        """
        Speed Measurement Update from SpeedNet or APM.
        """
        v_est = np.sqrt(self.x_state[2]**2 + self.x_state[3]**2)
        v_denom = max(v_est, 1e-3)
        H_v = np.array([0, 0, self.x_state[2]/v_denom, self.x_state[3]/v_denom, 0, 0, 0])
        
        y_v = v_meas - v_est
        S_v = float(H_v @ self.P @ H_v.T + self.R_v)
        K_v = (self.P @ H_v.T) / S_v
        
        self.x_state = self.x_state + K_v * y_v
        self.P = (np.eye(7) - np.outer(K_v, H_v)) @ self.P

    def update_nhc(self):
        """
        Fixed 2D Non-Holonomic Constraint (NHC) Update (Lateral Velocity v_lat = 0).
        """
        vx, vy, psi = self.x_state[2], self.x_state[3], self.x_state[4]
        v_lat_est = vx * np.cos(psi) - vy * np.sin(psi)
        H_nhc = np.array([0, 0, np.cos(psi), -np.sin(psi), -vx*np.sin(psi) - vy*np.cos(psi), 0, 0])
        
        y_nhc = 0.0 - v_lat_est
        S_nhc = float(H_nhc @ self.P @ H_nhc.T + self.R_nhc)
        K_nhc = (self.P @ H_nhc.T) / S_nhc
        
        self.x_state = self.x_state + K_nhc * y_nhc
        self.P = (np.eye(7) - np.outer(K_nhc, H_nhc)) @ self.P

    def update_zupt(self):
        """
        Zero-Velocity Update (ZUPT): [vx, vy] = [0, 0].
        """
        H_zupt = np.zeros((2, 7))
        H_zupt[0, 2] = 1.0; H_zupt[1, 3] = 1.0
        R_z = (0.20**2) * np.eye(2)
        
        z_zupt = np.array([0.0, 0.0])
        y_z = z_zupt - H_zupt @ self.x_state
        S_z = H_zupt @ self.P @ H_zupt.T + R_z
        K_z = self.P @ H_zupt.T @ np.linalg.inv(S_z)
        
        self.x_state = self.x_state + K_z @ y_z
        self.P = (np.eye(7) - K_z @ H_zupt) @ self.P
