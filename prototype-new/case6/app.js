// SIH 2026 IDR PROTOTYPE — CASE 06: PLANETARY NAVIGATION APP LOGIC

(function() {
  'use strict';

  // --- STATE VARIABLES ---
  let trajectoryData = [];
  let currentIndex = 0;
  let isPlaying = false;
  let playbackSpeed = 1;
  let animTimer = null;
  
  // --- LEAFLET MAP & LAYERS ---
  let map = null;
  let groundTruthPolyline = null;
  let m028Polyline = null;
  let rawInertialPolyline = null;
  let roverMarker = null;
  let landmarkMarker = null;

  // --- CHART.JS ---
  let driftChart = null;

  // --- DOM ELEMENTS ---
  const timeDisplay = document.getElementById('time-display');
  const timeScrubber = document.getElementById('time-scrubber');
  const btnStart = document.getElementById('btn-start');
  const btnPause = document.getElementById('btn-pause');
  const btnReset = document.getElementById('btn-reset');
  const landmarkAlert = document.getElementById('landmark-alert');
  const transitionModal = document.getElementById('transition-modal');
  const transitionMsgText = document.getElementById('transition-msg-text');

  // Status Displays
  const valEnvironment = document.getElementById('val-environment');
  const valGnss = document.getElementById('val-gnss');
  const valNavmode = document.getElementById('val-navmode');
  const valEngine = document.getElementById('val-engine');
  const valImu = document.getElementById('val-imu');
  const valNhc = document.getElementById('val-nhc');

  // Telemetry Displays
  const valSpeed = document.getElementById('val-speed');
  const valPitch = document.getElementById('val-pitch');
  const valAccel = document.getElementById('val-accel');
  const valDriftM028 = document.getElementById('val-drift-m028');
  const driftRawVal = document.getElementById('drift-raw-val');
  const driftM028Val = document.getElementById('drift-m028-val');

  // --- INITIALIZATION ---
  document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    initMap();
    initChart();
    setupEventListeners();
    updateUI(0);
  });

  async function loadData() {
    if (window.CASE6_DATA && window.CASE6_DATA.trajectory) {
      trajectoryData = window.CASE6_DATA.trajectory;
    } else if (window.CASE06_DATA && window.CASE06_DATA.trajectory) {
      trajectoryData = window.CASE06_DATA.trajectory;
    } else {
      try {
        const res = await fetch('data.json');
        const json = await res.json();
        trajectoryData = json.trajectory;
      } catch (err) {
        console.error("Failed loading data.json:", err);
      }
    }
  }

  function initMap() {
    if (!trajectoryData || trajectoryData.length === 0) return;

    const startLat = trajectoryData[0].lat_gt || trajectoryData[0].lat_m028 || trajectoryData[0].m028_lat || 18.3800;
    const startLng = trajectoryData[0].lon_gt || trajectoryData[0].lon_m028 || trajectoryData[0].m028_lon || 77.5800;

    // Initialize Leaflet Map
    map = L.map('map', {
      center: [startLat, startLng],
      zoom: 17,
      zoomControl: true,
      attributionControl: false
    });

    // Dark Mars Satellite Base Layer
    const tileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19
    }).addTo(map);

    // Canvas Topography Accent Overlay
    addMarsTopographyGrid();

    // Prepare LatLng arrays
    const gtCoords = trajectoryData.map(pt => [
      pt.lat_gt || pt.lat_m028 || pt.m028_lat,
      pt.lon_gt || pt.lon_m028 || pt.m028_lon
    ]);

    // Planned Route (Ground Truth cyan)
    groundTruthPolyline = L.polyline(gtCoords, {
      color: '#00d2ff',
      weight: 3,
      opacity: 0.7,
      dashArray: '6, 6'
    }).addTo(map);

    // Raw Inertial Drift Path (Red)
    rawInertialPolyline = L.polyline([], {
      color: '#ff4444',
      weight: 2,
      opacity: 0.6
    }).addTo(map);

    // M028 Concept Adapter Path (Mars Orange)
    m028Polyline = L.polyline([], {
      color: '#ff5522',
      weight: 4,
      opacity: 0.95
    }).addTo(map);

    // Custom Mars Rover Icon (SVG Directional Arrow)
    const roverIcon = L.divIcon({
      className: 'mars-rover-icon',
      html: `
        <div style="
          width: 32px; height: 32px;
          background: rgba(15, 23, 42, 0.9);
          border: 2px solid #ff7336;
          border-radius: 50%;
          box-shadow: 0 0 16px rgba(255, 85, 39, 0.8);
          display: flex; align-items: center; justify-content: center;
        ">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ff7336" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 19 21 12 17 5 21 12 2"/>
          </svg>
        </div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 16]
    });

    roverMarker = L.marker([startLat, startLng], { icon: roverIcon }).addTo(map);

    // Landmark Checkpoint Marker at t=180s (Index 1800) Offset to the Right
    if (trajectoryData.length > 1800) {
      const lmPt = trajectoryData[1800];
      const lmLat = lmPt.lat_gt || lmPt.lat_m028 || lmPt.m028_lat;
      const lmLon = lmPt.lon_gt || lmPt.lon_m028 || lmPt.m028_lon;
      const lmIcon = L.divIcon({
        className: 'landmark-icon',
        html: `
          <div style="display: flex; align-items: center; position: relative;">
            <div style="width: 12px; height: 12px; border-radius: 50%; background: #00ff88; border: 2px solid #ffffff; box-shadow: 0 0 10px #00ff88; flex-shrink: 0; z-index: 2;"></div>
            <div style="width: 18px; height: 2px; background: #00ff88; opacity: 0.8; flex-shrink: 0;"></div>
            <div style="
              padding: 5px 10px; background: rgba(15, 23, 42, 0.94);
              border: 1.5px solid #00ff88; border-radius: 6px;
              color: #00ff88; font-size: 10px; font-weight: bold;
              white-space: nowrap; box-shadow: 0 4px 14px rgba(0, 0, 0, 0.6);
            ">Belva Crater Landmark (t=180s)</div>
          </div>
        `,
        iconSize: [240, 32],
        iconAnchor: [6, 16]
      });
      landmarkMarker = L.marker([lmLat, lmLon], { icon: lmIcon }).addTo(map);
    }

    map.fitBounds(groundTruthPolyline.getBounds(), { padding: [40, 40] });
  }

  function addMarsTopographyGrid() {
    // Adds subtle visual grid lines to simulate Martian digital elevation map
    const bounds = map.getBounds();
    const latSpan = bounds.getNorth() - bounds.getSouth();
    const lngSpan = bounds.getEast() - bounds.getWest();

    for (let i = 1; i <= 4; i++) {
      const lat = bounds.getSouth() + (latSpan / 5) * i;
      L.polyline([[lat, bounds.getWest()], [lat, bounds.getEast()]], {
        color: 'rgba(255, 85, 39, 0.1)',
        weight: 1,
        dashArray: '2, 8'
      }).addTo(map);
    }
  }

  function initChart() {
    const ctx = document.getElementById('driftChart').getContext('2d');
    driftChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Raw Inertial Drift (m)',
            borderColor: '#ff4444',
            backgroundColor: 'rgba(255, 68, 68, 0.1)',
            borderWidth: 1.5,
            data: [],
            pointRadius: 0,
            fill: false
          },
          {
            label: 'M028 Concept Drift (m)',
            borderColor: '#00ff88',
            backgroundColor: 'rgba(0, 255, 136, 0.15)',
            borderWidth: 2,
            data: [],
            pointRadius: 0,
            fill: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#8a99ad', font: { size: 9 } }
          },
          y: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#8a99ad', font: { size: 9 } },
            suggestedMax: 10
          }
        }
      }
    });
  }

  function setupEventListeners() {
    btnStart.addEventListener('click', startSimulation);
    btnPause.addEventListener('click', pauseSimulation);
    btnReset.addEventListener('click', resetSimulation);

    // Speed Controls
    document.getElementById('btn-speed-1x').addEventListener('click', () => setSpeed(1));
    document.getElementById('btn-speed-2x').addEventListener('click', () => setSpeed(2));
    document.getElementById('btn-speed-5x').addEventListener('click', () => setSpeed(5));

    // Time Scrubber
    timeScrubber.addEventListener('input', (e) => {
      const timeSec = parseFloat(e.target.value);
      currentIndex = Math.min(Math.floor(timeSec * 10), trajectoryData.length - 1);
      updateUI(currentIndex);
    });

    // Map View Switches
    document.getElementById('btn-map-sat').addEventListener('click', (e) => {
      document.getElementById('btn-map-sat').classList.add('active');
      document.getElementById('btn-map-dark').classList.remove('active');
    });
    document.getElementById('btn-map-dark').addEventListener('click', (e) => {
      document.getElementById('btn-map-dark').classList.add('active');
      document.getElementById('btn-map-sat').classList.remove('active');
    });
  }

  function setSpeed(speed) {
    playbackSpeed = speed;
    document.querySelectorAll('.btn-speed').forEach(b => b.classList.remove('active'));
    document.getElementById(`btn-speed-${speed}x`).classList.add('active');
  }

  function startSimulation() {
    if (isPlaying) return;
    isPlaying = true;
    btnStart.disabled = true;
    btnPause.disabled = false;

    const intervalMs = 100 / playbackSpeed;
    animTimer = setInterval(() => {
      if (currentIndex < trajectoryData.length - 1) {
        currentIndex++;
        updateUI(currentIndex);
      } else {
        pauseSimulation();
      }
    }, intervalMs);
  }

  function pauseSimulation() {
    isPlaying = false;
    btnStart.disabled = false;
    btnPause.disabled = true;
    if (animTimer) {
      clearInterval(animTimer);
      animTimer = null;
    }
  }

  function resetSimulation() {
    pauseSimulation();
    currentIndex = 0;
    updateUI(0);
  }

  function updateUI(idx) {
    if (!trajectoryData || trajectoryData.length === 0) return;

    const pt = trajectoryData[idx];
    const tSec = pt.t !== undefined ? pt.t : (pt.time_sec !== undefined ? pt.time_sec : 0);

    // 1. Time Display & Scrubber
    timeDisplay.textContent = `T + ${formatTime(tSec)} / 05:00s`;
    timeScrubber.value = tSec;

    // 2. Stepper Phase Updates
    updateStepperPhase(tSec);

    // 3. Status Badge & Panel Updates
    if (tSec < 20) {
      valEnvironment.textContent = 'Earth Launchpad';
      valGnss.textContent = 'AVAILABLE (GPS L1/L2)';
      valGnss.className = 'status-val text-green';
      valNavmode.textContent = 'GNSS + INS FUSION';
    } else {
      valEnvironment.textContent = 'Mars Surface (Jezero Delta)';
      valGnss.textContent = 'NOT AVAILABLE';
      valGnss.className = 'status-val text-danger';
      valNavmode.textContent = pt.nav_mode || 'M029 MULTI-ANCHOR HEADING';
    }

    // 4. Telemetry Displays
    const speedKmh = pt.speed_m028_kmh !== undefined ? pt.speed_m028_kmh : (pt.speed_ms !== undefined ? pt.speed_ms * 3.6 : 0);
    const pitchDeg = pt.pitch_deg !== undefined ? pt.pitch_deg : 0;
    const accel = pt.accel_long !== undefined ? pt.accel_long : 0;
    const driftM028 = pt.drift_m028_m !== undefined ? pt.drift_m028_m : 0;
    const driftRaw = pt.drift_raw_m !== undefined ? pt.drift_raw_m : 0;

    valSpeed.textContent = `${speedKmh.toFixed(1)} km/h`;
    valPitch.textContent = `${pitchDeg.toFixed(1)}°`;
    valAccel.textContent = `${accel.toFixed(2)} m/s²`;
    valDriftM028.textContent = `${driftM028.toFixed(2)} m`;
    driftRawVal.textContent = `${driftRaw.toFixed(1)}m`;
    driftM028Val.textContent = `${driftM028.toFixed(2)}m`;

    // 5. Map Trajectories Update
    const m028Lat = pt.lat_m028 !== undefined ? pt.lat_m028 : pt.m028_lat;
    const m028Lon = pt.lon_m028 !== undefined ? pt.lon_m028 : pt.m028_lon;
    const rawLat = pt.lat_raw !== undefined ? pt.lat_raw : pt.raw_lat;
    const rawLon = pt.lon_raw !== undefined ? pt.lon_raw : pt.raw_lon;

    const m028Coords = trajectoryData.slice(0, idx + 1).map(p => [
      p.lat_m028 !== undefined ? p.lat_m028 : p.m028_lat,
      p.lon_m028 !== undefined ? p.lon_m028 : p.m028_lon
    ]);
    const rawCoords = trajectoryData.slice(0, idx + 1).map(p => [
      p.lat_raw !== undefined ? p.lat_raw : p.raw_lat,
      p.lon_raw !== undefined ? p.lon_raw : p.raw_lon
    ]);

    m028Polyline.setLatLngs(m028Coords);
    rawInertialPolyline.setLatLngs(rawCoords);
    if (roverMarker && m028Lat && m028Lon) {
      roverMarker.setLatLng([m028Lat, m028Lon]);
      if (pt.heading_deg !== undefined) {
        const el = roverMarker.getElement();
        if (el) {
          const svgIcon = el.querySelector('svg');
          if (svgIcon) {
            svgIcon.style.transform = `rotate(${pt.heading_deg}deg)`;
            svgIcon.style.transformOrigin = 'center center';
          }
        }
      }
    }

    if (isPlaying && m028Lat && m028Lon) {
      map.panTo([m028Lat, m028Lon], { animate: false });
    }

    // 6. Landmark Alert Banner at t=180s
    if (tSec >= 175 && tSec <= 190) {
      landmarkAlert.classList.remove('hidden');
    } else {
      landmarkAlert.classList.add('hidden');
    }

    // 7. Update Drift Chart
    updateChart(idx);
  }

  function updateStepperPhase(tSec) {
    document.querySelectorAll('.step-item').forEach(el => el.classList.remove('active'));
    if (tSec < 20) {
      document.getElementById('step-1').classList.add('active');
    } else if (tSec < 40) {
      document.getElementById('step-2').classList.add('active');
    } else if (tSec < 60) {
      document.getElementById('step-3').classList.add('active');
    } else if (tSec < 80) {
      document.getElementById('step-4').classList.add('active');
    } else {
      document.getElementById('step-5').classList.add('active');
    }
  }

  function updateChart(idx) {
    if (!driftChart) return;

    // Subsample chart data points every 5 seconds for smooth rendering
    const step = 50; // 5 seconds @ 10 Hz
    const sliced = trajectoryData.slice(0, idx + 1);
    const labels = [];
    const rawData = [];
    const m028Data = [];

    for (let i = 0; i < sliced.length; i += step) {
      const item = sliced[i];
      const tVal = item.t !== undefined ? item.t : item.time_sec;
      labels.push(`${tVal.toFixed(0)}s`);
      rawData.push(item.drift_raw_m !== undefined ? item.drift_raw_m : 0);
      m028Data.push(item.drift_m028_m !== undefined ? item.drift_m028_m : 0);
    }

    // Always include current point
    if (sliced.length > 0 && (sliced.length - 1) % step !== 0) {
      const last = sliced[sliced.length - 1];
      const tVal = last.t !== undefined ? last.t : last.time_sec;
      labels.push(`${tVal.toFixed(0)}s`);
      rawData.push(last.drift_raw_m !== undefined ? last.drift_raw_m : 0);
      m028Data.push(last.drift_m028_m !== undefined ? last.drift_m028_m : 0);
    }

    driftChart.data.labels = labels;
    driftChart.data.datasets[0].data = rawData;
    driftChart.data.datasets[1].data = m028Data;
    driftChart.update('none');
  }

  function formatTime(sec) {
    const mins = Math.floor(sec / 60);
    const secs = Math.floor(sec % 60);
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}s`;
  }

  // Window Global Functions for HTML buttons
  window.jumpToPhase = function(percent) {
    const targetIdx = Math.floor((percent / 100) * trajectoryData.length);
    currentIndex = Math.min(targetIdx, trajectoryData.length - 1);
    updateUI(currentIndex);
  };

  window.triggerTransitionAnimation = function() {
    transitionModal.classList.remove('hidden');
    transitionMsgText.textContent = "Initiating Earth Departure... Terrestrial GNSS signal fading... Switching to Autonomous Onboard Inertial Navigation System (M028 Concept Adapter). Target: Mars Jezero Crater.";
    setTimeout(() => {
      closeTransitionModal();
    }, 3500);
  };

  window.closeTransitionModal = function() {
    transitionModal.classList.add('hidden');
  };

})();
