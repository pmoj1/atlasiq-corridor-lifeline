# AtlasIQ Corridor Lifeline

[Project portfolio](https://github.com/pmoj1) · [Mining land restoration and closure review](https://github.com/pmoj1/mining-land-restoration)

A minimal, dependency-free Python prototype for the east-west rail corridor. It polls public BOM observation JSON and warning RSS feeds, reads a manually verified rail-status JSON file or HTTP endpoint, calculates an explainable score, and produces plain-language email drafts. No account, API key, paid service, LLM or third-party Python package is needed. It never sends email.

See [the organised project file guide](PROJECT_FILES.md) for the website revision, solo plan, creative projects and archived research. The [website workspace](website/README.md) contains the Corridor Lifeline narrative update and sole-founder presentation.

## Run locally

Install Python 3.10 or newer, then run from this project directory:

```sh
python3 -m corridor_lifeline demo
python3 -m unittest discover -s tests -v
```

The offline demo reads the same adapter formats as live mode. Results appear in `output/demo/2022/` and `output/demo/2024/`:

- `alert.txt`: subject and plain-language text, ready to review and paste into email.
- `alert.eml`: MIME email draft; open/import it in an email client and add recipients.
- `latest.json`: score components, reasons, source health, timestamps and historical provenance.

The 2022 reopening snapshot produces LOW, 0/100. The 2024 closure snapshot produces CRITICAL, 100/100. These are software demonstrations, **not proof of advance-warning accuracy**. Weather/warnings are explicitly illustrative, not recovered historical BOM measurements. See [fixture provenance](fixtures/README.md).

On this Mac, `/usr/bin/python3` requires missing Apple developer tools. The installed Codex runtime can run the prototype without installing anything:

```sh
/Users/a111/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m corridor_lifeline demo
```

## Live inputs and scheduling

1. Edit `config/rail-status.json` with a verified current rail update, its URL and verification time. The shipped example is deliberately stale and unknown.
2. Review `config/live.json`: URLs, weather stations, corridor keywords and maximum ages. Source file paths resolve relative to the config file, not your shell directory. Weather and warning sources can be repeated; exactly one rail source is required.
3. Run one collection, or leave the polling process running:

```sh
python3 -m corridor_lifeline once --config config/live.json
python3 -m corridor_lifeline watch --config config/live.json --interval 900
```

`watch` polls immediately, then every 900 seconds after the previous cycle finishes. Ctrl-C stops it. A single worker prevents overlapping cycles. Reads use a 20-second HTTP timeout and a 2 MB response limit. Each failed adapter is isolated and retried on the next cycle. Rail file content is reloaded each cycle; restart to apply config changes. The process must remain running and the computer awake. No system schedule is installed automatically.

Outputs are overwritten under `output/live/`; `--out /absolute/path` changes the output root. Each individual file is replaced atomically. Run only one writer per output directory. Each collection also retains a bounded SQLite history (the latest 1,000 distinct assessment payloads per output folder). Email delivery, subscriber management, a retry queue and notification deduplication are not implemented.

Exit codes: `0` successful complete collection/demo or clean stop; `2` a one-shot collection has incomplete data; `1` invalid configuration or output failure. HIGH/CRITICAL with healthy inputs is a successful collection, not a process error.

For an optional Unix cron schedule, use absolute paths for both Python and the project, replacing `/path/to/python3` with a real interpreter. Use cron **or** watch, not both:

```cron
*/15 * * * * cd /Users/a111/Desktop/AtlasIQ && /path/to/python3 -m corridor_lifeline once >> /Users/a111/Desktop/AtlasIQ/corridor.log 2>&1
```

## Rail input contract

Change the rail source in `config/live.json` to a local path or public HTTP(S) JSON URL. No ARTC machine-readable status API is assumed; this is a human-verified bridge to operator announcements.

```json
{
  "corridor_id": "east-west",
  "observed_at": "2026-09-21T04:00:00Z",
  "status": "unknown",
  "summary": "Awaiting operator confirmation for this corridor.",
  "source_url": "https://www.artc.com.au/artc-news/"
}
```

Allowed statuses: `open`, `restricted`, `closed`, `unknown`. `observed_at` is the time the status was verified, must include a timezone, and must not be refreshed just because the file was fetched. A planned future reopening stays `closed` until verified. The corridor ID must match the configured rail source.

## Transparent rules (version 1.0)

| Component | Rule | Points |
| --- | --- | --- |
| Rainfall | Latest station rain since local 9 am: below 25 / at least 25 / 50 / 100 mm | 0 / 10 / 25 / 40 |
| Warnings | Relevant hazard with corridor place-name match | 30 |
| Warnings | Relevant state-wide hazard, geographic relevance unconfirmed | 10 |
| Rail | Open / restricted / closed | 0 / 40 / 100 |

Take the maximum rainfall contribution across configured stations and the maximum warning contribution across feeds, then add rail points and cap at 100. Warnings include flood, severe weather, severe thunderstorm, cyclone and fire weather. Cancellation/final notices are excluded by title. LOW = 0–24, WATCH = 25–49, HIGH = 50–79, CRITICAL = 80–100. Thresholds are illustrative policy choices, not fitted probabilities.

Missing, malformed, future-dated (>5 minutes) or stale inputs never contribute zero as if healthy: they are excluded and explicitly listed as gaps. With gaps and a score below 25 the displayed level is UNKNOWN. Higher scores remain visible with incomplete coverage. Unknown rail status is also a gap. A stale closure is retained in the JSON feed detail but not represented as a current closure. No automatic all-clear is generated.

BOM `rain_trace` is **rain since local 9 am**, not rolling 24-hour rainfall; cumulative observations must not be summed. The counter resets daily and can lower the score. Observation time comes from `aifstime_utc`; warnings use RSS channel `lastBuildDate` or `pubDate`. Missing feed publication time is an error. A feed that does not refresh while empty becomes stale rather than silently implying all-clear.

Warning filtering is coarse text matching, not geospatial intersection or full warning lifecycle tracking. The default weather source covers only Kalgoorlie-Boulder; configure additional stations before assessing the whole corridor. Complete coverage means all **configured** sources passed checks, not that every corridor segment is monitored. No rainfall forecast, river model or closure prediction is implemented.

## Public sources and practical limits

- [BOM data services](https://www.bom.gov.au/catalogue/data-feeds.shtml) documents public observation products.
- [Kalgoorlie-Boulder observations](https://www.bom.gov.au/products/IDW60801/IDW60801.94637.shtml) links the JSON observation product used in config.
- [BOM RSS catalogue and terms](https://www.bom.gov.au/rss/) links state warning feeds. BOM restricts this RSS service to personal and non-commercial use; review permissions or an appropriately licensed feed before commercial deployment. Keep attribution and direct warning links. RSS is not intended as the sole warning channel.
- [ARTC news](https://www.artc.com.au/artc-news/) provides announcements for manual verification.

Public endpoints can change, block automated requests or return an HTML page. Such responses become visible data gaps; this prototype does not bypass access controls. Live endpoint availability is not guaranteed. Use the offline demo to verify local functionality independently of network access.

Validation on 21 September 2026: the observation endpoint and both land-warning RSS feeds fetched and parsed successfully in a network-enabled smoke test. The deliberately stale rail placeholder correctly kept the live result UNKNOWN. All 17 automated tests and both offline demos passed.

## Project map

`corridor_lifeline/adapters.py` handles transport, parsing and freshness; `engine.py` contains scoring rules; `alerts.py` generates deterministic copy and MIME drafts; `__main__.py` supplies the demo, one-shot and polling CLI. `tests/` exercises input failures, thresholds, replay output, email structure and scheduler retries.

## Local corridor workspace

View an existing result with the bundled Python interpreter:

```sh
/Users/a111/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m corridor_lifeline.dashboard --input output/demo/2024/latest.json --port 8770
```

Open http://127.0.0.1:8770, or double-click **Start Corridor.command**. The server binds only to this Mac. With no `--input`, the startup view uses `output/live/latest.json`. Use the selector to switch between saved/current and clearly labelled historical demonstrations. No data is fetched just by opening the workspace.

### Working features

- **Overview:** saved assessment, component charts, freshness, coverage gaps and evidence. Refresh reloads saved output; **Check configured sources now** explicitly collects weather/warnings and rereads the manual rail file. One background worker prevents overlapping button requests. Collection can take about a minute when public endpoints time out.
- **Locations:** seven searchable reference localities from Perth to Port Augusta, schematic route display, latitude/longitude checking and optional one-time browser position. Returns nearest reference locality and approximate segment distance with a 50 km screening buffer. Coordinates and connecting arcs are approximate; not track geometry, mine connectivity, local hazard intersection, vehicle tracking or operating permission. Off-corridor means outside this reference, not safe. Sources and coordinate limitations live in `config/locations.json`.
- **Evidence:** searchable source records, source-health filters, observation/fetch times and raw details. Saved source health is not reverified by viewing it.
- **Supply scenario:** editable stock, daily use, ETA, delay and safety buffer, depletion chart and sensitivity table. Inputs are illustrative assumptions; this does not forecast a delay or model incoming delivery quantities.
- **History and drafts:** latest 100 current collections displayed; latest 1,000 distinct payloads retained transactionally in `history.sqlite3`. Identical payloads deduplicate; a changed collection time creates a new record. Historical/demo output folders keep separate histories. Export selected assessment JSON, print a brief or download the latest current email draft. Nothing is sent.

Saved results older than 60 minutes are prominently stale; `--max-age-minutes` changes this display policy. Future/missing dates remain unknown. Historical demonstrations cannot establish current conditions. Failed feeds remain explicit gaps, and manual rail observation times are preserved.

`--config` chooses the server's fixed collection configuration; `--out` chooses its current-output folder (default `output/live`). Do not run another writer/watch process against that same folder. The CLI `watch` can still poll into a separate output folder; the browser itself does not install a schedule. Do not change the config to demo fixtures for a current collection.

History uses SQLite transactions; latest JSON/drafts each use atomic replacement, but the entire multi-file bundle is not one transaction. An output/archive failure can leave a partial new bundle: inspect timestamps and error messages. Restart preserves history; browser location checks are not written to the archive. Location query coordinates can appear in local server access logs. No coordinate requests go to a third-party map provider.

### Remaining operational boundaries

Rail status is still a manually verified bridge, not an automatic operator feed. Only Kalgoorlie weather plus configured WA/SA warning feeds are collected by default. Place-name warning matching does not prove hazard coverage at a chosen coordinate. The schematic map is a screening tool, not a routing or emergency-navigation system. BOM RSS permission limits above still apply before commercial use. Hosting, accounts, delivered alerts, surveyed route data, fleet tracking and validated closure predictions are not implemented.

Verification of the 25 October workspace build is recorded in `corridor_lifeline/verification/RESULTS.md`.

## Real event context

The **Real events** tab adds explicitly refreshed USGS magnitude2.5+ earthquake reports for the past7days, an upstream source also documented by World Monitor. This is a direct USGS connection, not data delivered by World Monitor. Events retain geographic coordinates, source links, event/update times and feed-generation/fetch times. Distance screening uses the same approximate corridor geometry; earthquakes do not change the rail score or establish closure. This single feed is not comprehensive hazard monitoring. Context is held in server memory and requires refresh after restart.

World Monitor hosted access remains unconnected: its official developer documentation requires subscription credentials for event data. Merely setting a key does not activate an unimplemented hosted adapter. No World Monitor platform code was copied. Hosted service/output terms are separate from its AGPL source licence. References: https://github.com/koala73/worldmonitor/blob/main/public/developers.md and https://github.com/koala73/worldmonitor/blob/main/docs/license.mdx . Do not paste credentials in chat or commit them to project files.

### November notice desk

The workspace opens on the Notice desk. Choose **Check event sources now** to collect public reports. Filter by road, rail news, weather or earthquake, then inspect the original source and the basis for a location match. Main Roads WA incident points can be screened against the approximate route. BOM WA/SA warnings and ARTC news without coordinates stay in the table; a place-name match is a candidate only. ARTC news is not a live operator-status service. The DFES source is explicitly unavailable when no verified queryable warning layer exists. Road records without a feed publication time have unknown feed freshness even after successful retrieval. These context feeds do not alter the rail assessment.

### If the local page refuses to connect

Double-click `Start Corridor.command`. It waits for the local server before opening the page and keeps the server detached from the launcher terminal. Closing the terminal will not intentionally stop the server. After a restart of your Mac, run the launcher again. Startup logs are in `~/Library/Logs/AtlasIQ/corridor.log`. This remains a local application; no login service or cloud hosting is installed.

## Freight rail replay and hotspot screening

Expand **Historical freight rail replay** on the Notice desk. The [offline report](research/rail-replay/comparison.html) and [row-level results](research/rail-replay/replay-results.csv) cover the 7 November 2026 collection. To reproduce the comparison locally, run:

```sh
python3 research/rail-replay/route_build.py
python3 research/rail-replay/replay.py
python3 research/rail-replay/render_report.py
```

The Notice desk screens coordinates against the reviewed Forrestfield freight terminal–Port Augusta line. The Locations explorer draws the same reviewed line, shows the nearest mapped section for a coordinate check and keeps the original town-based distance alongside it. Use **Refresh notices** for the three-day DEA satellite hotspot layer. Detection time and distance are evidence for investigation. Satellite detections can come from other heat sources, and cloud or overpass timing can hide fires. Gaps in notices do not establish safe operation. Data attribution: Geoscience Australia, Digital Earth Australia Hotspots (CC BY 4.0). See the [provider documentation](https://knowledge.dea.ga.gov.au/data/product/dea-hotspots/).

### Australia Operations workspace

National outlook opens by default. It shows the latest JMA Himawari observation across mainland Australia and Tasmania. The visible desk checks for updates every five minutes. Select a point or matrix row to inspect 48 hourly ECMWF AIFS forecasts. Twelve sample locations cover six states, the NT and the ACT. Signals charts reflect each feed’s geographic coverage. Site imagery uses the selected forecast location and shows a dated DEA Landsat annual composite in natural and false colour. East–west rail tools remain accessible separately.

ApiVault lists Open-Meteo and USGS in API_LIST.md. Satellite and land imagery are retrieved from JMA and Digital Earth Australia directly. Open-Meteo’s public endpoint is for non-commercial evaluation; operational closure probability remains unvalidated.

### Road watch and advance permit preparation

The running Mac dashboard server checks a pinned Wilson Street freight section in Port Hedland every ten minutes, including while the browser is closed. Keep the Mac awake and connected. The National outlook layers the road and point forecasts over the latest Himawari infrared observation. The monitor checks the satellite catalogue time and applies illustrative precipitation and wind thresholds to AIFS point forecasts. The image provides geographic and cloud context. Each actual crossing creates an internal preparation draft in the local check history (144 checks retained). Logistics can edit a working copy and download text. Confirm the road condition, load, alternate route, authority and permit requirement before using a draft.

Open **National outlook → Open road access watch** to monitor a logistics segment. While the Mac is awake and the local server is running, an independent worker checks the configured road every 15 minutes. Wilson Street (Port Hedland) uses three points on a published freight-road feature. Configure a different segment using 2–12 points. Point forecasts and satellite image brightness can coincide when several road points fall within the same model or satellite pixel. Brightness measures displayed Band 13 image intensity, on a 0–255 scale. The forecast triggers are illustrative. The generated access enquiry requires the planner to confirm the road status, authority, permit type and movement details.
