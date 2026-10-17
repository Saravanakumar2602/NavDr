#!/usr/bin/env python3
"""
STAGE 4E.2 — SCALABLE OFFLINE OSM ROAD NETWORK PREPROCESSING SCRIPT
Fetches genuine OpenStreetMap road data for any specified bounding box from Overpass API,
filters drivable road classes, parses geometries into 2-point sub-segments, precomputes
a 0.005° spatial grid index, and exports self-describing versioned regional map packages:
  - manifest.json (metadata & bounds)
  - roads.json    (segment geometries)
  - index.json    (spatial grid bucket index)
"""

import argparse
import json
import math
import os
import urllib.request
import urllib.parse
from datetime import datetime

GRID_SIZE_DEG = 0.005  # ~550m x 550m spatial cell size

ACCEPTABLE_HIGHWAYS = {
    'motorway', 'trunk', 'primary', 'secondary', 'tertiary',
    'residential', 'unclassified', 'service'
}

def calculate_initial_bearing(lat1, lon1, lat2, lon2):
    """Calculates initial bearing in degrees between two WGS84 points."""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)

    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
    bearing_rad = math.atan2(y, x)
    return (math.degrees(bearing_rad) + 360.0) % 360.0

def fetch_osm_data(south, west, north, east):
    """Queries Overpass API for drivable road ways and node geometries in the bounding box."""
    overpass_query = f"""
    [out:json][timeout:60];
    (
      way["highway"~"motorway|trunk|primary|secondary|tertiary|residential|unclassified|service"]
         ({south},{west},{north},{east});
    );
    out body;
    >;
    out skel qt;
    """
    url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({'data': overpass_query}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'NavDR-Stage4E2-Preprocessor/2.0'})

    print(f"[OVERPASS] Requesting OSM road data for bbox ({south}, {west}, {north}, {east})...")
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
        return json.loads(content)

def process_osm_to_package(osm_raw, region_id, region_name, south, west, north, east):
    """Parses raw OSM JSON into road segments and spatial grid bucket index."""
    elements = osm_raw.get('elements', [])
    nodes = {}
    ways = []

    for el in elements:
        if el['type'] == 'node':
            nodes[el['id']] = (el['lat'], el['lon'])
        elif el['type'] == 'way':
            ways.append(el)

    print(f"[PREPROCESS] Parsed {len(nodes)} nodes and {len(ways)} road ways.")

    segments = {}
    spatial_index = {}

    segment_counter = 0
    for way in ways:
        tags = way.get('tags', {})
        highway = tags.get('highway', '')
        if highway not in ACCEPTABLE_HIGHWAYS:
            continue

        way_nodes = way.get('nodes', [])
        if len(way_nodes) < 2:
            continue

        coords = []
        for nid in way_nodes:
            if nid in nodes:
                lat, lon = nodes[nid]
                coords.append([lon, lat])  # GeoJSON [longitude, latitude]

        if len(coords) < 2:
            continue

        name = tags.get('name', tags.get('ref', f"Road {way['id']}"))
        one_way = tags.get('oneway') in ['yes', '1', 'true']
        max_speed = None
        if 'maxspeed' in tags:
            try:
                max_speed = float(tags['maxspeed'].split()[0])
            except ValueError:
                pass

        # Split long ways into 2-point sub-segments for fine-grained spatial indexing & matching
        for i in range(len(coords) - 1):
            ptA = coords[i]
            ptB = coords[i + 1]

            heading_deg = calculate_initial_bearing(ptA[1], ptA[0], ptB[1], ptB[0])
            seg_id = f"osm_w{way['id']}_s{i}"

            seg_obj = {
                'id': seg_id,
                'osmWayId': str(way['id']),
                'name': name,
                'coordinates': [ptA, ptB],
                'headingDeg': round(heading_deg, 1),
                'roadType': highway,
                'oneWay': one_way,
            }
            if max_speed:
                seg_obj['speedLimitKmh'] = max_speed

            segments[seg_id] = seg_obj
            segment_counter += 1

            # Populate spatial grid buckets covering segment bounding box
            min_lat = min(ptA[1], ptB[1])
            max_lat = max(ptA[1], ptB[1])
            min_lon = min(ptA[0], ptB[0])
            max_lon = max(ptA[0], ptB[0])

            lat_curr = math.floor(min_lat / GRID_SIZE_DEG) * GRID_SIZE_DEG
            while lat_curr <= max_lat + 1e-5:
                lon_curr = math.floor(min_lon / GRID_SIZE_DEG) * GRID_SIZE_DEG
                while lon_curr <= max_lon + 1e-5:
                    cell_key = f"{lat_curr:.4f}_{lon_curr:.4f}"
                    if cell_key not in spatial_index:
                        spatial_index[cell_key] = []
                    if seg_id not in spatial_index[cell_key]:
                        spatial_index[cell_key].append(seg_id)
                    lon_curr += GRID_SIZE_DEG
                lat_curr += GRID_SIZE_DEG

    manifest = {
        'formatVersion': 1,
        'id': region_id,
        'name': region_name,
        'version': '1.0.0',
        'bounds': {'south': south, 'west': west, 'north': north, 'east': east},
        'roadCount': len(ways),
        'segmentCount': len(segments),
        'spatialCellCount': len(spatial_index),
        'gridSizeDeg': GRID_SIZE_DEG,
        'source': 'OpenStreetMap',
        'generatedAt': datetime.utcnow().isoformat() + 'Z',
        'license': 'ODbL',
    }

    return manifest, segments, spatial_index

