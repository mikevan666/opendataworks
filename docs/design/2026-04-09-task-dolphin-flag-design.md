# Task Dolphin Flag Design

**Date:** 2026-04-09
**Goal:** 为任务编辑补充 DolphinScheduler 任务级执行开关，使平台可显式控制 `flag=YES|NO`，并在发布、导入、版本、回滚链路中保持该字段不丢失。
**Tech Stack:** Vue 3 + Element Plus frontend, Java 8 + Spring Boot 2.7 backend

## Scope

- 在平台任务模型中新增任务级 `dolphin_flag`
- 任务编辑支持选择“正常执行 / 禁止执行”
- 发布到 Dolphin 时使用任务自身 `flag`
- 从 Dolphin 导入、运行态解析、版本快照、版本回滚、运行态修复时保留该字段

## Current State

- `data_task` 没有任务级 `flag` 字段，平台无法持久化这个配置
- `TaskEditDrawer` 没有对应表单项，create/update API 也不会显式提交该值
- `DolphinSchedulerService.buildTaskDefinition` 固定下发 `flag=YES`
- 运行态解析、工作流定义 JSON、版本快照与回滚恢复都没有 `flag` 字段，导致即便后端支持发布，值也会在后续链路丢失

## Problem

- 用户无法在平台上把单个 Dolphin 任务切换为“禁止执行”
- 平台发布总是覆盖成 `YES`，无法表达已有运行态配置
- 如果后续只改发布链路，不改导入/版本链路，`flag` 会在导入、反向同步、回滚后被静默重置

## Design

- 数据模型：
  - `data_task` 新增 `dolphin_flag VARCHAR(8) NOT NULL DEFAULT 'YES'`
  - `DataTask` 新增 `dolphinFlag`
  - 服务层统一规范化为大写 `YES` / `NO`，空值默认 `YES`
- 前端：
  - 任务编辑页新增“执行状态”单选项
  - 新建默认 `YES`
  - 编辑时回显已有值
  - 保存 payload 显式带 `task.dolphinFlag`
- Dolphin 发布：
  - `buildTaskDefinition` 增加 `dolphinFlag` 入参
  - `flag` 不再硬编码，使用任务值生成 payload
- 全链路保留：
  - `RuntimeTaskDefinition` 新增 `flag`
  - Dolphin 运行态解析时读取 `flag`
  - 工作流 `definitionJson`、运行态 diff 快照、版本快照、版本回滚恢复、运行态同步补齐 `flag`

## Interfaces / Data Model

- DB:
  - `data_task.dolphin_flag VARCHAR(8) NOT NULL DEFAULT 'YES'`
- Backend:
  - `DataTask.dolphinFlag`
  - `RuntimeTaskDefinition.flag`
  - `DolphinSchedulerService.buildTaskDefinition(..., dolphinFlag, ...)`
- Frontend:
  - `TaskEditDrawer` 表单模型增加 `dolphinFlag`

## Risks / Alternatives

- 风险：只改发布链路会让值在导入/回滚中丢失。本方案直接做全链路对齐，避免后续隐性覆盖
- 风险：老数据没有该值。通过 Flyway 默认值和服务层默认值双重兜底，保证老任务行为不变
- 备选：直接用通用 `flag` 命名。未采用，因为字段语义明显绑定 Dolphin，`dolphin_flag` 更安全

## Verification

- 后端单测覆盖 payload 输出、导入保留、运行态 diff 识别、回滚恢复
- 前端测试覆盖默认值和保存 payload 规范化
- 最小相关后端测试与前端 `vitest` 通过
