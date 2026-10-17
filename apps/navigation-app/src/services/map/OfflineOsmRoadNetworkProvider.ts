import { RoadNetworkProvider, RoadSegment } from './RoadNetworkProvider';

declare const require: any;
declare const process: any;
declare const __dirname: string;

interface OsmPackageMetadata {
  region: string;
  bounds: { south: number; west: number; north: number; east: number };
  extractionDate: string;
  gridSizeDeg: number;
  roadCount: number;
  segmentCount: number;
  spatialCellCount: number;
}

interface OsmPackageData {
  metadata: OsmPackageMetadata;
  segments: Record<string, RoadSegment>;
  spatialIndex: Record<string, string[]>;
}

/**
 * Production Offline OSM Road Network Provider (Stage 4E.1).
 * Serves real OpenStreetMap road candidates in O(1) time using an in-memory spatial grid index.
 * Requires ZERO network connectivity at runtime.
 */
export class OfflineOsmRoadNetworkProvider implements RoadNetworkProvider {
  private isLoaded: boolean = false;
  private metadata: OsmPackageMetadata | null = null;
  private segments: Record<string, RoadSegment> = {};
  private spatialIndex: Record<string, string[]> = {};
  private gridSizeDeg: number = 0.005;

  constructor() {
    this.loadPackage();
  }

  private safeNodeRequire(moduleName: string): any {
    if (typeof process !== 'undefined' && process.versions && process.versions.node && typeof window === 'undefined') {
      try {
        const req = eval('require');
        return req(moduleName);
      } catch {
        return null;
      }
    }
    return null;
  }

  private loadPackage(): void {
    try {
      let packageData: OsmPackageData | null = null;

      // 1. Attempt standard React Native asset require
      try {
        packageData = require('../../../assets/offline-maps/coimbatore_regional_osm.json');
      } catch (reqErr) {
        // 2. Fall back to Node.js fs loading (for standalone node test scripts)
        const fs = this.safeNodeRequire('fs');
        const path = this.safeNodeRequire('path');
        if (fs && path) {
          const candidatePaths = [
            path.resolve(__dirname, '../../../../assets/offline-maps/coimbatore_regional_osm.json'),
            path.resolve(process.cwd(), 'apps/navigation-app/assets/offline-maps/coimbatore_regional_osm.json'),
            path.resolve(process.cwd(), 'assets/offline-maps/coimbatore_regional_osm.json'),
          ];
          for (const assetPath of candidatePaths) {
            if (fs.existsSync(assetPath)) {
              const rawText = fs.readFileSync(assetPath, 'utf-8');
              packageData = JSON.parse(rawText);
              break;
            }
          }
        }
      }

      if (packageData && packageData.segments && packageData.spatialIndex) {
        this.metadata = packageData.metadata;
        this.segments = packageData.segments;
        this.spatialIndex = packageData.spatialIndex;
        this.gridSizeDeg = packageData.metadata?.gridSizeDeg || 0.005;
        this.isLoaded = true;
      }
    } catch (e) {
      console.warn('[OfflineOsmProvider] Offline dataset not loaded or unavailable:', e);
      this.isLoaded = false;
    }
  }

  public isAvailable(): boolean {
    return this.isLoaded && Object.keys(this.segments).length > 0;
  }

  public getMetadata(): OsmPackageMetadata | null {
    return this.metadata;
  }

  public async getCandidates(
    latitude: number,
    longitude: number,
    radiusMeters: number
  ): Promise<RoadSegment[]> {
    if (!this.isAvailable()) {
      return [];
    }

    // Convert search radius from meters to degrees (~111.13 km per degree lat)
    const radiusDeg = Math.max(this.gridSizeDeg, radiusMeters / 111132.92);

    const minLat = latitude - radiusDeg;
    const maxLat = latitude + radiusDeg;
    const minLon = longitude - radiusDeg;
    const maxLon = longitude + radiusDeg;

    const candidateIds = new Set<string>();

    // Scan spatial grid cells covering the search bounding box
    let latCurr = Math.floor(minLat / this.gridSizeDeg) * this.gridSizeDeg;
    while (latCurr <= maxLat + 1e-5) {
      let lonCurr = Math.floor(minLon / this.gridSizeDeg) * this.gridSizeDeg;
      while (lonCurr <= maxLon + 1e-5) {
        const cellKey = `${latCurr.toFixed(4)}_${lonCurr.toFixed(4)}`;
        const cellSegIds = this.spatialIndex[cellKey];
        if (cellSegIds) {
          for (let i = 0; i < cellSegIds.length; i++) {
            candidateIds.add(cellSegIds[i]);
          }
        }
        lonCurr += this.gridSizeDeg;
      }
      latCurr += this.gridSizeDeg;
    }

    const candidateSegments: RoadSegment[] = [];
    candidateIds.forEach((id) => {
      const seg = this.segments[id];
      if (seg) {
        candidateSegments.push(seg);
      }
    });

    return candidateSegments;
  }
}

export const offlineOsmRoadNetworkProvider = new OfflineOsmRoadNetworkProvider();
