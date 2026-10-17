import { RoadNetworkProvider, RoadSegment } from './RoadNetworkProvider';
import { TiledOfflineOsmRoadNetworkProvider } from './TiledOfflineOsmRoadNetworkProvider';
import { offlineOsmRoadNetworkProvider } from './OfflineOsmRoadNetworkProvider';
import { OfflineMapManifest, OfflineRegionBounds } from '../../types/navigation';

declare const require: any;
declare const process: any;
declare const __dirname: string;

interface LoadedLegacyRegionData {
  manifest: OfflineMapManifest;
  roads: Record<string, RoadSegment>;
  spatialIndex: Record<string, string[]>;
}

/**
 * Stage 4E.3 — Scalable Offline Map Packaging & Regional Tile Manager.
 * Implements RoadNetworkProvider. Supports both Format v1 (monolithic) and Format v2 (tiled).
 * Manages discovery, geographic bounds matching, active region loading/unloading, LRU tile caching,
 * and seamless active region handoffs.
 * 100% Decoupled from MapMatcher (MapMatcher only interacts with RoadNetworkProvider).
 */
export class OfflineMapManager implements RoadNetworkProvider {
  private registry: Map<string, OfflineMapManifest> = new Map();
  private loadedLegacyRegions: Map<string, LoadedLegacyRegionData> = new Map();
  private loadedTiledProviders: Map<string, TiledOfflineOsmRoadNetworkProvider> = new Map();
  private activeRegionId: string | null = null;

