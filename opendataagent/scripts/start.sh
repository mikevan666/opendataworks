#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOY_DIR="$PROJECT_ROOT/deploy"
LIB_DIR="$SCRIPT_DIR/lib"
COMPOSE_FILE_NAME="docker-compose.yml"
COMPOSE_FILE="$DEPLOY_DIR/$COMPOSE_FILE_NAME"
ENV_FILE="$DEPLOY_DIR/.env"
ENV_EXAMPLE="$DEPLOY_DIR/.env.example"

# shellcheck source=/dev/null
source "$LIB_DIR/container-runtime.sh"

read_env_value() {
    local key="$1"
    local env_file="$2"
    local line
    local value

    [[ -f "$env_file" ]] || return 0

    line="$(grep -E "^${key}=" "$env_file" | tail -n 1 || true)"
    [[ -n "$line" ]] || return 0

    value="${line#*=}"
    value="${value%$'\r'}"
    value="${value%\"}"
    value="${value#\"}"
    value="${value%\'}"
    value="${value#\'}"
    printf '%s' "$value"
}

resolve_compose_project_name() {
    local configured="${COMPOSE_PROJECT_NAME:-}"

    if [[ -z "$configured" ]]; then
        configured="$(read_env_value "COMPOSE_PROJECT_NAME" "$ENV_FILE")"
    fi

    printf '%s' "${configured:-opendataagent}"
}

[[ -f "$COMPOSE_FILE" ]] || { echo "compose file not found: $COMPOSE_FILE" >&2; exit 1; }

if [[ ! -f "$ENV_FILE" && -f "$ENV_EXAMPLE" ]]; then
    cp "$ENV_EXAMPLE" "$ENV_FILE"
fi

COMPOSE_PROJECT_NAME="$(resolve_compose_project_name)"

if ! detect_compose_cmd; then
    echo "no compose command found" >&2
    exit 1
fi
if ! ensure_container_runtime_ready "$COMPOSE_RUNTIME"; then
    echo "$COMPOSE_RUNTIME is not ready" >&2
    exit 1
fi

pushd "$DEPLOY_DIR" >/dev/null
if [[ "$COMPOSE_SUPPORTS_ENV_FILE" = true ]]; then
    "${COMPOSE_CMD[@]}" -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE_NAME" --env-file "$ENV_FILE" up -d
    "${COMPOSE_CMD[@]}" -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE_NAME" --env-file "$ENV_FILE" ps
else
    "${COMPOSE_CMD[@]}" -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE_NAME" up -d
    "${COMPOSE_CMD[@]}" -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE_NAME" ps
fi
popd >/dev/null

echo "Compose project: $COMPOSE_PROJECT_NAME"
echo "Web:    http://localhost:18080"
echo "Server: http://localhost:18900/api/v1/agent/health"
