import { DrPose, MatchedDrPose, MapMatchStatus, MapMatchConfidence } from '../../types/navigation';
import { RoadNetworkProvider, RoadSegment, RoadCandidate } from './RoadNetworkProvider';
import { unavailableRoadNetworkProvider } from './UnavailableRoadNetworkProvider';

export class MapMatcher {
  private provider: RoadNetworkProvider;
  private lastMatchedSegmentId: string | null = null;
  private lastMatchedPose: MatchedDrPose | null = null;
  private static readonly METERS_PER_DEG_LAT = 111132.92;
  private static readonly MAX_SEARCH_RADIUS_METERS = 35.0;
  private static readonly MAX_HEADING_ERROR_DEG = 65.0;

  constructor(provider: RoadNetworkProvider = unavailableRoadNetworkProvider) {
    this.provider = provider;
  }

  public setProvider(provider: RoadNetworkProvider): void {
    this.provider = provider;
    this.reset();
  }

  public reset(): void {
    this.lastMatchedSegmentId = null;
    this.lastMatchedPose = null;
  }

  /**
   * Evaluates a raw DrPose against nearby road network candidates and produces a MatchedDrPose.
   */
  public async processPose(drPose: DrPose): Promise<MatchedDrPose> {
    const rawLat = drPose.latitude;
    const rawLon = drPose.longitude;
    const drHeading = drPose.headingDeg;
    const now = drPose.timestamp;

    // 1. Check if road network provider is available
    if (!this.provider.isAvailable()) {
      return this.createFallbackPose(drPose, 'MAP_MATCH_UNAVAILABLE', 'UNAVAILABLE');
    }

    // 2. Query nearby candidate road segments
    let segments: RoadSegment[] = [];
    try {
      segments = await this.provider.getCandidates(rawLat, rawLon, MapMatcher.MAX_SEARCH_RADIUS_METERS);
    } catch (e) {
      return this.createFallbackPose(drPose, 'MAP_MATCH_UNAVAILABLE', 'UNAVAILABLE');
    }

    if (!segments || segments.length === 0) {
      return this.createFallbackPose(drPose, 'RAW_DR', 'UNAVAILABLE');
    }

    // 3. Evaluate each road candidate segment
    const candidates: RoadCandidate[] = [];

    for (const seg of segments) {
      if (!seg.coordinates || seg.coordinates.length < 2) continue;

      // Iterate through polyline sub-segments (A -> B)
      for (let i = 0; i < seg.coordinates.length - 1; i++) {
        const ptA = seg.coordinates[i];
        const ptB = seg.coordinates[i + 1];

        const segHeading = seg.headingDeg ?? this.calculateSegmentHeading(ptA, ptB);
        const projection = this.projectPointToSegment(rawLat, rawLon, ptA[1], ptA[0], ptB[1], ptB[0]);

        const headingError = this.calculateHeadingError(drHeading, segHeading, Boolean(seg.oneWay));

        // Reject candidates outside physical boundaries
        if (projection.distanceMeters > MapMatcher.MAX_SEARCH_RADIUS_METERS) continue;
        if (headingError > MapMatcher.MAX_HEADING_ERROR_DEG) continue;

        // Calculate candidate score
        const distNorm = projection.distanceMeters / MapMatcher.MAX_SEARCH_RADIUS_METERS;
        const headingNorm = headingError / 180.0;
        let score = 0.60 * distNorm + 0.40 * headingNorm;

        // Hysteresis Bonus: Bias continuity with previously matched road segment
        if (seg.id === this.lastMatchedSegmentId) {
          score -= 0.15;
        }

        candidates.push({
          segment: seg,
          matchedLatitude: projection.lat,
          matchedLongitude: projection.lon,
          distanceMeters: projection.distanceMeters,
          headingErrorDeg: headingError,
          score,
        });
      }
    }

    if (candidates.length === 0) {
      return this.createFallbackPose(drPose, 'RAW_DR', 'UNAVAILABLE');
    }

    // 4. Sort candidates by lowest score
    candidates.sort((a, b) => a.score - b.score);
    const best = candidates[0];

    // Hysteresis Check: Require new candidate to be noticeably better (> 0.15 score diff) to switch segments
    if (
      this.lastMatchedSegmentId &&
      this.lastMatchedSegmentId !== best.segment.id &&
      this.lastMatchedPose
    ) {
      const prevCandidate = candidates.find((c) => c.segment.id === this.lastMatchedSegmentId);
      if (prevCandidate && prevCandidate.score <= best.score + 0.15) {
        // Keep previous segment for trajectory stability
        return this.createMatchedPose(drPose, prevCandidate);
      }
    }

    // Accept best candidate
    this.lastMatchedSegmentId = best.segment.id;
    return this.createMatchedPose(drPose, best);
  }

