import { mapStyleService, MAP_STYLE_DEFINITIONS } from '../../services/map/MapStyleService';

export interface MapCameraPose {
  latitude: number;
  longitude: number;
  zoomLevel: number;
  heading: number;
  pitch: number;
}

// Development coordinate for cartographic map inspection (Bangalore center)
export const DEFAULT_CAMERA_POSE: MapCameraPose = {
  latitude: 12.9716,
  longitude: 77.5946,
  zoomLevel: 15.5,
  heading: 0,
  pitch: 35,
};

export const MAP_STYLES = {
  LIGHT: MAP_STYLE_DEFINITIONS.LIGHT.url,
  DARK: MAP_STYLE_DEFINITIONS.DARK.url,
  LIBERTY: MAP_STYLE_DEFINITIONS.LIBERTY.url,
};

export { mapStyleService, MAP_STYLE_DEFINITIONS };
