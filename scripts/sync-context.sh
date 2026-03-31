#!/usr/bin/env bash
#
# Sync context/ -> references/ so the comprehensive skill
# stays in sync with the shared source of truth.
# Run before releases or after updating context files.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SRC="$REPO_ROOT/context"
DST="$REPO_ROOT/references"

if [ ! -d "$SRC" ]; then
  echo "ERROR: Source directory not found: $SRC" >&2
  exit 1
fi

mkdir -p "$DST/examples"

cp "$SRC/sdk_reference.md" "$DST/"
cp "$SRC/patterns_and_gotchas.md" "$DST/"
cp "$SRC/metrics_reference.md" "$DST/"
cp "$SRC/examples/"* "$DST/examples/"

echo "Synced context/ -> references/"
echo "  sdk_reference.md       $(wc -l < "$DST/sdk_reference.md") lines"
echo "  patterns_and_gotchas.md $(wc -l < "$DST/patterns_and_gotchas.md") lines"
echo "  metrics_reference.md   $(wc -l < "$DST/metrics_reference.md") lines"
echo "  examples/              $(ls "$DST/examples/" | wc -l) files"
