"""Replay a saved Notice Desk snapshot against two routes. Reads files only."""
import argparse
import collections
import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from corridor_lifeline.locations import check_location, load_catalog
from corridor_lifeline.mapped_route import nearest, position, route_blocks


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(notices_path, route_path, catalog_path, output):
    source = json.loads(notices_path.read_bytes())['data']
    catalog = load_catalog(catalog_path)
    threshold = catalog['screening_buffer_km']
    blocks, properties = route_blocks(route_path)
    rows, counts, seen = [], collections.Counter(), {}
    for event in source['events']:
        key = (event['source_id'], event['id'])
        if key in seen:
            if event != seen[key]:
                raise ValueError('Conflicting event revisions in snapshot: ' + str(key))
            continue
        seen[key] = event
        row = {field: event.get(field) for field in ('source_id', 'id', 'title', 'url', 'observed_at',
                                                     'updated_at', 'lat', 'lon')}
        row['outcome'] = 'unlocated'
        if event.get('lat') is not None and event.get('lon') is not None:
            point = position([event['lon'], event['lat']])
            old = check_location(point['lat'], point['lon'], catalog)
            old_km = old['nearest_segment']['distance_km']
            old_inside = old['within_screening_buffer']
            if event.get('near_corridor') != old_inside or event.get('distance_km') != old_km:
                raise ValueError('Original screen differs from archived record: ' + str(key))
            km, (index, a, b) = nearest(point, blocks)
            pair = old_inside, km <= threshold
            row.update(outcome={(False, True): 'moved_in', (True, False): 'moved_out',
                                (True, True): 'inside_both', (False, False): 'outside_both'}[pair],
                       old_km=old_km, mapped_km=round(km, 3), old_section=old['nearest_segment']['name'],
                       mapped_feature_index=index, mapped_feature=json.dumps(properties[index], ensure_ascii=False),
                       mapped_edge=json.dumps([[p['lon'], p['lat']] for p in (a, b)]))
        counts[row['outcome']] += 1
        rows.append(row)
    summary = {'snapshot_time_utc': source['fetched_at'], 'snapshot_sha256': sha256(notices_path),
               'route_sha256': sha256(route_path), 'schematic_sha256': sha256(catalog_path),
               'buffer_km_inclusive': threshold, 'input_rows': len(source['events']),
               'duplicate_rows': len(source['events']) - len(seen), 'unique_notices': len(rows),
               'counts': {k: counts[k] for k in ('moved_in', 'moved_out', 'inside_both', 'outside_both', 'unlocated')}}
    output.mkdir(parents=True, exist_ok=True)
    fieldnames = ['source_id', 'id', 'title', 'url', 'observed_at', 'updated_at', 'lat', 'lon', 'outcome',
                  'old_km', 'mapped_km', 'old_section', 'mapped_feature_index', 'mapped_feature', 'mapped_edge']
    with (output / 'replay-results.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    (output / 'replay-summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--notices', type=Path, default=HERE / 'notices-2026-11-07.json')
    parser.add_argument('--route', type=Path, default=HERE / 'route.geojson')
    parser.add_argument('--catalog', type=Path, default=HERE.parents[1] / 'config/locations.json')
    parser.add_argument('--output', type=Path, default=HERE)
    args = parser.parse_args()
    print(json.dumps(replay(args.notices, args.route, args.catalog, args.output), indent=2))
