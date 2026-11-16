# AtlasIQ — One shipment. One promise.

A 60-second fictional story: a dispatcher prepares a shipment, conditions change across the Nullarbor, and clearer signals support a human decision and draft paperwork.

## Watch

- `exports/AtlasIQ-60s-voiceover.mp4`: primary film with Australian neural narration, original music and effects.
- `exports/AtlasIQ-60s-captioned.mp4`: same film with burned-in narration captions.
- `exports/AtlasIQ-60s-silent.mp4`: picture only.
- `exports/storyboard.jpg`: all ten scenes.

All three are 1920 × 1080, 30 fps, exactly 60.000 seconds. The completed brand card holds still for the final 2.5 seconds. The silent edition uses sparse titles, physical screen graphics and draft document typography; the captioned edition carries the full story when played muted.

## Edit locally

Double-click `Start Editor.command`, then open http://127.0.0.1:8768/project.html. Keep the terminal open while editing. The launcher uses this Mac's bundled Python. On another machine, install `requirements.txt` and run `python editor.py`.

The editor supports playback of each export, timeline scrubbing, layer isolation, title changes and re-rendering. Titles are in `film.json`; scene timing, camera moves, perspective screen/paper mapping, graphics, captions and audio placement are in `render.py`. New exports overwrite only this project's three MP4s. Editing source previews does not update a rendered MP4 until you render again. The composition uses raster photographs plus editable, programmatically drawn typography/interfaces. It is an HTML/Python project, not an After Effects or Premiere file.

Separate WAV stems in `audio/`: `voiceover.wav`, `music.wav`, `effects.wav`, `mix.wav`. Captions are also provided as SRT. The original neural take and its timing file are retained, with speech segments repositioned without time stretching. The voice is `en-AU-WilliamNeural`, synthesised at -10% rate.

Run `python render.py --stills` for ten source stills; `python render.py` for all exports; `python verify.py` to check frame counts, full decoding, audio presence, PCM clipping and final hold.

## Sources and limitations

Seven new photographic plates were generated using the built-in image tool. Exact prompts are in `assets/generation-prompts.json`. The departure and storm photographs are reused from the 30-second sibling project, whose original prompt record is included as `assets/REUSED-ASSET-PROMPTS.md`. The woman and story are fictional. Generated scenes are animated through image-based camera motion, perspective compositing and rain; people and trucks are not fully animated live-action performances. No live incident footage, customer results or successful shipment outcome is claimed. Neural narration is synthetic, not a human studio recording. Music, freight atmosphere, rain and chimes are procedural original synthesis.

Brand geometry and wordmark were reconstructed from the CSS of https://atlasiqco.com inspected in the preceding creative session: amber #FFA028, navy #071522 and Space Grotesk. The font license is included. Unused Natural Earth geography is retained as an optional reusable production asset; it is not an operational map.

`MASTER_PROMPT.md` records the direction before production. Final edit differences: the document cut begins at 43 seconds and the parked-truck cut at 50; the laptop uses three readable source panels instead of a map; photographic shots use shallow 44px top/bottom mattes; screen and paper information is static once revealed, with camera movement continuing. There are no moving lips, wheels or hand gestures, independent character performance or real lens simulation. Generated continuity is approximate, including fleet vehicles and office background detail. The final card returns to full frame.

Product screens and paperwork are illustrative concepts, not live operational data. Elevated risk is not a calibrated probability or guaranteed closure prediction. Rail information needs verification. Documents explicitly require human review and imply no permit approval. No publishing or product-code changes were performed.
