#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOY_DIR="$PROJECT_ROOT/deploy"
LIB_DIR="$SCRIPT_DIR/lib"
COMPOSE_FILE_NAME="docker-compose.yml"
ENV_FILE="$DEPLOY_DIR/.env"

# shellcheck source=/dev/null
source "$LIB_DIR/container-runtime.sh"

if ! detect_compose_cmd; then
    echo "no compose command found" >&2
    exit 1
fi

pushd "$DEPLOY_DIR" >/dev/null
if [[ "$COMPOSE_SUPPORTS_ENV_FILE" = true && -f "$ENV_FILE" ]]; then
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE_NAME" --env-file "$ENV_FILE" down
else
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE_NAME" down
fi
popd >/dev/null
