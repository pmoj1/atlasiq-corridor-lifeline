"""Spherical point distances to a mapped rail line, measured in kilometres."""

from functools import lru_cache
from pathlib import Path
import json
import math

from .locations import EARTH_RADIUS_KM, _angular_distance, _segment_distance


def position(xy):
    lon, lat = xy[:2]
    if any(isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n)
           for n in (lon, lat)) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError('Invalid longitude or latitude')
    return {'lat': lat, 'lon': lon}


def point_distance(a, b):
    return EARTH_RADIUS_KM * _angular_distance(a['lat'], a['lon'], b['lat'], b['lon'])


def route_blocks(path):
    features = json.loads(path.read_bytes())['features']
    blocks = []
    for index, feature in enumerate(features):
        geometry = feature['geometry']
        coords = geometry['coordinates']
        if geometry['type'] == 'LineString':
            coords = [coords]
        elif geometry['type'] != 'MultiLineString':
            raise ValueError('Expected only line features')
        for part in coords:
            points = [position(xy) for xy in part]
            if len(points) < 2:
                raise ValueError('Empty or single-point rail part')
            for start in range(0, len(points) - 1, 64):
                chunk = points[start:start + 65]
                edges = list(zip(chunk, chunk[1:]))
                # The full arc length bounds every point on this chunk from its start.
                radius = sum(point_distance(a, b) for a, b in edges)
                blocks.append((chunk[0], radius, index, edges))
    if not blocks:
        raise ValueError('No mapped rail segments')
    return blocks, [f.get('properties', {}) for f in features]


def nearest(point, blocks):
    lower_bounds = [(point_distance(point, anchor) - radius, i)
                    for i, (anchor, radius, _, _) in enumerate(blocks)]
    best = math.inf
    for lower, i in sorted(lower_bounds):
        if lower > best + 1e-8:
            break
        _, _, index, edges = blocks[i]
        for a, b in edges:
            distance = _segment_distance(point['lat'], point['lon'], a, b)
            if distance < best:
                best, match = distance, (index, a, b)
    return best, match

ROUTE_PATH = Path(__file__).resolve().parent.parent / 'research/rail-replay/route.geojson'


@lru_cache(maxsize=1)
def reviewed_route():
    return route_blocks(ROUTE_PATH)


def mapped_screen(lon, lat):
    blocks, sections = reviewed_route()
    distance, (index, _, _) = nearest(position([lon, lat]), blocks)
    section = sections[index]
    return {'section': section['section'], 'object_id': section['OBJECTID'],
            'distance_km': round(distance, 3), 'within_screening_buffer': distance <= 50}
