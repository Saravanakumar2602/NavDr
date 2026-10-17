import { LocationFix, FilteredGnssPose, SpeedEstimate, SpeedSource } from '../types/navigation';
import { calculateHaversineDistance } from '../utils/geo';

export class SpeedPipeline {
  private prevPose: FilteredGnssPose | null = null;
  private smoothedSpeedKmh: number | null = null;
  private readonly maxPhysicallyPlausibleSpeedKmh = 162.0; // 45 m/s (~162 km/h)
  private readonly maxDisplacementMeters = 250.0;
  private readonly alpha = 0.35; // Causal EMA smoothing gain

  public reset(): void {
    this.prevPose = null;
    this.smoothedSpeedKmh = null;
  }

  /**
   * Computes a validated, smoothed speed estimate prioritizing GNSS reported speed,
   * falling back to position-derived speed, and enforcing stationary & staleness guards.
   */
  public computeSpeed(
    rawFix: LocationFix | null,
    pose: FilteredGnssPose | null,
    isStale: boolean = false
  ): SpeedEstimate {
    const timestamp = pose ? pose.timestamp : rawFix ? rawFix.timestamp : Date.now();

    // 1. Staleness & Invalid Pose Guard
    if (isStale || !pose || pose.filterState === 'OUTLIER_REJECTED') {
      this.smoothedSpeedKmh = null;
      return {
        speedMps: null,
        speedKmh: null,
        source: 'NONE',
        confidence: 0.0,
        timestamp,
        valid: false,
      };
    }

    // 2. Stationary Guard (Highest Priority Override)
    if (pose.isStationary || pose.filterState === 'STATIONARY') {
      this.smoothedSpeedKmh = 0.0;
      this.prevPose = pose;
      return {
        speedMps: 0.0,
        speedKmh: 0.0,
        source: rawFix && rawFix.hasSpeed ? 'GNSS_REPORTED' : 'GNSS_DERIVED',
        confidence: 1.0,
        timestamp,
        valid: true,
      };
    }

    let rawSpeedMps: number | null = null;
    let selectedSource: SpeedSource = 'NONE';
    let confidence = 0.0;

    // 3. Priority 1: GNSS-Reported Speed
    if (
      rawFix &&
      rawFix.hasSpeed &&
      rawFix.speed !== null &&
      Number.isFinite(rawFix.speed) &&
      rawFix.speed >= 0
    ) {
      const reportedKmh = rawFix.speed * 3.6;
      if (reportedKmh <= this.maxPhysicallyPlausibleSpeedKmh) {
        rawSpeedMps = rawFix.speed;
        selectedSource = 'GNSS_REPORTED';
        confidence = rawFix.accuracy ? Math.min(1.0, Math.max(0.2, 10.0 / rawFix.accuracy)) : 0.85;
      }
    }

    // 4. Priority 2: Position-Derived Speed (fallback if reported speed unavailable/invalid)
    if (rawSpeedMps === null && this.prevPose) {
      const dtSeconds = (pose.timestamp - this.prevPose.timestamp) / 1000.0;

      if (dtSeconds > 0.1 && dtSeconds <= 5.0) {
        const distMeters = calculateHaversineDistance(
          this.prevPose.latitude,
          this.prevPose.longitude,
          pose.latitude,
          pose.longitude
        );

        if (distMeters <= this.maxDisplacementMeters) {
          const derivedMps = distMeters / dtSeconds;
          const derivedKmh = derivedMps * 3.6;

          if (Number.isFinite(derivedKmh) && derivedKmh <= this.maxPhysicallyPlausibleSpeedKmh) {
            rawSpeedMps = derivedMps;
            selectedSource = 'GNSS_DERIVED';
            confidence = 0.70;
          }
        }
      }
    }

    // Store current pose for next position-derived calculation
    this.prevPose = pose;

    // 5. Fallback: NONE
    if (rawSpeedMps === null || selectedSource === 'NONE') {
      this.smoothedSpeedKmh = null;
      return {
        speedMps: null,
        speedKmh: null,
        source: 'NONE',
        confidence: 0.0,
        timestamp,
        valid: false,
      };
    }

    // 6. Causal Speed Smoothing Layer (EMA)
    const rawKmh = rawSpeedMps * 3.6;
    if (this.smoothedSpeedKmh === null) {
      this.smoothedSpeedKmh = rawKmh;
    } else {
      this.smoothedSpeedKmh = (1 - this.alpha) * this.smoothedSpeedKmh + this.alpha * rawKmh;
    }

    // Quick zero clamp for micro movement noise
    if (this.smoothedSpeedKmh < 0.3) {
      this.smoothedSpeedKmh = 0.0;
    }

    const finalKmh = parseFloat(this.smoothedSpeedKmh.toFixed(1));
    const finalMps = parseFloat((finalKmh / 3.6).toFixed(2));

    return {
      speedMps: finalMps,
      speedKmh: finalKmh,
      source: selectedSource,
      confidence: parseFloat(confidence.toFixed(2)),
      timestamp,
      valid: true,
    };
  }
}

export const speedPipeline = new SpeedPipeline();
