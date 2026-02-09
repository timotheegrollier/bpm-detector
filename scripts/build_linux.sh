#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
VENV="$ROOT/.venv-build"

if [ ! -d "$VENV" ]; then
  "$PYTHON_BIN" -m venv "$VENV"
fi

# shellcheck source=/dev/null
source "$VENV/bin/activate"
python -m pip install --upgrade pip
pip install -r "$ROOT/requirements.txt" pyinstaller

FFMPEG_BIN="${FFMPEG_BINARY:-}"
if [ -z "$FFMPEG_BIN" ]; then
  CAND="$ROOT/packaging/ffmpeg/linux/ffmpeg"
  if [ -f "$CAND" ]; then
    FFMPEG_BIN="$CAND"
  fi
fi

if [ -z "$FFMPEG_BIN" ]; then
  echo "ffmpeg introuvable. Place-le dans packaging/ffmpeg/linux/ffmpeg ou definis FFMPEG_BINARY." >&2
  exit 1
fi

# Fix permissions for libraries that PyInstaller needs to scan
find "$VENV" -name "*.so*" -exec chmod +x {} + 2>/dev/null || true

chmod +x "$FFMPEG_BIN"

# Use the cross-platform spec file and force output to the project root dist/
pyinstaller --noconfirm --clean \
  --distpath "$ROOT/dist" \
  --workpath "$ROOT/build" \
  "$ROOT/bpm-detector.spec"

echo "OK -> $ROOT/dist/BPM-Detector-Pro"
