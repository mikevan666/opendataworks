# Design Documents

`docs/design/` 用于承载中大型变更的活动设计文档。

## 何时必须写 design

满足以下任一条件时，必须先写 design：

- 涉及架构、数据模型、公共接口或运行时契约
- 涉及前后端联动、跨模块协作或部署行为变化
- 涉及稳定性、超时、恢复、回滚、权限或运维风险

小范围局部修复、单文件调整、无接口与架构影响的改动，可以不单独写 design。

## 命名规则

- 文件名格式：`YYYY-MM-DD-<topic>-design.md`
- `<topic>` 使用英文 kebab-case
- 与配套 plan 使用同一 `<topic>` slug

## 必填结构

```md
# <Title>

**Date:** YYYY-MM-DD
**Goal:** 一句话说明设计目标
**Tech Stack:** 说明本设计涉及的前端、后端、DataAgent 或基础设施技术栈

## Scope

## Current State

## Problem

## Design

## Interfaces / Data Model

## Risks / Alternatives

## Verification
```

## 编写规则

- design 只写现状、问题、边界、方案、接口与取舍，不写逐任务执行清单
- design 必须先于 plan
- 涉及实现约束时，明确写出本设计对应的前端、后端、DataAgent 与基础设施技术栈
- 如果实施过程中范围变化，先更新 design，再更新 plan 和代码
- 如果已有同主题 design 且仍适用，优先更新原文档，不新建重复文档

## 当前样板

- [2026-03-12-nl2sql-async-background-design.md](2026-03-12-nl2sql-async-background-design.md)
