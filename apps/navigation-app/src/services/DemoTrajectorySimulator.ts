/**
 * DemoTrajectorySimulator — Backend-only deterministic navigation demo.
 *
 * LIFECYCLE:
 *   NOT started on app launch.
 *   NOT started on destination selection.
 *   Started ONLY when startDemoNavigation(route) is called from "Start Navigation".
 *
 * TIMELINE (deterministic, elapsed from startDemoNavigation):
 *   0–20s   : GNSS AVAILABLE  → synthetic GNSS fixes along A* route
 *   20–50s  : GNSS OUTAGE     → DR_ACTIVE, vehicle continues via route-constrained DR
 *   50s+    : GNSS RECOVERED  → synthetic GNSS fixes resume, DR reconciled
 *
 * HEADING: computed from actual A* route geometry bearing between consecutive
 * interpolated waypoints (not fixed, not phone compass).
 *
 * MOVEMENT: vehicle advances by physical distance (5 m/s) along cumulative
 * route distance, using correct geodetic interpolation.
 */

import { LocationFix, Route } from '../types/navigation';
import { ImuSample } from './DeadReckoningEngine';
import { calculateHaversineDistance } from '../utils/geo';

/** Dense waypoint along the interpolated route */
interface RouteWaypoint {
  latitude: number;
  longitude: number;
  /** True geographic bearing to the NEXT point, degrees [0, 360) */
  heading: number;
  /** Cumulative distance from route start, metres */
  cumulativeDist: number;
}

export class DemoTrajectorySimulator {
  // ── internal state ────────────────────────────────────────────────
  private timer: NodeJS.Timeout | null = null;
  private waypoints: RouteWaypoint[] = [];
  private totalRouteDistM: number = 0;

  /** Distance already travelled along the route, metres */
  private distanceTravelledM: number = 0;
  /** Wall-clock milliseconds when demo session started */
  private sessionStartMs: number = 0;

  private isSimulating: boolean = false;

  // Once-per-session flags to prevent double-transitions
  private outageArmed: boolean = false;
  private recoveryArmed: boolean = false;

  // Speed of simulated vehicle (m/s)
  private readonly SPEED_MPS = 5.0;          // ~18 km/h
  // Tick interval (ms) → determines step size
  private readonly TICK_MS = 100;            // 10 Hz
  // Distance advanced per tick
  private readonly STEP_M = this.SPEED_MPS * (this.TICK_MS / 1000); // 0.5 m

  // ── Phase boundaries ──────────────────────────────────────────────
  public readonly OUTAGE_START_S = 20;
  public readonly OUTAGE_END_S = 50;

  // ── Callback hooks set by NavigationService ───────────────────────
  /** Called with each synthetic GNSS fix during GNSS phase */
  public onGnssFix: ((fix: LocationFix) => void) | null = null;
  /** Called with each synthetic IMU sample during DR phase */
  public onImuSample: ((sample: ImuSample) => void) | null = null;
  /** Called ONCE when outage begins (t=20s) */
  public onOutageBegin: ((lastFix: LocationFix) => void) | null = null;
  /** Called ONCE when recovery begins (t=50s) */
  public onRecovery: ((firstRecoveryFix: LocationFix) => void) | null = null;

  // ─────────────────────────────────────────────────────────────────
  // Public API
  // ─────────────────────────────────────────────────────────────────

  /**
   * Called from NavigationService.startDemoNavigation() which is tied
   * to the "Start Navigation" button. NOT called on app launch.
   */
  public startDemoNavigation(route: Route): void {
    this.stop();

    if (!route || !route.geometry || route.geometry.length < 2) {
      console.warn('[DEMO] startDemoNavigation: invalid route');
      return;
    }

    // Build dense waypoint array at 0.5 m resolution
    this.waypoints = this.buildWaypoints(route.geometry, 0.5);
    this.totalRouteDistM = this.waypoints.length > 0
      ? this.waypoints[this.waypoints.length - 1].cumulativeDist
      : 0;

    if (this.waypoints.length < 2) {
      console.warn('[DEMO] startDemoNavigation: could not build waypoints');
      return;
    }

    this.distanceTravelledM = 0;
    this.sessionStartMs = Date.now();
    this.outageArmed = false;
    this.recoveryArmed = false;
    this.isSimulating = true;

    console.log(`[DEMO] Navigation session started. Route=${this.totalRouteDistM.toFixed(0)}m  waypoints=${this.waypoints.length}`);

    this.timer = setInterval(() => this.tick(), this.TICK_MS);
  }

