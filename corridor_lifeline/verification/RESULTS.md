# Corridor workspace verification — 25 October 2026

Authorised local build: location screening, responsive workspace, explicit source collection, persistent history, integrated supply scenario and exports.

- Bundled Python `-m unittest discover -s tests -v`: **49 passed**. Includes coordinate validation, spherical finite-segment distances/dateline/endpoints, unknown coverage, history retention/deduplication, missing-result rendering, JSON escaping round-trip, worker failure/single-flight and HTTP origin/token guards. Closure-review tests also pass.
- Bundled Python `-m corridor_lifeline demo --out /tmp/atlasiq-corridor-build-20261025`: exit0; 2022 LOW0, 2024 CRITICAL100. Illustrative historical weather/warnings remain labelled.
- Independent reviewer reran49tests/demos and archive concurrency/retention probes.500 concurrent repeated writes deduplicated100;1,001 unique insertions retained1,000. No blockers. Neutralised failure copy after reviewer demonstrated archive failure can follow latest.json publication.
- Browser: selected Kalgoorlie, confirmed0km at reference coordinates, checked0/0 outside buffer, verified unconfirmed local monitoring. Desktop1440×1000 and mobile390×844; mobile document width390, no horizontal overflow. Screenshots alongside this file. One-time actual device-position permission was not exercised; coordinate fallback tested.
- Browser source-collection button completed against current public endpoints: weather and WA/SA warnings healthy at assessment; deliberately stale manual rail input kept UNKNOWN/incomplete. No outgoing alerts. Network availability is a point-in-time result.
- Browser supply scenario:12,000t stock /1,500t daily use /4day ETA /10day delay /2day safety =8days cover,−8days buffer,9,000t shortfall; graph/table reflected inputs.
- JS syntax checks passed for location/monitor scripts. UI specialist additionally mocked search/validation/unavailable-geolocation and stale-request behavior.

Boundaries: approximate route geometry and illustrative50km buffer; no validated track alignment, mine connections, coordinate-level hazard intersection, live train tracking, automatic verified rail collection, delivered alerts, cloud deployment or calibrated prediction. README records feed licence limits and single-writer policy. Browser lookups stay local; coordinates may appear in server access logs.

## Real context extension
55tests passed, including6new mocked USGS tests. Independent reviewer verified transport bounds, malformed data, attribution, no score changes and source-age repair. Live upstream fetch406reports; no rejected records. WM hosted event API unconnected. Server re-age and browser60second source health updates preserve fetch timestamps. This is earthquake context only, not comprehensive corridor hazard coverage.
