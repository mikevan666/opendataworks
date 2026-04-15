#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat <<'EOF'
Usage: scripts/load-package-and-start.sh [options] --package <path>

Options:
  --package <path>     Path to offline tar.gz or extracted directory
  --target-dir <path>  Extraction target when --package is a tar.gz
                       (default: ./opendataagent-deployment)
  --no-start           Load images only
  --no-env-copy        Do not auto-copy deploy/.env.example to deploy/.env
  -h, --help           Show help
EOF
}

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

die() {
    log "ERROR: $*"
    exit 1
}

PACKAGE_PATH=""
TARGET_DIR="./opendataagent-deployment"
DO_START=true
AUTO_COPY_ENV=true

while [[ $# -gt 0 ]]; do
    case "$1" in
        --package)
            PACKAGE_PATH="$2"
            shift 2
            ;;
        --target-dir)
            TARGET_DIR="$2"
            shift 2
            ;;
        --no-start)
            DO_START=false
            shift
            ;;
        --no-env-copy)
            AUTO_COPY_ENV=false
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            if [[ -z "$PACKAGE_PATH" ]]; then
                PACKAGE_PATH="$1"
                shift
            else
                die "unexpected argument: $1"
            fi
            ;;
    esac
done

[[ -n "$PACKAGE_PATH" ]] || die "package path is required"
[[ -e "$PACKAGE_PATH" ]] || die "package path does not exist: $PACKAGE_PATH"

if [[ -f "$PACKAGE_PATH" ]]; then
    case "$PACKAGE_PATH" in
        *.tar.gz|*.tgz)
            ;;
        *)
            die "unsupported archive format: $PACKAGE_PATH"
            ;;
    esac
    mkdir -p "$TARGET_DIR"
    if [[ "$(ls -A "$TARGET_DIR" 2>/dev/null)" ]]; then
        die "target directory not empty: $TARGET_DIR"
    fi
    log "Extracting $PACKAGE_PATH to $TARGET_DIR"
    tar -xzf "$PACKAGE_PATH" --strip-components=1 -C "$TARGET_DIR"
    PACKAGE_DIR="$TARGET_DIR"
elif [[ -d "$PACKAGE_PATH" ]]; then
    PACKAGE_DIR="$PACKAGE_PATH"
else
    die "package path must be a tar.gz or directory"
fi

SCRIPTS_DIR="$PACKAGE_DIR/scripts"
DEPLOY_DIR="$PACKAGE_DIR/deploy"

[[ -d "$SCRIPTS_DIR" ]] || die "scripts directory not found in package"
[[ -d "$DEPLOY_DIR/docker-images" ]] || die "deploy/docker-images not found in package"

log "Loading images"
(cd "$PACKAGE_DIR" && bash "$SCRIPTS_DIR/load-images.sh")

if [[ "$AUTO_COPY_ENV" = true && ! -f "$DEPLOY_DIR/.env" && -f "$DEPLOY_DIR/.env.example" ]]; then
    cp "$DEPLOY_DIR/.env.example" "$DEPLOY_DIR/.env"
fi

if [[ "$DO_START" = true ]]; then
    log "Starting services"
    (cd "$PACKAGE_DIR" && bash "$SCRIPTS_DIR/start.sh")
else
    log "Skipping service start (--no-start)"
fi

log "Package ready at: $PACKAGE_DIR"
