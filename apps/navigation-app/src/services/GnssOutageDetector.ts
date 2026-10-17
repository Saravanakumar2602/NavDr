import {
  LocationFix,
  FilteredGnssPose,
  GnssOutageState,
  GnssNavigationState,
  GnssStateTransition,
} from '../types/navigation';

export class GnssOutageDetector {
  private currentState: GnssOutageState = 'GNSS_FIX';
  private lastValidFixTimestamp: number = 0;
  private recoveryFixCount: number = 0;
  private lastKnownPosition: { latitude: number; longitude: number } | null = null;
  private transitionHistory: GnssStateTransition[] = [];

  // Deterministic Threshold Constants
  public readonly T_DEGRADED_MS = 1800; // 1.8 seconds fix age threshold
  public readonly T_DENIED_MS = 4000; // 4.0 seconds fix age threshold
  public readonly MAX_ACCURACY_DEGRADED_M = 30.0; // Accuracy > 30m triggers degraded state
  public readonly RECOVERY_REQUIRED_FIXES = 3; // Hysteresis: 3 consecutive valid fixes required to restore FIX

  public reset(): void {
    this.currentState = 'GNSS_FIX';
    this.lastValidFixTimestamp = 0;
    this.recoveryFixCount = 0;
    this.lastKnownPosition = null;
    this.transitionHistory = [];
  }

  public getState(): GnssOutageState {
    return this.currentState;
  }

  public getTransitionHistory(): GnssStateTransition[] {
    return [...this.transitionHistory];
  }

  /**
   * Process incoming GNSS fix and update navigation outage state machine
   */
  public processFix(rawFix: LocationFix, pose: FilteredGnssPose): GnssNavigationState {
    const now = Date.now();
    const fixAgeMs = this.lastValidFixTimestamp > 0 ? now - this.lastValidFixTimestamp : 0;
    const isOutlier = pose.isOutlier || pose.filterState === 'OUTLIER_REJECTED';
    const isAccuratelyValid = rawFix.accuracy !== null && rawFix.accuracy <= this.MAX_ACCURACY_DEGRADED_M;
    const isValidFix = !isOutlier && isAccuratelyValid;

    if (isValidFix) {
      this.lastValidFixTimestamp = now;
      this.lastKnownPosition = { latitude: pose.latitude, longitude: pose.longitude };
    }

    const prevState = this.currentState;

    switch (this.currentState) {
      case 'GNSS_FIX':
        if (isOutlier || !isAccuratelyValid) {
          this.transitionTo('GNSS_DEGRADED', `Fix quality degraded (accuracy ${rawFix.accuracy ?? '--'}m)`);
        } else if (fixAgeMs > this.T_DEGRADED_MS && this.lastValidFixTimestamp > 0) {
          this.transitionTo('GNSS_DEGRADED', `Fix age exceeded degraded threshold (${fixAgeMs}ms)`);
        }
        break;

      case 'GNSS_DEGRADED':
        if (fixAgeMs > this.T_DENIED_MS && this.lastValidFixTimestamp > 0) {
          this.transitionTo('GNSS_DENIED', `Fix age exceeded denied threshold (${fixAgeMs}ms)`);
        } else if (isValidFix) {
          this.transitionTo('GNSS_FIX', `Valid fix restored (accuracy ${rawFix.accuracy?.toFixed(1)}m)`);
        }
        break;

      case 'GNSS_DENIED':
        if (isValidFix) {
          this.recoveryFixCount = 1;
          this.transitionTo(
            'GNSS_RECOVERY',
            `First valid fix received during outage (1/${this.RECOVERY_REQUIRED_FIXES})`
          );
        }
        break;

      case 'GNSS_RECOVERY':
        if (isValidFix) {
          this.recoveryFixCount++;
          if (this.recoveryFixCount >= this.RECOVERY_REQUIRED_FIXES) {
            this.transitionTo(
              'GNSS_FIX',
              `Recovery confirmed after ${this.recoveryFixCount} consecutive valid fixes`
            );
          }
        } else {
          // Re-degrade if returning fix was bad
          this.recoveryFixCount = 0;
          this.transitionTo('GNSS_DEGRADED', `Recovery interrupted by invalid fix`);
        }
        break;
    }

    const outageDurationMs =
      this.currentState === 'GNSS_DENIED' || this.currentState === 'GNSS_RECOVERY'
        ? now - this.lastValidFixTimestamp
        : 0;

    return {
      state: this.currentState,
      lastValidFixTimestamp: this.lastValidFixTimestamp,
      fixAgeMs: this.lastValidFixTimestamp > 0 ? now - this.lastValidFixTimestamp : 0,
      outageDurationMs,
      recoveryFixCount: this.recoveryFixCount,
      lastKnownPosition: this.lastKnownPosition,
      transitionHistory: [...this.transitionHistory],
    };
  }

  /**
   * Periodic stale fix evaluation (called by 500ms ticker)
   */
  public evaluateStaleTick(now: number = Date.now()): GnssNavigationState {
    if (this.lastValidFixTimestamp === 0) {
      return {
        state: this.currentState,
        lastValidFixTimestamp: 0,
        fixAgeMs: 0,
        outageDurationMs: 0,
        recoveryFixCount: this.recoveryFixCount,
        lastKnownPosition: this.lastKnownPosition,
        transitionHistory: [...this.transitionHistory],
      };
    }

    const fixAgeMs = now - this.lastValidFixTimestamp;

    if (this.currentState === 'GNSS_FIX' && fixAgeMs > this.T_DEGRADED_MS) {
      this.transitionTo('GNSS_DEGRADED', `Stale ticker: fix age ${fixAgeMs}ms > ${this.T_DEGRADED_MS}ms`);
    } else if (
      (this.currentState === 'GNSS_DEGRADED' || this.currentState === 'GNSS_FIX') &&
      fixAgeMs > this.T_DENIED_MS
    ) {
      this.transitionTo('GNSS_DENIED', `Stale ticker: fix age ${fixAgeMs}ms > ${this.T_DENIED_MS}ms`);
    }

    const outageDurationMs =
      this.currentState === 'GNSS_DENIED' || this.currentState === 'GNSS_RECOVERY'
        ? now - this.lastValidFixTimestamp
        : 0;

    return {
      state: this.currentState,
      lastValidFixTimestamp: this.lastValidFixTimestamp,
      fixAgeMs,
      outageDurationMs,
      recoveryFixCount: this.recoveryFixCount,
      lastKnownPosition: this.lastKnownPosition,
      transitionHistory: [...this.transitionHistory],
    };
  }

  private transitionTo(toState: GnssOutageState, reason: string): void {
    const fromState = this.currentState;
    if (fromState === toState) return;

    this.currentState = toState;
    const transition: GnssStateTransition = {
      timestamp: Date.now(),
      fromState,
      toState,
      reason,
    };

    this.transitionHistory.push(transition);
    if (this.transitionHistory.length > 50) {
      this.transitionHistory.shift();
    }

    // Log exact transition timestamp for audit validation
    const timeStr = new Date(transition.timestamp).toISOString().substring(11, 23);
    console.log(`[GNSS_STATE_TRANSITION] ${timeStr} | ${fromState} -> ${toState} | ${reason}`);
    console.log(`[DR-DIAG] ${toState} t=${transition.timestamp} (${timeStr}) reason=${reason}`);
  }
}

export const gnssOutageDetector = new GnssOutageDetector();
