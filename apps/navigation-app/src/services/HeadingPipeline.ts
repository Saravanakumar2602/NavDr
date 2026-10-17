import { LocationFix, FilteredGnssPose, HeadingEstimate, HeadingSource } from '../types/navigation';
import { filterCircularAngle } from '../utils/geo';

export class HeadingPipeline {
  private smoothedHeadingDeg: number | null = null;
  private readonly lowSpeedGateMps = 0.45; // ~1.62 km/h (B.2 heading gate threshold)
  private readonly alpha = 0.35; // Circular angle smoothing gain

  public reset(): void {
    this.smoothedHeadingDeg = null;
  }

  /**
   * Normalizes any angle in degrees to [0, 360)
   */
  public normalizeAngle(deg: number): number {
    return ((deg % 360) + 360) % 360;
  }

  /**
   * Computes a validated, circularly smoothed heading estimate using GNSS course,
   * respecting B.2 low-speed gating and stationary state hold.
   */
  public computeHeading(
    rawFix: LocationFix | null,
    pose: FilteredGnssPose | null,
    isStale: boolean = false
  ): HeadingEstimate {
    const timestamp = pose ? pose.timestamp : rawFix ? rawFix.timestamp : Date.now();

    // 1. Staleness & Invalid Pose Guard
    if (isStale || !pose || pose.filterState === 'OUTLIER_REJECTED') {
      this.smoothedHeadingDeg = null;
      return {
        headingDeg: null,
        source: 'NONE',
        confidence: 0.0,
        timestamp,
        valid: false,
      };
    }

    // 2. B.2 Stationary & Low-Speed Heading Gate
    const rawSpeedMps = rawFix && rawFix.hasSpeed && rawFix.speed !== null ? rawFix.speed : 0;
    const isGated =
      pose.isStationary ||
      pose.filterState === 'STATIONARY' ||
      rawSpeedMps < this.lowSpeedGateMps ||
      !rawFix ||
      !rawFix.hasBearing ||
      rawFix.bearing === null ||
      !Number.isFinite(rawFix.bearing);

    if (isGated) {
      // Do NOT invent heading from last course when stationary or low-speed!
      this.smoothedHeadingDeg = null;
      return {
        headingDeg: null,
        source: 'NONE',
        confidence: 0.0,
        timestamp,
        valid: false,
      };
    }

    // 3. Valid GNSS Course Normalization
    const rawHeading = this.normalizeAngle(rawFix.bearing!);

    // 4. Shortest-Path Circular Angle Smoothing (North-crossing safe: 359° -> 1° = +2°)
    if (this.smoothedHeadingDeg === null) {
      this.smoothedHeadingDeg = rawHeading;
    } else {
      this.smoothedHeadingDeg = filterCircularAngle(this.smoothedHeadingDeg, rawHeading, this.alpha);
    }

    const finalHeading = parseFloat(this.smoothedHeadingDeg.toFixed(1));

    return {
      headingDeg: finalHeading,
      source: 'GNSS_COURSE',
      confidence: rawFix.accuracy ? Math.min(1.0, Math.max(0.2, 12.0 / rawFix.accuracy)) : 0.85,
      timestamp,
      valid: true,
    };
  }
}

export const headingPipeline = new HeadingPipeline();
