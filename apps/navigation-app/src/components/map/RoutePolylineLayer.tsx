import React, { useMemo } from 'react';
import { Route } from '../../types/navigation';
import { useAppTheme } from '../../theme/ThemeContext';

interface RoutePolylineLayerProps {
  route: Route;
  MapLibre: any;
}

export const RoutePolylineLayer: React.FC<RoutePolylineLayerProps> = ({ route, MapLibre }) => {
  const { isDark } = useAppTheme();

  const SourceComponent = MapLibre ? (MapLibre.GeoJSONSource || MapLibre.ShapeSource) : null;
  const LineLayerComponent = MapLibre ? MapLibre.LineLayer : null;

  // Theme-adaptive crisp polyline colors
  const primaryColor = isDark ? '#38BDF8' : '#2563EB';
  const casingColor = isDark ? '#0369A1' : '#1D4ED8';

  // Memoize GeoJSON feature collection to prevent rebuilds on telemetry ticks
  const routeGeoJson = useMemo(() => {
    if (!route || !route.geometry || route.geometry.length < 2) return null;

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
  }, [route.id, route.geometry]);

  if (!routeGeoJson || !SourceComponent || !LineLayerComponent) {
    return null;
  }

  return (
    <SourceComponent id="routePolylineSource" shape={routeGeoJson}>
      {/* Outer Casing / High Contrast Glow Line */}
      <LineLayerComponent
        id="routePolylineCasing"
        style={{
          lineColor: casingColor,
          lineWidth: 8,
          lineCap: 'round',
          lineJoin: 'round',
          lineOpacity: 0.7,
        }}
      />
      {/* Primary Navigation Route Line */}
      <LineLayerComponent
        id="routePolylinePrimary"
        style={{
          lineColor: primaryColor,
          lineWidth: 5,
          lineCap: 'round',
          lineJoin: 'round',
          lineOpacity: 0.95,
        }}
      />
    </SourceComponent>
  );
};
