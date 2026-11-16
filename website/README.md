# AtlasIQ website revision

This local revision presents Corridor Lifeline as AtlasIQ's current project and Jay-deane Huni as its sole founder. The 13 October 2026 design brief adds a premium photographic presentation and animation using founder-supplied images.

## Files

- `original/`: public homepage, stylesheet, script and waitlist HTML recovered from atlasiqco.com on 12 October 2026. This is a public snapshot, not the original repository or a complete hosting backup.
- `corridor-lifeline-copy.md`: source-backed replacement copy based on the solo plan and current prototype README.
- `draft/`: revised static website for review. No backend or live corridor feed is added.
- `source-assets/photography/`: all eight supplied original JPEGs, retained unchanged. Downloads originals are also preserved.
- `source-assets/asset-manifest.json`: checksums, photographer filenames and responsive image dimensions/sizes.
- `premium-content-notes.md`: plan-based editorial guidance for the photographic redesign.
- `archive/narrative-draft-2026-10-13/`: previous local version, package and verification evidence.
- `verification/premium/`: photographic version's browser screenshots and verification evidence.
- `tools/`: reproducible responsive image preparation and static-resource verification scripts.

## Preview

From the AtlasIQ project root:

```sh
/Users/a111/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m http.server 8765 --bind 127.0.0.1 --directory website/draft
```

Open http://127.0.0.1:8765/. Stop with Ctrl-C when finished.

Alternatively, double-click `Start Website.command` in this folder, then open the printed address. It uses the project's existing Python runtime and serves only on this Mac.

## Photography and preparation

The public site uses selected road-freight, warehouse and industrial photography. Responsive WebP versions preserve the full original compositions; layout crops use CSS. The original JPEGs stay outside the public deployment directory. Names and Unsplash IDs are recorded from supplied filenames; the public credits page identifies the photography as illustrative, not footage of the corridor or specific incidents.

The font is the existing locally bundled Space Grotesk, with its SIL Open Font License included. The schematic Australia outline reuses the project's existing Natural Earth geometry. No confidential plan PDF is included in the public website.

Prepare image assets or check local resources with the bundled Python interpreter:

```sh
python website/tools/prepare_assets.py
python website/tools/verify_site.py
```

Replace `python` with the bundled path above on this Mac. Preparation requires the existing Pillow package; the resource check uses the bundled Node executable for JavaScript syntax.

## Hosting handoff

The existing domain's HTTP response identifies its server as Netlify. No matching connected Sites project or local website repository was found. Updating the existing site requires access to its Netlify project and confirmation of the deployment method, retained routes and settings.

Do not replace a full existing deployment without first preserving its current deployed files and checking additional pages and settings. The `original/` snapshot does not include every asset, route, function or hosting rule.

The draft's interest page uses the existing public contact email. The old waitlist's client submitted to Google Apps Script using an opaque response, which could not verify a recorded signup. This draft does not promise successful registration or send form data to that endpoint. Any future restored registration flow needs confirmed response handling and its own integration check.

The draft distinguishes working local monitoring and email drafts from proposed subscriber alerts and emergency paperwork support. It makes no closure-prediction or advance-warning performance claim.

## Completed verification — 13 October 2026

Static checks passed for three pages and 46 local references, including JavaScript syntax. Desktop, portrait mobile and short landscape browser checks passed for layout, navigation and plan tabs. Current screenshots and verification report are in `verification/premium/`. The latest ZIP contains the premium design and passed archive integrity checking. Live publication remains pending Netlify access.
