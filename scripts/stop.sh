#!/bin/bash

# OpenDataWorks 停止脚本
# 功能：停止所有服务

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOY_DIR="$REPO_ROOT/deploy"
LIB_DIR="$SCRIPT_DIR/lib"
COMPOSE_FILE_NAME="docker-compose.prod.yml"
COMPOSE_FILE="$DEPLOY_DIR/$COMPOSE_FILE_NAME"
ENV_FILE="$DEPLOY_DIR/.env"

# shellcheck source=/dev/null
source "$LIB_DIR/container-runtime.sh"

if ! detect_compose_cmd; then
    echo "❌ 错误: 未找到可用的 compose 命令（docker-compose、docker compose、podman compose、podman-compose）"
    exit 1
fi

echo "========================================="
echo "  OpenDataWorks 停止脚本"
echo "========================================="
echo ""

echo "🛑 停止 OpenDataWorks 服务..."
pushd "$DEPLOY_DIR" >/dev/null
ENV_FLAG_ARGS=()
if [ "$COMPOSE_SUPPORTS_ENV_FILE" = true ] && [ -f "$ENV_FILE" ]; then
    ENV_FLAG_ARGS=(--env-file "$ENV_FILE")
fi

"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE_NAME" "${ENV_FLAG_ARGS[@]}" down
popd >/dev/null

echo ""
echo "✅ 所有服务已停止"
echo ""
echo "📝 提示："
echo "  - 数据卷已保留，重新启动后数据不会丢失"
ENV_FLAG_TEXT=""
if [ ${#ENV_FLAG_ARGS[@]} -gt 0 ]; then
    ENV_FLAG_TEXT=" --env-file $ENV_FILE"
fi

echo "  - 如需完全清理（包括数据），运行: ${COMPOSE_CMD[*]} -f $COMPOSE_FILE$ENV_FLAG_TEXT down -v"
echo ""
