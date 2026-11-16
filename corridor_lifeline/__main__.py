import argparse
import json
import math
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone
from .adapters import collect, timestamp
from .engine import score
from .alerts import draft
from .history import record

ROOT = Path(__file__).resolve().parent.parent


def load_config(path):
    config = json.loads(path.read_text())
    if not isinstance(config.get('corridor'), str) or not config['corridor'].strip():
        raise ValueError('corridor name is required')
    if not config.get('warning_keywords') or not all(isinstance(x, str) and x.strip() for x in config['warning_keywords']):
        raise ValueError('warning_keywords must contain non-empty place names')
    sources = config.get('sources', [])
    if {s['kind'] for s in sources} != {'weather', 'warnings', 'rail'}:
        raise ValueError('configure weather, warnings and rail sources')
    if sum(s['kind'] == 'rail' for s in sources) != 1:
        raise ValueError('configure exactly one rail source')
    if len({s['name'] for s in sources}) != len(sources):
        raise ValueError('source names must be unique')
    for source in sources:
        if not source.get('source') or not math.isfinite(source['max_age_minutes']) or source['max_age_minutes'] <= 0:
            raise ValueError('sources require a path/URL and positive max_age_minutes')
        if source['kind'] == 'rail' and not source.get('corridor_id'):
            raise ValueError('rail source requires corridor_id')
    return config


def atomic(path, content):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(content)
    os.replace(temporary, path)


def run_once(config, base, out, now, demo=False):
    result = score(config, collect(config, base, now), now)
    if demo:
        result['fixture_note'] = config['fixture_note']
        result['event_facts'] = config['event_facts']
    plain, email = draft(result, demo)
    out.mkdir(parents=True, exist_ok=True)
    atomic(out / 'latest.json', (json.dumps(result, indent=2) + '\n').encode())
    atomic(out / 'alert.txt', plain.encode())
    atomic(out / 'alert.eml', email)
    record(out / 'history.sqlite3', result)
    print(f"{result['as_of']} | {result['level']:8} {result['score']:3}/100 | {result['coverage']} | {out}")
    return result


def main():
    parser = argparse.ArgumentParser(description='Corridor Lifeline: local monitoring and email drafts; never sends email.')
    parser.add_argument('command', choices=['demo', 'once', 'watch'])
    parser.add_argument('--config', type=Path, default=ROOT / 'config/live.json')
    parser.add_argument('--out', type=Path, default=ROOT / 'output')
    parser.add_argument('--interval', type=float, default=900, help='watch interval in seconds, minimum 60')
    args = parser.parse_args()
    try:
        if args.command == 'demo':
            for year in ('2022', '2024'):
                path = ROOT / 'fixtures' / year / 'config.json'
                config = load_config(path)
                run_once(config, path.parent, args.out / 'demo' / year, timestamp(config['as_of']), True)
            return 0
        config = load_config(args.config)
        if args.command == 'watch' and (not math.isfinite(args.interval) or args.interval < 60):
            raise ValueError('--interval must be finite and at least 60 seconds')
        while True:
            result = run_once(config, args.config.resolve().parent, args.out / 'live', datetime.now(timezone.utc))
            if args.command == 'once':
                return 2 if result['issues'] else 0
            # Single worker, no overlapping polls; failures retry at the next interval.
            time.sleep(args.interval)
    except KeyboardInterrupt:
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Configuration or output error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
