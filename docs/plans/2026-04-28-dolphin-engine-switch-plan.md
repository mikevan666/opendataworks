# Dolphin Engine Switch Plan

> Design: [2026-04-28-dolphin-engine-switch-design.md](../design/2026-04-28-dolphin-engine-switch-design.md)

**Goal:** 支持多个 DolphinScheduler 环境，并允许工作流切换绑定环境后重新发布。
**Tech Stack:** Java 8 + Spring Boot 2.7, MyBatis-Plus, Flyway, Vue 3 + Element Plus

## Task 1: Schema And Config Management

**Files:**
- `backend/src/main/resources/db/migration/V43__add_multi_dolphin_config.sql`
- `backend/src/main/java/com/onedata/portal/entity/DolphinConfig.java`
- `backend/src/main/java/com/onedata/portal/service/DolphinConfigService.java`
- `backend/src/main/java/com/onedata/portal/controller/DolphinConfigController.java`

**Steps:**
1. Add migration fields for named Dolphin configs and workflow/publish bindings.
2. Add service CRUD, default selection, enabled lookup and connection-tested switching helpers.
3. Keep legacy default-config endpoints compatible.

## Task 2: Workflow Binding And Runtime Calls

**Files:**
- `backend/src/main/java/com/onedata/portal/entity/DataWorkflow.java`
- `backend/src/main/java/com/onedata/portal/entity/WorkflowPublishRecord.java`
- `backend/src/main/java/com/onedata/portal/service/DolphinSchedulerService.java`
- `backend/src/main/java/com/onedata/portal/service/dolphin/DolphinOpenApiClient.java`
- `backend/src/main/java/com/onedata/portal/service/WorkflowPublishService.java`
- `backend/src/main/java/com/onedata/portal/service/WorkflowDeployService.java`
- `backend/src/main/java/com/onedata/portal/service/WorkflowScheduleService.java`
- `backend/src/main/java/com/onedata/portal/service/WorkflowService.java`

**Steps:**
1. Add explicit `dolphinConfigId` routing through Dolphin service and client methods.
2. Make workflow publish, online, offline, execute, backfill, schedule and instance sync use the workflow binding.
3. Add switch endpoint behavior that clears old runtime identifiers and preserves platform definition.

## Task 3: Frontend Management And Switch UI

**Files:**
- `frontend/src/api/settings.js`
- `frontend/src/api/workflow.js`
- `frontend/src/api/task.js`
- `frontend/src/views/settings/DolphinConfig.vue`
- `frontend/src/views/workflows/WorkflowDetail.vue`
- `frontend/src/views/tasks/TaskEditDrawer.vue`

**Steps:**
1. Replace single Dolphin config form with multi-environment table and dialog.
2. Add scheduler engine display and switch dialog to workflow detail.
3. Pass workflow-bound `dolphinConfigId` into Dolphin option APIs.

## Verification

- Run focused backend tests for `DolphinConfigService`, `WorkflowPublishService`, `WorkflowService`, `WorkflowScheduleService`, and `DolphinSchedulerService`.
- Run frontend unit tests for touched settings/workflow helpers where present.
- If a two-Dolphin local environment is unavailable, report that full cross-Dolphin smoke remains unrun.
