/**
 * SIH 2026 Problem Statement 26168 — Intelligent Dead Reckoning (IDR) System
 * DeadReckoningEngine.ts — Live 7-State ENU Kinematic Dead Reckoning Engine (Stage 4B)
 *
 * Implements the locked M032 IDR Kinematic Engine in React Native TypeScript:
 * 1. 7-State ENU State Vector: [eastM, northM, vx, vy, psi_rad, b_accel, b_gyro]
 * 2. Origin Anchoring: Anchors (0, 0) at the last confirmed valid B.2 GNSS fix (lat0, lon0)
 * 3. Timestamped Delta-t Kinematic Integration: Integrates actual dt from physical hardware timestamps
 * 4. Constraints: 2D NHC (v_lat = 0), ZUPT (stationary mode reset), Jerk-Gated APM, Verified Straight Bias Calib
 * 5. Metric-to-WGS84 Re-projection: Converts East/North displacements back to WGS84 (latitude, longitude)
 */

import { DrPose } from '../types/navigation';

export interface ImuSample {
  accelX: number; // m/s^2 (phone X / transverse lateral)
  accelY: number; // m/s^2 (phone Y / longitudinal forward)
  accelZ: number; // m/s^2 (phone Z / vertical)
  gyroX: number;  // rad/s
  gyroY: number;  // rad/s
  gyroZ: number;  // rad/s (yaw rate)
  timestamp: number; // ms
}

export type MotionMode = 'STATIONARY' | 'DYNAMIC_MANEUVER' | 'VERIFIED_STRAIGHT' | 'GENERAL_MOTION';

export class DeadReckoningEngine {
  // 7-State Vector: [x, y, vx, vy, psi, ba, bw]
  private state: [number, number, number, number, number, number, number] = [0, 0, 0, 0, 0, 0, 0];
  private isInitialized: boolean = false;
  private firstStepLogged: boolean = false;

  // Local ENU Origin
  private originLat: number = 0.0;
  private originLon: number = 0.0;
  private drStartTimeMs: number = 0;
  private lastTimestampMs: number = 0;
  private accumulatedDistanceMeters: number = 0.0;

  // Hysteresis & APM state
  private straightCounter: number = 0;
  private accelHistory: number[] = [];
  private speedHistory: number[] = [];

  // WGS84 Constants
  private static readonly METERS_PER_DEG_LAT = 111132.92;

  /**
   * Initializes or resets the DR Engine at a confirmed valid GNSS origin coordinate.
   */
  public resetOrigin(latitude: number, longitude: number, initialHeadingDeg: number = 0, initialSpeedMps: number = 0, timestampMs: number = Date.now()): void {
    const psiRad = (initialHeadingDeg * Math.PI) / 180.0;
    const vx0 = initialSpeedMps * Math.sin(psiRad);
    const vy0 = initialSpeedMps * Math.cos(psiRad);

    this.originLat = latitude;
    this.originLon = longitude;
    this.drStartTimeMs = timestampMs;
    this.lastTimestampMs = timestampMs;
    this.accumulatedDistanceMeters = 0.0;

    // State [x=0, y=0, vx, vy, psi, ba=0, bw=0]
    this.state = [0.0, 0.0, vx0, vy0, psiRad, 0.0, 0.0];
    this.straightCounter = 0;
    this.accelHistory = [];
    this.speedHistory = [];
    this.isInitialized = true;
    this.firstStepLogged = false;
    
    console.log(`[DR_ENGINE] Origin anchored at (${latitude.toFixed(6)}, ${longitude.toFixed(6)}), initial heading: ${initialHeadingDeg.toFixed(1)}°, speed: ${initialSpeedMps.toFixed(2)} m/s`);
    console.log(`[DR-DIAG] DR_INIT t=${timestampMs} lat=${latitude.toFixed(6)} lon=${longitude.toFixed(6)} heading=${initialHeadingDeg.toFixed(1)} speed=${initialSpeedMps.toFixed(2)}`);
  }

