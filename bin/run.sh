#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
  echo "ERROR: .venv not found. Run ./setup.sh first."
  exit 1
fi

source .venv/bin/activate
python src/main.py

