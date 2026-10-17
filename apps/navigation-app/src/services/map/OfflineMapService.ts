export interface OfflineRegion {
  id: string;
  name: string;
  bounds: {
    ne: [number, number];
    sw: [number, number];
  };
  minZoom: number;
  maxZoom: number;
  status: 'NOT_CONFIGURED' | 'DOWNLOADING' | 'READY' | 'ERROR';
  sizeBytes: number;
}

export class OfflineMapService {
  private isConfigured: boolean = false;
  private regions: OfflineRegion[] = [];

  public isOfflineManagerSupported(): boolean {
    return true; // MapLibre React Native supports OfflineManager natively
  }

  public async getOfflineRegions(): Promise<OfflineRegion[]> {
    return [...this.regions];
  }

  public async downloadRegion(
    regionId: string,
    name: string,
    bounds: { ne: [number, number]; sw: [number, number] },
    minZoom: number = 10,
    maxZoom: number = 16
  ): Promise<OfflineRegion> {
    const region: OfflineRegion = {
      id: regionId,
      name,
      bounds,
      minZoom,
      maxZoom,
      status: 'NOT_CONFIGURED',
      sizeBytes: 0,
    };
    return region;
  }

  public async deleteRegion(regionId: string): Promise<boolean> {
    this.regions = this.regions.filter((r) => r.id !== regionId);
    return true;
  }

  public async getRegionStatus(regionId: string): Promise<OfflineRegion['status']> {
    const r = this.regions.find((reg) => reg.id === regionId);
    return r ? r.status : 'NOT_CONFIGURED';
  }
}

export const offlineMapService = new OfflineMapService();
