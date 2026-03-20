# Portal MCP Plan

## Implementation Steps

1. 补充 `docs/design/2026-03-20-portal-mcp-design.md` 与本计划文档，明确双轨边界、query contract、auth flow、deploy topology
2. 在 `backend-agent-api` 中新增：
   - `AgentQueryController`
   - `AgentQueryService`
   - DDL / query DTO
   - `/v1/ai/query/**` 鉴权接入
3. 在 `backend/` 中实现：
   - `AgentMetadataService#ddl(...)`
   - `BackendAgentQueryService`
   - 通用 agent JDBC 执行器，统一处理 live DDL、只读 query、limit、timeout
4. 新增 `dataagent/portal-mcp/`：
   - FastMCP 远程服务
   - backend API client
   - front-door token middleware
   - 6 个 MCP tools
   - pytest
5. 新增 `portal-mcp` Dockerfile、requirements，并把 deploy compose、`.env.example`、部署文档、镜像构建/离线包脚本接入新服务
6. 更新部署文档，明确：
   - `portal-mcp` 是新增复用入口
   - 现有 `odw-cli` 与 DataAgent skill 主链路不变

## Verification

- Maven:
  - `backend-agent-api` 编译
  - backend agent controller / service / query service 测试
- Python:
  - `portal-mcp` pytest
  - `python -m py_compile` 检查服务源码
- Compose / docs:
  - deploy 文件引用一致
  - 离线包脚本和镜像加载脚本包含 `portal-mcp`

## Rollout

- v1 默认启用双轨模式：NL2SQL 继续走 CLI，复用客户端走 MCP
- backend 与 `portal-mcp` 使用独立 token，但二者均为服务身份
- 若 `portal-mcp` 出现问题，不影响现有 DataAgent skill 执行链路；可单独回滚 `portal-mcp` 镜像
