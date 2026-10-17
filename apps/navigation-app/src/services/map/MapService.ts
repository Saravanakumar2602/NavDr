import { DEFAULT_CAMERA_POSE, MapCameraPose } from '../../components/map/mapConfig';
import { mapStyleService } from './MapStyleService';

export type MapConnectivityState = 'ONLINE' | 'OFFLINE';

export class MapService {
  private connectivityState: MapConnectivityState = 'ONLINE';

  public getStyleUrl(isDark: boolean): string {
    return mapStyleService.getStyleUrlForTheme(isDark);
  }

  public getDefaultCamera(): MapCameraPose {
    return { ...DEFAULT_CAMERA_POSE };
  }

  public getConnectivityState(): MapConnectivityState {
    return this.connectivityState;
  }

  public setConnectivityState(state: MapConnectivityState) {
    this.connectivityState = state;
  }
}

export const mapService = new MapService();
