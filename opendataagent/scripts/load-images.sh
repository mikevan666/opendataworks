#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"
IMAGE_DIR="$PROJECT_ROOT/deploy/docker-images"

# shellcheck source=/dev/null
source "$LIB_DIR/container-runtime.sh"

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

die() {
    log "ERROR: $*"
    exit 1
}

if ! CONTAINER_CMD="$(detect_container_runtime)"; then
    die "docker or podman is required"
fi
if ! ensure_container_runtime_ready "$CONTAINER_CMD"; then
    die "$CONTAINER_CMD is not ready"
fi

[[ -d "$IMAGE_DIR" ]] || die "image directory not found: $IMAGE_DIR"

REQUIRED_IMAGES=(
    "opendataagent-server.tar"
    "opendataagent-web.tar"
    "mysql-8.0.tar"
)

for archive in "${REQUIRED_IMAGES[@]}"; do
    [[ -f "$IMAGE_DIR/$archive" ]] || die "missing image archive: $archive"
done

for archive in "${REQUIRED_IMAGES[@]}"; do
    log "Loading $archive"
    "$CONTAINER_CMD" load -i "$IMAGE_DIR/$archive"
done

IMAGE_TAG="latest"
if [[ -f "$IMAGE_DIR/manifest.json" ]]; then
    tag_line="$(grep -o '"target": *"opendataagent-server:[^"]*"' "$IMAGE_DIR/manifest.json" 2>/dev/null || true)"
    if [[ -n "$tag_line" ]]; then
        IMAGE_TAG="${tag_line##*:}"
        IMAGE_TAG="${IMAGE_TAG%\"}"
    fi
fi

for image in "opendataagent-server:${IMAGE_TAG}" "opendataagent-web:${IMAGE_TAG}" "mysql:8.0"; do
    localhost_image="localhost/$image"
    if "$CONTAINER_CMD" images --format "{{.Repository}}:{{.Tag}}" | grep -q "^$localhost_image$"; then
        log "Retagging $localhost_image -> $image"
        "$CONTAINER_CMD" tag "$localhost_image" "$image"
        "$CONTAINER_CMD" rmi "$localhost_image" >/dev/null 2>&1 || true
    fi
done

log "Loaded images:"
"$CONTAINER_CMD" images | grep -E "opendataagent|mysql" | grep -E "${IMAGE_TAG}|8.0" || true
