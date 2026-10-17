import React, { useState, useMemo, useRef, useEffect } from 'react';
import { View, StyleSheet, Platform, Text, TouchableOpacity } from 'react-native';
import { VehiclePose, TrajectoryPoint, GnssStatus, Destination, Route } from '../../types/navigation';
import { useAppTheme } from '../../theme/ThemeContext';
import { mapStyleService } from '../../services/map/MapStyleService';
import { VehicleMarker } from './VehicleMarker';
import { DestinationMarker } from './DestinationMarker';
import { MapControls } from './MapControls';
import { useLiveMarker } from '../../hooks/useLiveMarker';
import { calculateHaversineDistance } from '../../utils/geo';

// MapLibre v11 components — imported directly to ensure correct API usage
// v11 exports: Map, Camera, GeoJSONSource, Layer, Marker (NOT MapView/ShapeSource/LineLayer/PointAnnotation)
let MapLibreMap: any = null;
let MapLibreCamera: any = null;
let MapLibreGeoJSONSource: any = null;
let MapLibreLayer: any = null;
let MapLibreMarker: any = null;
try {
  const ML = require('@maplibre/maplibre-react-native');
  MapLibreMap = ML.Map;
  MapLibreCamera = ML.Camera;
  MapLibreGeoJSONSource = ML.GeoJSONSource;
  MapLibreLayer = ML.Layer;
  MapLibreMarker = ML.Marker;
} catch (e) {
  // MapLibre not available (web/fallback)
}

export type CameraFollowState = 'FOLLOWING' | 'USER_INTERACTED';

interface NavigationMapProps {
  pose: VehiclePose;
  gnssPoints: TrajectoryPoint[];
  idrPoints: TrajectoryPoint[];
  gnssStatus: GnssStatus;
  lastKnownPose: VehiclePose | null;
  isNavigating?: boolean;
  destination?: Destination | null;
  route?: Route | null;
}

