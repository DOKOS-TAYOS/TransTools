#!/usr/bin/env bash
set -euo pipefail

echo
echo "===================================="
echo "TransTools Installation"
echo "===================================="
echo

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is not installed."
  exit 1
fi

REPO_URL="${REPO_URL:-https://github.com/DOKOS-TAYOS/TransTools.git}"
REPO_NAME="${REPO_NAME:-TransTools}"

echo "[1/3] Git found:"
git --version

if [ -d "$REPO_NAME" ]; then
  echo
  echo "WARNING: Directory $REPO_NAME already exists."
  cd "$REPO_NAME"
else
  echo
  echo "[2/3] Cloning repository..."
  git clone "$REPO_URL" "$REPO_NAME"
  cd "$REPO_NAME"
fi

echo
echo "[3/3] Running setup..."
chmod +x setup.sh
./setup.sh

echo
echo "Installation complete at: $(pwd)"

