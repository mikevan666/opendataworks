#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PROJECT_ROOT/.." && pwd)"

SOURCE_ROOT="${1:-$REPO_ROOT/skills}"
TARGET_ROOT="${2:-$PROJECT_ROOT/server/skills}"

if [[ ! -d "$SOURCE_ROOT" ]]; then
  echo "skills source not found: $SOURCE_ROOT" >&2
  exit 1
fi

rm -rf "$TARGET_ROOT/bundled" "$TARGET_ROOT/bin" "$TARGET_ROOT/lib"
mkdir -p "$TARGET_ROOT/bundled" "$TARGET_ROOT/bin" "$TARGET_ROOT/lib"

if [[ -d "$SOURCE_ROOT/bin" ]]; then
  cp -R "$SOURCE_ROOT/bin/." "$TARGET_ROOT/bin/"
fi
if [[ -d "$SOURCE_ROOT/lib" ]]; then
  cp -R "$SOURCE_ROOT/lib/." "$TARGET_ROOT/lib/"
fi

for group in platform generic; do
  if [[ ! -d "$SOURCE_ROOT/$group" ]]; then
    continue
  fi
  for skill_dir in "$SOURCE_ROOT/$group"/*; do
    [[ -d "$skill_dir" ]] || continue
    cp -R "$skill_dir" "$TARGET_ROOT/bundled/$(basename "$skill_dir")"
  done
done

chmod +x "$TARGET_ROOT/bin/odw-cli" "$SCRIPT_DIR/sync-root-skills.sh" || true

echo "Synced root skills from $SOURCE_ROOT to $TARGET_ROOT"
