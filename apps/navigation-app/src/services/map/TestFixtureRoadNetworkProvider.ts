import { RoadNetworkProvider, RoadSegment } from './RoadNetworkProvider';

/**
 * Deterministic Test Fixture Road Network Provider.
 * Used strictly for unit testing MapMatcher algorithm math (segment projection, circular heading wrap,
 * candidate scoring, and hysteresis) without relying on external network/OSM services.
 */
export class TestFixtureRoadNetworkProvider implements RoadNetworkProvider {
  private segments: RoadSegment[] = [
    {
      id: 'SEG_MAIN_AVE_01',
      name: 'Main Avenue (Northbound)',
      coordinates: [
        [77.5946, 12.9716],
        [77.5946, 12.9750],
      ],
      headingDeg: 0, // North
      roadType: 'PRIMARY',
      oneWay: true,
    },
    {
      id: 'SEG_CROSS_ST_02',
      name: 'Cross Street (Eastbound)',
      coordinates: [
        [77.5946, 12.9750],
        [77.5990, 12.9750],
      ],
      headingDeg: 90, // East
      roadType: 'SECONDARY',
      oneWay: false,
    },
    {
      id: 'SEG_PARALLEL_RD_03',
      name: 'Parallel Road (Northbound)',
      coordinates: [
        [77.5951, 12.9716], // ~55 meters East of Main Ave
        [77.5951, 12.9750],
      ],
      headingDeg: 0, // North
      roadType: 'RESIDENTIAL',
      oneWay: false,
    },
  ];

  public async getCandidates(
    latitude: number,
    longitude: number,
    radiusMeters: number
  ): Promise<RoadSegment[]> {
    // Return segments within bounding box search radius
    const degSearch = radiusMeters / 111132.92;
    return this.segments.filter((seg) => {
      const segMinLat = Math.min(...seg.coordinates.map((c) => c[1]));
      const segMaxLat = Math.max(...seg.coordinates.map((c) => c[1]));
      const segMinLon = Math.min(...seg.coordinates.map((c) => c[0]));
      const segMaxLon = Math.max(...seg.coordinates.map((c) => c[0]));

      return (
        latitude >= segMinLat - degSearch &&
        latitude <= segMaxLat + degSearch &&
        longitude >= segMinLon - degSearch &&
        longitude <= segMaxLon + degSearch
      );
    });
  }

  public isAvailable(): boolean {
    return true;
  }
}