def main():
    parser = argparse.ArgumentParser(description='Build modular offline OSM regional map package.')
    parser.add_argument('--id', type=str, default='coimbatore', help='Region ID (e.g. coimbatore)')
    parser.add_argument('--name', type=str, default='Coimbatore Regional', help='Region display name')
    parser.add_argument('--bbox', type=str, default='10.8000,76.9000,11.0500,77.1000', help='Bounding box south,west,north,east')
    parser.add_argument('--format', type=str, choices=['tiled', 'monolithic'], default='tiled', help='Package format (tiled or monolithic)')
    parser.add_argument('--output-dir', type=str, default=None, help='Target output directory path')

    args = parser.parse_args()

    try:
        parts = [float(p.strip()) for p in args.bbox.split(',')]
        south, west, north, east = parts[0], parts[1], parts[2], parts[3]
    except Exception as e:
        print(f"[ERROR] Invalid bbox parameter '{args.bbox}': {e}")
        return

    default_out_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'apps', 'navigation-app', 'assets', 'offline-maps', args.id
    )
    output_dir = args.output_dir if args.output_dir else default_out_dir
    os.makedirs(output_dir, exist_ok=True)

    try:
        raw_osm = fetch_osm_data(south, west, north, east)
    except Exception as e:
        print(f"[ERROR] Failed to fetch OSM data from Overpass API: {e}")
        return

    manifest, segments, spatial_index = process_osm_to_package(raw_osm, args.id, args.name, south, west, north, east)

    manifest_path = os.path.join(output_dir, 'manifest.json')
    index_path = os.path.join(output_dir, 'index.json')

    if args.format == 'tiled':
        manifest['formatVersion'] = 2
        manifest['version'] = '2.0.0'
        manifest['tileCount'] = len(spatial_index)

        tiles_dir = os.path.join(output_dir, 'tiles')
        os.makedirs(tiles_dir, exist_ok=True)

        tile_index = {}
        tile_sizes = []
        total_tile_bytes = 0

        for cell_key, seg_ids in spatial_index.items():
            tile_filename = f"tile_{cell_key}.json"
            tile_rel_path = f"tiles/{tile_filename}"
            tile_full_path = os.path.join(tiles_dir, tile_filename)

            tile_segments = {seg_id: segments[seg_id] for seg_id in seg_ids if seg_id in segments}
            with open(tile_full_path, 'w', encoding='utf-8') as tf:
                json.dump(tile_segments, tf, separators=(',', ':'))

            tile_bytes = os.path.getsize(tile_full_path)
            tile_sizes.append(tile_bytes)
            total_tile_bytes += tile_bytes
            tile_index[cell_key] = tile_rel_path

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(tile_index, f, separators=(',', ':'))

        avg_tile_kb = (sum(tile_sizes) / len(tile_sizes)) / 1024.0 if tile_sizes else 0
        max_tile_kb = max(tile_sizes) / 1024.0 if tile_sizes else 0
        total_pkg_mb = (os.path.getsize(manifest_path) + os.path.getsize(index_path) + total_tile_bytes) / (1024.0 * 1024.0)

        print(f"\n====================================================")
        print(f"  OFFLINE MAP PACKAGE CREATED SUCCESSFULLY (STAGE 4E.3 TILED v2)")
        print(f"====================================================")
        print(f"  Package ID        : {args.id}")
        print(f"  Package Name      : {args.name}")
        print(f"  Format            : Spatial Tile-Based (v2)")
        print(f"  Output Directory  : {output_dir}")
        print(f"  Total Package Size: {total_pkg_mb:.1f} MB")
        print(f"  Tile Count        : {len(spatial_index)}")
        print(f"  Average Tile Size : {avg_tile_kb:.1f} KB")
        print(f"  Largest Tile Size : {max_tile_kb:.1f} KB")
        print(f"  Road Ways Count   : {manifest['roadCount']}")
        print(f"  Segment Sub-Count : {manifest['segmentCount']}")
        print(f"====================================================\n")

    else:
        # Legacy Monolithic v1 Format
        manifest['formatVersion'] = 1
        roads_path = os.path.join(output_dir, 'roads.json')

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        with open(roads_path, 'w', encoding='utf-8') as f:
            json.dump(segments, f, separators=(',', ':'))
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(spatial_index, f, separators=(',', ':'))

        total_size_mb = (os.path.getsize(manifest_path) + os.path.getsize(roads_path) + os.path.getsize(index_path)) / (1024.0 * 1024.0)

        print(f"\n====================================================")
        print(f"  OFFLINE MAP PACKAGE CREATED SUCCESSFULLY (STAGE 4E.2 MONOLITHIC v1)")
        print(f"====================================================")
        print(f"  Package ID        : {args.id}")
        print(f"  Package Name      : {args.name}")
        print(f"  Format            : Monolithic (v1)")
        print(f"  Output Directory  : {output_dir}")
        print(f"  Total Package Size: {total_size_mb:.1f} MB")
        print(f"  Road Ways Count   : {manifest['roadCount']}")
        print(f"  Segment Sub-Count : {manifest['segmentCount']}")
        print(f"  Spatial Cell Count: {manifest['spatialCellCount']}")
        print(f"====================================================\n")

    # Maintain single-file legacy asset coimbatore_regional_osm.json if outputting coimbatore
    if args.id == 'coimbatore':
        legacy_dir = os.path.dirname(output_dir)
        legacy_path = os.path.join(legacy_dir, 'coimbatore_regional_osm.json')
        legacy_package = {
            'metadata': {
                'region': args.name,
                'bounds': {'south': south, 'west': west, 'north': north, 'east': east},
                'extractionDate': manifest['generatedAt'],
                'gridSizeDeg': GRID_SIZE_DEG,
                'roadCount': manifest['roadCount'],
                'segmentCount': manifest['segmentCount'],
                'spatialCellCount': manifest['spatialCellCount'],
            },
            'segments': segments,
            'spatialIndex': spatial_index,
        }
        with open(legacy_path, 'w', encoding='utf-8') as f:
            json.dump(legacy_package, f, separators=(',', ':'))

if __name__ == '__main__':
    main()
