# OpenDataWorks Deployment Guide

This guide covers both Online (source code) and Offline (deployment package) deployment methods.

## Deployment Topology

当前仓库维持两条并行智能体产品线：

- 主前端内嵌的“智能问数”
  - 跟随根 `deploy/` 一起部署
  - 运行时依赖 `dataagent-backend`
  - 当前仍是生产可用主链
- 独立的 `opendataagent`
  - 使用 [opendataagent/deploy/docker-compose.yml](/Users/guoruping/.codex/worktrees/92ff/opendataworks/opendataagent/deploy/docker-compose.yml) 单独部署
  - 不由主前端内嵌，也不通过主前端菜单跳转
  - 与现有智能问数并行存在，不互相替换

根 `deploy/` 文档只覆盖主门户与现有智能问数链路。`opendataagent` 的部署说明见 [opendataagent/README.md](/Users/guoruping/.codex/worktrees/92ff/opendataworks/opendataagent/README.md)。

## Directory Contents

- `../scripts/start.sh`: Starts the application. Checks for `.env` and creates it if missing.
- `../scripts/stop.sh`: Stops all services.
- `../scripts/restart.sh`: Restarts all services.
- `../scripts/load-images.sh`: Loads Docker images from `docker-images/` (Offline mode).
- `../scripts/create-offline-package.sh`: Utility to generate an offline deployment package.
- `docker-compose.prod.yml`: Production configuration.
- `.env.example`: Template for environment variables.

---

## 1. Online Deployment (From Source)

Use this method if you have internet access and are deploying directly from the source code repository.

### Prerequisites
- Docker and Docker Compose installed.
- Internet access to pull images from Docker Hub.

### Steps
1. **Navigate to deploy directory**:
   ```bash
   cd deploy
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env for database credentials; DolphinScheduler config is set in System Settings after startup
   vim .env
   ```

3. **Start Services**:
   ```bash
   ../scripts/start.sh
   ```

   主链路默认地址：
   - 门户首页: `http://localhost:8081/`
   - 主前端智能问数入口: `http://localhost:8081/intelligent-query`
   - DataAgent Backend: `http://localhost:8900`
   - Portal MCP Health: `http://localhost:8801/health`
   - Portal MCP Streamable HTTP: `http://localhost:8801/mcp`

   说明：
   - 大模型供应商、Token 与候选模型在主前端配置页中维护，后端保存到 DataAgent 配置存储。
   - 可直接编辑挂载文件后生效：
     - `dataagent/.claude/skills/`
   - 现有智能问数仍通过 `dataagent-nl2sql/bin/odw-cli` 调 backend `/api/v1/ai/metadata/*` 只读接口获取 metadata / lineage / datasource 解析；需保证 `AGENT_API_SERVICE_TOKEN` 在 backend 与 DataAgent 容器中一致。
   - `portal-mcp` 继续随根部署提供，但它不是 `opendataagent` 共享平台 skill 的主链入口。
   - `opendataagent` 不随这里的 compose 自动启动，需要单独进入 `opendataagent/deploy/` 部署。
   - `skills/` 根目录中的共享 skill 主要服务 `opendataagent`；它不会替代当前生产智能问数使用的 `dataagent/.claude/skills/dataagent-nl2sql` 主链。
   - DataAgent 额外持久化一个名为 `dataagent-home` 的 Docker volume，用于保存 Claude Agent SDK 写入 `HOME` 下的本地 session 文件。当前镜像内 `HOME=/tmp/dataagent-home`，SDK 会将会话落到 `~/.claude/projects/<sanitized-cwd>/`，因此该 volume 可覆盖历史智能问数话题的 `resume` 所需文件。
   - 若执行 `docker compose down -v` 或手动删除 `dataagent-home` volume，Claude SDK 本地 session 文件会被清空；此时旧话题会退回到“重放历史 prompt”的兼容路径，直到该话题再次跑出新的真实 SDK session id。

   > **💡 数据库自动初始化**: MySQL 容器首次启动时，会自动执行 `deploy/database/mysql/` 目录下的初始化脚本，创建 `opendataworks` / `dataagent` 数据库，并分别初始化 `opendataworks`、`dataagent` 两个应用用户。DataAgent 容器启动时会先执行 `alembic upgrade head`，再启动服务。
   >
   > 若保留旧的 `mysql-data` volume 升级，初始化脚本不会重跑；切换到独立 `dataagent` 用户前，需要先手动补建该用户或清空 volume 重新初始化。
   >
   > DataAgent 在 `docker-compose.prod.yml` 中默认以非 root 用户运行（`DATAAGENT_RUNTIME_UID/GID`，默认 `1000:1000`）。若 `dataagent/.claude/skills/` 无法写入，请把这两个值改成宿主机目录拥有者的 UID/GID，或先调整目录权限。

