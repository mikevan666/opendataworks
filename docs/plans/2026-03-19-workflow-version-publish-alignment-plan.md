# Workflow Version Publish Alignment Plan

> Design: [2026-03-19-workflow-version-publish-alignment-design.md](../design/2026-03-19-workflow-version-publish-alignment-design.md)

**Goal:** 让工作流发布自动对齐最新版本快照，并改进版本历史原始 JSON 差异展示。
**Tech Stack:** Vue 3 + Element Plus frontend, Java 8 + Spring Boot 2.7 backend

## Architecture Summary

- 后端在 `deploy` 发布入口增加一次快照同步，确保发布记录 `versionId` 与实际发布内容一致
- 前端将“保存工作流”明确为“保存草稿”，保留草稿能力
- 原始 JSON diff 从纯文本渲染升级为带颜色和行内高亮的结构化视图

## Task 1: Add Publish-Time Version Sync

**Files:**
- `backend/src/main/java/com/onedata/portal/service/WorkflowService.java`
- `backend/src/main/java/com/onedata/portal/service/WorkflowPublishService.java`
- `backend/src/test/java/com/onedata/portal/service/WorkflowPublishServiceTest.java`

**Steps:**
1. 在 `WorkflowService` 增加基于当前工作流和当前绑定关系的同步方法，内部复用 `updateWorkflow`
2. 在 `WorkflowPublishService.publish` 的 `deploy` 分支前调用同步方法，再解析发布版本
3. 为同步后版本选择和无变化场景补充单元测试

**Expected Result:**
- 发布前会自动刷新 `currentVersionId`
- 发布记录 `versionId` 与本次实际部署内容一致
- 无变化时不会重复生成新版本

## Task 2: Clarify Draft Save Interaction

**Files:**
- `frontend/src/views/workflows/WorkflowTaskManager.vue`

**Steps:**
1. 将任务区按钮文案从“保存工作流”调整为“保存草稿”
2. 更新未保存任务提示文案，说明发布时会自动完成版本同步

**Expected Result:**
- 用户可以继续手工保存草稿
- UI 不再暗示“必须先保存工作流才能发布”

## Task 3: Improve Raw JSON Diff Rendering

**Files:**
- `frontend/src/views/workflows/WorkflowVersionComparePanel.vue`
- `frontend/src/views/workflows/workflowRawDiffHelper.js`
- `frontend/src/views/workflows/__tests__/workflowRawDiffHelper.spec.js`

**Steps:**
1. 新增 raw diff helper，把文本 diff 解析为带类型和 segment 的渲染模型
2. 在版本对比页按行着色，并对相邻删改行做行内高亮
3. 为 helper 补充测试，覆盖头部行、增删行和行内差异

**Expected Result:**
- 原始 JSON diff 可直接区分新增、删除和上下文
- 用户能更快定位值级别变化

## Verification

- `cd frontend && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nvm use && npm test -- --runInBand frontend/src/views/workflows/__tests__/publishPreviewHelper.spec.js frontend/src/views/workflows/__tests__/workflowRawDiffHelper.spec.js`
- `./mvnw -pl backend -Dtest=WorkflowPublishServiceTest test` 或仓库内等效最小测试命令

## Rollout / Backout

- Rollout: 先合入后端发布同步，再合入前端文案与 diff 视图，避免 UI 宣称的行为与后端不一致
- Backout: 若发布前同步引发回归，可先回退 `WorkflowPublishService.publish` 的同步调用；前端 diff 和按钮文案可独立保留或回退
