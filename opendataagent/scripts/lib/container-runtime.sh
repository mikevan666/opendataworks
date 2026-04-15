#!/usr/bin/env bash

detect_container_runtime() {
    if command -v docker >/dev/null 2>&1; then
        echo "docker"
        return 0
    fi
    if command -v podman >/dev/null 2>&1; then
        echo "podman"
        return 0
    fi
    return 1
}

ensure_container_runtime_ready() {
    local runtime="${1:-}"
    case "$runtime" in
        docker)
            docker info >/dev/null 2>&1
            ;;
        podman)
            podman info >/dev/null 2>&1
            ;;
        *)
            return 1
            ;;
    esac
}

detect_compose_cmd() {
    if command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD=(docker-compose)
        COMPOSE_RUNTIME="docker"
        COMPOSE_SUPPORTS_ENV_FILE=true
        return 0
    fi
    if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD=(docker compose)
        COMPOSE_RUNTIME="docker"
        COMPOSE_SUPPORTS_ENV_FILE=true
        return 0
    fi
    if command -v podman >/dev/null 2>&1 && podman compose version >/dev/null 2>&1; then
        COMPOSE_CMD=(podman compose)
        COMPOSE_RUNTIME="podman"
        COMPOSE_SUPPORTS_ENV_FILE=true
        return 0
    fi
    if command -v podman-compose >/dev/null 2>&1; then
        COMPOSE_CMD=(podman-compose)
        COMPOSE_RUNTIME="podman"
        COMPOSE_SUPPORTS_ENV_FILE=false
        return 0
    fi
    return 1
}
