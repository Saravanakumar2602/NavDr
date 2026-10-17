import {
  Route,
  Coordinate,
  NavigationInstruction,
  NavigationProgressState,
  ManeuverType,
  TurnByTurnNavigationStatus,
} from '../../types/navigation';
import { calculateHaversineDistance } from '../../utils/geo';

export class RouteNavigationEngine {
  private lastSegmentIndex: number = 0;
  private currentRoute: Route | null = null;

  /**
   * Resets engine progression state for a new route session.
   */
  public reset(): void {
    this.lastSegmentIndex = 0;
    this.currentRoute = null;
  }

  /**
   * Calculates bearing angle in degrees [0, 360) between two coordinates.
   */
  public calculateBearing(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const toRad = (d: number) => (d * Math.PI) / 180;
    const toDeg = (r: number) => (r * 180) / Math.PI;

    const phi1 = toRad(lat1);
    const phi2 = toRad(lat2);
    const dLon = toRad(lon2 - lon1);

    const y = Math.sin(dLon) * Math.cos(phi2);
    const x = Math.cos(phi1) * Math.sin(phi2) - Math.sin(phi1) * Math.cos(phi2) * Math.cos(dLon);

    const brng = toDeg(Math.atan2(y, x));
    return (brng + 360) % 360;
  }

  /**
   * Computes shortest circular angle delta in range [-180, +180] degrees.
   * Properly handles North transitions (e.g. 359° -> 1° = +2°).
   */
  public calculateTurnAngle(bIncoming: number, bOutgoing: number): number {
    return ((bOutgoing - bIncoming + 540) % 360) - 180;
  }

  /**
   * Classifies turn maneuver type based on turn angle delta.
   */
  public classifyManeuver(angleDeg: number): ManeuverType {
    const absAngle = Math.abs(angleDeg);
    if (absAngle <= 20) return 'CONTINUE';
    if (angleDeg > 20 && angleDeg <= 45) return 'SLIGHT_RIGHT';
    if (angleDeg > 45 && angleDeg <= 135) return 'TURN_RIGHT';
    if (angleDeg < -20 && angleDeg >= -45) return 'SLIGHT_LEFT';
    if (angleDeg < -45 && angleDeg >= -135) return 'TURN_LEFT';
    return 'U_TURN';
  }

  /**
   * Generates human-readable instruction text.
   */
  private formatInstructionText(
    type: ManeuverType,
    distanceMeters: number,
    roadName?: string
  ): string {
    const distText =
      distanceMeters >= 1000
        ? `${(distanceMeters / 1000).toFixed(1)} km`
        : `${Math.round(distanceMeters / 10) * 10} m`;

    let verb = 'CONTINUE';
    if (type === 'START') verb = 'HEAD TOWARDS';
    else if (type === 'CONTINUE') verb = 'CONTINUE STRAIGHT';
    else if (type === 'SLIGHT_RIGHT') verb = 'SLIGHT RIGHT';
    else if (type === 'TURN_RIGHT') verb = 'TURN RIGHT';
    else if (type === 'SLIGHT_LEFT') verb = 'SLIGHT LEFT';
    else if (type === 'TURN_LEFT') verb = 'TURN LEFT';
    else if (type === 'U_TURN') verb = 'MAKE A U-TURN';
    else if (type === 'ARRIVE') return 'ARRIVED AT DESTINATION';

    const ontoRoad = roadName && roadName.trim() !== '' ? ` onto ${roadName}` : '';
    return `${verb} in ${distText}${ontoRoad}`;
  }

  /**
   * Sanitizes raw OSM way IDs and returns user-friendly road names or classifications.
   */
  public formatUserFriendlyRoadName(rawName?: string, roadType?: string): string | undefined {
    if (!rawName || rawName.trim() === '') {
      if (roadType) {
        const typeUpper = roadType.toUpperCase();
        if (typeUpper.includes('PRIMARY')) return 'Primary Road';
        if (typeUpper.includes('SECONDARY')) return 'Secondary Road';
        if (typeUpper.includes('TERTIARY')) return 'Tertiary Road';
        if (typeUpper.includes('TRUNK')) return 'Main Highway';
        if (typeUpper.includes('RESIDENTIAL')) return 'Local Road';
      }
      return undefined;
    }

    const trimmed = rawName.trim();

    // Never display raw OSM way IDs like "Road 658253308" or "osm_w658253308"
    if (/^(Road\s+\d+|osm_w\d+|\d+)$/i.test(trimmed)) {
      if (roadType) {
        const typeUpper = roadType.toUpperCase();
        if (typeUpper.includes('PRIMARY')) return 'Primary Road';
        if (typeUpper.includes('SECONDARY')) return 'Secondary Road';
        if (typeUpper.includes('TERTIARY')) return 'Tertiary Road';
        if (typeUpper.includes('TRUNK')) return 'Main Highway';
        if (typeUpper.includes('RESIDENTIAL')) return 'Local Road';
      }
      return 'unnamed road';
    }

    return trimmed;
  }