  constructor() {
    this.discoverInstalledRegions();
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
   * Discovers installed regional map packages locally.
   */
  private discoverInstalledRegions(): void {
    try {
      // 1. Try React Native require of Coimbatore manifest
      try {
        const coimbatoreManifest: OfflineMapManifest = require('../../../assets/offline-maps/coimbatore/manifest.json');
        if (coimbatoreManifest && coimbatoreManifest.id) {
          this.registerRegion(coimbatoreManifest);
        }
      } catch (err) {
        // Fall back to Node fs discovery if running in test environment
        const fs = this.safeNodeRequire('fs');
        const path = this.safeNodeRequire('path');
        if (fs && path) {
          const candidateBaseDirs = [
            path.resolve(__dirname, '../../../../assets/offline-maps'),
            path.resolve(process.cwd(), 'apps/navigation-app/assets/offline-maps'),
            path.resolve(process.cwd(), 'assets/offline-maps'),
          ];

          for (const baseDir of candidateBaseDirs) {
            if (fs.existsSync(baseDir)) {
              const entries = fs.readdirSync(baseDir);
              for (const entry of entries) {
                const manifestPath = path.join(baseDir, entry, 'manifest.json');
                if (fs.existsSync(manifestPath)) {
                  const manifestRaw = fs.readFileSync(manifestPath, 'utf-8');
                  const manifest: OfflineMapManifest = JSON.parse(manifestRaw);
                  if (manifest && manifest.id) {
                    this.registerRegion(manifest);
                  }
                }
              }
            }
          }
        }
      }
    } catch (e) {
      console.warn('[OfflineMapManager] Error discovering regional map packages:', e);
    }
  }

  /**
   * Registers a discovered region manifest in the registry.
   */
  public registerRegion(manifest: OfflineMapManifest): void {
    if (!manifest || !manifest.id) return;
    this.registry.set(manifest.id, manifest);
    // If no active region is loaded yet, load this region as default
    if (!this.activeRegionId) {
      this.loadRegion(manifest.id);
    }
  }

  /**
   * Returns manifests of all installed regional packages.
   */
  public getInstalledRegions(): OfflineMapManifest[] {
    return Array.from(this.registry.values());
  }

  /**
   * Returns currently active region manifest or null.
   */
  public getActiveRegion(): OfflineMapManifest | null {
    if (!this.activeRegionId) return null;
    return this.registry.get(this.activeRegionId) || null;
  }

  /**
   * Returns currently active tiled provider or null.
   */
  public getActiveTiledProvider(): TiledOfflineOsmRoadNetworkProvider | null {
    if (!this.activeRegionId) return null;
    return this.loadedTiledProviders.get(this.activeRegionId) || null;
  }

  /**
   * Performs 2D geographic bounding box coordinate check to find installed region covering coordinate.
   */
  public findRegionForLocation(latitude: number, longitude: number): OfflineMapManifest | null {
    for (const manifest of this.registry.values()) {
      if (this.isCoordinateInBounds(latitude, longitude, manifest.bounds)) {
        return manifest;
      }
    }
    return null;
  }

  /**
   * Checks if a lat/lon coordinate falls inside bounding box bounds.
   */
  private isCoordinateInBounds(lat: number, lon: number, bounds: OfflineRegionBounds): boolean {
    if (!bounds) return false;
    return (
      lat >= bounds.south &&
      lat <= bounds.north &&
      lon >= bounds.west &&
      lon <= bounds.east
    );
  }

  /**
   * Loads regional map data (Format v2 tiled or Format v1 legacy monolithic).
   */
  public async loadRegion(regionId: string): Promise<boolean> {
    if (this.loadedTiledProviders.has(regionId) || this.loadedLegacyRegions.has(regionId)) {
      this.activeRegionId = regionId;
      return true;
    }

    const manifest = this.registry.get(regionId);
    if (!manifest) {
      console.warn(`[OfflineMapManager] Cannot load unregistered region: ${regionId}`);
      return false;
    }

    try {
      // FORMAT v2 (Tiled) Loading Strategy
      if (manifest.formatVersion === 2) {
        let tileIndex: Record<string, string> | null = null;
        try {
          if (regionId === 'coimbatore') {
            tileIndex = require('../../../assets/offline-maps/coimbatore/index.json');
          }
        } catch (rnErr) {
          const fs = this.safeNodeRequire('fs');
          const path = this.safeNodeRequire('path');
          if (fs && path) {
            const candidateBaseDirs = [
              path.resolve(__dirname, '../../../../assets/offline-maps', regionId),
              path.resolve(process.cwd(), 'apps/navigation-app/assets/offline-maps', regionId),
              path.resolve(process.cwd(), 'assets/offline-maps', regionId),
            ];
            for (const regionDir of candidateBaseDirs) {
              const indexPath = path.join(regionDir, 'index.json');
              if (fs.existsSync(indexPath)) {
                tileIndex = JSON.parse(fs.readFileSync(indexPath, 'utf-8'));
                break;
              }
            }
          }
        }

        if (tileIndex) {
          const tiledProvider = new TiledOfflineOsmRoadNetworkProvider(manifest, tileIndex);
          this.loadedTiledProviders.set(regionId, tiledProvider);
          this.activeRegionId = regionId;
          return true;
        }
      }

      // FORMAT v1 (Legacy Monolithic) Fallback Strategy
      let roads: Record<string, RoadSegment> | null = null;
      let spatialIndex: Record<string, string[]> | null = null;

      try {
        if (regionId === 'coimbatore') {
          roads = require('../../../assets/offline-maps/coimbatore/roads.json');
          spatialIndex = require('../../../assets/offline-maps/coimbatore/index.json');
        }
      } catch (err) {
        // Node.js fs fallback
        const fs = this.safeNodeRequire('fs');
        const path = this.safeNodeRequire('path');
        if (fs && path) {
          const candidateBaseDirs = [
            path.resolve(__dirname, '../../../../assets/offline-maps', regionId),
            path.resolve(process.cwd(), 'apps/navigation-app/assets/offline-maps', regionId),
            path.resolve(process.cwd(), 'assets/offline-maps', regionId),
          ];

          for (const regionDir of candidateBaseDirs) {
            const roadsFile = path.join(regionDir, 'roads.json');
            const indexFile = path.join(regionDir, 'index.json');
            if (fs.existsSync(roadsFile) && fs.existsSync(indexFile)) {
              roads = JSON.parse(fs.readFileSync(roadsFile, 'utf-8'));
              spatialIndex = JSON.parse(fs.readFileSync(indexFile, 'utf-8'));
              break;
            }
          }
        }
      }

      if (roads && spatialIndex) {
        this.loadedLegacyRegions.set(regionId, { manifest, roads, spatialIndex });
        this.activeRegionId = regionId;
        return true;
      }
    } catch (e) {
      console.error(`[OfflineMapManager] Failed to load region ${regionId}:`, e);
    }

    return false;
  }

  /**
   * Unloads region data from memory.
   */
  public unloadRegion(regionId: string): void {
    this.loadedLegacyRegions.delete(regionId);
    this.loadedTiledProviders.delete(regionId);
    if (this.activeRegionId === regionId) {
      this.activeRegionId = null;
    }
  }

  /**
   * RoadNetworkProvider implementation check.
   */
  public isAvailable(): boolean {
    if (!this.activeRegionId) return false;
    const tiled = this.loadedTiledProviders.get(this.activeRegionId);
    if (tiled) return tiled.isAvailable();

    const legacy = this.loadedLegacyRegions.get(this.activeRegionId);
    return !!legacy && Object.keys(legacy.roads).length > 0;
  }

  /**
   * Retrieves candidate road segments for a lat/lon coordinate in O(1) time.
   * Performs automatic active region handoff if position moves into another registered region.
   * Returns [] if position is out-of-bounds of all registered regions (falling back to RAW_DR).
   */
  public async getCandidates(
    latitude: number,
    longitude: number,
    radiusMeters: number
  ): Promise<RoadSegment[]> {
    // 1. Check if position is inside currently active region bounds
    let activeRegion = this.getActiveRegion();
    if (!activeRegion || !this.isCoordinateInBounds(latitude, longitude, activeRegion.bounds)) {
      // Position is outside active region bounds. Find covering region in registry.
      const targetManifest = this.findRegionForLocation(latitude, longitude);
      if (targetManifest) {
        // Perform clean regional handoff
        const loaded = await this.loadRegion(targetManifest.id);
        if (loaded) {
          activeRegion = targetManifest;
        } else {
          return []; // Handoff load failed
        }
      } else {
        // Out of bounds of all registered regions: fall back to RAW_DR
        return [];
      }
    }

    // 2. Format v2 (Tiled Provider) delegate
    const tiledProvider = this.loadedTiledProviders.get(activeRegion.id);
    if (tiledProvider) {
      const tiledCandidates = await tiledProvider.getCandidates(latitude, longitude, radiusMeters);
      if (tiledCandidates && tiledCandidates.length > 0) {
        return tiledCandidates;
      }
    }

    // 3. Fallback to monolithic OfflineOsmRoadNetworkProvider
    if (offlineOsmRoadNetworkProvider.isAvailable()) {
      const fallbackCandidates = await offlineOsmRoadNetworkProvider.getCandidates(latitude, longitude, radiusMeters);
      if (fallbackCandidates && fallbackCandidates.length > 0) {
        return fallbackCandidates;
      }
    }

    // 3. Format v1 (Legacy Monolithic) candidate lookup
    const loadedData = this.loadedLegacyRegions.get(activeRegion.id);
    if (!loadedData || !loadedData.roads || !loadedData.spatialIndex) {
      return [];
    }

    const gridSizeDeg = activeRegion.gridSizeDeg || 0.005;
    const radiusDeg = Math.max(gridSizeDeg, radiusMeters / 111132.92);

    const minLat = latitude - radiusDeg;
    const maxLat = latitude + radiusDeg;
    const minLon = longitude - radiusDeg;
    const maxLon = longitude + radiusDeg;

    const candidateIds = new Set<string>();

    let latCurr = Math.floor(minLat / gridSizeDeg) * gridSizeDeg;
    while (latCurr <= maxLat + 1e-5) {
      let lonCurr = Math.floor(minLon / gridSizeDeg) * gridSizeDeg;
      while (lonCurr <= maxLon + 1e-5) {
        const cellKey = `${latCurr.toFixed(4)}_${lonCurr.toFixed(4)}`;
        const cellSegIds = loadedData.spatialIndex[cellKey];
        if (cellSegIds) {
          for (let i = 0; i < cellSegIds.length; i++) {
            candidateIds.add(cellSegIds[i]);
          }
        }
        lonCurr += gridSizeDeg;
      }
      latCurr += gridSizeDeg;
    }

    const candidateSegments: RoadSegment[] = [];
    candidateIds.forEach((id) => {
      const seg = loadedData.roads[id];
      if (seg) {
        candidateSegments.push(seg);
      }
    });

    return candidateSegments;
  }
}

export const offlineMapManager = new OfflineMapManager();
