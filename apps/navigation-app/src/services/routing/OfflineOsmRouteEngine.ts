import { Coordinate, Route, RouteSegment as AppRouteSegment } from '../../types/navigation';
import { RouteEngine, RouteCalculationResult } from './RouteEngine';
import { RoadNetworkProvider, RoadSegment as OsmRoadSegment } from '../map/RoadNetworkProvider';
import { offlineMapManager } from '../map/OfflineMapManager';
import { offlineOsmRoadNetworkProvider } from '../map/OfflineOsmRoadNetworkProvider';
import { calculateHaversineDistance } from '../../utils/geo';

interface GraphEdge {
  toNode: string;
  weight: number;
  segmentId: string;
  roadName?: string;
  roadType?: string;
  uLat: number;
  uLon: number;
  vLat: number;
  vLon: number;
}

class PriorityQueue<T> {
  private elements: { element: T; priority: number }[] = [];

  public enqueue(element: T, priority: number): void {
    this.elements.push({ element, priority });
    this.elements.sort((a, b) => a.priority - b.priority);
  }

  public dequeue(): T | undefined {
    return this.elements.shift()?.element;
  }

  public isEmpty(): boolean {
    return this.elements.length === 0;
  }
}

export class OfflineOsmRouteEngine implements RouteEngine {
  private provider: RoadNetworkProvider;

  constructor(provider?: RoadNetworkProvider) {
    if (provider) {
      this.provider = provider;
    } else if (offlineMapManager.isAvailable()) {
      this.provider = offlineMapManager;
    } else {
      this.provider = offlineOsmRoadNetworkProvider;
    }
  }

  public setProvider(provider: RoadNetworkProvider): void {
    this.provider = provider;
  }

  public isAvailable(): boolean {
    return this.provider && this.provider.isAvailable();
  }

  private toNodeKey(lon: number, lat: number): string {
    return `${lon.toFixed(6)},${lat.toFixed(6)}`;
  }

  /**
   * Snaps a lat/lon coordinate to the nearest node/point on candidate road segments.
   */
  private snapToNearestNode(
    lat: number,
    lon: number,
    candidates: OsmRoadSegment[],
    maxRadiusMeters: number = 800
  ): { nodeKey: string; lat: number; lon: number; distanceMeters: number } | null {
    let bestKey: string | null = null;
    let bestLat = 0;
    let bestLon = 0;
    let minDist = Infinity;

    for (const seg of candidates) {
      for (const [sLon, sLat] of seg.coordinates) {
        const d = calculateHaversineDistance(lat, lon, sLat, sLon);
        if (d < minDist && d <= maxRadiusMeters) {
          minDist = d;
          bestKey = this.toNodeKey(sLon, sLat);
          bestLat = sLat;
          bestLon = sLon;
        }
      }
    }

    if (!bestKey || minDist === Infinity) {
      return null;
    }

    return {
      nodeKey: bestKey,
      lat: bestLat,
      lon: bestLon,
      distanceMeters: minDist,
    };
  }

