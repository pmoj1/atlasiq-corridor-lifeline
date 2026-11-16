"""Australian point forecasts from ECMWF AIFS via Open-Meteo."""
from datetime import datetime, timezone, timedelta
import json
import math
from threading import Lock
from time import monotonic
from urllib.parse import urlencode
from urllib.request import urlopen

# Reference localities, not claims about individual mine boundaries.
NATIONAL_SITES = (
    ("Port Hedland", "WA", -20.31, 118.60),
    ("Kalgoorlie", "WA", -30.75, 121.47),
    ("Darwin", "NT", -12.46, 130.84),
    ("Gove", "NT", -12.22, 136.77),
    ("Mount Isa", "QLD", -20.73, 139.49),
    ("Moranbah", "QLD", -22.00, 148.05),
    ("Roxby Downs", "SA", -30.56, 136.90),
    ("Port Augusta", "SA", -32.49, 137.76),
    ("Newcastle", "NSW", -32.93, 151.78),
    ("Canberra", "ACT", -35.28, 149.13),
    ("Portland", "VIC", -38.35, 141.61),
    ("Burnie", "TAS", -41.05, 145.91),
)

SOURCE = "https://open-meteo.com/en/docs/ecmwf-api"
MODEL = "ECMWF AIFS Single"
UNITS = {"time": "iso8601", "temperature_2m": "°C", "wind_speed_10m": "km/h", "precipitation": "mm"}
_lock = Lock()
_cache = None
_expires = 0


def exposure(rain, wind):
    if (rain is not None and rain >= 5) or (wind is not None and wind >= 50):
        return "watch"
    return "unknown" if rain is None or wind is None else "below threshold"


def series(row, site, now):
    if (row["utc_offset_seconds"] != 0 or row["hourly_units"] != UNITS or
            abs(row["latitude"] - site["lat"]) > 0.5 or abs(row["longitude"] - site["lon"]) > 0.5):
        raise ValueError("Unexpected units, timezone or model grid")
    data = row["hourly"]
    times = data["time"]
    if len(times) != 48 or any(len(data[key]) != 48 for key in UNITS):
        raise ValueError("Incomplete forecast window")
    hours = []
    previous = None
    for i, stamp in enumerate(times):
        dt = datetime.strptime(stamp, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)
        if (previous is None and abs((now-dt).total_seconds()) > 3600) or (previous and dt-previous != timedelta(hours=1)):
            raise ValueError("Stale or discontinuous forecast window")
        previous = dt
        def number(key, minimum):
            value = data[key][i]
            return value if type(value) in (int, float) and math.isfinite(value) and value >= minimum else None
        rain, wind, temp = number("precipitation", 0), number("wind_speed_10m", 0), number("temperature_2m", -273.15)
        hours.append(dict(time=dt.isoformat(), rain_mm=rain, wind_kmh=wind, temp_c=temp, exposure=exposure(rain, wind)))
    return dict(site, hours=hours)


def forecast():
    global _cache, _expires
    with _lock:
        if _cache is not None and monotonic() < _expires:
            return _cache
        now = datetime.now(timezone.utc)
        result = dict(status="unavailable", fetched_at=now.isoformat(), model=MODEL, source_url=SOURCE,
                      model_run_at=None, sites=[], error=None)
        try:
            sites = [dict(name=name, state=state, lat=lat, lon=lon)
                     for name, state, lat, lon in NATIONAL_SITES]
            query = urlencode(dict(latitude=",".join(str(s["lat"]) for s in sites),
                                   longitude=",".join(str(s["lon"]) for s in sites), hourly="temperature_2m,precipitation,wind_speed_10m",
                                   forecast_hours=48, models="ecmwf_aifs025_single", timezone="GMT"))
            with urlopen("https://api.open-meteo.com/v1/forecast?" + query, timeout=10) as response:
                raw = response.read(250001)
            if len(raw) > 250000:
                raise ValueError("Oversize response")
            rows = json.loads(raw)
            if not isinstance(rows, list) or len(rows) != len(sites):
                raise ValueError("Missing sites")
            parsed = [series(row, site, now) for row, site in zip(rows, sites)]
            missing = any(None in (h["temp_c"], h["rain_mm"], h["wind_kmh"]) for s in parsed for h in s["hours"])
            result.update(sites=parsed, status="partial" if missing else "ok",
                          error="Some forecast measurements are unavailable." if missing else None)
        except (ValueError, OSError, TypeError, KeyError, IndexError):
            result["error"] = "Current AIFS weather forecast unavailable or outside the expected forecast window."
        _cache = result
        _expires = monotonic() + (300 if result["sites"] else 30)
        return result
