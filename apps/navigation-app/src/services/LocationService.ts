import * as Location from 'expo-location';
import { LocationFix, LocationPermissionStatus } from '../types/navigation';
import { calculateHaversineDistance } from '../utils/geo';

export class LocationService {
  private subscription: Location.LocationSubscription | null = null;
  private onFixCallback: ((fix: LocationFix) => void) | null = null;
  private onErrorCallback: ((error: string) => void) | null = null;
  private isWatching: boolean = false;
  private lastFix: LocationFix | null = null;

  /**
   * Request foreground location permission and check location services availability
   */
  async requestPermissions(): Promise<LocationPermissionStatus> {
    try {
      const isServicesEnabled = await Location.hasServicesEnabledAsync();
      if (!isServicesEnabled) {
        return 'SERVICES_DISABLED';
      }

      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status === Location.PermissionStatus.GRANTED) {
        return 'GRANTED';
      } else {
        return 'DENIED';
      }
    } catch (e) {
      console.warn('[LocationService] Permission check failed:', e);
      return 'DENIED';
    }
  }

  /**
   * Start watching live Android location fixes
   */
  async startTracking(
    onFix: (fix: LocationFix) => void,
    onError?: (error: string) => void
  ): Promise<boolean> {
    if (this.isWatching) return true;

    this.onFixCallback = onFix;
    this.onErrorCallback = onError || null;
    this.lastFix = null;

    try {
      const perm = await this.requestPermissions();
      if (perm !== 'GRANTED') {
        if (this.onErrorCallback) {
          this.onErrorCallback(
            perm === 'SERVICES_DISABLED'
              ? 'LOCATION SERVICES DISABLED'
              : 'LOCATION PERMISSION REQUIRED'
          );
        }
        return false;
      }

      this.subscription = await Location.watchPositionAsync(
        {
          accuracy: Location.Accuracy.BestForNavigation,
          timeInterval: 500,
          distanceInterval: 0,
        },
        (loc: Location.LocationObject) => {
          const fix = this.sanitizeLocationObject(loc);
          if (fix && this.onFixCallback) {
            this.lastFix = fix;
            this.onFixCallback(fix);
          }
        }
      );

      this.isWatching = true;
      return true;
    } catch (e: any) {
      console.error('[LocationService] Error starting position watch:', e);
      if (this.onErrorCallback) {
        this.onErrorCallback(e?.message || 'FAILED TO INITIALIZE LOCATION');
      }
      return false;
    }
  }

  /**
   * Stop watching location and clear subscription handle cleanly
   */
  stopTracking(): void {
    if (this.subscription) {
      this.subscription.remove();
      this.subscription = null;
    }
    this.isWatching = false;
    this.onFixCallback = null;
    this.onErrorCallback = null;
    this.lastFix = null;
  }

  /**
   * Sanitize location objects to prevent NaN or corrupted values and derive diagnostic metrics
   */
  private sanitizeLocationObject(loc: Location.LocationObject): LocationFix | null {
    if (!loc || !loc.coords) return null;

    const { latitude, longitude, altitude, accuracy, speed, heading } = loc.coords;

    // Validate coordinate bounds & non-NaN/non-zero
    if (
      typeof latitude !== 'number' ||
      typeof longitude !== 'number' ||
      isNaN(latitude) ||
      isNaN(longitude) ||
      !isFinite(latitude) ||
      !isFinite(longitude) ||
      Math.abs(latitude) > 90 ||
      Math.abs(longitude) > 180 ||
      (latitude === 0 && longitude === 0)
    ) {
      return null;
    }

    const timestamp = typeof loc.timestamp === 'number' && loc.timestamp > 0 ? loc.timestamp : Date.now();
    const hasSpeed = typeof speed === 'number' && !isNaN(speed) && speed >= 0;
    const hasBearing = typeof heading === 'number' && !isNaN(heading) && heading >= 0 && heading <= 360;

    let deltaTimeMs: number | undefined;
    let distanceMeters: number | undefined;
    let derivedSpeedMps: number | undefined;

    if (this.lastFix) {
      deltaTimeMs = Math.max(1, timestamp - this.lastFix.timestamp);
      distanceMeters = calculateHaversineDistance(
        this.lastFix.latitude,
        this.lastFix.longitude,
        latitude,
        longitude
      );
      derivedSpeedMps = distanceMeters / (deltaTimeMs / 1000);
    }

    const provider = (loc as any).mocked ? 'mock' : 'android_gps';

    return {
      timestamp,
      latitude,
      longitude,
      altitude: typeof altitude === 'number' && !isNaN(altitude) ? altitude : null,
      accuracy: typeof accuracy === 'number' && !isNaN(accuracy) && accuracy >= 0 ? accuracy : null,
      speed: hasSpeed ? speed : null, // m/s
      hasSpeed,
      bearing: hasBearing ? heading : null, // degrees
      hasBearing,
      provider,
      deltaTimeMs,
      distanceMeters,
      derivedSpeedMps,
    };
  }
}
