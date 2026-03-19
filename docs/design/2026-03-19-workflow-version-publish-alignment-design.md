# Workflow Version Publish Alignment Design

**Date:** 2026-03-19
**Goal:** 对齐工作流发布内容与版本历史，避免“发布了最新任务定义但版本记录仍停留在旧快照”，并提升版本原始 JSON 差异的可读性。
**Tech Stack:** Vue 3 + Element Plus frontend, Java 8 + Spring Boot 2.7 backend

## Scope

- 调整工作流发布前的版本同步行为，使发布内容与 `currentVersionId` 对齐
- 明确工作流详情页中“保存工作流”按钮的语义，保留草稿保存能力但不再要求发布前手工保存
- 优化版本历史“原始 JSON 差异”展示，增加红绿高亮和行内变化提示

## Current State

- `WorkflowService.updateWorkflow` 会基于当前工作流、任务绑定和任务定义重建 `definitionJson`，并在快照变化时创建新版本
- `WorkflowPublishService.publish` 会记录一个 `versionId`，但发布预检与实际部署读取的是 `DataWorkflow`、`WorkflowTaskRelation`、`DataTask` 的当前库内状态
- `WorkflowDeployService.deploy` 直接按当前工作流和任务表构建 Dolphin 定义，不消费 `WorkflowVersion.structureSnapshot`
- 工作流详情页中的任务区提供“保存工作流”按钮，用于把最新任务状态快照成新版本
- 版本对比页中的 `rawDiff` 以纯文本 `pre` 渲染，没有颜色区分和行内高亮

## Problem

- 用户更新任务定义后，即使没有手工保存工作流，发布仍可能携带最新任务内容，因为任务表已经被单独保存，但工作流版本历史尚未刷新
- 当前发布记录中的 `versionId` 可能只是一条历史标记，而不是本次实际发布内容的真实快照
- “保存工作流”与“发布”的职责边界不清，导致用户需要理解内部版本生成机制
- 纯文本 JSON diff 可读性差，定位值变化成本高

## Design

- 后端在 `deploy` 发布前先执行一次“当前工作流快照同步”
  - 读取工作流当前字段与当前任务绑定
  - 复用 `updateWorkflow` 的快照生成逻辑
  - 仅当快照内容发生变化时创建新版本
  - 同步完成后再解析 `currentVersionId` 作为本次发布记录的 `versionId`
- 不修改现有 `publish` API 形状，保持调用方兼容
- 前端任务区按钮语义调整为“保存草稿”
  - 保留手工保存能力，满足“先落库、暂不发布”的场景
  - 发布不再要求用户先理解并手动触发版本同步
- 原始 JSON diff 改为结构化渲染
  - 按 `+/-/ /@@/---/+++` 分类行类型
  - 对新增、删除行应用背景色和前缀色
  - 对相邻 `-` / `+` 行做行内差异高亮，突出具体变更值

## Interfaces / Data Model

- 新增 `WorkflowService` 内部同步方法，复用现有 `WorkflowDefinitionRequest` / `updateWorkflow` 路径，不引入新表和新接口
- `WorkflowPublishService.publish` 的 `deploy` 分支改为在解析发布版本前调用同步方法
- 前端版本差异面板新增本地 helper，将 `rawDiff: string` 转成带类型和 segment 的渲染模型

## Risks / Alternatives

- 风险：发布前自动同步会在真正发布前生成新版本。这个行为是预期的，因为目标就是让发布内容和版本历史对齐
- 风险：如果同步逻辑与手工保存逻辑分叉，后续会再次出现语义漂移。本设计要求复用 `updateWorkflow`
- 备选方案：让部署直接从 `WorkflowVersion.structureSnapshot` 还原定义。该方案语义更强，但改动范围更大，涉及部署构建路径重写；本次先采用“发布前同步快照”的低风险方案
- 备选方案：移除“保存草稿”按钮。该方案会丢失“保存但不发布”的能力，因此本次不采纳

## Verification

- 后端单测覆盖“发布前同步生成新版本”和“无变化不重复生成版本”
- 前端测试覆盖 raw diff 渲染模型的颜色分类与行内高亮
- 运行最小相关前端测试与后端测试，必要时补充工作流发布链路的手工验证说明
