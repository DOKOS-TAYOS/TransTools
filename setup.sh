#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
  python3 src/bootstrap_cli.py setup "$@"
  exit $?
fi

if command -v python >/dev/null 2>&1; then
  python src/bootstrap_cli.py setup "$@"
  exit $?
fi

echo "ERROR: Python 3.12 or newer is required."
echo "Install Python and then run ./setup.sh again."
exit 1

