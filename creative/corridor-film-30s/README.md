# AtlasIQ — Before the disruption

A 30.000-second / 1920 × 1080 / 30 fps brand film, developed from the founder's request for a cinematic premium technology-keynote treatment, realistic narration, photographic animation and a clear motion-graphics story. The original 15-second project is preserved in the sibling corridor-explainer folder.

## Deliverables

- exports/AtlasIQ-30s-voiceover.mp4 — full stereo voice, original music and effects
- exports/AtlasIQ-30s-captioned.mp4 — the same film with burned-in narration captions
- exports/AtlasIQ-30s-silent.mp4 — no audio stream; the on-screen story stands alone
- exports/AtlasIQ-captions.srt — editable timed captions
- MASTER_PROMPT.md — the master creative prompt, written before production
- film.json — editable titles, scene timing, palette and production metadata
- render.py — separate photographic, vehicle, atmosphere/map, interface, typography and logo functions
- audio/ — separate narration, music and effects WAV stems, plus the neural voice source
- project.html + editor.py — local motion editor with scrubbing, layer isolation, title editing and re-rendering

## Open and edit

On this Mac, double-click Start Editor.command, then open http://127.0.0.1:8767/project.html. This serves only on the local loopback address. Stop it with Ctrl-C in its terminal. It does not publish the project.

You can play the completed exports, click a scene thumbnail, scrub a frame, turn individual layers on/off, edit the six headlines and save. “Render all three MP4s” renders from the current source. Export renders use all layers; visibility switches are preview isolation controls. If moving the project to another machine, install requirements.txt and run `python editor.py`; the supplied launcher points to this Mac's bundled interpreter.

The editable delivery is a Python/HTML motion project with full-resolution assets and independent audio stems. It is not an After Effects, Premiere, Blender or DaVinci Resolve native project. Motion/layout/materials are editable in render.py; six main titles are editable in the browser. Interface wording is editable in its corresponding renderer function.

## Visual production

The photographic scenes were generated with the built-in image-generation tool. They are illustrative imagery, not real incident footage or location documentation. The opening vehicle is separately extracted and composited with independent position/scale movement over a clean road plate. Other photographic scenes use camera travel and atmosphere layers. The map uses public-domain Natural Earth country geometry set on a shallow dimensional plane. Route paths are geographic schematics, not navigation data. Rain, data traces, pulses, interface perspective, title entrances, transitions and anamorphic light accents are animated in the renderer.

This is image-based photographic animation plus designed motion graphics, not a fully generated live-action video. Runway was discovered and suggested for full video generation; the authentication check returned USER_NOT_LOGGED_IN, so no Runway generation or purchase was performed.

The film takes general craft cues from premium technology launch films: ample space, limited colour, large typography, optical depth, restrained timing and clear visual hierarchy. No Apple branding, copied interface or trademark sound is included.

## Brand and sources

Logo geometry and typography preserve the AtlasIQ website CSS observed at https://atlasiqco.com/ on 11 October 2026: 30px amber mark with 9px rounding, six-point inset cutout, Space Grotesk bold wordmark with amber IQ. Colour palette uses #071522, #FFA028 and #EAF0F9. Space Grotesk comes from Google Fonts under the included SIL OFL license. Geography: Natural Earth 1:110m admin-0 country polygons, public domain, copied from the previous project.

## Narration and sound

The new narration uses Australian English neural speech, en-AU-WilliamNeural, via edge-tts (https://github.com/rany2/edge-tts). This is synthetic narration, not a human actor. A complete natural-rate take was generated, and the sentence groups were spaced to match the edit with tiny boundary fades. No time compression or pitch shifting was used. The written pronunciation is “Atlas IQ”; on-screen branding remains “AtlasIQ”.

Music and effects are original procedural stereo synthesis at 102 BPM. Narration is centred; soft harmonies, pulse, atmosphere, signal ticks and a resolving chord sit underneath. audio/audio-report.json records the mix peak and segment placement. No third-party music recording is used.

## Verification

Run `python verify.py` using the same interpreter as the renderer. Verification checks all three MP4 dimensions, 30 fps, 900 frames, exactly 30 seconds, expected audio streams, full decode, audio peak and the final two-second static source-frame hold. The final hold is checked against the source because lossy encoders can introduce tiny changes in decoded identical frames. The browser editor is also checked for playback, frame scrubbing and layer isolation. See verification.json for actual results.

## Scope

The film depicts an in-development concept. “Concept preview”, “In development”, “Ready for review” and “Review before submission” are preserved. It does not claim calibrated prediction accuracy, automatic regulatory acceptance or a working permit-submission product. No product code, live corridor inputs, alert delivery or commercial deployment was changed. A vertical edition requires recomposition; this is a 16:9 master.
