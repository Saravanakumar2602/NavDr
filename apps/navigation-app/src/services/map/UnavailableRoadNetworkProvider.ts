import { RoadNetworkProvider, RoadSegment } from './RoadNetworkProvider';

/**
 * Production Default Road Network Provider for Stage 4D.1.
 * Safely reports UNAVAILABLE when offline OSM graph is not packaged,
 * ensuring map matcher falls back to raw DR without fake snapping or crashes.
 */
export class UnavailableRoadNetworkProvider implements RoadNetworkProvider {
  public async getCandidates(
    _latitude: number,
    _longitude: number,
    _radiusMeters: number
  ): Promise<RoadSegment[]> {
    return [];
  }

  public isAvailable(): boolean {
    return false;
  }
}

export const unavailableRoadNetworkProvider = new UnavailableRoadNetworkProvider();