  /**
   * Projects point (pLat, pLon) onto line segment (aLat, aLon) -> (bLat, bLon) in local ENU metric frame.
   */
  public projectPointToSegment(
    pLat: number,
    pLon: number,
    aLat: number,
    aLon: number,
    bLat: number,
    bLon: number
  ): { lat: number; lon: number; distanceMeters: number } {
    const cosLatA = Math.cos((aLat * Math.PI) / 180.0);
    const metersPerDegLonA = MapMatcher.METERS_PER_DEG_LAT * cosLatA;

    // Convert B and P to ENU relative to A (origin A = [0, 0])
    const xB = (bLon - aLon) * metersPerDegLonA;
    const yB = (bLat - aLat) * MapMatcher.METERS_PER_DEG_LAT;

    const xP = (pLon - aLon) * metersPerDegLonA;
    const yP = (pLat - aLat) * MapMatcher.METERS_PER_DEG_LAT;

    const vLenSq = xB * xB + yB * yB;
    let t = 0.0;
    if (vLenSq > 1e-6) {
      t = (xP * xB + yP * yB) / vLenSq;
      t = Math.max(0.0, Math.min(1.0, t));
    }

    // Matched point in local ENU
    const xM = t * xB;
    const yM = t * yB;

    // Convert ENU match back to WGS84
    const mLat = aLat + yM / MapMatcher.METERS_PER_DEG_LAT;
    const mLon = aLon + xM / metersPerDegLonA;

    const dx = xP - xM;
    const dy = yP - yM;
    const distanceMeters = Math.sqrt(dx * dx + dy * dy);

    return { lat: mLat, lon: mLon, distanceMeters };
  }

  /**
   * Calculates circular angular heading difference handling 0° / 360° wrap cleanly.
   */
  public calculateCircularHeadingError(h1: number, h2: number): number {
    const diff = Math.abs(h1 - h2) % 360;
    return diff > 180 ? 360 - diff : diff;
  }

  /**
   * Evaluates heading difference against segment orientation, considering one-way rules.
   */
  public calculateHeadingError(drHeading: number, segmentHeading: number, oneWay: boolean): number {
    const directErr = this.calculateCircularHeadingError(drHeading, segmentHeading);
    if (oneWay) {
      return directErr;
    }
    const reverseErr = this.calculateCircularHeadingError(drHeading, (segmentHeading + 180) % 360);
    return Math.min(directErr, reverseErr);
  }

  private calculateSegmentHeading(ptA: [number, number], ptB: [number, number]): number {
    const lon1 = (ptA[0] * Math.PI) / 180.0;
    const lat1 = (ptA[1] * Math.PI) / 180.0;
    const lon2 = (ptB[0] * Math.PI) / 180.0;
    const lat2 = (ptB[1] * Math.PI) / 180.0;

    const dLon = lon2 - lon1;
    const y = Math.sin(dLon) * Math.cos(lat2);
    const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
    const brngRad = Math.atan2(y, x);
    return ((brngRad * 180.0) / Math.PI + 360.0) % 360.0;
  }

  private createMatchedPose(drPose: DrPose, candidate: RoadCandidate): MatchedDrPose {
    const confidenceScore = Math.max(0.0, Math.min(1.0, 1.0 - candidate.score));
    let confidence: MapMatchConfidence = 'LOW';
    if (candidate.score <= 0.25) confidence = 'HIGH';
    else if (candidate.score <= 0.50) confidence = 'MEDIUM';

    const matchedPose: MatchedDrPose = {
      latitude: candidate.matchedLatitude,
      longitude: candidate.matchedLongitude,
      timestamp: drPose.timestamp,
      headingDeg: candidate.segment.headingDeg ?? drPose.headingDeg,
      speedMps: drPose.speedMps,
      source: 'MAP_MATCHED',
      matchedSegmentId: candidate.segment.id,
      confidence,
      confidenceScore,
      rawDrLatitude: drPose.latitude,
      rawDrLongitude: drPose.longitude,
      distanceToRoadMeters: parseFloat(candidate.distanceMeters.toFixed(1)),
      headingErrorDeg: parseFloat(candidate.headingErrorDeg.toFixed(1)),
    };

    this.lastMatchedPose = matchedPose;
    return matchedPose;
  }

  private createFallbackPose(
    drPose: DrPose,
    status: MapMatchStatus,
    confidence: MapMatchConfidence
  ): MatchedDrPose {
    return {
      latitude: drPose.latitude,
      longitude: drPose.longitude,
      timestamp: drPose.timestamp,
      headingDeg: drPose.headingDeg,
      speedMps: drPose.speedMps,
      source: 'RAW_DR',
      matchedSegmentId: null,
      confidence,
      confidenceScore: 0.0,
      rawDrLatitude: drPose.latitude,
      rawDrLongitude: drPose.longitude,
      distanceToRoadMeters: 0.0,
      headingErrorDeg: 0.0,
    };
  }
}

export const mapMatcher = new MapMatcher();
