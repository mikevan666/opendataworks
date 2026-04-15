#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PROJECT_ROOT/.." && pwd)"

VERSION_FILE="$PROJECT_ROOT/VERSION"
VERSION="${VERSION:-}"
GOOS="${GOOS:-linux}"
GOARCH="${GOARCH:-amd64}"
OUTPUT_ROOT="${OUTPUT_ROOT:-$REPO_ROOT/output/releases/opendataagent}"
SYNC_SCRIPT="$PROJECT_ROOT/scripts/sync-root-skills.sh"

usage() {
  cat <<'EOF'
Usage: opendataagent/scripts/build-release.sh [options]

Options:
  --version <version>   Release version, defaults to opendataagent/VERSION
  --goos <goos>         Target GOOS, default linux
  --goarch <goarch>     Target GOARCH, default amd64
  --output <path>       Output root, default output/releases/opendataagent
  -h, --help            Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      VERSION="$2"
      shift 2
      ;;
    --goos)
      GOOS="$2"
      shift 2
      ;;
    --goarch)
      GOARCH="$2"
      shift 2
      ;;
    --output)
      OUTPUT_ROOT="$2"
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

if [[ -z "$VERSION" ]]; then
  VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"
fi

"$SYNC_SCRIPT"

RELEASE_ROOT="$OUTPUT_ROOT/$VERSION"
PACKAGE_ROOT="$RELEASE_ROOT/opendataagent"
SERVER_OUT="$PACKAGE_ROOT/server"
WEB_OUT="$PACKAGE_ROOT/web"
DEPLOY_OUT="$PACKAGE_ROOT/deploy"
PACKAGE_NAME="opendataagent-${VERSION}-${GOOS}-${GOARCH}"
ARCHIVE_PATH="$OUTPUT_ROOT/${PACKAGE_NAME}.tar.gz"

rm -rf "$PACKAGE_ROOT"
mkdir -p "$SERVER_OUT" "$WEB_OUT" "$DEPLOY_OUT"

export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [[ -s "$NVM_DIR/nvm.sh" ]]; then
  # shellcheck source=/dev/null
  . "$NVM_DIR/nvm.sh"
  nvm use >/dev/null
fi

pushd "$PROJECT_ROOT/web" >/dev/null
npm ci
npm run build
popd >/dev/null

unset GOROOT
export PATH="/usr/local/bin:$PATH"
eval "$(/usr/local/bin/goenv init -)"
export GOCACHE="${GOCACHE:-/tmp/odw-go-cache}"

pushd "$PROJECT_ROOT/server" >/dev/null
CGO_ENABLED=0 GOOS="$GOOS" GOARCH="$GOARCH" go build -o "$SERVER_OUT/opendataagent" ./cmd/opendataagent
popd >/dev/null

cp -R "$PROJECT_ROOT/web/dist/." "$WEB_OUT/"
cp "$PROJECT_ROOT/VERSION" "$PACKAGE_ROOT/VERSION"
cp "$PROJECT_ROOT/README.md" "$PACKAGE_ROOT/README.md"
cp -R "$PROJECT_ROOT/deploy/." "$DEPLOY_OUT/"
cp -R "$PROJECT_ROOT/server/skills" "$SERVER_OUT/skills"
cp -R "$PROJECT_ROOT/server/migrations" "$SERVER_OUT/migrations"

pushd "$RELEASE_ROOT" >/dev/null
find opendataagent -type f -print0 | sort -z | xargs -0 shasum -a 256 > SHA256SUMS
tar -czf "$ARCHIVE_PATH" opendataagent SHA256SUMS
popd >/dev/null

echo "Release bundle created:"
echo "  $ARCHIVE_PATH"
