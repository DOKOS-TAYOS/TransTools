#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo
echo "===================================="
echo "TransTools Setup (Linux/macOS)"
echo "===================================="
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is not installed or not in PATH"
  exit 1
fi

echo "[1/6] Checking Python version..."
python3 --version
python3 - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 12) else 1)
PY
echo "Python version OK"

echo
echo "[2/6] Creating virtual environment..."
if [ -d ".venv" ]; then
  echo "Virtual environment already exists"
else
  python3 -m venv .venv
  echo "Virtual environment created"
fi

echo
echo "[3/6] Activating virtual environment..."
source .venv/bin/activate

echo
echo "[4/6] Upgrading pip..."
python -m pip install --upgrade pip

echo
echo "[5/6] Installing dependencies..."
pip install -r requirements.txt

echo
echo "[6/6] Setting up environment file..."
if [ -f ".env" ]; then
  echo ".env already exists, skipping"
else
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo ".env created from .env.example"
  else
    echo "Warning: .env.example not found"
  fi
fi

echo
echo "Setup complete."
echo "Run: ./bin/run.sh"

