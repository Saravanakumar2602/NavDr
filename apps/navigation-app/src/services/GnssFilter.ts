import { LocationFix, FilteredGnssPose } from '../types/navigation';
import { calculateHaversineDistance, latLngToEnu, enuToLatLng, filterCircularAngle } from '../utils/geo';

export class GnssFilter {
  private lastAcceptedFix: LocationFix | null = null;
  private currentPose: FilteredGnssPose | null = null;
  private refLat: number | null = null;
  private refLon: number | null = null;
  private filteredE: number = 0;
  private filteredN: number = 0;

  // Hysteresis counters for stationary detection
  private stationaryCandidateCount: number = 0;
  private isStationaryState: boolean = true; // start stationary by default

  // Counter telemetry
  private acceptedFixCount: number = 0;
  private rejectedOutlierCount: number = 0;

  // Speed and course state
  private filteredSpeedKmH: number | null = null;
  private filteredHeadingDeg: number | null = null;

  public reset(): void {
    this.lastAcceptedFix = null;
    this.currentPose = null;
    this.refLat = null;
    this.refLon = null;
    this.filteredE = 0;
    this.filteredN = 0;
    this.stationaryCandidateCount = 0;
    this.isStationaryState = true;
    this.acceptedFixCount = 0;
    this.rejectedOutlierCount = 0;
    this.filteredSpeedKmH = null;
    this.filteredHeadingDeg = null;
  }

