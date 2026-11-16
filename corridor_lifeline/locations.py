"""Offline geographic screening against a deliberately schematic corridor.

This geometry is not a surveyed track alignment. Proximity says nothing about
freight connections, monitoring coverage, or current operational conditions.
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

EARTH_RADIUS_KM = 6371.0088
CATALOG_PATH = Path(__file__).resolve().parent.parent / 'config' / 'locations.json'
LIMITATIONS = [
    'Approximate place coordinates joined by straight schematic segments; not surveyed rail alignment.',
    'Distance is a geographic screening estimate, not track distance, road access or freight routing.',
    'Inside the buffer does not establish monitoring coverage, a mine connection or rail operating status.',
    'The 50 km default buffer is an illustrative screening choice, not an operational safety boundary.',
]


def _number(value, name, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name} must be a finite number')
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f'{name} must be between {minimum} and {maximum}')
    return float(value)


def _validate_catalog(catalog):
    if not isinstance(catalog, dict) or catalog.get('geometry_kind') != 'schematic':
        raise ValueError('Catalog must declare schematic geometry')
    _number(catalog.get('screening_buffer_km'), 'screening_buffer_km', 0, 1000)
    points, segments = catalog.get('points'), catalog.get('segments')
    if not isinstance(points, list) or len(points) < 2 or not isinstance(segments, list) or not segments:
        raise ValueError('Catalog needs at least two points and one segment')
    ids = set()
    for p in points:
        if not isinstance(p, dict) or not isinstance(p.get('id'), str) or not p['id'] or p['id'] in ids:
            raise ValueError('Point IDs must be unique nonempty strings')
        if not isinstance(p.get('name'), str) or not p['name']:
            raise ValueError('Points require names')
        _number(p.get('lat'), 'latitude', -90, 90)
        _number(p.get('lon'), 'longitude', -180, 180)
        ids.add(p['id'])
    segment_ids = set()
    for s in segments:
        if not isinstance(s, dict) or not isinstance(s.get('id'), str) or not s['id'] or s['id'] in segment_ids:
            raise ValueError('Segment IDs must be unique nonempty strings')
        if not isinstance(s.get('name'), str) or not s['name']:
            raise ValueError('Segments require names')
        if not isinstance(s.get('from'), str) or not isinstance(s.get('to'), str) or s['from'] not in ids or s['to'] not in ids or s['from'] == s['to']:
            raise ValueError('Segments require two distinct known point IDs')
        segment_ids.add(s['id'])
    return catalog


def load_catalog(path=None):
    """Load and validate JSON catalog, independently of the process directory."""
    try:
        catalog = json.loads(Path(path or CATALOG_PATH).read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f'Could not load location catalog: {exc}') from exc
    return _validate_catalog(catalog)


def _angular_distance(lat1, lon1, lat2, lon2):
    a, b = math.radians(lat1), math.radians(lat2)
    dlat, dlon = b - a, math.radians(lon2 - lon1)
    h = math.sin(dlat / 2) ** 2 + math.cos(a) * math.cos(b) * math.sin(dlon / 2) ** 2
    return 2 * math.asin(math.sqrt(max(0, min(1, h))))


def _bearing(lat1, lon1, lat2, lon2):
    a, b, dl = math.radians(lat1), math.radians(lat2), math.radians(lon2-lon1)
    return math.atan2(math.sin(dl)*math.cos(b), math.cos(a)*math.sin(b)-math.sin(a)*math.cos(b)*math.cos(dl))


def _segment_distance(lat, lon, start, end):
    """Shortest spherical distance to the finite great-circle schematic arc."""
    length = _angular_distance(start['lat'], start['lon'], end['lat'], end['lon'])
    d = _angular_distance(start['lat'], start['lon'], lat, lon)
    endpoint = _angular_distance(end['lat'], end['lon'], lat, lon)
    if length < 1e-12 or length >= math.pi - 1e-12:
        return min(d, endpoint) * EARTH_RADIUS_KM
    angle = _bearing(start['lat'], start['lon'], lat, lon) - _bearing(start['lat'], start['lon'], end['lat'], end['lon'])
    along = math.atan2(math.sin(d)*math.cos(angle), math.cos(d))
    if 0 <= along <= length:
        cross = math.asin(max(-1, min(1, math.sin(d)*math.sin(angle))))
        return abs(cross) * EARTH_RADIUS_KM
    return min(d, endpoint) * EARTH_RADIUS_KM


def check_location(lat, lon, catalog=None):
    """Validate coordinates and return screening only, never operational status."""
    lat = _number(lat, 'latitude', -90, 90)
    lon = _number(lon, 'longitude', -180, 180)
    catalog = load_catalog() if catalog is None else _validate_catalog(catalog)
    points = {p['id']: p for p in catalog['points']}
    p = min(points.values(), key=lambda p: _angular_distance(lat, lon, p['lat'], p['lon']))
    nearest = {**copy.deepcopy(p), 'distance_km': round(EARTH_RADIUS_KM*_angular_distance(lat, lon, p['lat'], p['lon']), 2)}
    segments = [(s, _segment_distance(lat, lon, points[s['from']], points[s['to']])) for s in catalog['segments']]
    s, distance = min(segments, key=lambda item: item[1])
    return {
        'location': {'lat': lat, 'lon': lon},
        'nearest_waypoint': nearest,
        'nearest_segment': {**copy.deepcopy(s), 'distance_km': round(distance, 2)},
        'within_screening_buffer': distance <= catalog['screening_buffer_km'],
        'screening_buffer_km': catalog['screening_buffer_km'],
        'geometry_kind': 'schematic',
        'limitations': list(LIMITATIONS),
        'monitoring_coverage': 'not_assessed',
        'rail_status': 'not_assessed',
        'mine_connection': 'not_assessed',
    }
