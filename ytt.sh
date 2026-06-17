#!/usr/bin/env bash
# ytt.sh — macOS/Linux launcher for ytt.py. Ensures deps, then passes args through.
# Usage:  ./ytt.sh https://youtu.be/VIDEOID --format srt --out ~/transcripts
#         ./ytt.sh            (prompts for a URL/ID and saves into the current folder)
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "Error: Python 3 is not installed." >&2
  exit 1
fi
PIP="$(command -v pip3 || command -v pip || true)"

"$PY" -c "import youtube_transcript_api" 2>/dev/null || {
  echo "Installing youtube-transcript-api ..."
  "${PIP:-pip3}" install youtube-transcript-api
}
"$PY" -c "import pyperclip" 2>/dev/null || {
  echo "Installing pyperclip (clipboard support) ..."
  "${PIP:-pip3}" install pyperclip || true
}

exec "$PY" "$DIR/ytt.py" "$@"
