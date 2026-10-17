import { NavigationState, TrajectoryPoint, VehiclePose, SensorTelemetry, ActiveTab } from '../types/navigation';

export class DemoDataProvider {
  private state: NavigationState;
  private timer: any = null;
  private outageTimer: any = null;
  private recoveryTimeout: any = null;
  private step: number = 0;
  private listeners: ((state: NavigationState) => void)[] = [];

  constructor() {
    this.state = {
      pose: {
        x: 0,
        y: 0,
        latitude: 12.9716,
        longitude: 77.5946,
        heading: 127,
        speed: 42.0,
      },
      currentFix: null,
      filteredPose: null,
      positionUncertainty: 1.2,
      gnssStatus: 'AVAILABLE',
      navigationMode: 'GNSS NAVIGATION',
      locationPermissionStatus: 'GRANTED',
      updateRateHz: 10,
      imuStatus: 'CONNECTED',
      mapStatus: 'OFFLINE VECTOR',
      isNavigating: false,
      demoStateIndex: 0,
      outageDurationSeconds: 0,
      confidence: 98,
      processingLatencyMs: 9.4,
      lastKnownGnssPose: null,
      gnssTrajectory: [],
      idrTrajectory: [],
      mapMatchedTrajectory: [],
      activeBannerMessage: null,
      activeTab: 'NAVIGATE',
      telemetryHistory: [],
      diagnostics: {
        fixCount: 0,
        acceptedFixCount: 0,
        rejectedOutlierCount: 0,
        lastFixAgeSeconds: 0,
        updateRateHz: 10,
        meanIntervalMs: 100,
        medianIntervalMs: 100,
        minIntervalMs: 90,
        maxIntervalMs: 110,
        currentAccuracy: 1.2,
        minAccuracy: 1.0,
        maxAccuracy: 2.0,
        meanAccuracy: 1.2,
        reportedSpeedKmH: 42.0,
        hasSpeed: true,
        derivedSpeedKmH: 42.0,
        filteredSpeedKmH: 42.0,
        reportedBearing: 127,
        hasBearing: true,
        filteredHeadingDeg: 127,
        filterState: 'MOVING',
        rawJitterMaxMeters: 0.2,
        rawJitterMeanMeters: 0.1,
        filteredJitterMaxMeters: 0.05,
        filteredJitterMeanMeters: 0.02,
        filterLatencyMs: 2.1,
        rawLatitude: 12.9716,
        rawLongitude: 77.5946,
        filteredLatitude: 12.9716,
        filteredLongitude: 77.5946,
      },
    };

    this.initDemoTrajectories();
    this.initTelemetryHistory();
  }

  private initDemoTrajectories() {
    const points: TrajectoryPoint[] = [];
    const n = 120;
    let cx = 0;
    let cy = 0;
    let heading = 127;

    for (let i = 0; i < n; i++) {
      const turn = Math.sin(i / 15) * 2.0;
      heading = (heading + turn + 360) % 360;
      const rad = (heading * Math.PI) / 180;
      const dist = 3.5;
      cx += Math.sin(rad) * dist;
      cy += Math.cos(rad) * dist;

      points.push({
        x: cx,
        y: cy,
        latitude: 12.9716 + cy * 0.000009,
        longitude: 77.5946 + cx * 0.000009,
        type: 'gnss',
        timestamp: Date.now() + i * 100,
      });
    }

    this.state.gnssTrajectory = points.slice(0, 40);
    this.state.idrTrajectory = points.slice(0, 40);
    this.state.mapMatchedTrajectory = points.slice(0, 40);
  }

  private initTelemetryHistory() {
    const history: SensorTelemetry[] = [];
    const now = Date.now();
    for (let i = 20; i >= 0; i--) {
      history.push({
        accelX: Math.sin(i / 3) * 0.4 + 0.02,
        accelY: Math.cos(i / 2) * 0.3 + 0.15,
        accelZ: 9.81 + Math.sin(i / 5) * 0.1,
        gyroX: Math.cos(i / 4) * 0.02,
        gyroY: Math.sin(i / 3) * 0.015,
        gyroZ: Math.sin(i / 2) * 0.08,
        timestamp: now - i * 50,
      });
    }
    this.state.telemetryHistory = history;
  }

  public getState(): NavigationState {
    return { ...this.state };
  }