  /**
   * Evaluates turn-by-turn navigation progress for a given route and current vehicle position.
   */
  public updateProgress(
    route: Route,
    currentPose: { latitude: number; longitude: number; heading?: number | null }
  ): NavigationProgressState {
    if (!route || !route.geometry || route.geometry.length < 2) {
      return {
        navigationStatus: 'IDLE',
        currentInstruction: null,
        nextInstruction: null,
        currentSegmentIndex: 0,
        distanceToDestinationMeters: 0,
        distanceToManeuverMeters: 0,
        isArrived: false,
      };
    }

    if (this.currentRoute?.id !== route.id) {
      this.currentRoute = route;
      this.lastSegmentIndex = 0;
    }

    const { latitude: curLat, longitude: curLon } = currentPose;
    const geometry = route.geometry;
    const numPoints = geometry.length;

    // 1. Calculate distance to destination
    const distToDestMeters = calculateHaversineDistance(
      curLat,
      curLon,
      route.destination.latitude,
      route.destination.longitude
    );

    // 2. Check Arrival Condition (within 25m of destination or near end of route geometry)
    if (distToDestMeters <= 25.0) {
      return {
        navigationStatus: 'ARRIVED',
        currentInstruction: {
          type: 'ARRIVE',
          distanceMeters: distToDestMeters,
          instructionText: 'ARRIVED AT DESTINATION',
          routeSegmentIndex: numPoints - 1,
          junctionCoordinate: route.destination,
        },
        nextInstruction: null,
        currentSegmentIndex: numPoints - 1,
        distanceToDestinationMeters: Math.round(distToDestMeters),
        distanceToManeuverMeters: 0,
        isArrived: true,
      };
    }

    // 3. Find closest point on route geometry with hysteresis
    let closestIndex = this.lastSegmentIndex;
    let minPointDist = Infinity;

    for (let i = this.lastSegmentIndex; i < numPoints; i++) {
      const [gLon, gLat] = geometry[i];
      const d = calculateHaversineDistance(curLat, curLon, gLat, gLon);
      if (d < minPointDist) {
        minPointDist = d;
        closestIndex = i;
      }
    }

    // Hysteresis guard: update lastSegmentIndex strictly monotonically
    if (closestIndex > this.lastSegmentIndex) {
      this.lastSegmentIndex = closestIndex;
    }

    // 4. Scan ahead for upcoming turn maneuvers along route geometry
    let upcomingManeuverIndex = numPoints - 1;
    let upcomingManeuverType: ManeuverType = 'ARRIVE';
    let upcomingRoadName: string | undefined;
    let upcomingRoadType: string | undefined;

    for (let j = closestIndex + 1; j < numPoints - 1; j++) {
      const [prevLon, prevLat] = geometry[j - 1];
      const [currLon, currLat] = geometry[j];
      const [nextLon, nextLat] = geometry[j + 1];

      const bIn = this.calculateBearing(prevLat, prevLon, currLat, currLon);
      const bOut = this.calculateBearing(currLat, currLon, nextLat, nextLon);
      const angle = this.calculateTurnAngle(bIn, bOut);
      const mType = this.classifyManeuver(angle);

      if (mType !== 'CONTINUE') {
        upcomingManeuverIndex = j;
        upcomingManeuverType = mType;

        // Associate road name from matching segment if available
        if (route.segments && route.segments.length > 0) {
          const segMatch = route.segments.find((s) =>
            s.coordinates.some(([slon, slat]) =>
              Math.abs(slon - currLon) < 1e-4 && Math.abs(slat - currLat) < 1e-4
            )
          );
          if (segMatch) {
            upcomingRoadName = segMatch.name;
            upcomingRoadType = segMatch.roadType;
          }
        }
        break;
      }
    }

    // 5. Calculate cumulative distance along geometry to upcoming maneuver
    let distToManeuver = calculateHaversineDistance(
      curLat,
      curLon,
      geometry[closestIndex][1],
      geometry[closestIndex][0]
    );

    for (let k = closestIndex; k < upcomingManeuverIndex; k++) {
      distToManeuver += calculateHaversineDistance(
        geometry[k][1],
        geometry[k][0],
        geometry[k + 1][1],
        geometry[k + 1][0]
      );
    }

    distToManeuver = Math.round(distToManeuver);

    const [juncLon, juncLat] = geometry[upcomingManeuverIndex];
    const cleanRoadName = this.formatUserFriendlyRoadName(upcomingRoadName, upcomingRoadType);

    const currentInstruction: NavigationInstruction = {
      type: upcomingManeuverType,
      distanceMeters: distToManeuver,
      instructionText: this.formatInstructionText(
        upcomingManeuverType,
        distToManeuver,
        cleanRoadName
      ),
      roadName: cleanRoadName,
      routeSegmentIndex: upcomingManeuverIndex,
      junctionCoordinate: { latitude: juncLat, longitude: juncLon },
    };

    const status: TurnByTurnNavigationStatus =
      distToManeuver <= 150 ? 'APPROACHING_MANEUVER' : 'FOLLOWING_ROUTE';

    return {
      navigationStatus: status,
      currentInstruction,
      nextInstruction: null,
      currentSegmentIndex: closestIndex,
      distanceToDestinationMeters: Math.round(distToDestMeters),
      distanceToManeuverMeters: distToManeuver,
      isArrived: false,
    };
  }
}

export const routeNavigationEngine = new RouteNavigationEngine();
