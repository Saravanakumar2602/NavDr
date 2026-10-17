export type GnssStatus = 'AVAILABLE' | 'DENIED' | 'RECOVERING' | 'WAITING' | 'SIGNAL_LOST' | 'PERMISSION_REQUIRED';
export type NavigationMode = 'GNSS NAVIGATION' | 'WAITING FOR LOCATION' | 'LOCATION PERMISSION REQUIRED' | 'GNSS SIGNAL LOST' | 'DEAD RECKONING ACTIVE';
export type ImuStatus = 'CONNECTED' | 'DISCONNECTED';
export type MapStatus = 'OFFLINE VECTOR' | 'LOADING' | 'AVAILABLE';
export type ActiveTab = 'NAVIGATE' | 'SYSTEM' | 'SETTINGS';
export type LocationPermissionStatus = 'UNDETERMINED' | 'GRANTED' | 'DENIED' | 'SERVICES_DISABLED';

export type SpeedSource = 'GNSS_REPORTED' | 'GNSS_DERIVED' | 'AI_SPEED' | 'NONE';

export interface SpeedEstimate {
  speedMps: number | null;
  speedKmh: number | null;
  source: SpeedSource;
  confidence: number; // 0.0 to 1.0
  timestamp: number;
  valid: boolean;
}

export type HeadingSource = 'GNSS_COURSE' | 'IMU_HEADING' | 'NONE';

export interface HeadingEstimate {
  headingDeg: number | null; // normalized [0, 360)
  source: HeadingSource;
  confidence: number; // 0.0 to 1.0
  timestamp: number;
  valid: boolean;
}

export type GnssOutageState = 'GNSS_FIX' | 'GNSS_DEGRADED' | 'GNSS_DENIED' | 'GNSS_RECOVERY';

export interface GnssStateTransition {
  timestamp: number;
  fromState: GnssOutageState;
  toState: GnssOutageState;
  reason: string;
}

export interface GnssNavigationState {
  state: GnssOutageState;
  lastValidFixTimestamp: number;
  fixAgeMs: number;
  outageDurationMs: number;
  recoveryFixCount: number;
  lastKnownPosition: { latitude: number; longitude: number } | null;
  transitionHistory: GnssStateTransition[];
}

export interface LocationFix {
  timestamp: number;
  latitude: number;
  longitude: number;
  altitude: number | null;
  accuracy: number | null;
  speed: number | null; // m/s
  hasSpeed: boolean;
  bearing: number | null; // degrees (GNSS course)
  hasBearing: boolean;
  provider: string;
  deltaTimeMs?: number;
  distanceMeters?: number;
  derivedSpeedMps?: number;
}

export interface FilteredGnssPose {
  latitude: number;
  longitude: number;
  speedKmH: number | null;
  headingDeg: number | null;
  accuracyMeters: number | null;
  timestamp: number;
  isStationary: boolean;
  isOutlier: boolean;
  filterState: 'STATIONARY' | 'MOVING' | 'OUTLIER_REJECTED' | 'INITIALIZING';
  latencyMs: number;
  speedEstimate?: SpeedEstimate;
  headingEstimate?: HeadingEstimate;
}

export interface GnssDiagnostics {
  fixCount: number;
  acceptedFixCount: number;
  rejectedOutlierCount: number;
  lastFixAgeSeconds: number;
  updateRateHz: number;
  meanIntervalMs: number;
  medianIntervalMs: number;
  minIntervalMs: number;
  maxIntervalMs: number;
  currentAccuracy: number | null;
  minAccuracy: number | null;
  maxAccuracy: number | null;
  meanAccuracy: number | null;
  reportedSpeedKmH: number | null; // km/h
  hasSpeed: boolean;
  derivedSpeedKmH: number | null; // km/h
  filteredSpeedKmH: number | null; // km/h
  reportedBearing: number | null; // deg
  hasBearing: boolean;
  filteredHeadingDeg: number | null; // deg
  filterState: 'STATIONARY' | 'MOVING' | 'OUTLIER_REJECTED' | 'INITIALIZING';
  rawJitterMaxMeters: number;
  rawJitterMeanMeters: number;
  filteredJitterMaxMeters: number;
  filteredJitterMeanMeters: number;
  filterLatencyMs: number;
  rawLatitude: number | null;
  rawLongitude: number | null;
  filteredLatitude: number | null;
  filteredLongitude: number | null;
  speedEstimate?: SpeedEstimate;
  headingEstimate?: HeadingEstimate;
}

export interface VehiclePose {
  x: number;
  y: number;
  latitude: number;
  longitude: number;
  heading: number | null; // degrees 0-360 (GNSS course)
  speed: number | null; // km/h
  speedEstimate?: SpeedEstimate;
  headingEstimate?: HeadingEstimate;
}

export interface TrajectoryPoint {
  x: number;
  y: number;
  latitude: number;
  longitude: number;
  type: 'gnss' | 'idr' | 'map_matched';
  timestamp: number;
}

export interface SensorTelemetry {
  accelX: number;
  accelY: number;
  accelZ: number;
  gyroX: number;
  gyroY: number;
  gyroZ: number;
  timestamp: number;
}

export interface DrPose {
  latitude: number;
  longitude: number;
  eastM: number;
  northM: number;
  velocityMps: number;
  speedMps: number;
  headingDeg: number;
  timestamp: number;
  confidence: number; // 0.0 to 1.0
  valid: boolean;
  drDurationMs: number;
  drDistanceMeters: number;
  motionMode: 'STATIONARY' | 'DYNAMIC_MANEUVER' | 'VERIFIED_STRAIGHT' | 'GENERAL_MOTION';
}

