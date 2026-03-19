# NL2SQL Backend CLI Plan

## Implementation Steps

1. 新增根 Maven reactor，并创建 `backend-agent-api` 独立模块
2. 在 `backend-agent-api` 中定义 agent controller、DTO、SPI、service-token 鉴权拦截
3. 在 `backend/` 中实现 `AgentMetadataService`，复用现有 metadata / lineage / datasource 相关 mapper 和 service
4. 新增 skill 自带 `dataagent/.claude/skills/dataagent-nl2sql/bin/odw-cli`，通过 `curl` 调 backend agent API
5. 修改 DataAgent 运行时与 skill 脚本：
   - 新增 backend CLI 相关环境变量
   - `inspect_metadata.py` / `query_opendataworks_metadata.py` / `_opendataworks_runtime.resolve_datasource()` 固定走 backend CLI
   - metadata 相关脚本执行前固定检查 `${DATAAGENT_SKILL_ROOT}/bin/odw-cli`，缺失时直接提示用户先安装到该路径
6. 修改 backend / dataagent Dockerfile、CI 和构建脚本，统一从仓库根 build context 构建
7. 修改 Compose 与 `.env.example`，接入 shared service token 和 backend CLI 环境变量，并移除 metadata provider 兼容开关
8. 更新 skill 文档、部署文档和 DataAgent README，明确 CLI 的固定路径检查规则，以及缺失时由用户自行安装
9. 将旧的 static metadata exporter / loader 标注为 legacy，但先不删除

## Verification

- Maven:
  - `backend-agent-api` 单测
  - backend agent controller / service 测试
- DataAgent:
  - `test_nl2sql_agent.py`
  - metadata CLI bridge pytest
- Build:
  - reactor 下 backend 编译
  - dataagent Dockerfile 路径检查

## Rollout

- Compose 中固定提供 backend CLI 所需环境变量
- 若线上出现 agent API 或 CLI 问题，需要回滚到上一个仍包含旧路径的镜像版本；不再通过环境变量切换兼容分支
- backend agent API 继续保留，作为唯一 metadata 入口
