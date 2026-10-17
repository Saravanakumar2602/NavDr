import { RoadNetworkProvider, RoadSegment } from './RoadNetworkProvider';
import { OfflineMapManifest } from '../../types/navigation';

declare const require: any;
declare const process: any;
declare const __dirname: string;

/**
 * Stage 4E.3 — Spatial Tile-Based Offline Map Storage & Lazy Loading Provider.
 * Implements RoadNetworkProvider with lazy tile loading and a bounded LRU tile cache.
 * 100% Decoupled from MapMatcher.
 */
export class TiledOfflineOsmRoadNetworkProvider implements RoadNetworkProvider {
  private manifest: OfflineMapManifest;
  private tileIndex: Record<string, string>;
  private tileCache: Map<string, Record<string, RoadSegment>> = new Map();
  private maxCachedTiles: number;
  private regionId: string;
  private cacheHits: number = 0;
  private cacheMisses: number = 0;
  private evictions: number = 0;

  constructor(
    manifest: OfflineMapManifest,
    tileIndex: Record<string, string>,
    maxCachedTiles: number = 16
  ) {
    this.manifest = manifest;
    this.tileIndex = tileIndex || {};
    this.maxCachedTiles = maxCachedTiles;
    this.regionId = manifest.id;
  }

  public isAvailable(): boolean {
    return !!this.manifest && Object.keys(this.tileIndex).length > 0;
  }

  public getLoadedTileCount(): number {
    return this.tileCache.size;
  }

  public getCacheStats(): { hits: number; misses: number; evictions: number; cachedTiles: number } {
    return {
      hits: this.cacheHits,
      misses: this.cacheMisses,
      evictions: this.evictions,
      cachedTiles: this.tileCache.size,
    };
  }

  /**
   * Retrieves a spatial tile from the LRU cache or loads it on-demand.
   */
  private getTile(cellKey: string): Record<string, RoadSegment> | null {
    if (this.tileCache.has(cellKey)) {
      this.cacheHits++;
      // LRU promote: delete and re-insert to move to MRU
      const tileData = this.tileCache.get(cellKey)!;
      this.tileCache.delete(cellKey);
      this.tileCache.set(cellKey, tileData);
      return tileData;
    }

    this.cacheMisses++;

    // Check if cell is present in regional tile index
    const tileRelPath = this.tileIndex[cellKey];
    if (!tileRelPath) {
      return null;
    }

    const tileData = this.loadTileFromDisk(cellKey, tileRelPath);
    if (!tileData) {
      return null;
    }

    // Insert into LRU cache with eviction check
    if (this.tileCache.size >= this.maxCachedTiles) {
      const lruKey = this.tileCache.keys().next().value;
      if (lruKey !== undefined) {
        this.tileCache.delete(lruKey);
        this.evictions++;
      }
    }

    this.tileCache.set(cellKey, tileData);
    return tileData;
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

  /**
   * Platform-agnostic lazy tile loader.
   */
  private loadTileFromDisk(cellKey: string, tileRelPath: string): Record<string, RoadSegment> | null {
    try {
      // 1. Try Node.js fs environment (test runner / staging)
      const fs = this.safeNodeRequire('fs');
      const path = this.safeNodeRequire('path');
      if (fs && path) {
        const candidateBaseDirs = [
          path.resolve(__dirname, '../../../../assets/offline-maps', this.regionId),
          path.resolve(process.cwd(), 'apps/navigation-app/assets/offline-maps', this.regionId),
          path.resolve(process.cwd(), 'assets/offline-maps', this.regionId),
        ];

        for (const baseDir of candidateBaseDirs) {
          const fullPath = path.join(baseDir, tileRelPath);
          if (fs.existsSync(fullPath)) {
            const raw = fs.readFileSync(fullPath, 'utf-8');
            return JSON.parse(raw);
          }
        }
      }


    } catch (e) {
      console.warn(`[TiledOfflineProvider] Error loading tile ${cellKey}:`, e);
    }

    return null;
  }

  /**
   * Retrieves candidate road segments for a lat/lon coordinate in O(1) time using lazy-loaded tiles.
   */
  public async getCandidates(
    latitude: number,
    longitude: number,
    radiusMeters: number
  ): Promise<RoadSegment[]> {
    if (!this.isAvailable()) {
      return [];
    }

    const gridSizeDeg = this.manifest.gridSizeDeg || 0.005;
    const radiusDeg = Math.max(gridSizeDeg, radiusMeters / 111132.92);

    const minLat = latitude - radiusDeg;
    const maxLat = latitude + radiusDeg;
    const minLon = longitude - radiusDeg;
    const maxLon = longitude + radiusDeg;

    const candidateIds = new Set<string>();
    const candidateSegments: RoadSegment[] = [];

    let latCurr = Math.floor(minLat / gridSizeDeg) * gridSizeDeg;
    while (latCurr <= maxLat + 1e-5) {
      let lonCurr = Math.floor(minLon / gridSizeDeg) * gridSizeDeg;
      while (lonCurr <= maxLon + 1e-5) {
        const cellKey = `${latCurr.toFixed(4)}_${lonCurr.toFixed(4)}`;
        const tileData = this.getTile(cellKey);
        if (tileData) {
          for (const segId in tileData) {
            if (!candidateIds.has(segId)) {
              candidateIds.add(segId);
              candidateSegments.push(tileData[segId]);
            }
          }
        }
        lonCurr += gridSizeDeg;
      }
      latCurr += gridSizeDeg;
    }

    return candidateSegments;
  }
}
