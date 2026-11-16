#!/bin/zsh
cd "${0:A:h}" || exit 1
desk_python='/usr/bin/python3'
if [[ ! -x "$desk_python" ]]; then desk_python=python3; fi
desk_url='http://127.0.0.1:8770/'
desk_logdir="$HOME/Library/Logs/AtlasIQ"
desk_ready() {
  curl --silent --fail --max-time 1 "${desk_url}api/status" | grep -q '"running"'
}
if ! desk_ready; then
  mkdir -p "$desk_logdir" || exit 1
  # Detach from the launcher terminal; no login item or schedule is installed.
  desk_pid=$("$desk_python" - "$desk_logdir/corridor.log" <<'PYLAUNCH'
import subprocess, sys
with open(sys.argv[1], 'ab', buffering=0) as log:
    process = subprocess.Popen([sys.executable, '-u', '-m', 'corridor_lifeline.dashboard', '--port', '8770'],
        stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
print(process.pid)
PYLAUNCH
)
  for desk_attempt in {1..120}; do
    if desk_ready; then break; fi
    if ! kill -0 "$desk_pid" 2>/dev/null; then
      print "AtlasIQ could not start. See $desk_logdir/corridor.log"
      exit 1
    fi
    sleep 0.5
  done
fi
if ! desk_ready; then
  print "AtlasIQ did not become ready. See $desk_logdir/corridor.log"
  exit 1
fi
if [[ "${1:-}" != '--no-open' ]]; then open "${desk_url}#weather"; fi