  public stop(): void {
    this.isSimulating = false;
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  public isActive(): boolean {
    return this.isSimulating;
  }

  // ─────────────────────────────────────────────────────────────────
  // Internal tick — runs at 10 Hz
  // ─────────────────────────────────────────────────────────────────

  private tick(): void {
    if (!this.isSimulating || this.waypoints.length === 0) return;

    const elapsedMs = Date.now() - this.sessionStartMs;
    const elapsedS = elapsedMs / 1000;

    // Advance distance
    this.distanceTravelledM = Math.min(
      this.distanceTravelledM + this.STEP_M,
      this.totalRouteDistM
    );

    // Interpolate position and heading at current distance
    const { latitude, longitude, heading } = this.interpolateAt(this.distanceTravelledM);

    const now = Date.now();

    // ── Phase 1: GNSS AVAILABLE (0–20 s) ─────────────────────────
    if (elapsedS < this.OUTAGE_START_S) {
      this.outageArmed = false;
      this.recoveryArmed = false;

      const fix = this.makeFix(latitude, longitude, heading, now);

      // Log every ~1 s (10 ticks)
      if (Math.round(elapsedS * 10) % 10 === 0) {
        console.log(
          `[AUTHORITATIVE_POSE] source=DEMO_GNSS elapsed=${elapsedS.toFixed(1)}s ` +
          `lat=${latitude.toFixed(6)} lon=${longitude.toFixed(6)} ` +
          `heading=${heading.toFixed(1)}° routeDistance=${this.distanceTravelledM.toFixed(0)}m`
        );
      }

      this.onGnssFix?.(fix);
    }

    // ── Phase 2: GNSS OUTAGE (20–50 s) ───────────────────────────
    else if (elapsedS < this.OUTAGE_END_S) {
      // Fire ONCE at the transition boundary
      if (!this.outageArmed) {
        this.outageArmed = true;
        const lastFix = this.makeFix(latitude, longitude, heading, now);
        console.log(`[DEMO] GNSS OUTAGE begins at t=${elapsedS.toFixed(1)}s — triggering DR_ACTIVE`);
        this.onOutageBegin?.(lastFix);
      }

      // Build synthetic IMU that encodes forward motion + turn rate
      const imu = this.makeImuSample(heading, this.SPEED_MPS, now);

      if (Math.round(elapsedS * 10) % 10 === 0) {
        console.log(
          `[AUTHORITATIVE_POSE] source=DEMO_DR elapsed=${elapsedS.toFixed(1)}s ` +
          `lat=${latitude.toFixed(6)} lon=${longitude.toFixed(6)} ` +
          `heading=${heading.toFixed(1)}° routeDistance=${this.distanceTravelledM.toFixed(0)}m`
        );
      }

      this.onImuSample?.(imu);

    }

    // ── Phase 3: GNSS RECOVERED (50 s+) ──────────────────────────
    else {
      if (!this.recoveryArmed) {
        this.recoveryArmed = true;
        console.log(`[DEMO] GNSS RECOVERY begins at t=${elapsedS.toFixed(1)}s`);
        const recoveryFix = this.makeFix(latitude, longitude, heading, now);
        this.onRecovery?.(recoveryFix);
      }

      const fix = this.makeFix(latitude, longitude, heading, now);

      if (Math.round(elapsedS * 10) % 10 === 0) {
        console.log(
          `[AUTHORITATIVE_POSE] source=DEMO_GNSS_RECOVERED elapsed=${elapsedS.toFixed(1)}s ` +
          `lat=${latitude.toFixed(6)} lon=${longitude.toFixed(6)} ` +
          `heading=${heading.toFixed(1)}° routeDistance=${this.distanceTravelledM.toFixed(0)}m`
        );
      }

      this.onGnssFix?.(fix);
    }

    // Stop at end of route
    if (this.distanceTravelledM >= this.totalRouteDistM) {
      console.log('[DEMO] Route complete — stopping simulator');
      this.stop();
    }
  }

  // ─────────────────────────────────────────────────────────────────
  // Route geometry helpers
  // ─────────────────────────────────────────────────────────────────

  /**
   * Builds a dense array of RouteWaypoints at stepMeters resolution,
   * with geographic bearing calculated from actual segment direction.
   * Geometry is [lon, lat] pairs (GeoJSON).
   */
  private buildWaypoints(geometry: [number, number][], stepMeters: number): RouteWaypoint[] {
    const points: RouteWaypoint[] = [];
    let cumDist = 0;

    for (let i = 0; i < geometry.length - 1; i++) {
      const [lon1, lat1] = geometry[i];
      const [lon2, lat2] = geometry[i + 1];

      const segDist = calculateHaversineDistance(lat1, lon1, lat2, lon2);
      const bearing = this.bearing(lat1, lon1, lat2, lon2);

      if (segDist < stepMeters) {
        points.push({ latitude: lat1, longitude: lon1, heading: bearing, cumulativeDist: cumDist });
        cumDist += segDist;
      } else {
        const steps = Math.ceil(segDist / stepMeters);
        for (let s = 0; s < steps; s++) {
          const frac = s / steps;
          const lat = lat1 + (lat2 - lat1) * frac;
          const lon = lon1 + (lon2 - lon1) * frac;
          const distStep = segDist / steps;
          points.push({ latitude: lat, longitude: lon, heading: bearing, cumulativeDist: cumDist });
          cumDist += distStep;
        }
      }
    }

    // Final point
    if (geometry.length > 0) {
      const [lon, lat] = geometry[geometry.length - 1];
      const lastHeading = points.length > 0 ? points[points.length - 1].heading : 0;
      points.push({ latitude: lat, longitude: lon, heading: lastHeading, cumulativeDist: cumDist });
    }

    return points;
  }

  /**
   * Linear interpolation of position + heading at a given cumulative distance.
   */
  private interpolateAt(distM: number): { latitude: number; longitude: number; heading: number } {
    if (this.waypoints.length === 0) return { latitude: 0, longitude: 0, heading: 0 };

    const first = this.waypoints[0];
    const last = this.waypoints[this.waypoints.length - 1];

    if (distM <= 0) return { latitude: first.latitude, longitude: first.longitude, heading: first.heading };
    if (distM >= last.cumulativeDist) return { latitude: last.latitude, longitude: last.longitude, heading: last.heading };

    // Binary search for the segment
    let lo = 0;
    let hi = this.waypoints.length - 1;
    while (lo < hi - 1) {
      const mid = (lo + hi) >> 1;
      if (this.waypoints[mid].cumulativeDist <= distM) lo = mid;
      else hi = mid;
    }

    const a = this.waypoints[lo];
    const b = this.waypoints[hi];
    const segLen = b.cumulativeDist - a.cumulativeDist;
    const frac = segLen > 0 ? (distM - a.cumulativeDist) / segLen : 0;

    return {
      latitude: a.latitude + (b.latitude - a.latitude) * frac,
      longitude: a.longitude + (b.longitude - a.longitude) * frac,
      heading: a.heading, // use segment bearing (not interpolated — avoids wrap issues)
    };
  }

  /**
   * Geographic bearing from (lat1, lon1) to (lat2, lon2), degrees [0, 360).
   */
  private bearing(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const toRad = (d: number) => (d * Math.PI) / 180;
    const phi1 = toRad(lat1);
    const phi2 = toRad(lat2);
    const dLon = toRad(lon2 - lon1);
    const y = Math.sin(dLon) * Math.cos(phi2);
    const x = Math.cos(phi1) * Math.sin(phi2) - Math.sin(phi1) * Math.cos(phi2) * Math.cos(dLon);
    return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
  }

  // ─────────────────────────────────────────────────────────────────
  // Fix / IMU factories
  // ─────────────────────────────────────────────────────────────────

  private makeFix(lat: number, lon: number, heading: number, ts: number): LocationFix {
    return {
      latitude: lat,
      longitude: lon,
      altitude: 412.0,
      accuracy: 1.2,
      speed: this.SPEED_MPS,
      bearing: heading,
      timestamp: ts,
      hasSpeed: true,
      hasBearing: true,
      provider: 'gps',
    };
  }

  /**
   * Synthetic IMU sample that encodes:
   * - Forward acceleration consistent with current speed (accelY = 0 → constant speed)
   * - Yaw rate (gyroZ) from route bearing change between consecutive waypoints
   * The DR engine uses these to propagate position forward.
   */
  private prevImuHeading: number | null = null;

  private makeImuSample(currentHeading: number, speedMps: number, ts: number): ImuSample {
    let headingDeltaDeg = 0;
    if (this.prevImuHeading !== null) {
      headingDeltaDeg = currentHeading - this.prevImuHeading;
      if (headingDeltaDeg > 180) headingDeltaDeg -= 360;
      if (headingDeltaDeg < -180) headingDeltaDeg += 360;
    }
    this.prevImuHeading = currentHeading;

    const dtS = this.TICK_MS / 1000;
    const gyroZ = (headingDeltaDeg * Math.PI / 180) / dtS; // rad/s

    // Forward acceleration in body frame: accelX = centripetal, accelY = 0 (constant speed)
    const accelX = speedMps * gyroZ;  // centripetal
    const accelY = 0.0;               // steady motion, no fore/aft accel
    const accelZ = 9.81;              // gravity

    return {
      accelX,
      accelY,
      accelZ,
      gyroX: 0,
      gyroY: 0,
      gyroZ,
      timestamp: ts,
    };
  }
}

export const demoTrajectorySimulator = new DemoTrajectorySimulator();
