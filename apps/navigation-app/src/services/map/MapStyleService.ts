export type MapStyleType = 'LIGHT' | 'DARK' | 'LIBERTY';

export interface MapStyleDefinition {
  id: MapStyleType;
  name: string;
  url: string;
  attribution: string;
  source: 'OpenStreetMap' | 'OpenFreeMap';
}

export const MAP_STYLE_DEFINITIONS: Record<MapStyleType, MapStyleDefinition> = {
  LIGHT: {
    id: 'LIGHT',
    name: 'NavDR Light Vector',
    url: 'https://tiles.openfreemap.org/styles/bright',
    attribution: '© OpenStreetMap contributors, OpenFreeMap',
    source: 'OpenFreeMap',
  },
  DARK: {
    id: 'DARK',
    name: 'NavDR Dark Vector',
    url: 'https://tiles.openfreemap.org/styles/dark',
    attribution: '© OpenStreetMap contributors, OpenFreeMap',
    source: 'OpenFreeMap',
  },
  LIBERTY: {
    id: 'LIBERTY',
    name: 'NavDR Liberty Vector',
    url: 'https://tiles.openfreemap.org/styles/liberty',
    attribution: '© OpenStreetMap contributors, OpenFreeMap',
    source: 'OpenFreeMap',
  },
};

export class MapStyleService {
  public getStyle(styleType: MapStyleType): MapStyleDefinition {
    return MAP_STYLE_DEFINITIONS[styleType] || MAP_STYLE_DEFINITIONS.LIGHT;
  }

  public getStyleUrlForTheme(isDark: boolean): string {
    return isDark ? MAP_STYLE_DEFINITIONS.DARK.url : MAP_STYLE_DEFINITIONS.LIGHT.url;
  }
}

export const mapStyleService = new MapStyleService();
