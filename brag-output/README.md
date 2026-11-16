# AtlasIQ Corridor Lifeline film

22-second, 1920×1080, 30fps local prototype film with music and interface sounds. No narration. Open brag.mp4 to watch; brag.jpg is the chosen notice-desk poster, baked into frame zero. share-copy.txt is the caption. Credits are in CREDITS.md.

Editable Hyperframes source lives in composition/. The local preview is http://localhost:8780/#project/composition while the preview server is running.

## Verification
Hyperframes 0.9.21 check passed: zero lint, runtime, layout, contrast or audio errors; 22/22 sampled text contrast checks passed. Two intentional still-screen holds were flagged as craft warnings and retained for reading. All five scene midpoints and the final hold were visually inspected in the contact sheet. Screenshots contain existing saved and illustrative states, not newly collected live data.

Final file: H.264 video, AAC audio, 660 video frames, 30fps, 22.016-second container duration (22 seconds of video plus audio padding). Entire final export decoded without errors. media-verification.json, decode-verification.log, check.json and audio-verification.log retain results.

The optional audio-reactive treatment was omitted because its helper was unavailable. All rendering was local. No product behaviour, current rail verification, live data, alerts or hosting changed.

To render again on this Mac, add the following directories to the command path: /Users/a111/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin and /Users/a111/.local/share/atlasiq-video-tools/bin. Run /Users/a111/.local/share/atlasiq-video-tools/node_modules/.bin/hyperframes from composition/. A new machine needs Node 22+, FFmpeg/FFprobe and Hyperframes 0.9.21.