export type MapMatchStatus = 'MATCHED' | 'RAW_DR' | 'MAP_MATCH_UNAVAILABLE';
export type MapMatchConfidence = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNAVAILABLE';

export interface MatchedDrPose {
  latitude: number;
  longitude: number;
  timestamp: number;
  headingDeg: number;
  speedMps: number;
  source: 'MAP_MATCHED' | 'RAW_DR';
  matchedSegmentId: string | null;
  confidence: MapMatchConfidence;
  confidenceScore: number; // 0.0 to 1.0
  rawDrLatitude: number;
  rawDrLongitude: number;
  distanceToRoadMeters: number;
  headingErrorDeg: number;
}

export type DrState = 'DR_INACTIVE' | 'DR_READY' | 'DR_ACTIVE';

export interface PlaceSearchResult {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  type?: string;
}

export interface Destination {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
}

export type NavigationIntent = 'IDLE' | 'DESTINATION_SELECTED';

export interface Coordinate {
  latitude: number;
  longitude: number;
}

export interface RouteSegment {
  id: string;
  name?: string;
  coordinates: [number, number][]; // [[lon, lat], ...]
  distanceMeters: number;
  roadType?: string;
}

export interface Route {
  id: string;
  origin: Coordinate;
  destination: Coordinate;
  segments: RouteSegment[];
  geometry: [number, number][]; // WGS84 coordinates [[longitude, latitude], ...]
  distanceMeters: number;
}

export type RouteStatus = 'NONE' | 'CALCULATING' | 'READY' | 'ERROR';

export type RouteError =
  | 'NO_START_ROAD'
  | 'NO_DESTINATION_ROAD'
  | 'NO_ROUTE'
  | 'OUTSIDE_OFFLINE_COVERAGE'
  | 'NETWORK_NOT_REQUIRED'
  | 'UNKNOWN';

export type ManeuverType =
  | 'START'
  | 'CONTINUE'
  | 'SLIGHT_LEFT'
  | 'TURN_LEFT'
  | 'SLIGHT_RIGHT'
  | 'TURN_RIGHT'
  | 'U_TURN'
  | 'ARRIVE';

export type TurnByTurnNavigationStatus =
  | 'IDLE'
  | 'FOLLOWING_ROUTE'
  | 'APPROACHING_MANEUVER'
  | 'MANEUVER_ACTIVE'
  | 'ARRIVED';

export interface NavigationInstruction {
  type: ManeuverType;
  distanceMeters: number;
  instructionText: string;
  roadName?: string;
  routeSegmentIndex: number;
  junctionCoordinate?: Coordinate;
  confidence?: number;
}

export interface NavigationProgressState {
  navigationStatus: TurnByTurnNavigationStatus;
  currentInstruction: NavigationInstruction | null;
  nextInstruction: NavigationInstruction | null;
  currentSegmentIndex: number;
  distanceToDestinationMeters: number;
  distanceToManeuverMeters: number;
  isArrived: boolean;
}

export interface NavigationState {
  pose: VehiclePose;
  currentFix: LocationFix | null;
  filteredPose: FilteredGnssPose | null;
  positionUncertainty: number | null; // meters
  gnssStatus: GnssStatus;
  navigationMode: NavigationMode;
  locationPermissionStatus: LocationPermissionStatus;
  updateRateHz: number;
  imuStatus: ImuStatus;
  mapStatus: MapStatus;
  isNavigating: boolean;
  outageDurationSeconds: number;
  confidence: number; // percentage 0-100%
  processingLatencyMs: number;
  lastKnownGnssPose: VehiclePose | null;
  gnssTrajectory: TrajectoryPoint[];
  idrTrajectory: TrajectoryPoint[];
  mapMatchedTrajectory: TrajectoryPoint[];
  activeBannerMessage: string | null;
  activeTab: ActiveTab;
  telemetryHistory: SensorTelemetry[];
  diagnostics: GnssDiagnostics;
  speedEstimate?: SpeedEstimate;
  headingEstimate?: HeadingEstimate;
  gnssNavState?: GnssNavigationState;
  drPose?: DrPose;
  drState?: DrState;
  drDistanceMeters?: number;
  matchedDrPose?: MatchedDrPose;
  mapMatchStatus?: MapMatchStatus;
  demoStateIndex?: number;
  destination?: Destination | null;
  navigationIntent?: NavigationIntent;
  route?: Route | null;
  routeStatus?: RouteStatus;
  routeError?: RouteError | null;
  turnByTurnStatus?: TurnByTurnNavigationStatus;
  currentInstruction?: NavigationInstruction | null;
  nextInstruction?: NavigationInstruction | null;
  distanceToDestinationMeters?: number;
}

export interface SystemInfo {
  appName: string;
  fullName: string;
  tagline: string;
  version: string;
  isDemoMode: boolean;
  benchmark: {
    dataset: string;
    m028Baseline: string;
    m029Candidate: string;
    improvement: string;
    disclaimer: string;
  };
}

export interface OfflineRegionBounds {
  south: number;
  west: number;
  north: number;
  east: number;
}

export interface OfflineMapManifest {
  formatVersion: number;
  id: string;
  name: string;
  version: string;
  bounds: OfflineRegionBounds;
  roadCount: number;
  segmentCount: number;
  spatialCellCount: number;
  gridSizeDeg: number;
  tileCount?: number;
  tileSizeDeg?: number;
  source: string;
  generatedAt: string;
  license: string;
}

export interface OfflineMapPackage {
  manifest: OfflineMapManifest;
  roads: Record<string, any>;
  spatialIndex: Record<string, string[]>;
}

