#!/usr/bin/env bash
set -euo pipefail

echo
echo "===================================="
echo "TransTools Installation"
echo "===================================="
echo

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is not installed or not in PATH."
  exit 1
fi

REPO_URL="${REPO_URL:-https://github.com/DOKOS-TAYOS/TransTools.git}"
REPO_NAME="${REPO_NAME:-TransTools}"

echo "[1/4] Git found:"
git --version

echo
echo "[2/4] Preparing target folder..."
if [ -e "$REPO_NAME" ] && [ ! -d "$REPO_NAME" ]; then
  echo "ERROR: $REPO_NAME already exists and is not a directory."
  exit 1
fi

if [ -d "$REPO_NAME" ]; then
  if [ -f "$REPO_NAME/setup.sh" ] && [ -f "$REPO_NAME/pyproject.toml" ]; then
    echo "Existing TransTools checkout detected in $REPO_NAME."
    cd "$REPO_NAME"
  else
    echo "ERROR: $REPO_NAME already exists but does not look like a TransTools checkout."
    echo "Choose another folder name with REPO_NAME or rename the existing directory and try again."
    exit 1
  fi
else
  echo
  echo "[3/4] Cloning repository..."
  git clone "$REPO_URL" "$REPO_NAME"
  cd "$REPO_NAME"
fi

echo
echo "[4/4] Running setup..."
bash "./setup.sh" "$@"

echo
echo "Installation complete."
echo "Folder: $(pwd)"
echo "Next run command: ./bin/run.sh"