  public subscribe(listener: (state: NavigationState) => void): () => void {
    this.listeners.push(listener);
    listener(this.getState());
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  private notify() {
    const currentState = this.getState();
    this.listeners.forEach((l) => l(currentState));
  }

  public setActiveTab(tab: ActiveTab) {
    this.state.activeTab = tab;
    this.notify();
  }

  public startNavigation() {
    if (this.state.isNavigating) return;
    this.state.isNavigating = true;
    this.step = 0;

    this.timer = setInterval(() => {
      this.tick();
    }, 100);

    this.notify();
  }

  public stopNavigation() {
    this.state.isNavigating = false;
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    this.stopOutageTimer();
    this.notify();
  }

  private startOutageTimer() {
    this.stopOutageTimer();
    this.outageTimer = setInterval(() => {
      this.state.outageDurationSeconds += 1;
      this.notify();
    }, 1000);
  }

  private stopOutageTimer() {
    if (this.outageTimer) {
      clearInterval(this.outageTimer);
      this.outageTimer = null;
    }
  }

  public setDemoState(index: number) {
    this.state.demoStateIndex = index;
    if (this.recoveryTimeout) {
      clearTimeout(this.recoveryTimeout);
      this.recoveryTimeout = null;
    }

    if (index === 0) {
      // GNSS AVAILABLE
      this.stopOutageTimer();
      this.state.gnssStatus = 'AVAILABLE';
      this.state.navigationMode = 'GNSS NAVIGATION';
      this.state.positionUncertainty = 1.2;
      this.state.outageDurationSeconds = 0;
      this.state.confidence = 98;
      this.state.activeBannerMessage = null;
    } else if (index === 1) {
      // GNSS DENIED (DEAD RECKONING ACTIVE)
      this.state.lastKnownGnssPose = { ...this.state.pose };
      this.state.gnssStatus = 'DENIED';
      this.state.navigationMode = 'DEAD RECKONING ACTIVE';
      this.state.positionUncertainty = 4.8;
      this.state.confidence = 94;
      this.state.activeBannerMessage = 'GNSS SIGNAL LOST — DEAD RECKONING ACTIVE';
      this.startOutageTimer();
    } else if (index === 2) {
      // GNSS RECOVERING (GNSS REACQUIRED)
      this.stopOutageTimer();
      this.state.gnssStatus = 'RECOVERING';
      this.state.navigationMode = 'GNSS NAVIGATION';
      this.state.positionUncertainty = 2.1;
      this.state.confidence = 97;
      this.state.activeBannerMessage = 'GNSS RECOVERING — Synchronizing navigation state...';

      // Auto-transition back to GNSS AVAILABLE after 3.5 seconds
      this.recoveryTimeout = setTimeout(() => {
        this.setDemoState(0);
      }, 3500);
    }
    this.notify();
  }

  public cycleDemoState() {
    const nextState = ((this.state.demoStateIndex ?? 0) + 1) % 3;
    this.setDemoState(nextState);
  }

  public triggerGnssOutage() {
    if (this.state.gnssStatus === 'AVAILABLE') {
      this.setDemoState(1);
    } else if (this.state.gnssStatus === 'DENIED') {
      this.setDemoState(2);
    } else {
      this.setDemoState(0);
    }
  }

  public resetPosition() {
    this.step = 0;
    this.initDemoTrajectories();
    this.state.pose = {
      x: 0,
      y: 0,
      latitude: 12.9716,
      longitude: 77.5946,
      heading: 127,
      speed: 42.0,
    };
    this.state.outageDurationSeconds = 0;
    this.state.lastKnownGnssPose = null;
    this.notify();
  }

  private tick() {
    this.step++;
    const turnRate = Math.sin(this.step / 20) * 1.5;
    const currentHeading = this.state.pose.heading ?? 127;
    const newHeading = (currentHeading + turnRate + 360) % 360;
    const speed = 42.0 + Math.sin(this.step / 10) * 4.0;
    const speedMps = speed / 3.6;
    const dt = 0.1;

    const rad = (newHeading * Math.PI) / 180;
    const dx = Math.sin(rad) * speedMps * dt;
    const dy = Math.cos(rad) * speedMps * dt;

    const newX = this.state.pose.x + dx;
    const newY = this.state.pose.y + dy;
    const newLat = 12.9716 + newY * 0.000009;
    const newLon = 77.5946 + newX * 0.000009;

    this.state.pose = {
      x: newX,
      y: newY,
      latitude: newLat,
      longitude: newLon,
      heading: Math.round(newHeading),
      speed: Math.round(speed * 10) / 10,
    };

    // Update processing latency dynamically (8.8ms - 11.2ms)
    this.state.processingLatencyMs = Math.round((9.4 + Math.sin(this.step / 5) * 0.8) * 10) / 10;

    // Simulate IMU sensor telemetry stream
    const now = Date.now();
    const newTelemetry: SensorTelemetry = {
      accelX: Math.round((Math.sin(this.step / 4) * 0.45 + 0.02) * 100) / 100,
      accelY: Math.round((Math.cos(this.step / 3) * 0.35 + 0.15) * 100) / 100,
      accelZ: Math.round((9.81 + Math.sin(this.step / 8) * 0.12) * 100) / 100,
      gyroX: Math.round((Math.cos(this.step / 5) * 0.025) * 1000) / 1000,
      gyroY: Math.round((Math.sin(this.step / 4) * 0.018) * 1000) / 1000,
      gyroZ: Math.round(((turnRate * Math.PI) / 180 + Math.sin(this.step / 3) * 0.01) * 1000) / 1000,
      timestamp: now,
    };

    this.state.telemetryHistory.push(newTelemetry);
    if (this.state.telemetryHistory.length > 25) {
      this.state.telemetryHistory.shift();
    }

    const newPoint: TrajectoryPoint = {
      x: newX,
      y: newY,
      latitude: newLat,
      longitude: newLon,
      type: this.state.gnssStatus === 'DENIED' ? 'idr' : 'gnss',
      timestamp: now,
    };

    if (this.state.gnssStatus === 'AVAILABLE') {
      this.state.gnssTrajectory.push(newPoint);
      if (this.state.gnssTrajectory.length > 200) this.state.gnssTrajectory.shift();
    }

    this.state.idrTrajectory.push({ ...newPoint, type: 'idr' });
    if (this.state.idrTrajectory.length > 200) this.state.idrTrajectory.shift();

    this.state.mapMatchedTrajectory.push({ ...newPoint, type: 'map_matched' });
    if (this.state.mapMatchedTrajectory.length > 200) this.state.mapMatchedTrajectory.shift();

    this.notify();
  }
}

