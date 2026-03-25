# OpenDataWorks Deployment Guide

This guide covers both Online (source code) and Offline (deployment package) deployment methods.

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

   DataAgent 默认地址：
   - 主前端智能问数入口: `http://localhost:8081/intelligent-query`
   - DataAgent Backend: `http://localhost:8900`
   - Portal MCP Health: `http://localhost:8801/health`
   - Portal MCP Streamable HTTP: `http://localhost:8801/mcp`
   - 大模型供应商、Token 与候选模型请在主前端配置页中维护，后端保存到 DataAgent 配置存储
   - 可直接编辑挂载文件后生效：
     - `dataagent/.claude/skills/`（Skills 目录）
     - 动态元数据查询示例在 skill 的 `references/` / `scripts/` 中，不再由后端同步生成 metadata 快照
   - DataAgent 默认通过 skill 自带的 `dataagent-nl2sql/bin/odw-cli` 调 backend `/api/v1/ai/metadata/*` 只读接口获取 metadata / lineage / datasource 解析；需保证 `AGENT_API_SERVICE_TOKEN` 在 backend 与 DataAgent 容器中一致
   - 若对应 skill 目录下缺少 `dataagent-nl2sql/bin/odw-cli`，需由用户先自行安装到该固定路径，再启动 DataAgent
   - `scripts/start.sh` 会在启动前对挂载的 `odw-cli` 执行一次宿主机侧 `chmod +x`；即使 bind mount 丢了执行位，DataAgent runtime 也会回退为 `sh /app/.claude/skills/dataagent-nl2sql/bin/odw-cli ...`
   - `portal-mcp` 是新增复用入口，默认通过 `X-Portal-MCP-Token` 访问；它调用 backend `/api/v1/ai/metadata/*` 与 `/api/v1/ai/query/read`，但不会替代现有 NL2SQL skill 主链路
   - 主前端默认通过同源 `/api` 代理访问 DataAgent 后端，无需额外配置前端地址

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

   DataAgent 默认地址：
   - 主前端智能问数入口: `http://localhost:8081/intelligent-query`
   - DataAgent Backend: `http://localhost:8900`
   - Portal MCP Health: `http://localhost:8801/health`
   - Portal MCP Streamable HTTP: `http://localhost:8801/mcp`
   - 离线包内保留 `deploy/dataagent-runtime/skills/` 可直接编辑
   - 大模型供应商、Token 与候选模型仍通过主前端配置页管理
   - 动态元数据查询示例保留在 skill 的 `references/` / `scripts/` 中
   - DataAgent 默认通过 skill 自带的 `dataagent-nl2sql/bin/odw-cli` 调 backend `/api/v1/ai/metadata/*` 只读接口获取 metadata / lineage / datasource 解析；需保证 `AGENT_API_SERVICE_TOKEN` 在 backend 与 DataAgent 容器中一致
   - 若对应 skill 目录下缺少 `dataagent-nl2sql/bin/odw-cli`，需由用户先自行安装到该固定路径，再启动 DataAgent
   - `scripts/start.sh` 会在启动前对挂载的 `odw-cli` 执行一次宿主机侧 `chmod +x`；即使 bind mount 丢了执行位，DataAgent runtime 也会回退为 `sh /app/.claude/skills/dataagent-nl2sql/bin/odw-cli ...`
   - `portal-mcp` 作为独立远程 MCP 服务一并部署，客户端需带 `X-Portal-MCP-Token`

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
