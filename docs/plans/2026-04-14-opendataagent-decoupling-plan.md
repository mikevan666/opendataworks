# OpenDataWorks 与 Opendataagent 并行共存实施计划

## Goal

在不影响现有智能问数生产链路的前提下，完成以下收敛：

- 主前端保留原智能问数入口与管理能力
- `opendataagent` 保持独立产品定位
- 根目录建立共享 `skills/`
- `opendataagent` 镜像加载根 `skills/`
- OpenDataWorks 平台能力统一通过 `odw-cli` 提供给 `opendataagent`
- 平台 skill 不包含 `workflow-context`

## Scope

本轮覆盖：

- 恢复主前端原智能问数路由、菜单和配置入口
- 移除主前端新增的 `opendataagent` 外链入口
- 根目录 `skills/` 初始化
- `odw-cli` 初始化
- `opendataagent` 共享 skills 镜像加载
- 新增并行共存设计/计划文档

本轮不覆盖：

- 退役或删除 `dataagent/dataagent-backend`
- 退役主前端智能问数页面
- 主前端与 `opendataagent` 之间的跳转联动
- `workflow-context` Java API

## Execution Steps

### Phase 1: 恢复主前端生产入口

- 恢复 `/intelligent-query`
- 恢复 `/nl2sql -> /intelligent-query`
- 恢复主导航“智能问数”
- 恢复配置页中的 `DataAgentConfig` 和 `SkillStudio`
- 删除主前端中新增的 `opendataagent` 外链按钮

### Phase 2: 共享 Skills 目录

- 新增根目录 `skills/`
- 新增：
  - `skills/platform/opendataworks-platform/`
  - `skills/platform/opendataworks-readonly-sql/`
  - `skills/generic/python-analysis/`
  - `skills/generic/chart-visualization/`
- 新增 `skills/bin/odw-cli`
- 新增 `skills/lib/*` 公共运行时辅助模块

### Phase 3: Opendataagent 镜像加载

- 扩展 `opendataagent/server/internal/config/config.go`
- 扩展 `opendataagent/server/internal/skills/service.go`
- 在应用启动时把根 `skills/` 镜像到 `opendataagent/server/skills/`
- 在 build/release/docker 脚本中统一先执行 root skills sync

### Phase 4: Java API 边界

- 保持 `backend-agent-api` 只读能力主接口：
  - `inspect`
  - `lineage`
  - `resolve-datasource`
  - `export`
  - `ddl`
  - `read-query`
- 不新增 `workflow-context`
- 删除仓库内已落下的 `workflow-context` 半成品

### Phase 5: 文档回归

- 新增设计文档：
  - `docs/design/2026-04-14-opendataagent-decoupling-design.md`
- 新增实施计划：
  - `docs/plans/2026-04-14-opendataagent-decoupling-plan.md`
- 文档明确：
  - 主前端智能问数与 `opendataagent` 并行共存
  - 平台能力统一走 CLI
  - `opendataagent` 保留通用 MCP
  - 平台 skill 不含 `workflow-context`
  - SQL skill 单独存在

## Touched Files

- `frontend/src/router/index.js`
- `frontend/src/views/Layout.vue`
- `frontend/src/views/settings/ConfigurationManagement.vue`
- `backend-agent-api/src/main/java/com/onedata/portal/agentapi/controller/AgentMetadataController.java`
- `backend-agent-api/src/main/java/com/onedata/portal/agentapi/service/AgentMetadataService.java`
- `skills/bin/odw-cli`
- `skills/platform/opendataworks-platform/SKILL.md`
- `skills/platform/opendataworks-readonly-sql/SKILL.md`
- `skills/generic/python-analysis/SKILL.md`
- `skills/generic/chart-visualization/SKILL.md`
- `opendataagent/server/internal/config/config.go`
- `opendataagent/server/internal/skills/service.go`
- `opendataagent/server/internal/app/app.go`
- `opendataagent/scripts/sync-root-skills.sh`
- `opendataagent/scripts/build-release.sh`
- `opendataagent/scripts/docker-build.sh`
- `docs/design/2026-04-14-opendataagent-decoupling-design.md`
- `docs/plans/2026-04-14-opendataagent-decoupling-plan.md`

## Verification

- 搜索确认仓库内不存在 `workflow-context` 平台主链引用
- 主前端恢复 `intelligent-query` 路由和菜单
- 主前端不出现 `opendataagent` 外链按钮
- `go test ./internal/skills/...` 通过
- `nvm use && npm --prefix frontend run build` 通过
- `nvm use && npm --prefix opendataagent/web run build` 通过
- `odw-cli --help` 可见的子命令集不包含 `workflow-context`

## Rollout

- 先完成 Phase 1-5
- 保持现有智能问数生产链路不变
- `opendataagent` 作为独立产品继续演进
- 后续若需要门户级入口策略，再单独立 topic 讨论

## Backout

- 如果共享 `skills/` 加载链路异常，可暂时回退到 `opendataagent/server/skills/bundled`
- 如果主前端入口恢复引起问题，可单独回退本轮前端入口调整，不影响共享 skills 与 CLI 链路
