# AtlasIQ Corridor Lifeline — 15-second concept film

Open project.html in a browser for playback, frame scrubbing, layer isolation, exact text editing and SVG frame export. Exports contains the voiceover, burned-in-caption and silent MP4s, plus an SRT companion and five review stills.

The editable project is code + named vector groups, not an After Effects/Premiere project. Each SVG keeps map, interface, typography, logo and background-texture groups separate. Audio stems are separate WAV files. The HTML editor embeds the vector timeline and font; keep the audio directory beside it for playback. Browser text changes do not rewrite render.py; use the source renderer for durable full-film changes.

Re-render with the project's bundled Python:

```sh
/Users/a111/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 creative/corridor-explainer/render.py
/Users/a111/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 creative/corridor-explainer/package.py
```

Dependencies: Pillow, numpy, imageio-ffmpeg. Narration source AIFFs were generated using the macOS Karen Australian synthetic voice, split into five timed phrases. render.py assembles them with pitch-preserving tempo adjustments. Music and effects are original procedural audio at 105 BPM. No third-party music recording is used.

Brand source: https://atlasiqco.com/ inspected 11 October 2026 in the in-app browser. The website logo is CSS geometry and a Space Grotesk wordmark, not an image asset. The renderer preserves its 30px amber square, 9px corner radius, inset six-point cutout, wordmark font/weight/tracking and amber IQ. Website amber #FFA028 and white #EAF0F9 replace the brief's approximate colours. Font: Google Fonts Space Grotesk, SIL OFL license included. Geographic geometry: Natural Earth 1:110m countries, public domain. Routes are simplified illustrative paths from Kalgoorlie to Port Augusta; no operational navigation or live conditions.

The five scenes occupy 0–3, 3–6, 6–9, 9–12 and 12–15 seconds. Voice ends by 13.5 seconds. Frames 405–449 are identical for the final 1.5-second hold. Main workflow is centred; a vertical composition needs rearranged headings and side cards, rather than a direct crop.

This film illustrates a development concept. It does not extend the Python prototype, collect live weather, submit permits or publish anything. The existing prototype does not implement permit drafting, closure prediction or live business alerts. Draft review and concept labels are retained throughout the relevant scenes.
