"""Prepare responsive website derivatives; preserve supplied originals unchanged."""
from pathlib import Path
from PIL import Image, ImageOps
import hashlib
import json
import shutil

WEB = Path(__file__).resolve().parents[1]
PROJECT = WEB.parent
SOURCE = WEB / "source-assets/photography"
ASSETS = WEB / "draft/assets"
PHOTOS = ASSETS / "photos"
PHOTOS.mkdir(parents=True, exist_ok=True)

SELECTED = {
    "corridor-truck": ("levi-meir-clancy-i7-s2wuykiU-unsplash.jpg", "Levi Meir Clancy", "i7-s2wuykiU", [800, 1440, 2200]),
    "freight-on-road": ("gabriel-santos-GBVDilE8yvI-unsplash.jpg", "Gabriel Santos", "GBVDilE8yvI", [800, 1440]),
    "warehouse": ("marcin-jozwiak-oh0DITWoHi4-unsplash.jpg", "Marcin Jozwiak", "oh0DITWoHi4", [800, 1440]),
    "industry": ("miningwatch-portugal-YG0qc-e6hgg-unsplash.jpg", "MiningWatch Portugal", "YG0qc-e6hgg", [800, 1440]),
}

manifest = {"prepared_on": "2026-10-13", "source": "Founder-supplied Unsplash files; photographer names and photo IDs taken from filenames.", "originals": [], "derivatives": []}
for original in sorted(SOURCE.glob("*.jpg")):
    manifest["originals"].append({"filename": original.name, "sha256": hashlib.sha256(original.read_bytes()).hexdigest(), "bytes": original.stat().st_size})
for slug, (filename, photographer, photo_id, sizes) in SELECTED.items():
    with Image.open(SOURCE / filename) as source:
        original = ImageOps.exif_transpose(source).convert("RGB")
        for width in sizes:
            height = round(width * original.height / original.width)
            output = PHOTOS / f"{slug}-{width}.webp"
            original.resize((width, height), Image.Resampling.LANCZOS).save(output, "WEBP", quality=84, method=6)
            manifest["derivatives"].append({"filename": str(output.relative_to(ASSETS)), "source": filename, "photographer": photographer, "photo_id": photo_id, "dimensions": [width, height], "bytes": output.stat().st_size})

fonts = ASSETS / "fonts"
fonts.mkdir(exist_ok=True)
for filename in ["SpaceGrotesk.ttf", "FONT-LICENSE.txt"]:
    shutil.copy2(PROJECT / "creative/corridor-explainer/assets" / filename, fonts / filename)

# Reuse the project’s Natural Earth geometry for a schematic outline only.
world = json.loads((PROJECT / "creative/corridor-explainer/assets/countries.geojson").read_text())
au = next(f for f in world["features"] if f["properties"].get("ADMIN") == "Australia")
paths = []
for polygon in au["geometry"]["coordinates"]:
    for ring in polygon:
        points = [((lon - 110) / 46 * 800, (-lat - 9) / 36 * 640) for lon, lat in ring]
        paths.append("M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points) + " Z")
svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 640" fill="none"><title>Australia outline</title><path d="' + " ".join(paths) + '" fill="#1d2526" stroke="#48504e" stroke-width="1.5"/></svg>'
(ASSETS / "australia-outline.svg").write_text(svg)
(WEB / "source-assets/asset-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"Prepared {len(manifest['derivatives'])} responsive photographs, local font and Australia outline.")
print(f"Responsive photos total: {sum(x['bytes'] for x in manifest['derivatives']):,} bytes")
