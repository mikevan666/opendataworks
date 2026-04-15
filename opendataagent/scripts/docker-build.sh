#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SYNC_SCRIPT="$PROJECT_ROOT/scripts/sync-root-skills.sh"

VERSION="$(tr -d '[:space:]' < "$PROJECT_ROOT/VERSION")"
TAG="${TAG:-$VERSION}"

usage() {
  cat <<'EOF'
Usage: opendataagent/scripts/docker-build.sh [options]

Options:
  --version <version>   Override version label
  --tag <tag>           Image tag, defaults to VERSION
  -h, --help            Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      VERSION="$2"
      shift 2
      ;;
    --tag)
      TAG="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

"$SYNC_SCRIPT"

docker build -t "opendataagent-server:${TAG}" "$PROJECT_ROOT/server"
docker build -t "opendataagent-web:${TAG}" "$PROJECT_ROOT/web"

echo "Built images:"
echo "  opendataagent-server:${TAG}"
echo "  opendataagent-web:${TAG}"
