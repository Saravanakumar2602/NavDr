/* ==========================================================================
   SIH 2026 INTELLIGENT DEAD-RECKONING (IDR) SHOWCASE DASHBOARD JS
   Leaflet Map Integration, Real-Time Telemetry & GNSS Outage Recovery Logic
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // Global State Variables
  let trajectoryData = [];
  let currentIndex = 0;
  let isPlaying = false;
  let playbackInterval = null;
  let speedMultiplier = 2; // Default 2x
  let gnssMode = 'ONLINE'; // 'ONLINE', 'OUTAGE', 'RECOVERED'
  let outageStartTime = 0;

  // DOM Elements
  const btnToggleGNSS = document.getElementById('btnToggleGNSS');
  const btnPlayPause = document.getElementById('btnPlayPause');
  const btnReset = document.getElementById('btnReset');
  const speedSelect = document.getElementById('speedMultiplier');

  const modeBadge = document.getElementById('modeBadge');
  const modeStatusText = document.getElementById('modeStatusText');
  const outageTimerDisplay = document.getElementById('outageTimerDisplay');

  const speedValue = document.getElementById('speedValue');
  const speedGT = document.getElementById('speedGT');
  
  const driftRawVal = document.getElementById('driftRawVal');
  const driftIDRVal = document.getElementById('driftIDRVal');
  const barRaw = document.getElementById('barRaw');
  const barIDR = document.getElementById('barIDR');

  const ledJerk = document.getElementById('ledJerk');
  const jerkValue = document.getElementById('jerkValue');
  const ledZupt = document.getElementById('ledZupt');
  const zuptStatus = document.getElementById('zuptStatus');
  const ledApm = document.getElementById('ledApm');
  const apmStatus = document.getElementById('apmStatus');
  const headingVal = document.getElementById('headingVal');

  const hudCoords = document.getElementById('hudCoords');
  const hudDrift = document.getElementById('hudDrift');

  // Initialize Leaflet Map
  const map = L.map('map', {
    center: [12.9716, 77.5946],
    zoom: 16,
    zoomControl: false
  });

  // ESRI World Dark Gray Base (Free, Dark, Sleek, No API Key Required)
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ'
  }).addTo(map);

  // Add zoom control at top right
  L.control.zoom({ position: 'topright' }).addTo(map);

  // Trajectory Polylines
  const polyGT = L.polyline([], { color: '#00F5D4', weight: 4, opacity: 0.85 }).addTo(map);
  const polyRaw = L.polyline([], { color: '#FF0055', weight: 3, opacity: 0.6, dashArray: '6, 6' }).addTo(map);
  const polyIDR = L.polyline([], { color: '#10B981', weight: 5, opacity: 0.95 }).addTo(map);
  const polyRecovery = L.polyline([], { color: '#FEE440', weight: 4, opacity: 0.9, dashArray: '4, 4' }).addTo(map);

  // Vehicle Icon Marker
  const vehicleIcon = L.divIcon({
    className: 'vehicle-marker-icon',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  });

  const vehicleMarker = L.marker([12.9716, 77.5946], { icon: vehicleIcon }).addTo(map);

  // Fetch Trajectory Data from data.json
  fetch('data.json')
    .then(response => response.json())
    .then(data => {
      trajectoryData = data.trajectory;
      console.log(`Loaded ${trajectoryData.length} trajectory samples.`);
      resetSimulation();
    })
    .catch(err => {
      console.error("Error loading trajectory dataset:", err);
    });

  // Button Event Listeners
  btnPlayPause.addEventListener('click', togglePlayPause);
  btnReset.addEventListener('click', resetSimulation);
  btnToggleGNSS.addEventListener('click', toggleGNSSMode);

  speedSelect.addEventListener('change', (e) => {
    speedMultiplier = parseInt(e.target.value);
    if (isPlaying) {
      restartPlaybackTimer();
    }
  });

  function togglePlayPause() {
    isPlaying = !isPlaying;
    if (isPlaying) {
      btnPlayPause.innerHTML = 'PAUSE';
      btnPlayPause.classList.replace('btn-primary', 'btn-secondary');
      restartPlaybackTimer();
    } else {
      btnPlayPause.innerHTML = 'PLAY';
      btnPlayPause.classList.replace('btn-secondary', 'btn-primary');
      clearInterval(playbackInterval);
    }
  }

  function restartPlaybackTimer() {
    clearInterval(playbackInterval);
    const intervalMs = Math.max(10, intVal(100 / speedMultiplier));
    playbackInterval = setInterval(stepSimulation, intervalMs);
  }

  function intVal(val) {
    return Math.floor(val);
  }

  function resetSimulation() {
    isPlaying = false;
    clearInterval(playbackInterval);
    currentIndex = 0;
    gnssMode = 'ONLINE';
    outageStartTime = 0;

    btnPlayPause.innerHTML = 'PLAY';
    btnPlayPause.classList.replace('btn-secondary', 'btn-primary');

    updateModeBadge();

    polyGT.setLatLngs([]);
    polyRaw.setLatLngs([]);
    polyIDR.setLatLngs([]);
    polyRecovery.setLatLngs([]);

    if (trajectoryData.length > 0) {
      updateDisplayAtStep(0);
      const firstPt = [trajectoryData[0].lat_gt, trajectoryData[0].lon_gt];
      map.setView(firstPt, 16);
    }
  }

  function toggleGNSSMode() {
    if (gnssMode === 'ONLINE') {
      gnssMode = 'OUTAGE';
      outageStartTime = trajectoryData[currentIndex] ? trajectoryData[currentIndex].t : 0;
      btnToggleGNSS.innerHTML = 'RESTORE GNSS SIGNAL';
      btnToggleGNSS.classList.replace('btn-warning', 'btn-primary');
    } else if (gnssMode === 'OUTAGE') {
      gnssMode = 'RECOVERED';
      btnToggleGNSS.innerHTML = 'TRIGGER GNSS OUTAGE';
      btnToggleGNSS.classList.replace('btn-primary', 'btn-warning');
      
      // Draw Kalman Smoothing bridge vector
      if (currentIndex < trajectoryData.length) {
        const pt = trajectoryData[currentIndex];
        const bridgeCoords = [
          [pt.lat_idr, pt.lon_idr],
          [pt.lat_gt, pt.lon_gt]
        ];
        polyRecovery.setLatLngs(bridgeCoords);
      }
    } else {
      gnssMode = 'ONLINE';
      btnToggleGNSS.innerHTML = 'TRIGGER GNSS OUTAGE';
      btnToggleGNSS.classList.replace('btn-primary', 'btn-warning');
      polyRecovery.setLatLngs([]);
    }
    updateModeBadge();
  }

  function updateModeBadge() {
    modeBadge.className = 'badge';
    if (gnssMode === 'ONLINE') {
      modeBadge.classList.add('badge-gnss');
      modeStatusText.innerText = 'GNSS SIGNAL ONLINE';
    } else if (gnssMode === 'OUTAGE') {
      modeBadge.classList.add('badge-outage');
      modeStatusText.innerText = 'GNSS LOST — DEAD RECKONING ACTIVE';
    } else {
      modeBadge.classList.add('badge-recovered');
      modeStatusText.innerText = 'GNSS SIGNAL RESTORED — RE-CORRECTING';
    }
  }

  function stepSimulation() {
    if (currentIndex >= trajectoryData.length - 1) {
      togglePlayPause(); // Auto pause at end
      return;
    }
    currentIndex++;
    updateDisplayAtStep(currentIndex);
  }

  function updateDisplayAtStep(idx) {
    if (!trajectoryData || trajectoryData.length === 0) return;
    const pt = trajectoryData[idx];

    // Outage Timer
    let elapsedOutage = 0;
    if (gnssMode === 'OUTAGE' || gnssMode === 'RECOVERED') {
      elapsedOutage = pt.t - outageStartTime;
      if (elapsedOutage < 0) elapsedOutage = 0;
    }
    outageTimerDisplay.innerText = `${formatSeconds(elapsedOutage)}s`;

    // Coordinates & Active Trajectory Points
    const gtPt = [pt.lat_gt, pt.lon_gt];
    const rawPt = [pt.lat_raw, pt.lon_raw];
    const idrPt = [pt.lat_idr, pt.lon_idr];

    // Append points to polylines
    polyGT.addLatLng(gtPt);
    polyRaw.addLatLng(rawPt);
    polyIDR.addLatLng(idrPt);

    // Vehicle position depends on mode
    let currentVehiclePt = gtPt;
    if (gnssMode === 'OUTAGE') {
      currentVehiclePt = idrPt;
    } else if (gnssMode === 'RECOVERED') {
      currentVehiclePt = gtPt;
    }

    vehicleMarker.setLatLng(currentVehiclePt);
    map.panTo(currentVehiclePt, { animate: true, duration: 0.1 });

    // Speed Gauges
    speedValue.innerText = pt.speed_idr_kmh.toFixed(1);
    speedGT.innerText = `${pt.speed_gt_kmh.toFixed(1)} km/h`;

    // Drift Counters
    driftRawVal.innerText = `${pt.drift_raw_m.toFixed(1)} m`;
    driftIDRVal.innerText = `${pt.drift_idr_m.toFixed(1)} m`;

    const maxRawRatio = Math.min(100, (pt.drift_raw_m / 6420.0) * 100);
    const maxIDRRatio = Math.min(100, (pt.drift_idr_m / 6420.0) * 100 * 20); // Scale up for visibility
    barRaw.style.width = `${Math.max(5, maxRawRatio)}%`;
    barIDR.style.width = `${Math.max(2, maxIDRRatio)}%`;

    // Physical Layer Indicators
    // 1. Jerk Gate
    jerkValue.innerText = `${pt.jerk_long.toFixed(2)} m/s³`;
    if (pt.jerk_long < -1.00) {
      ledJerk.className = 'led-light led-alert';
    } else {
      ledJerk.className = 'led-light led-off';
    }

    // 2. ZUPT Stop Detector
    zuptStatus.innerText = pt.zupt_active ? 'ZUPT ACTIVE (0.00 m/s)' : `P(stat) = ${pt.p_stat.toFixed(2)}`;
    if (pt.zupt_active) {
      ledZupt.className = 'led-light led-blue';
    } else {
      ledZupt.className = 'led-light led-off';
    }

    // 3. APM Damping
    apmStatus.innerText = pt.apm_active ? `-${pt.apm_corr_ms.toFixed(2)} m/s Damping` : '0.00 m/s Damping';
    if (pt.apm_active) {
      ledApm.className = 'led-light led-alert';
    } else {
      ledApm.className = 'led-light led-off';
    }

    // 4. Heading
    headingVal.innerText = `${pt.heading_deg.toFixed(1)}°`;

    // HUD Text
    hudCoords.innerText = `${currentVehiclePt[0].toFixed(6)}° N, ${currentVehiclePt[1].toFixed(6)}° E`;
    hudDrift.innerText = `${pt.drift_idr_m.toFixed(2)} m (vs ${pt.drift_raw_m.toFixed(1)} m raw)`;
  }

  function formatSeconds(sec) {
    const m = Math.floor(sec / 60);
    const s = (sec % 60).toFixed(1);
    const mStr = m < 10 ? `0${m}` : `${m}`;
    const sStr = s < 10 ? `0${s}` : `${s}`;
    return `${mStr}:${sStr}`;
  }
});
