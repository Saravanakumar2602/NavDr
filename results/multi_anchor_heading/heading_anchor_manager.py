"""
SIH 2026 Problem Statement 26168 — Intelligent Dead Reckoning (IDR) System
Stage 6: Multi-Anchor Heading Manager Module (heading_anchor_manager.py)

Implements a causal, prioritized state machine for multi-anchor vehicle heading estimation:
1. GNSS Course (Absolute Orientation Anchor when v >= 2.0 m/s and variance < 0.05)
2. Motion-Gated Zero-Yaw Constraint (Kinematic Drift Stabilizer during N >= 10 straight motion)
3. SpeedNet Yaw-Rate Fusion (Neural Angular Rate Anchor during turns/dynamics)
4. MEMS Gyro Propagation (Inertial Fallback when all anchors are uncertain)

Does NOT use future GNSS data, ground truth, or non-causal smoothing.
"""

import numpy as np

class HeadingAnchorManager:
    """
    Causal Multi-Anchor Heading Manager State Machine.
    """
    def __init__(self, dt=0.1, v_min_gnss=2.0, n_straight_threshold=10):
        self.dt = dt
        self.v_min_gnss = v_min_gnss
        self.n_straight_threshold = n_straight_threshold

        # Current State Tracking
        self.state = 'STATE_1_GNSS_INVALID'
        self.anchor_source = 'GYRO_PROPAGATION'
        self.heading_confidence = 0.50
        self.straight_counter = 0
        self.last_valid_gnss_course = None
        self.is_gnss_available = True

    def compute_gnss_confidence(self, v_gnss, circ_var, n_samples):
        """Computes continuous confidence score for GNSS course (0.0 to 1.0)."""
        if v_gnss < self.v_min_gnss or n_samples < 5:
            return 0.0
        speed_score = min(1.0, (v_gnss - 1.0) / 4.0)
        var_score = max(0.0, 1.0 - (circ_var / 0.05))
        return float(speed_score * var_score)

    def compute_motion_confidence(self, straight_counter, w_gyro, a_long, j_long):
        """Computes confidence score for motion-gated zero-yaw constraint."""
        if straight_counter < self.n_straight_threshold:
            return 0.0
        pers_score = min(1.0, straight_counter / 20.0)
        yaw_score = max(0.0, 1.0 - (abs(w_gyro) / 0.035))
        acc_score = max(0.0, 1.0 - (abs(a_long) / 0.80))
        jerk_score = max(0.0, 1.0 - (abs(j_long) / 2.50))
        return float(pers_score * yaw_score * acc_score * jerk_score)

    def update(self, is_gnss_available, v_gnss, circ_var_gnss, gnss_course_deg, n_gnss_samples,
               v_snet, w_snet, w_gyro, a_long, j_long, prob_stat):
        """
        Causal step update executed at every timestep dt.
        Returns:
            anchor_source (str): 'GNSS_COURSE', 'MOTION_ZERO_YAW', 'SPEEDNET_YAW', 'GYRO_PROPAGATION'
            anchor_valid (bool): True if an anchor constraint is actively updating the filter
            confidence (float): Heading confidence [0.0, 1.0]
            transition_event (str): Description of state transition if any occurred
        """
        old_source = self.anchor_source
        self.is_gnss_available = is_gnss_available

        # Compute Confidence Scores
        c_gnss = self.compute_gnss_confidence(v_gnss, circ_var_gnss, n_gnss_samples) if is_gnss_available else 0.0

        # Motion State Classification
        is_stat = (prob_stat > 0.70) or (v_snet < 0.30 and abs(a_long) < 0.20)
        is_ab = (a_long < -1.0) or (a_long > 1.2) or (abs(j_long) > 2.5)
        is_turn = (abs(w_gyro) >= 0.035) or (abs(w_snet) >= 0.035)
        is_straight = (v_snet >= 0.50) and (abs(w_gyro) < 0.030) and (abs(w_snet) < 0.030) and (-0.8 <= a_long <= 0.8) and not is_ab and not is_stat

        if is_straight:
            self.straight_counter += 1
        else:
            self.straight_counter = 0

        c_motion = self.compute_motion_confidence(self.straight_counter, w_gyro, a_long, j_long)

        # State Machine Priority Logic
        if is_gnss_available and c_gnss > 0.70:
            self.state = 'STATE_0_GNSS_AVAILABLE'
            self.anchor_source = 'GNSS_COURSE'
            self.heading_confidence = 0.95
            self.last_valid_gnss_course = gnss_course_deg
            anchor_valid = True

        elif not is_stat and self.straight_counter >= self.n_straight_threshold and c_motion > 0.50:
            self.state = 'STATE_2_STRAIGHT_MOTION'
            self.anchor_source = 'MOTION_ZERO_YAW'
            self.heading_confidence = min(0.90, 0.70 + c_motion * 0.20)
            anchor_valid = True

        elif is_turn or (abs(w_snet) > 0.015):
            self.state = 'STATE_3_TURNING'
            self.anchor_source = 'SPEEDNET_YAW'
            self.heading_confidence = max(0.40, self.heading_confidence - 0.001)
            anchor_valid = True

        elif is_stat:
            self.state = 'STATE_4_STATIONARY'
            self.anchor_source = 'SPEEDNET_YAW'
            self.heading_confidence = self.heading_confidence  # Heading holds flat during ZUPT
            anchor_valid = False

        else:
            self.state = 'STATE_5_UNCERTAIN'
            self.anchor_source = 'GYRO_PROPAGATION'
            self.heading_confidence = max(0.10, self.heading_confidence - 0.002)
            anchor_valid = False

        transition_event = "NONE"
        if old_source != self.anchor_source:
            transition_event = f"{old_source}_TO_{self.anchor_source}"

        return self.anchor_source, anchor_valid, self.heading_confidence, transition_event
