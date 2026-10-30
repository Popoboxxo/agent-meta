#!/usr/bin/env bash
# Local CI mirror: isolated venv, same flags as .github/workflows/orchestration-test.yml.
# Usage: scripts/ci-local.sh [smoke|full]   (default: smoke)
#   smoke: sync.py --validate only
#   full:  --validate + pytest -n 2 --dist loadfile (long-running)
set -euo pipefail

cd "$(dirname "$0")/.."
mode="${1:-smoke}"
export PYTHONNOUSERSITE=1

venv=".tmp/ci-venv"
if [ ! -d "$venv" ]; then
  python3 -m venv "$venv"
fi
"$venv/bin/python" -m pip install -q -r tests/requirements.txt

"$venv/bin/python" scripts/sync.py --validate
case "$mode" in
  smoke) ;;
  full) "$venv/bin/python" -m pytest tests/ -q -n 2 --dist loadfile ;;
  *) echo "usage: $0 [smoke|full]" >&2; exit 2 ;;
esac
