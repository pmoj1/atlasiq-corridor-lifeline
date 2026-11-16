"""Rebuild the reviewed screening alignment from a pinned official API snapshot."""
import collections
import gzip
import hashlib
import heapq
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = 'https://spatial.infrastructure.gov.au/server/rest/services/KeyFreightRoutes/Key_Freight_Routes/MapServer'
ARC = 'https://www.arcinfra.com/ARCInfrastructure/media/documents/Network%20Specifications/ARC_Map_Network.pdf'
ARTC = 'https://www.artc.com.au/customers/operations/nib/kalgoorlie-serviceton-and-parkes-corridor/'
# Vertices shared by consecutive freight features in the reviewed five-decimal query.
JUNCTION = (116.00557, -31.89311)
WEST = (121.47361, -30.73788)
EAST = (121.48354, -30.73067)
PORT = (137.76693, -32.49311)
TERMINAL = (115.98978293188704, -31.968278433498106)  # layer 2, OBJECTID 13


def km(a, b):
    """Local vertex weighting for path selection, in km."""
    scale = math.cos(math.radians((a[1] + b[1]) / 2))
    return 111.195 * math.hypot(scale * (a[0] - b[0]), a[1] - b[1])


def graph(parts):
    adjacency = collections.defaultdict(set)
    for part in parts:
        for a, b in zip(part, part[1:]):
            a, b = tuple(a), tuple(b)
            adjacency[a].add(b)
            adjacency[b].add(a)
    return adjacency


def through_path(adjacency, start, end):
    """Use actual source edges only. An unconnected source fails closed."""
    distances = {start: 0}
    parent = {}
    queue = [(0, start)]
    while queue:
        dist, at = heapq.heappop(queue)
        if at == end:
            path = [end]
            while path[-1] != start:
                path.append(parent[path[-1]])
            return path[::-1]
        if dist != distances[at]:
            continue
        for other in sorted(adjacency[at]):
            length = dist + km(at, other)
            if length < distances.get(other, math.inf):
                distances[other] = length
                parent[other] = at
                heapq.heappush(queue, (length, other))
    raise ValueError('Source feature is disconnected between the reviewed vertices')


def cut_border(points, west):
    # Both state geometries overlap near 129°E. Trim each on its own edge.
    crossings = [i for i, (a, b) in enumerate(zip(points, points[1:])) if a[0] < 129 <= b[0]]
    if len(crossings) != 1:
        raise ValueError('State border geometry requires review')
    i, = crossings
    a, b = points[i:i+2]
    cross = (129.0, round(a[1] + (b[1] - a[1]) * (129 - a[0]) / (b[0] - a[0]), 8))
    return points[:i+1] + [cross] if west else [cross] + points[i+1:]


def main():
    with gzip.open(HERE / 'route_source.geojson.gz', 'rb') as file:
        raw = file.read()
    collection = json.loads(raw)
    parts = {f['id']: graph(f['geometry']['coordinates']) for f in collection['features']}
    first = min(parts[205], key=lambda p: km(TERMINAL, p))
    if km(first, TERMINAL) > 0.5:
        raise ValueError('Terminal no longer close to source line')
    specs = [
        (205, first, JUNCTION, 'Forrestfield terminal approach', ARC),
        (192, JUNCTION, WEST, 'Midland district via Avon and Merredin to Kalgoorlie', ARC),
        (189, WEST, EAST, 'Kalgoorlie connection', ARTC),
        (181, EAST, max(parts[181]), 'Kalgoorlie via Rawlinna and Forrest to the state border', ARTC),
        (5, min(parts[5]), PORT, 'State border via Cook, Tarcoola and Pimba to Port Augusta', ARTC),
    ]
    features = []
    joins = []
    for oid, start, end, section, source in specs:
        points = through_path(parts[oid], start, end)
        if oid in (181, 5):
            points = cut_border(points, west=(oid == 181))
        if features:
            distance = km(features[-1]['geometry']['coordinates'][-1], points[0])
            joins.append(round(distance * 1000, 2))
            if distance > 0.1:
                raise ValueError('Inter-feature gap exceeds reviewed tolerance')
        features.append({
            'type': 'Feature',
            'properties': {'OBJECTID': oid, 'name': section, 'section': section,
                           'operator_reference': source, 'source_url': BASE + '/6'},
            'geometry': {'type': 'LineString', 'coordinates': points}
        })
    route = {'type': 'FeatureCollection', 'name': 'Forrestfield freight terminal to Port Augusta',
             'source_sha256': hashlib.sha256(raw).hexdigest(),
             'terminal_vertex_offset_m': round(1000 * km(TERMINAL, first), 1),
             'consecutive_section_gaps_m': joins, 'features': features}
    (HERE / 'route.geojson').write_text(json.dumps(route, separators=(',', ':')) + '\n')
    print('Terminal offset metres:', route['terminal_vertex_offset_m'], 'joins metres:', joins)
    for f in features:
        pts = f['geometry']['coordinates']
        print(f['properties']['OBJECTID'], len(pts), round(sum(km(a,b) for a,b in zip(pts,pts[1:])),2))


if __name__ == '__main__':
    main()