  /**
   * Processes a single physical IMU sensor callback and advances the 7-State ENU DR state.
   */
  public processStep(sample: ImuSample): DrPose | null {
    if (!this.isInitialized) {
      return null;
    }

    const now = sample.timestamp;
    if (!this.firstStepLogged) {
      this.firstStepLogged = true;
      console.log(`[DR-DIAG] FIRST_DR_STEP t=${now} drDurationMs=${now - this.drStartTimeMs}`);
    }
    let dt = (now - this.lastTimestampMs) / 1000.0; // convert ms to seconds
    if (dt <= 0 || dt > 1.0) {
      dt = 0.1; // Default 10 Hz fallback if timestamp gap is abnormal
    }
    this.lastTimestampMs = now;

    // Map physical phone sensor stream to vehicle coordinate frame
    // Vehicle Longitudinal = accelY (Forward)
    // Vehicle Transverse Lateral = accelX (Right)
    // Vehicle Yaw Rate = gyroZ (Vertical)
    const aLong = sample.accelY;
    const aLat = sample.accelX;
    const wYaw = sample.gyroZ;

    // Extract current state variables
    let [x, y, vx, vy, psi, ba, bw] = this.state;

    // 1. Heading Propagation via MEMS Gyro Yaw Rate
    const wCorr = wYaw - bw;
    psi = psi + wCorr * dt;
    // Normalize psi to [-PI, PI]
    psi = Math.atan2(Math.sin(psi), Math.cos(psi));

    // Current speed estimate magnitude
    let vEst = Math.sqrt(vx * vx + vy * vy);

    // 2. Motion Mode Classification (M032 Adaptive Hybrid Classifier)
    const mode = this.classifyMotionMode(wCorr, aLat, vEst, sample);

    // 3. Apply Kinematic & Environmental Constraints
    if (mode === 'STATIONARY') {
      // ZUPT (Zero Velocity Update)
      vx = 0.0;
      vy = 0.0;
      vEst = 0.0;
    } else {
      // Predict longitudinal velocity from forward acceleration
      let aNet = aLong - ba;
      
      // APM Jerk Damping: Detect harsh braking overshoot
      this.accelHistory.push(aNet);
      if (this.accelHistory.length > 5) this.accelHistory.shift();
      const jerkLong = (this.accelHistory.length >= 2) ? (aNet - this.accelHistory[this.accelHistory.length - 2]) / dt : 0.0;

      if (jerkLong < -1.0 && vEst > 1.0) {
        aNet = Math.max(aNet, -2.5); // Dampen harsh deceleration overshoot
      }

      // Update speed along heading direction
      vEst = Math.max(0.0, vEst + aNet * dt);

      // Enforce 2D Non-Holonomic Constraint (NHC: zero lateral chassis slip)
      vx = vEst * Math.sin(psi);
      vy = vEst * Math.cos(psi);

      // Verified Straight Bias Calibration (calibrate gyro bias bw on straight motion)
      if (mode === 'VERIFIED_STRAIGHT') {
        const hErr = wYaw - bw;
        bw = bw + 0.005 * hErr * dt; // Smooth online gyro bias tracking
      }
    }

    // 4. Metric Position Integration along local East (x) and North (y)
    const dx = vx * dt;
    const dy = vy * dt;
    x = x + dx;
    y = y + dy;

    // Accumulate metric trajectory distance
    const stepDist = Math.sqrt(dx * dx + dy * dy);
    this.accumulatedDistanceMeters += stepDist;

    // Update internal state
    this.state = [x, y, vx, vy, psi, ba, bw];
    this.speedHistory.push(vEst);
    if (this.speedHistory.length > 50) this.speedHistory.shift();

    // 5. Convert Local Metric ENU Displacement back to WGS84 Coordinates
    const metersPerDegLon = DeadReckoningEngine.METERS_PER_DEG_LAT * Math.cos((this.originLat * Math.PI) / 180.0);
    const drLat = this.originLat + (y / DeadReckoningEngine.METERS_PER_DEG_LAT);
    const drLon = this.originLon + (x / metersPerDegLon);

    const headingDeg = ((psi * 180.0) / Math.PI + 360.0) % 360.0;
    const drDurationMs = now - this.drStartTimeMs;

    // Safety Audit: Verify output is finite
    const isValid = Number.isFinite(drLat) && Number.isFinite(drLon) && Number.isFinite(vEst) && Number.isFinite(headingDeg);
    
    // Confidence decay over duration (starts at 0.95, degrades gently over 300s)
    const confidence = isValid ? Math.max(0.20, 0.95 - (drDurationMs / 300000.0) * 0.50) : 0.0;

    return {
      latitude: isValid ? drLat : this.originLat,
      longitude: isValid ? drLon : this.originLon,
      eastM: isValid ? x : 0.0,
      northM: isValid ? y : 0.0,
      velocityMps: vEst,
      speedMps: vEst,
      headingDeg: isValid ? headingDeg : 0.0,
      timestamp: now,
      confidence,
      valid: isValid,
      drDurationMs,
      drDistanceMeters: Math.round(this.accumulatedDistanceMeters * 10) / 10,
      motionMode: mode,
    };
  }

  /**
   * M032 Motion Mode Classifier: Categorizes motion state based on corrected gyro & lateral accel.
   */
  private classifyMotionMode(wCorrRad: number, aLat: number, vEst: number, sample: ImuSample): MotionMode {
    const wCorrDeg = Math.abs((wCorrRad * 180.0) / Math.PI);
    const aLatAbs = Math.abs(aLat);
    const accelMag = Math.sqrt(sample.accelX * sample.accelX + sample.accelY * sample.accelY + sample.accelZ * sample.accelZ);

    // Stationary test: low dynamic variance or near-zero speed
    if (vEst < 0.2 && Math.abs(accelMag - 9.81) < 0.5 && wCorrDeg < 1.0) {
      this.straightCounter = 0;
      return 'STATIONARY';
    }

    if (wCorrDeg > 1.5 || aLatAbs > 0.5) {
      this.straightCounter = 0;
      return 'DYNAMIC_MANEUVER';
    } else if (wCorrDeg <= 0.5 && aLatAbs <= 0.20 && vEst >= 1.0) {
      this.straightCounter++;
      if (this.straightCounter >= 10) {
        return 'VERIFIED_STRAIGHT';
      }
      return 'GENERAL_MOTION';
    } else {
      this.straightCounter = 0;
      return 'GENERAL_MOTION';
    }
  }
}

export const deadReckoningEngine = new DeadReckoningEngine();