  /**
   * Process raw GNSS fix and produce trustworthy FilteredGnssPose
   */
  public processFix(rawFix: LocationFix): FilteredGnssPose {
    const startTime = performance.now();

    // 1. Quality Gate
    if (!this.isValidQuality(rawFix)) {
      const latencyMs = parseFloat((performance.now() - startTime).toFixed(2));
      return (
        this.currentPose || {
          latitude: rawFix.latitude,
          longitude: rawFix.longitude,
          speedKmH: null,
          headingDeg: null,
          accuracyMeters: rawFix.accuracy,
          timestamp: rawFix.timestamp,
          isStationary: true,
          isOutlier: true,
          filterState: 'OUTLIER_REJECTED',
          latencyMs,
        }
      );
    }

    // Initialize origin reference on first valid fix
    if (this.refLat === null || this.refLon === null) {
      this.refLat = rawFix.latitude;
      this.refLon = rawFix.longitude;
      this.filteredE = 0;
      this.filteredN = 0;
      this.lastAcceptedFix = rawFix;
      this.acceptedFixCount = 1;
      this.isStationaryState = true;

      const latencyMs = parseFloat((performance.now() - startTime).toFixed(2));
      this.currentPose = {
        latitude: rawFix.latitude,
        longitude: rawFix.longitude,
        speedKmH: rawFix.hasSpeed && rawFix.speed !== null ? rawFix.speed * 3.6 : 0,
        headingDeg: null,
        accuracyMeters: rawFix.accuracy,
        timestamp: rawFix.timestamp,
        isStationary: true,
        isOutlier: false,
        filterState: 'INITIALIZING',
        latencyMs,
      };
      return this.currentPose;
    }

    // 2. Outlier Rejection Check
    const prevFix = this.lastAcceptedFix!;
    const dtSeconds = Math.max(0.001, (rawFix.timestamp - prevFix.timestamp) / 1000.0);
    const distMeters = calculateHaversineDistance(
      prevFix.latitude,
      prevFix.longitude,
      rawFix.latitude,
      rawFix.longitude
    );
    const impliedSpeedMps = distMeters / dtSeconds;

    // Reject physically implausible jumps (>162 km/h or >100m displacement with poor accuracy)
    const isOutlier =
      impliedSpeedMps > 45.0 || (distMeters > 100 && (rawFix.accuracy ?? 50) > 25);

    if (isOutlier) {
      this.rejectedOutlierCount++;
      const latencyMs = parseFloat((performance.now() - startTime).toFixed(2));
      return {
        ...this.currentPose!,
        timestamp: rawFix.timestamp,
        isOutlier: true,
        filterState: 'OUTLIER_REJECTED',
        latencyMs,
      };
    }

    // Accepted Fix
    this.acceptedFixCount++;
    this.lastAcceptedFix = rawFix;

    // 3. Stationary Detection with Hysteresis / Debounce
    const rawSpeedMps = rawFix.hasSpeed && rawFix.speed !== null ? rawFix.speed : 0;
    const isStationaryCandidate = rawSpeedMps < 0.5 && distMeters < 1.0;

    if (isStationaryCandidate) {
      this.stationaryCandidateCount++;
      if (this.stationaryCandidateCount >= 3) {
        this.isStationaryState = true;
      }
    } else {
      if (rawSpeedMps > 0.8 || distMeters > 1.5) {
        this.stationaryCandidateCount = 0;
        this.isStationaryState = false;
      }
    }

    // 4. Local ENU Adaptive Position Filter
    const { e: rawE, n: rawN } = latLngToEnu(
      rawFix.latitude,
      rawFix.longitude,
      this.refLat,
      this.refLon
    );

    let filteredLat = rawFix.latitude;
    let filteredLon = rawFix.longitude;

    if (this.isStationaryState) {
      // Hold stationary position steady to eliminate GPS jitter completely!
      const curr = enuToLatLng(this.filteredE, this.filteredN, this.refLat, this.refLon);
      filteredLat = curr.lat;
      filteredLon = curr.lon;
    } else {
      // Adaptive alpha gain based on accuracy and speed
      const acc = rawFix.accuracy ?? 15;
      let alpha = Math.min(0.85, Math.max(0.15, 10.0 / acc));
      if (rawSpeedMps > 1.5) {
        alpha = Math.min(0.90, alpha + 0.35); // responsive moving gain
      }

      this.filteredE = this.filteredE + alpha * (rawE - this.filteredE);
      this.filteredN = this.filteredN + alpha * (rawN - this.filteredN);

      const filteredGeo = enuToLatLng(this.filteredE, this.filteredN, this.refLat, this.refLon);
      filteredLat = filteredGeo.lat;
      filteredLon = filteredGeo.lon;
    }

    // 5. Speed Filter
    if (this.isStationaryState) {
      this.filteredSpeedKmH = 0.0;
    } else if (rawFix.hasSpeed && rawFix.speed !== null && rawFix.speed >= 0) {
      const rawKmH = rawFix.speed * 3.6;
      if (this.filteredSpeedKmH === null) {
        this.filteredSpeedKmH = rawKmH;
      } else {
        const alphaV = 0.4;
        this.filteredSpeedKmH = (1 - alphaV) * this.filteredSpeedKmH + alphaV * rawKmH;
      }
    } else {
      this.filteredSpeedKmH = null;
    }

    // 6. Low-Speed Heading Gating & Circular Angle Filter
    if (
      this.isStationaryState ||
      rawSpeedMps < 0.45 ||
      !rawFix.hasBearing ||
      rawFix.bearing === null
    ) {
      this.filteredHeadingDeg = null; // --° when stationary or low speed
    } else {
      this.filteredHeadingDeg = filterCircularAngle(this.filteredHeadingDeg, rawFix.bearing, 0.35);
    }

    const latencyMs = parseFloat((performance.now() - startTime).toFixed(2));

    this.currentPose = {
      latitude: filteredLat,
      longitude: filteredLon,
      speedKmH: this.filteredSpeedKmH !== null ? parseFloat(this.filteredSpeedKmH.toFixed(1)) : null,
      headingDeg: this.filteredHeadingDeg,
      accuracyMeters: rawFix.accuracy !== null ? parseFloat(rawFix.accuracy.toFixed(1)) : null,
      timestamp: rawFix.timestamp,
      isStationary: this.isStationaryState,
      isOutlier: false,
      filterState: this.isStationaryState ? 'STATIONARY' : 'MOVING',
      latencyMs,
    };

    return this.currentPose;
  }

  private isValidQuality(fix: LocationFix): boolean {
    if (!fix) return false;
    if (isNaN(fix.latitude) || isNaN(fix.longitude)) return false;
    if (Math.abs(fix.latitude) > 90 || Math.abs(fix.longitude) > 180) return false;
    if (fix.latitude === 0 && fix.longitude === 0) return false;
    return true;
  }

  public getAcceptedFixCount(): number {
    return this.acceptedFixCount;
  }

  public getRejectedOutlierCount(): number {
    return this.rejectedOutlierCount;
  }
}
