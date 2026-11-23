#!/usr/bin/env bash
# Terminal 1 — the web app (real port 15200; the audience uses it via mitmproxy on 18080)
#   ./run.sh          → start the app
#   ./run.sh reset    → recreate school.db AND comment the fix lines in
#                       load_student() back out (state before the demo)
set -euo pipefail
cd "$(dirname "$0")"
PY=python3
for p in .venv/bin/python ../.venv/bin/python; do [ -x "$p" ] && PY=$p && break; done
case "${1:-run}" in
  reset)
    rm -f school.db
    "$PY" - <<'EOF'
import re
p = "app.py"
s = open(p, encoding="utf-8").read()
s = re.sub(r'^    if student\["mssv"\] != g\.user\["mssv"\]:(.*)\n        abort\(404\)\n',
           r'    # if student["mssv"] != g.user["mssv"]:\1\n    #     abort(404)\n', s, flags=re.M)
open(p, "w", encoding="utf-8").write(s)
EOF
    echo "school.db removed; fix lines in load_student() commented out (IDOR is back)" ;;
  *) exec "$PY" app.py ;;
esac