---

## 2. Offline Deployment (Using Package)

Use this method for isolated environments without internet access. You will use the `opendataworks-deployment-*.tar.gz` package.

### Prerequisites
- Docker or Podman installed on the target machine.
- The offline deployment package (`opendataworks-deployment-*.tar.gz`).

### Steps
1. **Extract Package**:
   ```bash
   tar -xzf opendataworks-deployment-*.tar.gz
   cd opendataworks-deployment
   ```

2. **Load Images**:
   This loads all required Docker images from the local archive.
   ```bash
   scripts/load-images.sh
   ```

3. **Configure Environment**:
   ```bash
   cp deploy/.env.example deploy/.env
   # Edit .env and configure settings
   vim deploy/.env
   ```

4. **Start Services**:
   ```bash
   scripts/start.sh
   ```

   离线包中的主链地址：
   - 门户首页: `http://localhost:8081/`
   - 主前端智能问数入口: `http://localhost:8081/intelligent-query`
   - DataAgent Backend: `http://localhost:8900`
   - Portal MCP Health: `http://localhost:8801/health`
   - Portal MCP Streamable HTTP: `http://localhost:8801/mcp`

   说明：
   - 离线包内保留 `deploy/dataagent-runtime/skills/` 可直接编辑。
   - 大模型供应商、Token 与候选模型仍通过主前端配置页管理。
   - 现有智能问数仍通过 `dataagent-nl2sql/bin/odw-cli` 调 backend `/api/v1/ai/metadata/*` 只读接口获取 metadata / lineage / datasource 解析。
   - `portal-mcp` 作为独立兼容服务一并部署，但不代表 `opendataagent` 平台 skill 依赖 MCP。
   - `opendataagent` 需要用它自己的部署包或 compose 单独部署，不包含在这里的离线包主链描述中。
   - DataAgent 额外持久化一个名为 `dataagent-home` 的 Docker volume，用于保存 Claude Agent SDK 写入 `HOME` 下的本地 session 文件。当前镜像内 `HOME=/tmp/dataagent-home`，SDK 会将会话落到 `~/.claude/projects/<sanitized-cwd>/`，因此该 volume 可覆盖历史智能问数话题的 `resume` 所需文件。
   - 若执行 `docker compose down -v` 或手动删除 `dataagent-home` volume，Claude SDK 本地 session 文件会被清空；此时旧话题会退回到“重放历史 prompt”的兼容路径，直到该话题再次跑出新的真实 SDK session id。

   > **💡 数据库自动初始化**: MySQL 容器首次启动时，会自动执行 `deploy/database/mysql/` 目录下的初始化脚本，创建 `opendataworks` / `dataagent` 数据库，并分别初始化 `opendataworks`、`dataagent` 两个应用用户。DataAgent 容器启动时会先执行 `alembic upgrade head`，再启动服务。
   >
   > 若保留旧的 `mysql-data` volume 升级，初始化脚本不会重跑；切换到独立 `dataagent` 用户前，需要先手动补建该用户或清空 volume 重新初始化。
   >
   > 离线包中的 DataAgent 也默认以非 root 用户运行（`DATAAGENT_RUNTIME_UID/GID`，默认 `1000:1000`）。若 `deploy/dataagent-runtime/skills/` 无法写入，请把这两个值改成目标机器目录拥有者的 UID/GID，或先调整目录权限。

---

## Common Operations

### Stop Services
```bash
# Online (from root)
scripts/stop.sh
# Offline (from package root)
scripts/stop.sh
```

### Restart Services
```bash
# Online (from root)
scripts/restart.sh
# Offline (from package root)
scripts/restart.sh
```

### Check Logs
```bash
# View logs for a specific service (e.g., backend)
docker-compose -f docker-compose.prod.yml logs -f backend
```
