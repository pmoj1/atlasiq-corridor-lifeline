"""Versioned heuristic, not a probability or a calibrated closure forecast."""
import re

VERSION = '1.0'


def score(config, feeds, now):
    reasons, issues, links = [], [], set()
    rain_points = warning_points = rail_points = 0
    rail_status = 'unknown'
    for feed in feeds:
        links.add(feed['source'])
        if feed['health'] != 'ok':
            issues.append(f"{feed['name']}: {feed.get('error', feed['health'])}")
            continue
        data = feed['data']
        if feed['kind'] == 'weather':
            rain = data['rain_since_9am_mm']
            points = 40 if rain >= 100 else 25 if rain >= 50 else 10 if rain >= 25 else 0
            rain_points = max(rain_points, points)
            reasons.append(f"{data['station']}: {rain:g} mm since local 9 am (+{points} rainfall points; station maximum used).")
        elif feed['kind'] == 'warnings':
            for item in data['items']:
                title = item['title'].lower()
                links.add(item['url'])
                if re.search(r'cancel|final|no (?:current )?warnings', title):
                    continue
                if not re.search(r'flood|severe weather|severe thunderstorm|cyclone|fire weather', title):
                    continue
                content = (title + ' ' + item['description']).lower()
                matched = any(re.search(r'\b' + re.escape(place.lower()) + r'\b', content)
                              for place in config['warning_keywords'])
                points = 30 if matched else 10
                warning_points = max(warning_points, points)
                reasons.append(f"Bureau of Meteorology: {item['title']} (+{points} warning points; "
                               + ('corridor place-name match).' if matched else 'state-wide relevance unconfirmed).'))
        else:
            rail_status = data['status']
            links.add(data['source_url'])
            rail_points = {'open': 0, 'restricted': 40, 'closed': 100, 'unknown': 0}[rail_status]
            reasons.append(f"Rail input reports {rail_status}: {data['summary']} (+{rail_points} rail points).")
            if rail_status == 'unknown':
                issues.append('Rail status has not been verified.')
    components = {'rainfall': rain_points, 'warnings': warning_points, 'rail': rail_points}
    total = min(100, sum(components.values()))
    band = 'CRITICAL' if total >= 80 else 'HIGH' if total >= 50 else 'WATCH' if total >= 25 else 'LOW'
    # Never present a reassuring classification when observation coverage is incomplete.
    label = 'UNKNOWN' if issues and total < 25 else band
    return {'corridor': config['corridor'], 'as_of': now.isoformat(), 'rule_version': VERSION,
            'score': total, 'level': label, 'components': components, 'rail_status': rail_status,
            'coverage': 'incomplete' if issues else 'complete for configured inputs',
            'reasons': reasons, 'issues': issues, 'sources': sorted(links), 'feeds': feeds}
