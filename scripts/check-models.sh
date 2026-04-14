#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CACHE="${MODEL_CACHE_DIR:-/models_cache}"
MANIFEST="${ROOT}/config/models_manifest.yaml"
echo "MODEL_CACHE_DIR=${CACHE}"
if [[ ! -f "${CACHE}/bootstrap_status.json" ]]; then
  echo "bootstrap_status.json missing — run bootstrap-models first"
  exit 1
fi
python3 - <<'PY'
import json, os, sys
from pathlib import Path
c = Path(os.environ.get("MODEL_CACHE_DIR", "/models_cache"))
st = c / "bootstrap_status.json"
if not st.exists():
    sys.exit(1)
d = json.loads(st.read_text())
print(json.dumps(d, indent=2))
if not d.get("ok"):
    sys.exit(1)
PY
