"""Build the local customer view from the completed historical replay."""
import csv
import json
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def render():
    summary = json.loads((HERE / "replay-summary.json").read_text())
    route = json.loads((HERE / "route.geojson").read_text())
    catalog = json.loads((ROOT / "config/locations.json").read_text())
    with (HERE / "replay-results.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    counts = summary["counts"]
    # Local equirectangular overview at the latitude of the corridor.
    def xy(lon, lat):
        return f"{35+(lon-115)*35:.1f},{52+(-30-lat)*41:.1f}"

    paths = []
    for feature in route["features"]:
        geometry = feature["geometry"]
        parts = geometry["coordinates"] if geometry["type"] == "MultiLineString" else [geometry["coordinates"]]
        for coords in parts:
            paths.append('<polyline points="' + ' '.join(xy(*point[:2]) for point in coords) + '"/>')
    points = catalog["points"]
    old = ' '.join(xy(p["lon"], p["lat"]) for p in points)
    labels = []
    for p in points:
        x, y = xy(p["lon"], p["lat"]).split(',')
        labels.append(f'<text x="{x}" y="{float(y)+18}" text-anchor="middle">{escape(p["name"])}</text>')
    nearby = sorted((r for r in rows if r["outcome"] in {"moved_in", "moved_out", "inside_both"}), key=lambda r: float(r["mapped_km"]))
    tr = ''.join('<tr>' + ''.join(f'<td>{escape(str(v))}</td>' for v in (
        r["title"], r["source_id"].upper(), r["old_km"], r["mapped_km"], r["outcome"].replace("_", " "))) + '</tr>' for r in nearby)
    statement = ("No archived notice crossed the 50 km threshold." if counts["moved_in"] + counts["moved_out"] == 0
                 else f'{counts["moved_in"]} entered and {counts["moved_out"]} left the 50 km screen.')
    eligible = len(rows)-counts["unlocated"]
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AtlasIQ · Freight rail replay</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f6f5f0;color:#192521;font:16px/1.5 system-ui}}main{{max-width:1000px;margin:auto;padding:clamp(18px,4vw,56px)}}header{{border-bottom:2px solid #b78535;padding-bottom:16px}}h1{{font-size:clamp(2rem,5vw,3.5rem);line-height:1.05;margin:.25em 0}}section{{margin:22px 0;background:white;border:1px solid #deded5;padding:20px;border-radius:14px}}figure{{margin:0;overflow-x:auto}}svg{{min-width:650px;width:100%}}text{{font:12px system-ui;fill:#34433e}}table{{width:100%;border-collapse:collapse}}td,th{{text-align:left;padding:8px;border-bottom:1px solid #ddd}}.scroll{{overflow:auto}}a{{color:#205748}}</style><main>
<header><a href="/#context" target="_top">Open notice desk</a><br><b>AtlasIQ · Corridor Lifeline</b><h1>Freight rail replay</h1><p>Perth region to Port Augusta · Archive collected {escape(summary["snapshot_time_utc"])}</p></header>
<section><h2>{statement}</h2><p>{eligible} notices had coordinates. {counts["inside_both"]} fell inside both routes’ screening areas and {counts["outside_both"]} fell outside both. Another {counts["unlocated"]} lacked coordinates.</p></section>
<section><h2>Two representations of the corridor</h2><figure><svg viewBox="0 0 930 215" role="img" aria-label="Overview of the mapped freight route and original town connections">
<g fill="none" stroke="#236956" stroke-width="3">{''.join(paths)}</g><polyline fill="none" stroke="#b9791e" stroke-width="2" stroke-dasharray="6 4" points="{old}"/>{''.join(labels)}</svg>
<figcaption>Green starts at Forrestfield freight terminal. The old route starts in central Perth. Green shows the selected federal freight rail geometry. Dashed amber connects the original reference towns. This overview is schematic. The replay measures distances on the sphere.</figcaption></figure></section>
<section><h2>Notices within 50 km of either route</h2><div class="scroll"><table><thead><tr><th>Notice</th><th>Source</th><th>Original km</th><th>Mapped km</th><th>Result</th></tr></thead><tbody>{tr}</tbody></table></div></section>
<section><h2>Operator map check</h2><p>Arc Infrastructure shows the western line through Midland, the Avon Valley, Merredin and Kalgoorlie. ARTC shows the eastern line through Rawlinna, Cook, Tarcoola and Spencer Junction. These references support the selected through route. The western endpoint is the Forrestfield freight terminal.</p></section>
<p>Road notices and satellite observations alone cannot verify rail operating conditions. This archive covers one collection.</p>
<p><a href="https://spatial.infrastructure.gov.au/server/rest/services/KeyFreightRoutes/Key_Freight_Routes/MapServer/6">Australian Government freight rail layer</a> · <a href="https://www.artc.com.au/customers/operations/nib/kalgoorlie-serviceton-and-parkes-corridor/">ARTC section references</a> · <a href="https://www.arcinfra.com/ARCInfrastructure/media/documents/Network%20Specifications/ARC_Map_Network.pdf">Arc Infrastructure network map</a></p></main></html>'''


if __name__ == "__main__":
    (HERE / "comparison.html").write_text(render(), encoding="utf-8")
