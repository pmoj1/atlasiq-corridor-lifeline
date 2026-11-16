#!/bin/zsh
cd -- "$(dirname -- "$0")" || exit 1
PYTHON="/Users/a111/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
echo "AtlasIQ local preview: http://127.0.0.1:8765"
echo "Press Control-C to stop."
"$PYTHON" -m http.server 8765 --bind 127.0.0.1 --directory draft
