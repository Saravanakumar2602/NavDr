/**
 * STAGE 4D.1 MAP MATCHER UNIT TEST SUITE
 * Verifies segment projection, circular heading wrap, candidate scoring, hysteresis, and fallback behavior.
 */

import { MapMatcher } from '../apps/navigation-app/src/services/map/MapMatcher';
import { TestFixtureRoadNetworkProvider } from '../apps/navigation-app/src/services/map/TestFixtureRoadNetworkProvider';
import { UnavailableRoadNetworkProvider } from '../apps/navigation-app/src/services/map/UnavailableRoadNetworkProvider';
import { OfflineOsmRoadNetworkProvider } from '../apps/navigation-app/src/services/map/OfflineOsmRoadNetworkProvider';
import { OfflineMapManager } from '../apps/navigation-app/src/services/map/OfflineMapManager';
import { DrPose } from '../apps/navigation-app/src/types/navigation';

declare const require: any;
declare const process: any;

async function runMapMatcherTests() {
  console.log('====================================================');
  console.log('   NAVDR STAGE 4D.1 — MAP MATCHER UNIT TEST SUITE');
  console.log('====================================================\n');

  let passedTests = 0;
  let totalTests = 0;

  function assert(condition: boolean, testName: string, detail?: string) {
    totalTests++;
    if (condition) {
      passedTests++;
      console.log(`  ✅ [PASS] ${testName}${detail ? ` (${detail})` : ''}`);
    } else {
      console.error(`  ❌ [FAIL] ${testName}${detail ? ` (${detail})` : ''}`);
    }
  }

  const testProvider = new TestFixtureRoadNetworkProvider();
  const unavailableProvider = new UnavailableRoadNetworkProvider();
  const matcher = new MapMatcher(testProvider);

  // TEST 1: Circular Heading Error Calculation (0° / 360° Wrap)
  console.log('[TEST GROUP 1] Circular Angular Heading Difference');
  const hErr1 = matcher.calculateCircularHeadingError(359, 1);
  assert(hErr1 === 2, '359° vs 1° wrap error', `expected 2°, got ${hErr1}°`);

  const hErr2 = matcher.calculateCircularHeadingError(0, 180);
  assert(hErr2 === 180, '0° vs 180° error', `expected 180°, got ${hErr2}°`);

  const hErr3 = matcher.calculateCircularHeadingError(10, 350);
  assert(hErr3 === 20, '10° vs 350° wrap error', `expected 20°, got ${hErr3}°`);

  // TEST 2: Local ENU Metric Segment Projection
  console.log('\n[TEST GROUP 2] Local ENU Metric Segment Projection');
  // Segment A(12.9716, 77.5946) -> B(12.9750, 77.5946) [Northbound]
  // Point P(12.9730, 77.5947) [~10.8m East of line]
  const proj = matcher.projectPointToSegment(12.9730, 77.5947, 12.9716, 77.5946, 12.9750, 77.5946);
  assert(Math.abs(proj.lat - 12.9730) < 0.0001, 'Projection latitude matches perpendicular point');
  assert(Math.abs(proj.lon - 77.5946) < 0.00001, 'Projection longitude snaps to segment longitude');
  assert(proj.distanceMeters > 9.0 && proj.distanceMeters < 12.0, 'Metric distance to road ~10.8m', `got ${proj.distanceMeters.toFixed(1)}m`);

  // TEST 3: Nearest Road Selection & Successful Map Match
  console.log('\n[TEST GROUP 3] Nearest Road Candidate Selection');
  matcher.reset();
  const drPose1: DrPose = {
    latitude: 12.9730,
    longitude: 77.59462, // Very close to SEG_MAIN_AVE_01 (~2.1m East)
    headingDeg: 2,       // Northbound, consistent with SEG_MAIN_AVE_01 (0°)
    speedMps: 12.5,
    velocityMps: 12.5,
    eastM: 0,
    northM: 0,
    timestamp: Date.now(),
    confidence: 0.9,
    valid: true,
    drDurationMs: 5000,
    drDistanceMeters: 50,
    motionMode: 'GENERAL_MOTION',
  };

  const matched1 = await matcher.processPose(drPose1);
  assert(matched1.source === 'MAP_MATCHED', 'Match status is MAP_MATCHED');
  assert(matched1.matchedSegmentId === 'SEG_MAIN_AVE_01', 'Matched correct road segment SEG_MAIN_AVE_01');
  assert(matched1.confidence === 'HIGH', 'Match confidence is HIGH', `score=${matched1.confidenceScore.toFixed(2)}`);

  // TEST 4: Heading Mismatch Penalty
  console.log('\n[TEST GROUP 4] Heading Mismatch Penalty');
  matcher.reset();
  const drPoseHeadingMismatch: DrPose = {
    ...drPose1,
    headingDeg: 180, // Southbound on one-way Northbound SEG_MAIN_AVE_01 (180° mismatch)
  };
  const matchedHeadingMismatch = await matcher.processPose(drPoseHeadingMismatch);
  assert(matchedHeadingMismatch.source === 'RAW_DR', 'Heading mismatch rejects candidate and falls back to RAW_DR');

  // TEST 5: Hysteresis / Segment Continuity Preference
  console.log('\n[TEST GROUP 5] Hysteresis Continuity Preference');
  matcher.reset();
  // First match to SEG_MAIN_AVE_01
  await matcher.processPose(drPose1);

  // Position equidistant between SEG_MAIN_AVE_01 and SEG_PARALLEL_RD_03
  const drPoseEquidistant: DrPose = {
    ...drPose1,
    longitude: 77.59485, // Midpoint between 77.5946 and 77.5951
  };
  const matchedHysteresis = await matcher.processPose(drPoseEquidistant);
  assert(matchedHysteresis.matchedSegmentId === 'SEG_MAIN_AVE_01', 'Hysteresis maintains previous road segment SEG_MAIN_AVE_01');

  // TEST 6: Unavailable Road Provider Fallback
  console.log('\n[TEST GROUP 6] Unavailable Road Provider Fallback (Production Mode)');
  const unavailableMatcher = new MapMatcher(unavailableProvider);
  const matchedUnavailable = await unavailableMatcher.processPose(drPose1);
  assert(matchedUnavailable.source === 'RAW_DR', 'Fallback pose source is RAW_DR');
  assert(matchedUnavailable.confidence === 'UNAVAILABLE', 'Fallback pose confidence is UNAVAILABLE');
  assert(matchedUnavailable.latitude === drPose1.latitude, 'Preserves raw latitude');
  assert(matchedUnavailable.longitude === drPose1.longitude, 'Preserves raw longitude');

  // TEST 7: Distant Out-of-Bounds Rejection
  console.log('\n[TEST GROUP 7] Out-of-Bounds / Distant Road Rejection');
  matcher.reset();
  const drPoseDistant: DrPose = {
    ...drPose1,
    latitude: 12.9000, // Very far away (> 5km)
    longitude: 77.5000,
  };
  const matchedDistant = await matcher.processPose(drPoseDistant);
  assert(matchedDistant.source === 'RAW_DR', 'Distant pose (>35m) returns RAW_DR fallback');

  // TEST 8: Real Offline OSM Provider (Sri Eshwar / Coimbatore Region)
  console.log('\n[TEST GROUP 8] Real Offline OSM Provider (Sri Eshwar / Coimbatore Region)');
  const realOsmProvider = new OfflineOsmRoadNetworkProvider();

  assert(realOsmProvider.isAvailable() === true, 'Real Offline OSM dataset loaded successfully from local asset');

  const meta = realOsmProvider.getMetadata();
  assert(meta !== null && meta.segmentCount > 0, 'OSM metadata validated', `segmentCount=${meta?.segmentCount}, gridCells=${meta?.spatialCellCount}`);

  // Test position directly on real OSM segment osm_w131226571_s32 (Kinathukadavu - Cochin Frontier Road)
  const realOsmCandidates = await realOsmProvider.getCandidates(10.8284159, 77.0096874, 35.0);
  assert(realOsmCandidates.length > 0, 'O(1) Spatial bucket index returned candidate OSM roads', `got ${realOsmCandidates.length} candidate segments`);

  const realOsmMatcher = new MapMatcher(realOsmProvider);
  const drPoseSriEshwar: DrPose = {
    latitude: 10.8284159,
    longitude: 77.0096874,
    headingDeg: 245.0,
    speedMps: 15.0,
    velocityMps: 15.0,
    eastM: 0,
    northM: 0,
    timestamp: Date.now(),
    confidence: 0.9,
    valid: true,
    drDurationMs: 8000,
    drDistanceMeters: 120,
    motionMode: 'GENERAL_MOTION',
  };

  // TEST 9: OfflineMapManager Discovery, Manifest Parsing & Bounds Matching (Stage 4E.2)
  console.log('\n[TEST GROUP 9] OfflineMapManager Discovery, Manifest Parsing & Bounds Matching (Stage 4E.2)');
  const manager = new OfflineMapManager();

  const installed = manager.getInstalledRegions();
  assert(installed.length > 0, 'OfflineMapManager discovered installed regional map packages', `installedCount=${installed.length}`);
  const activeRegion = manager.getActiveRegion();
  assert(activeRegion !== null && activeRegion.id === 'coimbatore', 'Active region initialized to coimbatore', `activeRegionId=${activeRegion?.id}`);
  assert(activeRegion?.roadCount === 28700, 'Manifest road count matches (28,700 roads)', `roadCount=${activeRegion?.roadCount}`);

  const regionAtSriEshwar = manager.findRegionForLocation(10.8284159, 77.0096874);
  assert(regionAtSriEshwar !== null && regionAtSriEshwar.id === 'coimbatore', 'findRegionForLocation matched coordinate to coimbatore bounds');

  const regionAtDelhi = manager.findRegionForLocation(28.6139, 77.2090);
  assert(regionAtDelhi === null, 'findRegionForLocation returned null for out-of-bounds Delhi coordinate');

  // TEST 10: Multi-Region Active Handoff, Out-of-Bounds Fallback & MapMatcher Decoupling
  console.log('\n[TEST GROUP 10] Multi-Region Active Handoff, Out-of-Bounds Fallback & MapMatcher Decoupling');
  
  // Register dynamic mock second region (Chennai)
  manager.registerRegion({
    formatVersion: 1,
    id: 'chennai-test',
    name: 'Chennai Test Region',
    version: '1.0.0',
    bounds: { south: 12.9000, west: 80.1000, north: 13.2000, east: 80.3000 },
    roadCount: 500,
    segmentCount: 1500,
    spatialCellCount: 40,
    gridSizeDeg: 0.005,
    source: 'OpenStreetMap',
    generatedAt: new Date().toISOString(),
    license: 'ODbL',
  });

  assert(manager.getInstalledRegions().length >= 2, 'Registry contains multiple regions (Coimbatore & Chennai)');
  const regionAtChennai = manager.findRegionForLocation(13.0827, 80.2707);
  assert(regionAtChennai !== null && regionAtChennai.id === 'chennai-test', 'findRegionForLocation dynamically located Chennai region');

  // MapMatcher Decoupling Test: MapMatcher uses manager strictly via RoadNetworkProvider contract
  const managerMatcher = new MapMatcher(manager);
  const matchedSriEshwar = await managerMatcher.processPose(drPoseSriEshwar);
  assert(matchedSriEshwar.source === 'MAP_MATCHED', 'MapMatcher works seamlessly via OfflineMapManager provider');

  // Test Out-of-Bounds coordinate (New Delhi)
  const drPoseDelhi: DrPose = {
    latitude: 28.6139,
    longitude: 77.2090,
    headingDeg: 90.0,
    speedMps: 20.0,
    velocityMps: 20.0,
    eastM: 0,
    northM: 0,
    timestamp: Date.now(),
    confidence: 0.8,
    valid: true,
    drDurationMs: 5000,
    drDistanceMeters: 100,
    motionMode: 'GENERAL_MOTION',
  };

  const matchedDelhi = await managerMatcher.processPose(drPoseDelhi);
  assert(matchedDelhi.source === 'RAW_DR', 'Out-of-bounds pose returns RAW_DR fallback');
  assert(matchedDelhi.confidence === 'UNAVAILABLE', 'Out-of-bounds pose confidence is UNAVAILABLE');
  assert(matchedDelhi.latitude === 28.6139 && matchedDelhi.longitude === 77.2090, 'Out-of-bounds pose preserves raw DR position');

  // TEST 11: Tiled Format v2 Manifest Parsing & Lazy Loading (Stage 4E.3)
  console.log('\n[TEST GROUP 11] Tiled Format v2 Manifest Parsing & Lazy Loading (Stage 4E.3)');
  const activeTiledProvider = manager.getActiveTiledProvider();
  assert(activeTiledProvider !== null, 'OfflineMapManager initialized active TiledOfflineOsmRoadNetworkProvider for formatVersion 2');

  const candidatesSriEshwar = await manager.getCandidates(10.8284159, 77.0096874, 50);
  assert(candidatesSriEshwar.length > 0, 'Lazy tile provider returned candidate road segments on demand', `candidateCount=${candidatesSriEshwar.length}`);
  const cacheStats1 = activeTiledProvider?.getCacheStats();
  assert(cacheStats1 !== undefined && cacheStats1.cachedTiles > 0, 'LRU cache populated after on-demand tile lookup', `cachedTiles=${cacheStats1?.cachedTiles}`);

  // TEST 12: LRU Tile Cache Eviction & Bounded Memory (Stage 4E.3)
  console.log('\n[TEST GROUP 12] LRU Tile Cache Eviction & Bounded Memory (Stage 4E.3)');
  const mockManifest: any = {
    formatVersion: 2,
    id: 'coimbatore',
    name: 'Coimbatore',
    version: '2.0.0',
    bounds: { south: 10.8, west: 76.9, north: 11.05, east: 77.1 },
    roadCount: 100,
    segmentCount: 500,
    spatialCellCount: 10,
    gridSizeDeg: 0.005,
    source: 'OSM',
    generatedAt: new Date().toISOString(),
    license: 'ODbL',
  };

  const fs = require('fs');
  const path = require('path');
  const indexPathResolved = path.resolve(process.cwd(), 'apps/navigation-app/assets/offline-maps/coimbatore/index.json');
  const coimbatoreIndexRaw = JSON.parse(fs.readFileSync(indexPathResolved, 'utf-8'));
  const { TiledOfflineOsmRoadNetworkProvider } = require('../apps/navigation-app/src/services/map/TiledOfflineOsmRoadNetworkProvider');
  
  // Create small LRU cache with limit of 4 tiles
  const smallCacheProvider = new TiledOfflineOsmRoadNetworkProvider(mockManifest, coimbatoreIndexRaw, 4);

  // Query 6 distinct tile coordinates across Coimbatore region
  const coordsToQuery = [
    [10.805, 76.905],
    [10.815, 76.915],
    [10.825, 76.925],
    [10.835, 76.935],
    [10.845, 76.945],
    [10.855, 76.955],
  ];

  for (const [lat, lon] of coordsToQuery) {
    await smallCacheProvider.getCandidates(lat, lon, 20);
  }

  const smallStats = smallCacheProvider.getCacheStats();
  assert(smallStats.cachedTiles <= 4, 'LRU cache size bounded strictly to max limit (4 tiles)', `cachedTiles=${smallStats.cachedTiles}`);
  assert(smallStats.evictions > 0, 'LRU cache evicted least-recently used tiles upon reaching capacity', `evictions=${smallStats.evictions}`);

  // TEST 13: Cross-Tile Boundary Road Segment Candidate Test (Stage 4E.3)
  console.log('\n[TEST GROUP 13] Cross-Tile Boundary Road Segment Candidate Test (Stage 4E.3)');
  // Create mock tile provider with a road segment spanning boundary cell 10.8250_77.0050 and 10.8250_77.0100
  const crossBoundarySegment = {
    id: 'CROSS_TILE_ROAD_01',
    osmWayId: '99999',
    name: 'Cross Boundary Expressway',
    coordinates: [[77.0048, 10.8252], [77.0102, 10.8252]], // Crosses 77.0050 boundary
    headingDeg: 90.0,
    roadType: 'primary',
    oneWay: false,
  };

  const tileCellWest = { 'CROSS_TILE_ROAD_01': crossBoundarySegment };
  const tileCellEast = { 'CROSS_TILE_ROAD_01': crossBoundarySegment };

  const crossBoundaryProvider = new TiledOfflineOsmRoadNetworkProvider(mockManifest, {
    '10.8250_77.0050': 'tiles/tile_west.json',
    '10.8250_77.0100': 'tiles/tile_east.json',
  }, 10);

  // Directly inject test tiles into cache to test candidate retrieval near boundary
  (crossBoundaryProvider as any).tileCache.set('10.8250_77.0050', tileCellWest);
  (crossBoundaryProvider as any).tileCache.set('10.8250_77.0100', tileCellEast);

  const candidatesWestSide = await crossBoundaryProvider.getCandidates(10.8252, 77.0049, 10);
  const candidatesEastSide = await crossBoundaryProvider.getCandidates(10.8252, 77.0101, 10);

  assert(
    candidatesWestSide.some((s: any) => s.id === 'CROSS_TILE_ROAD_01'),
    'Cross-boundary road candidate returned on West side of boundary'
  );
  assert(
    candidatesEastSide.some((s: any) => s.id === 'CROSS_TILE_ROAD_01'),
    'Cross-boundary road candidate returned on East side of boundary'
  );

  // TEST 14: Missing Tile Degraded Fallback & Format v1/v2 Compatibility (Stage 4E.3)
  console.log('\n[TEST GROUP 14] Missing Tile Fallback & v1/v2 Format Compatibility (Stage 4E.3)');
  const candidatesMissingTile = await smallCacheProvider.getCandidates(10.0000, 70.0000, 50);
  assert(candidatesMissingTile.length === 0, 'Missing/unmapped tile safely returns [] candidates without throwing');

  // Verify format v1 legacy package backward compatibility
  manager.registerRegion({
    formatVersion: 1,
    id: 'legacy-v1-test',
    name: 'Legacy v1 Test Package',
    version: '1.0.0',
    bounds: { south: 11.0, west: 78.0, north: 11.2, east: 78.2 },
    roadCount: 10,
    segmentCount: 20,
    spatialCellCount: 2,
    gridSizeDeg: 0.005,
    source: 'OSM',
    generatedAt: new Date().toISOString(),
    license: 'ODbL',
  });

  const legacyInstalled = manager.getInstalledRegions().find(r => r.id === 'legacy-v1-test');
  assert(legacyInstalled !== undefined && legacyInstalled.formatVersion === 1, 'OfflineMapManager seamlessly registers formatVersion 1 legacy package');

  console.log('\n====================================================');
  console.log(`  RESULTS: ${passedTests} / ${totalTests} TESTS PASSED`);
  console.log('====================================================\n');

  if (passedTests === totalTests) {
    process.exit(0);
  } else {
    process.exit(1);
  }
}

runMapMatcherTests().catch((err) => {
  console.error('Test runner exception:', err);
  process.exit(1);
});
