# Task Dolphin Flag Plan

> Design: [2026-04-09-task-dolphin-flag-design.md](../design/2026-04-09-task-dolphin-flag-design.md)

**Goal:** 为任务编辑增加 Dolphin `flag` 支持，并在导入、发布、版本和回滚链路中保持该字段一致。
**Tech Stack:** Vue 3 + Element Plus frontend, Java 8 + Spring Boot 2.7 backend

## Architecture Summary

- `data_task` 增加 `dolphin_flag`
- 任务编辑页支持 `YES / NO`
- Dolphin 发布 payload 使用任务自身 `flag`
- 运行态、快照、版本和回滚都读写同一字段

## Task 1: Persist Task Flag

**Files:**
- `backend/src/main/resources/db/migration/V42__add_dolphin_flag_to_data_task.sql`
- `backend/src/main/java/com/onedata/portal/entity/DataTask.java`
- `backend/src/main/java/com/onedata/portal/service/DataTaskService.java`

**Steps:**
1. 为 `data_task` 增加 `dolphin_flag`
2. 为 `DataTask` 增加 `dolphinFlag`
3. 在任务 create/update 校验和元数据规范化时统一收敛为 `YES / NO`

**Expected Result:**
- 新老任务都能稳定持久化任务级执行开关
- 空值不会破坏历史行为，统一默认 `YES`

## Task 2: Wire Flag Through Runtime and Publish Paths

**Files:**
- `backend/src/main/java/com/onedata/portal/service/DolphinSchedulerService.java`
- `backend/src/main/java/com/onedata/portal/service/DolphinRuntimeDefinitionService.java`
- `backend/src/main/java/com/onedata/portal/service/WorkflowDeployService.java`
- `backend/src/main/java/com/onedata/portal/service/WorkflowPublishService.java`
- `backend/src/main/java/com/onedata/portal/service/WorkflowRuntimeSyncService.java`
- `backend/src/main/java/com/onedata/portal/service/WorkflowDefinitionLifecycleService.java`
- `backend/src/main/java/com/onedata/portal/service/WorkflowService.java`
- `backend/src/main/java/com/onedata/portal/service/WorkflowRuntimeDiffService.java`
- `backend/src/main/java/com/onedata/portal/service/WorkflowVersionOperationService.java`

**Steps:**
1. 运行态任务 DTO 增加 `flag`
2. Dolphin 导入解析、平台定义 JSON、运行态修复与版本快照补充 `flag`
3. 发布和部署调用 `buildTaskDefinition` 时传入任务 `dolphinFlag`
4. 版本回滚和运行态同步恢复 `dolphinFlag`

**Expected Result:**
- `flag` 不再在导入、修复、发布、回滚之间丢失
- 发布到 Dolphin 的 payload 可以明确输出 `YES / NO`

## Task 3: Add Task Edit UI

**Files:**
- `frontend/src/views/tasks/TaskEditDrawer.vue`
- `frontend/src/views/tasks/taskEditForm.js`

**Steps:**
1. 在任务编辑页增加“执行状态”单选项
2. 统一默认值和提交 payload 规范化逻辑
3. 编辑回显时把历史值统一映射到 `YES / NO`

**Expected Result:**
- 用户可在 UI 上直接切换“正常执行 / 禁止执行”
- 保存请求稳定携带 `task.dolphinFlag`

## Verification

- `/usr/local/bin/mvn -pl backend -am -DfailIfNoTests=false -Dtest=DolphinSchedulerServiceTest,WorkflowDefinitionLifecycleServiceTest,WorkflowRuntimeDiffServiceTest,WorkflowVersionOperationServiceTest,WorkflowDeployServiceTest,DolphinExportDefinitionParserTest,WorkflowServiceMetadataPersistenceTest test`
- `cd frontend && export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && nvm use && npm test -- src/views/tasks/__tests__/taskEditForm.spec.js`

## Rollout / Backout

- Rollout: 先执行 Flyway，再发布后端，最后发布前端；这样旧前端也不会因为新增字段出错
- Backout: 如需回退，可先回退前端展示和后端发布链路；数据库字段可保留，不影响旧逻辑继续以默认 `YES` 运行