  public async calculateRoute(
    origin: Coordinate,
    destination: Coordinate
  ): Promise<RouteCalculationResult> {
    const t0 = performance.now();

    if (!origin || !destination) {
      return {
        success: false,
        status: 'ERROR',
        error: 'UNKNOWN',
        errorMessage: 'Invalid origin or destination coordinates',
      };
    }

    // Check same origin and destination
    const directDist = calculateHaversineDistance(
      origin.latitude,
      origin.longitude,
      destination.latitude,
      destination.longitude
    );

    if (directDist < 5.0) {
      const pointRoute: Route = {
        id: `route_${Date.now()}`,
        origin,
        destination,
        segments: [],
        geometry: [
          [origin.longitude, origin.latitude],
          [destination.longitude, destination.latitude],
        ],
        distanceMeters: directDist,
      };

      return {
        success: true,
        route: pointRoute,
        status: 'READY',
        calculationTimeMs: performance.now() - t0,
      };
    }

    // Determine query bounding box to fetch candidate road segments
    const centerLat = (origin.latitude + destination.latitude) / 2;
    const centerLon = (origin.longitude + destination.longitude) / 2;
    const searchRadiusMeters = Math.max(directDist / 2 + 1500, 2000);

    const candidateSegments = await this.provider.getCandidates(
      centerLat,
      centerLon,
      searchRadiusMeters
    );

    if (!candidateSegments || candidateSegments.length === 0) {
      return {
        success: false,
        status: 'ERROR',
        error: 'OUTSIDE_OFFLINE_COVERAGE',
        errorMessage: 'Origin or destination is outside installed offline map bounds.',
      };
    }

    // Snap start and end to nearest road network nodes
    const startSnap = this.snapToNearestNode(origin.latitude, origin.longitude, candidateSegments, 1000);
    if (!startSnap) {
      return {
        success: false,
        status: 'ERROR',
        error: 'NO_START_ROAD',
        errorMessage: 'No valid road segment found near start location.',
      };
    }

    const endSnap = this.snapToNearestNode(destination.latitude, destination.longitude, candidateSegments, 1000);
    if (!endSnap) {
      return {
        success: false,
        status: 'ERROR',
        error: 'NO_DESTINATION_ROAD',
        errorMessage: 'No valid road segment found near destination location.',
      };
    }

    // Build directed adjacency graph from candidate OSM segments
    const graph = new Map<string, GraphEdge[]>();
    const nodeCoords = new Map<string, { lat: number; lon: number }>();

    const addEdge = (
      uKey: string,
      vKey: string,
      dist: number,
      seg: OsmRoadSegment,
      uLat: number,
      uLon: number,
      vLat: number,
      vLon: number
    ) => {
      if (!graph.has(uKey)) graph.set(uKey, []);
      graph.get(uKey)!.push({
        toNode: vKey,
        weight: dist,
        segmentId: seg.id,
        roadName: seg.name,
        roadType: seg.roadType,
        uLat,
        uLon,
        vLat,
        vLon,
      });
      nodeCoords.set(uKey, { lat: uLat, lon: uLon });
      nodeCoords.set(vKey, { lat: vLat, lon: vLon });
    };

    for (const seg of candidateSegments) {
      const coords = seg.coordinates;
      for (let i = 0; i < coords.length - 1; i++) {
        const [uLon, uLat] = coords[i];
        const [vLon, vLat] = coords[i + 1];
        const uKey = this.toNodeKey(uLon, uLat);
        const vKey = this.toNodeKey(vLon, vLat);
        const dist = calculateHaversineDistance(uLat, uLon, vLat, vLon);

        addEdge(uKey, vKey, dist, seg, uLat, uLon, vLat, vLon);
        if (!seg.oneWay) {
          addEdge(vKey, uKey, dist, seg, vLat, vLon, uLat, uLon);
        }
      }
    }

    const startKey = startSnap.nodeKey;
    const endKey = endSnap.nodeKey;
    const endCoord = nodeCoords.get(endKey)!;

    // Run A* Search Algorithm
    const frontier = new PriorityQueue<string>();
    frontier.enqueue(startKey, 0);

    const cameFrom = new Map<string, { prevNode: string; edge: GraphEdge }>();
    const costSoFar = new Map<string, number>();

    costSoFar.set(startKey, 0);

    let pathFound = false;

    while (!frontier.isEmpty()) {
      const current = frontier.dequeue()!;

      if (current === endKey) {
        pathFound = true;
        break;
      }

      const neighbors = graph.get(current) || [];
      for (const edge of neighbors) {
        const next = edge.toNode;
        const newCost = costSoFar.get(current)! + edge.weight;

        if (!costSoFar.has(next) || newCost < costSoFar.get(next)!) {
          costSoFar.set(next, newCost);
          const nextCoord = nodeCoords.get(next)!;
          const h = calculateHaversineDistance(
            nextCoord.lat,
            nextCoord.lon,
            endCoord.lat,
            endCoord.lon
          );
          const priority = newCost + h;
          frontier.enqueue(next, priority);
          cameFrom.set(next, { prevNode: current, edge });
        }
      }
    }

    if (!pathFound) {
      return {
        success: false,
        status: 'ERROR',
        error: 'NO_ROUTE',
        errorMessage: 'No connected road path found between start and destination.',
      };
    }

    // Reconstruct Path & Geometry
    let curr = endKey;
    const reversedEdges: GraphEdge[] = [];

    while (curr !== startKey) {
      const parentInfo = cameFrom.get(curr);
      if (!parentInfo) break;
      reversedEdges.push(parentInfo.edge);
      curr = parentInfo.prevNode;
    }

    reversedEdges.reverse();

    // Construct detailed geometry coordinate array [[lon, lat], ...]
    const geometry: [number, number][] = [];
    geometry.push([origin.longitude, origin.latitude]);

    let routeDistanceMeters = 0;
    const routeSegments: AppRouteSegment[] = [];

    for (let i = 0; i < reversedEdges.length; i++) {
      const edge = reversedEdges[i];
      if (i === 0) {
        geometry.push([edge.uLon, edge.uLat]);
      }
      geometry.push([edge.vLon, edge.vLat]);
      routeDistanceMeters += edge.weight;

      routeSegments.push({
        id: edge.segmentId,
        name: edge.roadName,
        coordinates: [
          [edge.uLon, edge.uLat],
          [edge.vLon, edge.vLat],
        ],
        distanceMeters: edge.weight,
        roadType: edge.roadType,
      });
    }

    geometry.push([destination.longitude, destination.latitude]);

    const generatedRoute: Route = {
      id: `route_${Date.now()}`,
      origin,
      destination,
      segments: routeSegments,
      geometry,
      distanceMeters: Math.round(routeDistanceMeters),
    };

    return {
      success: true,
      route: generatedRoute,
      status: 'READY',
      calculationTimeMs: parseFloat((performance.now() - t0).toFixed(2)),
    };
  }
}

export const offlineOsmRouteEngine = new OfflineOsmRouteEngine();