export const NavigationMap: React.FC<NavigationMapProps> = ({
  pose,
  gnssPoints,
  idrPoints,
  gnssStatus,
  isNavigating = false,
  destination,
  route,
}) => {
  const { isDark, theme } = useAppTheme();
  const [zoomLevel, setZoomLevel] = useState(15.5);
  const [cameraState, setCameraState] = useState<CameraFollowState>('FOLLOWING');
  const isFollowing = cameraState === 'FOLLOWING';
  const cameraRef = useRef<any>(null);
  const lastCamLatRef = useRef<number>(0);
  const lastCamLonRef = useRef<number>(0);
  // Camera follow throttle: only send flyTo at most every 500ms during navigation
  const lastCamUpdateRef = useRef<number>(0);
  const isDenied = gnssStatus === 'DENIED';

  // Live Marker Hook — passes pose directly at 10 Hz during navigation (no lag-inducing animation window)
  const { lat: markerLat, lon: markerLon, heading: markerHeading } = useLiveMarker(pose, isNavigating);

  // Position validity check for safety (prevents camera jumps to [0,0] or null)
  const hasValidPosition = Boolean(
    markerLat &&
    markerLon &&
    Number.isFinite(markerLat) &&
    Number.isFinite(markerLon) &&
    (markerLat !== 0 || markerLon !== 0)
  );

  const styleUrl = mapStyleService.getStyleUrlForTheme(isDark);

  // MapLibre v11 correct component references
  const MapComponent = MapLibreMap;
  const CameraComponent = MapLibreCamera;
  const SourceComponent = MapLibreGeoJSONSource;  // uses `data` prop
  const LayerComponent = MapLibreLayer;           // uses type="line" + paint prop
  const MarkerComponent = MapLibreMarker;         // uses lngLat prop only

  const isNativeMapSupported = Platform.OS !== 'web' && MapComponent != null;

  // When user taps Start Navigation (isNavigating transitions to true),
  // zoom/fly camera ONCE to the vehicle navigation position.
  useEffect(() => {
    if (isNavigating && markerLat && markerLon && cameraRef.current) {
      setCameraState('FOLLOWING');
      lastCamLatRef.current = markerLat;
      lastCamLonRef.current = markerLon;
      lastCamUpdateRef.current = Date.now();

      if (typeof cameraRef.current.flyTo === 'function') {
        cameraRef.current.flyTo({
          center: [markerLon, markerLat] as [number, number],
          zoom: 16.5,
          duration: 800,
        });
      }
    }
  }, [isNavigating]);

  // Camera transition to Destination when a new destination is selected
  useEffect(() => {
    if (destination && destination.latitude && destination.longitude && cameraRef.current && !route) {
      setCameraState('USER_INTERACTED');
      // MapLibre v11 Camera.flyTo: { center: LngLat, zoom, duration }
      if (typeof cameraRef.current.flyTo === 'function') {
        cameraRef.current.flyTo({
          center: [destination.longitude, destination.latitude],
          zoom: 15.0,
          duration: 800,
        });
      } else if (typeof cameraRef.current.easeTo === 'function') {
        cameraRef.current.easeTo({
          center: [destination.longitude, destination.latitude],
          zoom: 15.0,
          duration: 800,
        });
      }
    }
  }, [destination?.id, destination?.latitude, destination?.longitude]);

  // Route Overview Camera Framing & Bounding Box computation
  // IMPORTANT: deps do NOT include pose coords — route bounds are stable, computed once.
  const routeCenterAndZoom = useMemo(() => {
    if (!route || !route.geometry || route.geometry.length < 2) return null;
    let minLat = route.geometry[0][1];
    let maxLat = route.geometry[0][1];
    let minLon = route.geometry[0][0];
    let maxLon = route.geometry[0][0];

    for (const [lon, lat] of route.geometry) {
      if (lat < minLat) minLat = lat;
      if (lat > maxLat) maxLat = lat;
      if (lon < minLon) minLon = lon;
      if (lon > maxLon) maxLon = lon;
    }

    const centerLat = (minLat + maxLat) / 2;
    const centerLon = (minLon + maxLon) / 2;
    return {
      center: [centerLon, centerLat],
      zoom: 13.5,
      bounds: { minLat, maxLat, minLon, maxLon },
    };
  }, [route?.id]);

  // Route Overview Camera Framing Effect: Fit bounds to include vehicle position, route geometry, and destination
  useEffect(() => {
    if (route && routeCenterAndZoom && cameraRef.current) {
      const { bounds, center, zoom } = routeCenterAndZoom;
      // MapLibre v11 Camera.fitBounds: (bounds: [west, south, east, north], options?)
      if (typeof cameraRef.current.fitBounds === 'function') {
        cameraRef.current.fitBounds(
          [bounds.minLon, bounds.minLat, bounds.maxLon, bounds.maxLat],
          { padding: { top: 100, right: 40, bottom: 140, left: 40 }, duration: 800 }
        );
      } else if (typeof cameraRef.current.flyTo === 'function') {
        cameraRef.current.flyTo({
          center: center as [number, number],
          zoom,
          duration: 800,
        });
      }
    }
  }, [route?.id, routeCenterAndZoom]);

  // Real-time camera follow effect — runs ONLY during active turn-by-turn navigation
  useEffect(() => {
    if (!isNavigating || cameraState !== 'FOLLOWING' || !markerLat || !markerLon || !cameraRef.current) return;

    const now = Date.now();
    // Throttle camera follow updates to 2 Hz (500ms) during active navigation
    if (now - lastCamUpdateRef.current < 500) return;

    const dist = calculateHaversineDistance(
      lastCamLatRef.current,
      lastCamLonRef.current,
      markerLat,
      markerLon
    );

    if (dist > 0.5 || lastCamLatRef.current === 0) {
      lastCamLatRef.current = markerLat;
      lastCamLonRef.current = markerLon;
      lastCamUpdateRef.current = now;

      if (typeof cameraRef.current.flyTo === 'function') {
        cameraRef.current.flyTo({
          center: [markerLon, markerLat] as [number, number],
          zoom: 16.5,
          duration: 450,
        });
      } else if (typeof cameraRef.current.easeTo === 'function') {
        cameraRef.current.easeTo({
          center: [markerLon, markerLat] as [number, number],
          zoom: 16.5,
          duration: 450,
        });
      }
    }
  }, [markerLat, markerLon, cameraState, isNavigating]);

  // Transform GNSS trajectory points into GeoJSON LineString feature
  const gnssGeoJson = useMemo(() => {
    if (!gnssPoints || gnssPoints.length < 2) return null;
    const coordinates = gnssPoints.map((pt) => [pt.longitude, pt.latitude]);
    return {
      type: 'FeatureCollection' as const,
      features: [
        {
          type: 'Feature' as const,
          properties: {},
          geometry: {
            type: 'LineString' as const,
            coordinates,
          },
        },
      ],
    };
  }, [gnssPoints]);

  // Transform IDR trajectory points into GeoJSON LineString feature
  const idrGeoJson = useMemo(() => {
    if (!idrPoints || idrPoints.length < 2) return null;
    const coordinates = idrPoints.map((pt) => [pt.longitude, pt.latitude]);
    return {
      type: 'FeatureCollection' as const,
      features: [
        {
          type: 'Feature' as const,
          properties: {},
          geometry: {
            type: 'LineString' as const,
            coordinates,
          },
        },
      ],
    };
  }, [idrPoints]);

  // Transform offline route geometry points into GeoJSON LineString feature for Native MapLibre
  // IMPORTANT: deps do NOT include pose coords — route GeoJSON is stable once calculated.
  // Recreating it on every pose update (10 Hz) would re-upload geometry to MapLibre every 100ms.
  const routeGeoJson = useMemo(() => {
    if (!route || !route.geometry || route.geometry.length < 2) return null;
    const first = route.geometry[0];
    const last = route.geometry[route.geometry.length - 1];
    console.log(`[ROUTE] start=[${first[1].toFixed(6)}, ${first[0].toFixed(6)}] end=[${last[1].toFixed(6)}, ${last[0].toFixed(6)}] points=${route.geometry.length}`);
    return {
      type: 'FeatureCollection' as const,
      features: [
        {
          type: 'Feature' as const,
          properties: {},
          geometry: {
            type: 'LineString' as const,
            coordinates: route.geometry,
          },
        },
      ],
    };
  }, [route?.id]);

  // Handle Zoom & Recenter Actions
  const handleZoomIn = () => {
    setZoomLevel((prevZoom) => {
      const nextZ = Math.min(Math.round((prevZoom + 1.0) * 10) / 10, 19.0);
      if (cameraRef.current) {
        if (typeof cameraRef.current.zoomTo === 'function') {
          // MapLibre v11: zoomTo(zoom, options?)
          cameraRef.current.zoomTo(nextZ, { duration: 250 });
        }
      }
      return nextZ;
    });
  };

  const handleZoomOut = () => {
    setZoomLevel((prevZoom) => {
      const nextZ = Math.max(Math.round((prevZoom - 1.0) * 10) / 10, 10.0);
      if (cameraRef.current) {
        if (typeof cameraRef.current.zoomTo === 'function') {
          cameraRef.current.zoomTo(nextZ, { duration: 250 });
        }
      }
      return nextZ;
    });
  };

  const handleRecenter = () => {
    if (!hasValidPosition || !cameraRef.current) return;

    // Reset displacement reference so subsequent camera follow updates proceed cleanly
    lastCamLatRef.current = markerLat;
    lastCamLonRef.current = markerLon;
    lastCamUpdateRef.current = 0;

    setCameraState('FOLLOWING');

    // MapLibre v11: flyTo({ center: LngLat, zoom, duration })
    if (typeof cameraRef.current.flyTo === 'function') {
      cameraRef.current.flyTo({
        center: [markerLon, markerLat] as [number, number],
        zoom: zoomLevel,
        duration: 400,
      });
    } else if (typeof cameraRef.current.easeTo === 'function') {
      cameraRef.current.easeTo({
        center: [markerLon, markerLat] as [number, number],
        zoom: zoomLevel,
        duration: 400,
      });
    }
  };

  // Render Real MapLibre Native Map View
  if (isNativeMapSupported && MapComponent) {
    return (
      <View style={styles.container}>
        <MapComponent
          style={styles.mapView}
          mapStyle={styleUrl}
          logo={false}
          attribution={false}
          compass={false}
          dragPan={true}
          touchZoom={true}
          touchRotate={true}
          touchPitch={true}
          onRegionWillChange={(event: any) => {
            // MapLibre v11: userInteraction is in event.nativeEvent
            const isUser = event?.nativeEvent?.userInteraction ?? event?.userInteraction;
            if (isUser && cameraState === 'FOLLOWING') {
              setCameraState('USER_INTERACTED');
            }
          }}
          onRegionIsChanging={(event: any) => {
            const isUser = event?.nativeEvent?.userInteraction ?? event?.userInteraction;
            if (isUser && cameraState === 'FOLLOWING') {
              setCameraState('USER_INTERACTED');
            }
          }}
        >
          {CameraComponent && (
            // MapLibre v11 Camera: initial mount-time position only.
            // All subsequent movement is driven imperatively via cameraRef.current.flyTo().
            // Reactive pose props are intentionally REMOVED to prevent dual animation.
            <CameraComponent
              ref={cameraRef}
              center={[77.0705, 10.8281] as [number, number]}
              zoom={14}
              bearing={0}
              pitch={0}
            />
          )}

          {/* Offline A* Route Polyline — MapLibre v11 correct API */}
          {/* GeoJSONSource uses `data` prop; Layer uses type="line" + paint prop; no belowLayerID */}
          {routeGeoJson && SourceComponent && LayerComponent && (
            <SourceComponent id="routePolylineSource" data={routeGeoJson}>
              {/* Casing (outer dark blue border) */}
              <LayerComponent
                id="routePolylineCasing"
                type="line"
                paint={{
                  'line-color': isDark ? '#0284C7' : '#1D4ED8',
                  'line-width': 10,
                  'line-cap': 'round',
                  'line-join': 'round',
                  'line-opacity': 0.9,
                }}
              />
              {/* Primary bright cyan line on top */}
              <LayerComponent
                id="routePolylinePrimary"
                type="line"
                paint={{
                  'line-color': '#00F0FF',
                  'line-width': 6,
                  'line-cap': 'round',
                  'line-join': 'round',
                  'line-opacity': 1.0,
                }}
              />
            </SourceComponent>
          )}

          {/* GNSS Vector Path Layer — MapLibre v11 API */}
          {gnssGeoJson && SourceComponent && LayerComponent && (
            <SourceComponent id="gnssPathSource" data={gnssGeoJson}>
              <LayerComponent
                id="gnssPathLayer"
                type="line"
                paint={{
                  'line-color': theme.colors.gnssPath,
                  'line-width': 4,
                  'line-cap': 'round',
                  'line-join': 'round',
                }}
              />
            </SourceComponent>
          )}

          {/* Dead Reckoning Vector Path Layer (Dashed) — MapLibre v11 API */}
          {idrGeoJson && SourceComponent && LayerComponent && (
            <SourceComponent id="idrPathSource" data={idrGeoJson}>
              <LayerComponent
                id="idrPathLayer"
                type="line"
                paint={{
                  'line-color': theme.colors.idrPath,
                  'line-width': 4,
                  'line-dasharray': [2, 2],
                  'line-cap': 'round',
                  'line-join': 'round',
                }}
              />
            </SourceComponent>
          )}

          {/* Vehicle Position Marker — MapLibre v11: lngLat prop only */}
          {MarkerComponent && markerLon && markerLat && (
            <MarkerComponent
              id="vehicleMarkerPoint"
              lngLat={[markerLon, markerLat] as [number, number]}
            >
              <VehicleMarker heading={markerHeading} isDenied={isDenied} />
            </MarkerComponent>
          )}

          {/* Destination Marker — MapLibre v11: lngLat prop only */}
          {destination && destination.longitude && destination.latitude && MarkerComponent && (
            <MarkerComponent
              id="destinationMarkerPoint"
              lngLat={[destination.longitude, destination.latitude] as [number, number]}
            >
              <DestinationMarker name={destination.name} />
            </MarkerComponent>
          )}
        </MapComponent>

        {/* Compact Top-Right Compass Button (36x36dp) */}
        <TouchableOpacity
          style={[styles.compassBtn, { backgroundColor: theme.colors.card, borderColor: theme.colors.cardBorder }]}
          onPress={() => {
            if (cameraRef.current) {
              // MapLibre v11 Camera: use flyTo with bearing=0 to reset north
              if (typeof cameraRef.current.flyTo === 'function') {
                cameraRef.current.flyTo({
                  center: [markerLon || pose.longitude, markerLat || pose.latitude] as [number, number],
                  bearing: 0,
                  duration: 300,
                });
              }
            }
          }}
          activeOpacity={0.8}
        >
          <View style={[styles.compassNeedle, { transform: [{ rotate: `${(pose.heading || 0) * -1}deg` }] }]}>
            <View style={styles.needleNorth} />
            <View style={styles.needleSouth} />
          </View>
        </TouchableOpacity>

        {/* Small Unobtrusive Map Attribution */}
        <View style={styles.attributionBox}>
          <Text style={[styles.attributionText, { color: theme.colors.textMuted }]}>
            © OpenStreetMap contributors, OpenFreeMap
          </Text>
        </View>

        {/* Floating Map Controls */}
        <MapControls
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onRecenter={handleRecenter}
          isFollowing={isFollowing}
          hasValidPosition={hasValidPosition}
        />
      </View>
    );
  }

  // High-Performance Leaflet / Vector Fallback View
  let WebViewComp: any = null;
  try {
    WebViewComp = require('react-native-webview').WebView;
  } catch (e) {
    WebViewComp = null;
  }

  if (WebViewComp) {
    const routeLatLngs = route && route.geometry && route.geometry.length >= 2
      ? JSON.stringify(route.geometry.map(([lon, lat]) => [lat, lon]))
      : 'null';

    const destLat = destination?.latitude || null;
    const destLon = destination?.longitude || null;
    const destName = destination?.name ? JSON.stringify(destination.name) : '""';

    const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
          body { margin: 0; padding: 0; background: ${isDark ? '#0B0F19' : '#F1F5F9'}; }
          #map { width: 100vw; height: 100vh; }
          .leaflet-tile { filter: ${isDark ? 'brightness(0.6) invert(1) contrast(3) hue-rotate(200deg) saturate(0.3)' : 'none'}; }
          .dest-marker { background: #EF4444; border: 2px solid #FFFFFF; border-radius: 50%; width: 14px; height: 14px; box-shadow: 0 0 6px rgba(0,0,0,0.5); }
        </style>
      </head>
      <body>
        <div id="map"></div>
        <script>
          const initialLat = ${pose.latitude || 10.8281};
          const initialLon = ${pose.longitude || 77.0605};
          const map = L.map('map', { zoomControl: false }).setView([initialLat, initialLon], 15);

          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);

          // Vehicle Position Marker
          L.circleMarker([initialLat, initialLon], {
            radius: 9, fillColor: '${isDenied ? '#EF4444' : '#3B82F6'}', color: '#FFFFFF', weight: 3, fillOpacity: 1.0
          }).addTo(map);

          // Destination Pin Marker
          const destLat = ${destLat};
          const destLon = ${destLon};
          if (destLat && destLon) {
            L.circleMarker([destLat, destLon], {
              radius: 10, fillColor: '#EF4444', color: '#FFFFFF', weight: 3, fillOpacity: 1.0
            }).addTo(map).bindPopup(${destName});
          }

          // Offline A* Route Polyline Layer with [lat, lon] coordinate mapping
          const routeCoords = ${routeLatLngs};
          if (routeCoords && routeCoords.length >= 2) {
            // Outer high-contrast casing line
            L.polyline(routeCoords, {
              color: '${isDark ? '#0369A1' : '#1D4ED8'}',
              weight: 10,
              opacity: 0.8,
              lineCap: 'round',
              lineJoin: 'round'
            }).addTo(map);

            // Primary bright navigation route line
            const polyline = L.polyline(routeCoords, {
              color: '#38BDF8',
              weight: 6,
              opacity: 0.98,
              lineCap: 'round',
              lineJoin: 'round'
            }).addTo(map);

            // Auto-frame viewport bounds to cover the complete route from start to destination
            map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
          }
        </script>
      </body>
      </html>
    `;
    return (
      <View style={styles.container}>
        <View style={styles.mapView}>
          <WebViewComp originWhitelist={['*']} source={{ html: htmlContent }} style={{ flex: 1 }} />
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={[styles.mapView, { backgroundColor: isDark ? '#0B0F19' : '#E2E8F0', justifyContent: 'center', alignItems: 'center' }]}>
        <Text style={{ color: theme.colors.primary, fontSize: 18, fontWeight: '900' }}>NavDR Real-Time Trajectory Engine</Text>
        <Text style={{ color: theme.colors.textSecondary, fontSize: 12, marginTop: 6 }}>
          Lat: {pose.latitude.toFixed(5)}° | Lon: {pose.longitude.toFixed(5)}° | Speed: {((pose.speed || 0) * 3.6).toFixed(1)} km/h
        </Text>
        <View style={{ marginTop: 16, paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, backgroundColor: isDenied ? '#EF444422' : '#10B98122' }}>
          <Text style={{ color: isDenied ? '#EF4444' : '#10B981', fontWeight: '800', fontSize: 13 }}>
            {isDenied ? 'GNSS OUTAGE (DEAD RECKONING ACTIVE)' : 'GNSS AVAILABLE (3D LOCK)'}
          </Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 8,
    paddingVertical: 6,
  },
  mapView: {
    flex: 1,
    borderRadius: 10,
    overflow: 'hidden',
  },
  compassBtn: {
    position: 'absolute',
    top: 14,
    right: 14,
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 15,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
  },
  compassNeedle: {
    width: 16,
    height: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  needleNorth: {
    width: 0,
    height: 0,
    borderLeftWidth: 3.5,
    borderRightWidth: 3.5,
    borderBottomWidth: 7,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    borderBottomColor: '#EF4444',
  },
  needleSouth: {
    width: 0,
    height: 0,
    borderLeftWidth: 3.5,
    borderRightWidth: 3.5,
    borderTopWidth: 7,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    borderTopColor: '#94A3B8',
  },
  attributionBox: {
    position: 'absolute',
    bottom: 12,
    left: 14,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    backgroundColor: 'rgba(0, 0, 0, 0.25)',
    zIndex: 10,
  },
  attributionText: {
    fontSize: 8,
    fontWeight: '600',
    color: '#FFFFFF',
    opacity: 0.85,
  },
  errorContainer: {
    flex: 1,
    margin: 12,
    borderRadius: 12,
    borderWidth: 1,
    padding: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorIconBox: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(239, 68, 68, 0.12)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 14,
  },
  errorIcon: {
    fontSize: 22,
  },
  errorTitle: {
    fontSize: 16,
    fontWeight: '900',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  errorDesc: {
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: 12,
  },
  errorSub: {
    fontSize: 10,
    fontWeight: '700',
    fontVariant: ['tabular-nums'],
  },
});
