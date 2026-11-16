"""JMA Himawari Band 13 latest continental imagery for Australia."""
from datetime import datetime, timedelta, timezone
import json
from urllib.request import Request, urlopen

BASE = "https://www.jma.go.jp/bosai/himawari/data/satimg"
CATALOG = BASE + "/targetTimes_fd.json"
SOURCE = "https://www.jma.go.jp/bosai/map.html#contents=himawari&lang=en"
GRID = {"zoom": 5, "x": 26, "y": 16, "columns": 4, "rows": 5}
BYTE_LIMIT = 100_000


def parse_frames(records, now):
    if not isinstance(records, list):
        raise ValueError("Invalid imagery manifest")
    available = {}
    for entry in records:
        if not isinstance(entry, dict):
            continue
        stamp = entry.get("validtime")
        if not isinstance(stamp, str) or not (len(stamp) == 14 and stamp.isascii() and stamp.isdigit()):
            continue
        if stamp != entry.get("basetime"):
            continue
        try:
            observed = datetime.strptime(stamp, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if observed <= now:
            available[stamp] = observed
    if not available:
        raise ValueError("No observed frame available")
    stamp = max(available)
    path = f"{BASE}/{stamp}/fd/{stamp}/B13/TBB/{GRID['zoom']}"
    tiles = [f"{path}/{x}/{y}.jpg"
             for y in range(GRID['y'], GRID['y'] + GRID['rows'])
             for x in range(GRID['x'], GRID['x'] + GRID['columns'])]
    return [{"observed_at": available[stamp].isoformat(), "tiles": tiles}]


def satellite():
    now = datetime.now(timezone.utc)
    result = {"source": "Japan Meteorological Agency · Himawari", "source_url": SOURCE,
              "product": "Band 13 · thermal infrared", "fetched_at": now.isoformat(),
              "grid": GRID, "frames": [], "status": "unavailable"}
    try:
        request = Request(CATALOG, headers={"User-Agent": "AtlasIQ-Corridor/1.0"})
        with urlopen(request, timeout=8) as response:
            raw = response.read(BYTE_LIMIT + 1)
        if len(raw) > BYTE_LIMIT:
            raise ValueError("Manifest exceeds size limit")
        frames = parse_frames(json.loads(raw), now)
        latest = datetime.fromisoformat(frames[-1]["observed_at"])
        stale = now - latest > timedelta(minutes=45)
        result.update(frames=frames, status="stale" if stale else "ok",
                      detail="Latest observation is over 45 minutes old." if stale else
                             "Infrared brightness temperature. Lighter shades usually indicate colder cloud tops.")
    except (OSError, ValueError) as exc:
        result["detail"] = f"Imagery catalogue unavailable ({type(exc).__name__})."
    return result
