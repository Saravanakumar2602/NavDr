export interface RoadSegment {
  id: string;
  name?: string;
  coordinates: [number, number][]; // WGS84 coordinates [[longitude, latitude], ...]
  headingDeg?: number;
  roadType?: string;
  speedLimitKmh?: number;
  oneWay?: boolean;
}

export interface RoadCandidate {
  segment: RoadSegment;
  matchedLatitude: number;
  matchedLongitude: number;
  distanceMeters: number;
  headingErrorDeg: number;
  score: number;
}

export interface RoadNetworkProvider {
  getCandidates(latitude: number, longitude: number, radiusMeters: number): Promise<RoadSegment[]>;
  isAvailable(): boolean;
}
