# AtlasIQ business brand kit

Created 14 October 2026 from the existing local website design in `../website/draft/`. This kit preserves the website's geometric A mark, Space Grotesk typography, letter spacing and ink/ivory/amber palette. It is a reusable export of that design.

## Choose a logo

- `logos/atlasiq-logo-dark-background.png`: primary logo on an ink background.
- `logos/atlasiq-logo-light-background.png`: logo on an ivory background.
- `logos/atlasiq-logo-transparent-for-dark.png`: ivory/amber lettering with a transparent background, for dark surfaces.
- `logos/atlasiq-logo-transparent-for-light.png`: ink/amber lettering with a transparent background, for light surfaces.
- `logos/atlasiq-logo-transparent-white.png` and `logos/atlasiq-logo-transparent-black.png`: single-colour transparent versions.
- `logos/atlasiq-mark-transparent.png`: amber symbol by itself.
- `logos/atlasiq-mark-dark-background.png`: amber symbol on ink.

Each PNG has a matching SVG. SVG lettering is converted to vector outlines, so recipients do not need the font installed. PNG wordmarks are 3520 × 896 pixels; symbols are 1280 × 1280 pixels. Transparent PNGs contain real alpha transparency.

## Colours and typography

| Colour | HEX | RGB |
| --- | --- | --- |
| Ink | #0B0E10 | 11, 14, 16 |
| Ivory | #F1EEE6 | 241, 238, 230 |
| Amber | #E9AA4B | 233, 170, 75 |
| Muted grey | #A8ADAE | 168, 173, 174 |

Space Grotesk is included in `fonts/`, with its existing SIL Open Font License. The website uses weight 600 for Atlas and 500 for IQ; headings use 500. Use ink and ivory for primary surfaces and amber for the mark, emphasis and accents.

## Practical usage guidance

Keep proportions intact. Choose the transparent variant for the intended surface. Leave at least one mark-width of surrounding space where practical. Avoid effects, recolouring, stretching or placing the logo over busy photography. These are suggested usage conventions for these exports, not a separately approved brand strategy.

`brand-kit-preview.png` shows the main variants. `build-kit.py` preserves the generation source; it uses Pillow and fontTools, with the latter installed only in `/tmp/atlasiq-brand-deps` during this session. Change that dependency path if regenerating elsewhere. Source fonts are included; paths in the script currently refer to this project location.

Verification: all eight SVGs parsed, all PNGs decoded, transparent exports checked for both fully transparent and opaque pixels, and the preview visually inspected. Website and product files were not changed.
