/**
 * JavaScript Showcase Controller for Case 02: Underground Tunnel Navigation
 * Powered by M028 Production Pipeline Data, Esri World Imagery Satellite Tiles & Leaflet.js
 */

document.addEventListener('DOMContentLoaded', async () => {
  // DOM Elements
  const mapElement = document.getElementById('map');
  const btnStart = document.getElementById('btn-start');
  const btnPause = document.getElementById('btn-pause');
  const btnReset = document.getElementById('btn-reset');
  const timelineSlider = document.getElementById('timeline-slider');
  
  const btnSpeed1x = document.getElementById('btn-speed-1x');
  const btnSpeed2x = document.getElementById('btn-speed-2x');
  const btnSpeed5x = document.getElementById('btn-speed-5x');

  const btnMapSat = document.getElementById('btn-map-sat');
  const btnMapDark = document.getElementById('btn-map-dark');
  const tunnelOverlay = document.getElementById('tunnel-ambient-overlay');

  // Status & Telemetry Elements
  const gnssStatusBadge = document.getElementById('gnss-status-badge');
  const gnssStatusText = document.getElementById('gnss-status-text');
  const statGnssCondition = document.getElementById('stat-gnss-condition');
  const statNavMode = document.getElementById('stat-nav-mode');
  const statOutageTimer = document.getElementById('stat-outage-timer');
  const tunnelPctText = document.getElementById('tunnel-pct');
  const tunnelPctBar = document.getElementById('tunnel-pct-bar');
  
  const camStatusBadge = document.getElementById('cam-status-badge');
  const tunnelCamFeed = document.getElementById('tunnel-cam-feed');
  const camOverlayText = document.getElementById('cam-overlay-text');

  const speedValue = document.getElementById('speed-value');
  const teleAccel = document.getElementById('tele-accel');
  const teleJerk = document.getElementById('tele-jerk');
  const teleHeading = document.getElementById('tele-heading');
  const telePstat = document.getElementById('tele-pstat');
  
  const ledSpeednet = document.getElementById('led-speednet');
  const ledNhc = document.getElementById('led-nhc');
  const ledZupt = document.getElementById('led-zupt');
  const ledApm = document.getElementById('led-apm');
  const ledJerk = document.getElementById('led-jerk');
  
  const driftM028Value = document.getElementById('drift-m028-value');
  const driftRawValue = document.getElementById('drift-raw-value');

  // App State
  let scenarioConfig = null;
  let trajectoryData = [];
  let map = null;
  let currentIndex = 0;
  let isPlaying = false;
  let playbackSpeed = 1.0;
  let animationInterval = null;

  // Map Tile Layers
  let satTileLayer = null;
  let darkTileLayer = null;
  let labelsOverlayLayer = null;

  // Map Layers & Markers
  let polylineGt = null;
  let polylineM028 = null;
  let polylineRaw = null;
  let polylineReconnect = null;
  let vehicleMarker = null;

  // Data Loading (supports both HTTP fetch and file:// window fallback)
  if (window.CASE2_SCENARIO && window.CASE2_DATA) {
    scenarioConfig = window.CASE2_SCENARIO;
    trajectoryData = window.CASE2_DATA.trajectory;
  } else {
    try {
      const [scenResp, dataResp] = await Promise.all([
        fetch('scenario.json'),
        fetch('data.json')
      ]);
      scenarioConfig = await scenResp.json();
      const payload = await dataResp.json();
      trajectoryData = payload.trajectory;
    } catch (err) {
      console.error("Failed to load scenario or trajectory data via fetch:", err);
      return;
    }
  }

  // Initialize Map
  const startLat = scenarioConfig.environment.lat_center;
  const startLon = scenarioConfig.environment.lon_center;
  
  map = L.map(mapElement, {
    center: [startLat, startLon],
    zoom: 14,
    zoomControl: false
  });

  L.control.zoom({ position: 'topright' }).addTo(map);

  // High-Resolution Esri World Imagery Satellite Tile Layer (shows mountain ridge & terrain above tunnel)
  satTileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
  });

  // Dark Vector Tile Layer
  darkTileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    maxZoom: 19,
    subdomains: 'abcd',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
  });

  // CartoDB Reference Labels Overlay
  labelsOverlayLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png', {
    maxZoom: 19,
    subdomains: 'abcd',
    pane: 'shadowPane'
  });

  // Default to Satellite View so real mountain terrain is visible immediately!
  satTileLayer.addTo(map);
  labelsOverlayLayer.addTo(map);

  // Waypoints & Tunnel Geometry Setup
  const waypoints = scenarioConfig.waypoints;

  // Subterranean Tunnel Casing Overlay directly along the tunnel route (t=30s to t=270s)
  const tunnelPathCoords = trajectoryData
    .filter(s => s.t >= 30.0 && s.t <= 270.0)
    .map(s => [s.lat_gt, s.lon_gt]);

  // Outer Tunnel Vault Shield (Glow effect under mountain rock)
  L.polyline(tunnelPathCoords, {
    color: '#0284c7',
    weight: 22,
    opacity: 0.45,
    lineCap: 'square'
  }).addTo(map);

  // Inner Dark Tunnel Vault Tube
  L.polyline(tunnelPathCoords, {
    color: '#0f172a',
    weight: 12,
    opacity: 0.95,
    lineCap: 'round'
  }).addTo(map);

  // Neon Tunnel Vault Centerline
  L.polyline(tunnelPathCoords, {
    color: '#38bdf8',
    weight: 4,
    opacity: 0.95,
    dashArray: '8, 8'
  }).addTo(map);

  // Custom Portal Arch Gate Icons Offset to the Right
  const createPortalArchIcon = (title, label, color) => {
    return L.divIcon({
      className: 'portal-arch-marker',
      html: `
        <div style="display: flex; align-items: center; position: relative;">
          <!-- GPS Waypoint Dot directly on coordinate -->
          <div style="
            width: 12px; height: 12px;
            border-radius: 50%;
            background: ${color};
            border: 2px solid #ffffff;
            box-shadow: 0 0 10px ${color};
            flex-shrink: 0;
            z-index: 2;
          "></div>
          
          <!-- Leader Line extending to the right -->
          <div style="
            width: 18px; height: 2px;
            background: ${color};
            opacity: 0.8;
            flex-shrink: 0;
          "></div>

          <!-- Callout Card Offset to the Right -->
          <div style="
            background: rgba(15, 23, 42, 0.94);
            border: 1.5px solid ${color};
            border-radius: 6px;
            padding: 5px 9px;
            color: #ffffff;
            font-family: 'Inter', sans-serif;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.6);
            white-space: nowrap;
            z-index: 1;
          ">
            <div style="font-size: 10px; font-weight: 800; color: ${color}; letter-spacing: 0.5px; text-transform: uppercase;">${title}</div>
            <div style="font-size: 9px; color: #94a3b8;">${label}</div>
          </div>
        </div>
      `,
      iconSize: [260, 36],
      iconAnchor: [6, 18]
    });
  };

  // Dynamically anchor portal markers to exact trajectory tunnel points
  const ptEntry = trajectoryData.find(s => s.t >= 30.0) || trajectoryData[0];
  const ptMid = trajectoryData.find(s => s.t >= 150.0) || trajectoryData[Math.floor(trajectoryData.length / 2)];
  const ptExit = trajectoryData.find(s => s.t >= 270.0) || trajectoryData[trajectoryData.length - 1];

  L.marker([ptEntry.lat_gt, ptEntry.lon_gt], {
    icon: createPortalArchIcon("SOUTH PORTAL ENTRANCE", "Chenani Gate • Blackout Start (30s)", "#ef4444")
  }).addTo(map).bindPopup("<b>South Portal Entrance (Chenani)</b><br/>GNSS Signal Lost upon entering mountain tunnel.");

  L.marker([ptExit.lat_gt, ptExit.lon_gt], {
    icon: createPortalArchIcon("NORTH PORTAL EXIT", "Nashri Gate • Re-acquisition (270s)", "#10b981")
  }).addTo(map).bindPopup("<b>North Portal Exit (Nashri)</b><br/>GNSS Signal Restored upon exiting mountain tunnel.");

  // Mid-Tunnel Subterranean Marker Offset
  L.marker([ptMid.lat_gt, ptMid.lon_gt], {
    icon: L.divIcon({
      className: 'mid-tunnel-marker',
      html: `
        <div style="display: flex; align-items: center; position: relative;">
          <div style="width: 10px; height: 10px; border-radius: 50%; background: #0284c7; border: 1.5px solid #38bdf8; flex-shrink: 0;"></div>
          <div style="width: 14px; height: 2px; background: #0284c7; flex-shrink: 0;"></div>
          <div style="background: rgba(2,132,199,0.95); color: #fff; padding: 4px 9px; border-radius: 6px; font-size: 9.5px; font-weight: 700; border: 1px solid #38bdf8; white-space: nowrap;">SUBTERRANEAN TUNNEL VAULT (9.2 KM)</div>
        </div>
      `,
      iconSize: [240, 24],
      iconAnchor: [5, 12]
    })
  }).addTo(map);

  // Create Trajectory Polylines
  polylineGt = L.polyline([], { color: '#06b6d4', weight: 3.5, opacity: 0.85 }).addTo(map);
  polylineM028 = L.polyline([], { color: '#10b981', weight: 4.0, opacity: 0.95 }).addTo(map);
  polylineRaw = L.polyline([], { color: '#ef4444', weight: 2.5, opacity: 0.75, dashArray: '4, 4' }).addTo(map);
  polylineReconnect = L.polyline([], { color: '#f59e0b', weight: 3.5, opacity: 0.95 }).addTo(map);

  // Custom Vehicle Marker Icon (SVG Directional Arrow)
  const createVehicleIcon = (headingDeg) => {
    return L.divIcon({
      className: 'vehicle-marker-icon',
      html: `
        <div style="
          width: 30px; height: 30px;
          background: rgba(15, 23, 42, 0.9);
          border: 2px solid #38bdf8;
          border-radius: 50%;
          box-shadow: 0 0 14px rgba(56, 189, 248, 0.7);
          display: flex; align-items: center; justify-content: center;
          transform: rotate(${headingDeg || 0}deg);
        ">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 19 21 12 17 5 21 12 2"/>
          </svg>
        </div>
      `,
      iconSize: [30, 30],
      iconAnchor: [15, 15]
    });
  };

  vehicleMarker = L.marker([trajectoryData[0].lat_gt, trajectoryData[0].lon_gt], {
    icon: createVehicleIcon(trajectoryData[0].heading_deg)
  }).addTo(map);

  // Update Frame Function
  const updateFrame = (index) => {
    if (index < 0 || index >= trajectoryData.length) return;
    
    currentIndex = index;
    const sample = trajectoryData[index];

    // Update Slider
    timelineSlider.value = sample.t;

    // Collect Polyline Points up to current frame
    const ptsGt = [];
    const ptsM028 = [];
    const ptsRaw = [];
    const ptsReconnect = [];

    for (let i = 0; i <= index; i++) {
      const s = trajectoryData[i];
      ptsGt.push([s.lat_gt, s.lon_gt]);
      ptsM028.push([s.lat_m028, s.lon_m028]);
      ptsRaw.push([s.lat_raw, s.lon_raw]);
      
      if (s.gnss_state === "REACQUIRING" || s.gnss_state === "GNSS-RESTORED") {
        ptsReconnect.push([s.lat_m028, s.lon_m028]);
      }
    }

    polylineGt.setLatLngs(ptsGt);
    polylineM028.setLatLngs(ptsM028);
    polylineRaw.setLatLngs(ptsRaw);
    polylineReconnect.setLatLngs(ptsReconnect);

    // Update Vehicle Position & Heading
    const currentLat = sample.gnss_state === "GNSS-AIDED" ? sample.lat_gt : sample.lat_m028;
    const currentLon = sample.gnss_state === "GNSS-AIDED" ? sample.lon_gt : sample.lon_m028;
    
    vehicleMarker.setLatLng([currentLat, currentLon]);
    vehicleMarker.setIcon(createVehicleIcon(sample.heading_deg));

    // Smoothly Pan Map
    if (isPlaying) {
      map.panTo([currentLat, currentLon], { animate: true, duration: 0.1 });
    }

    // Toggle Subterranean Tunnel Vault Ambient Overlay & Camera HUD
    if (sample.gnss_state === "GNSS-DENIED") {
      tunnelOverlay.classList.add('active');
      if (camStatusBadge) {
        camStatusBadge.className = 'badge-cam subterranean';
        camStatusBadge.textContent = 'UNDERGROUND TUNNEL';
      }
      if (tunnelCamFeed) {
        tunnelCamFeed.className = 'tunnel-cam-feed inside-tunnel';
      }
      if (camOverlayText) {
        camOverlayText.textContent = `SUBTERRANEAN BLACKOUT — ${sample.t.toFixed(1)}s (GNSS DENIED)`;
      }
    } else {
      tunnelOverlay.classList.remove('active');
      if (camStatusBadge) {
        camStatusBadge.className = 'badge-cam open';
        camStatusBadge.textContent = 'OPEN ROAD';
      }
      if (tunnelCamFeed) {
        tunnelCamFeed.className = 'tunnel-cam-feed open-road';
      }
      if (camOverlayText) {
        camOverlayText.textContent = sample.gnss_state === 'REACQUIRING' ? 'REACQUIRING SATELLITES...' : 'SAT SIGNAL 100% — OPEN SKY';
      }
    }

    // Update Telemetry & Status HUD
    speedValue.textContent = sample.speed_m028_kmh.toFixed(1);
    teleAccel.textContent = `${sample.accel_long.toFixed(2)} m/s²`;
    teleJerk.textContent = `${sample.jerk_long.toFixed(2)} m/s³`;
    teleHeading.textContent = `${sample.heading_deg.toFixed(1)}°`;
    telePstat.textContent = sample.p_stat.toFixed(2);

    driftM028Value.textContent = `${sample.drift_m028_m.toFixed(2)} m`;
    driftRawValue.textContent = `${sample.drift_raw_m.toFixed(2)} m`;

    // Update Subsystem LEDs
    ledSpeednet.className = `led-light ${sample.speed_m028_kmh > 0 ? 'active' : ''}`;
    ledNhc.className = 'led-light active'; // Fixed NHC always active
    ledZupt.className = `led-light ${sample.zupt_active ? 'active' : ''}`;
    ledApm.className = `led-light ${sample.apm_active ? 'active' : ''}`;
    ledJerk.className = `led-light ${sample.jerk_long < -1.0 ? 'active' : ''}`;

    // Calculate & Update Tunnel Progress Percentage
    let progressPct = 0;
    if (sample.t >= 30.0 && sample.t <= 270.0) {
      progressPct = Math.min(100, Math.max(0, ((sample.t - 30.0) / 240.0) * 100));
    } else if (sample.t > 270.0) {
      progressPct = 100;
    }
    tunnelPctText.textContent = `${Math.round(progressPct)}%`;
    tunnelPctBar.style.width = `${progressPct}%`;

    // Update Outage Timer & GNSS State
    if (sample.gnss_state === "GNSS-AIDED") {
      gnssStatusBadge.className = 'status-badge gnss-online';
      gnssStatusText.textContent = 'GNSS ONLINE';
      statGnssCondition.textContent = 'GNSS-AIDED';
      statGnssCondition.className = 'stat-value color-online';
      statNavMode.textContent = 'GNSS-AIDED NAVIGATION';
      statOutageTimer.textContent = '00:00 / 04:00';
    } else if (sample.gnss_state === "GNSS-DENIED") {
      gnssStatusBadge.className = 'status-badge gnss-denied';
      gnssStatusText.textContent = 'GNSS DENIED';
      statGnssCondition.textContent = 'SUBTERRANEAN BLACKOUT';
      statGnssCondition.className = 'stat-value color-denied';
      statNavMode.textContent = sample.nav_mode || 'M029 MULTI-ANCHOR HEADING';

      const outageSec = Math.max(0, sample.t - 30.0);
      const mins = Math.floor(outageSec / 60);
      const secs = Math.floor(outageSec % 60);
      statOutageTimer.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')} / 04:00`;
    } else if (sample.gnss_state === "REACQUIRING") {
      gnssStatusBadge.className = 'status-badge gnss-reconnecting';
      gnssStatusText.textContent = 'REACQUIRING';
      statGnssCondition.textContent = 'SIGNAL RE-ACQUISITION';
      statGnssCondition.className = 'stat-value color-online';
      statNavMode.textContent = 'KALMAN RE-ALIGNMENT';
      statOutageTimer.textContent = '04:00 / 04:00';
    } else {
      gnssStatusBadge.className = 'status-badge gnss-online';
      gnssStatusText.textContent = 'GNSS RESTORED';
      statGnssCondition.textContent = 'GNSS-AIDED';
      statGnssCondition.className = 'stat-value color-online';
      statNavMode.textContent = 'GNSS-AIDED NAVIGATION';
      statOutageTimer.textContent = '04:00 / 04:00';
    }
  };

  // Playback Control Functions
  const startPlayback = () => {
    if (isPlaying) return;
    isPlaying = true;
    btnStart.disabled = true;
    btnPause.disabled = false;

    const intervalMs = Math.max(20, 100 / playbackSpeed);
    animationInterval = setInterval(() => {
      if (currentIndex >= trajectoryData.length - 1) {
        pausePlayback();
        return;
      }
      updateFrame(currentIndex + 1);
    }, intervalMs);
  };

  const pausePlayback = () => {
    isPlaying = false;
    btnStart.disabled = false;
    btnPause.disabled = true;
    if (animationInterval) {
      clearInterval(animationInterval);
      animationInterval = null;
    }
  };

  const resetPlayback = () => {
    pausePlayback();
    updateFrame(0);
    map.setView([startLat, startLon], 14);
  };

  // Map Tile Toggle Listeners
  btnMapSat.addEventListener('click', () => {
    btnMapSat.classList.add('active');
    btnMapDark.classList.remove('active');
    if (map.hasLayer(darkTileLayer)) map.removeLayer(darkTileLayer);
    satTileLayer.addTo(map);
    labelsOverlayLayer.addTo(map);
  });

  btnMapDark.addEventListener('click', () => {
    btnMapDark.classList.add('active');
    btnMapSat.classList.remove('active');
    if (map.hasLayer(satTileLayer)) map.removeLayer(satTileLayer);
    if (map.hasLayer(labelsOverlayLayer)) map.removeLayer(labelsOverlayLayer);
    darkTileLayer.addTo(map);
  });

  // Controls Event Listeners
  btnStart.addEventListener('click', startPlayback);
  btnPause.addEventListener('click', pausePlayback);
  btnReset.addEventListener('click', resetPlayback);

  timelineSlider.addEventListener('input', (e) => {
    pausePlayback();
    const tVal = parseFloat(e.target.value);
    const targetIdx = Math.min(
      trajectoryData.length - 1,
      Math.max(0, Math.round(tVal * 10))
    );
    updateFrame(targetIdx);
  });

  const setSpeed = (spd, activeBtn) => {
    playbackSpeed = spd;
    [btnSpeed1x, btnSpeed2x, btnSpeed5x].forEach(b => b.classList.remove('active'));
    activeBtn.classList.add('active');
    if (isPlaying) {
      pausePlayback();
      startPlayback();
    }
  };

  btnSpeed1x.addEventListener('click', () => setSpeed(1.0, btnSpeed1x));
  btnSpeed2x.addEventListener('click', () => setSpeed(2.0, btnSpeed2x));
  btnSpeed5x.addEventListener('click', () => setSpeed(5.0, btnSpeed5x));

  // Initialize at frame 0
  updateFrame(0);
});
