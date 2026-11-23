#!/usr/bin/env bash
# Terminal 2 — mitmweb as a reverse proxy in front of the app.
#   Open the app through : http://127.0.0.1:18080   (every packet passes mitmproxy)
#   Watch packets at     : http://127.0.0.1:18081   (mitmweb UI)
# Keep this running for the whole demo: restarting the app after the fix
# does not clear the captured flows, so before/after stay side by side.
set -euo pipefail
cd "$(dirname "$0")"
MITMWEB=mitmweb
for p in .venv/bin/mitmweb ../.venv/bin/mitmweb; do [ -x "$p" ] && MITMWEB=$p && break; done
fuser -k 18080/tcp 18081/tcp 2>/dev/null || true
exec "$MITMWEB" --mode reverse:http://127.0.0.1:15200@18080 \
  --listen-host 127.0.0.1 --set web_port=18081 --set web_open_browser=false
