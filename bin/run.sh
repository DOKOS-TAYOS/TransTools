#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -x ".venv/bin/python" ]; then
  echo "ERROR: .venv/bin/python was not found. Run ./setup.sh first."
  exit 1
fi

.venv/bin/python src/bootstrap_cli.py run "$@"

