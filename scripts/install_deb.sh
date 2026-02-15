#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 /path/to/bpm-detector_VERSION_amd64.deb" >&2
}

if [ $# -ne 1 ]; then
  usage
  exit 2
fi

if ! command -v apt >/dev/null 2>&1; then
  echo "Error: apt is not available on this system." >&2
  exit 1
fi

DEB_PATH="$1"
if [ ! -f "$DEB_PATH" ]; then
  echo "Error: file not found: $DEB_PATH" >&2
  exit 2
fi

# Stage in /tmp so _apt can read it, avoiding the unsandboxed download warning.
STAGE_DIR="/tmp/bpm-detector-deb"
mkdir -p "$STAGE_DIR"
STAGE_PATH="$STAGE_DIR/$(basename "$DEB_PATH")"
install -m 0644 "$DEB_PATH" "$STAGE_PATH"

echo "Installing package from: $STAGE_PATH"
sudo apt install -- "$STAGE_PATH"
