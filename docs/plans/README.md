# Implementation Plans

`docs/plans/` 用于承载与设计文档配套的可执行实施计划。

## 何时必须写 plan

- 所有要求先写 design 的中大型变更，都必须配套一份 plan
- plan 应在 design 稳定后编写
- plan 面向工程师和 agent 直接执行，不应把关键实现决策留给实施者

## 命名规则

- 文件名格式：`YYYY-MM-DD-<topic>-plan.md`
- `<topic>` 使用英文 kebab-case
- 必须与对应 design 共享同一 `<topic>` slug

## 必填结构

```md
# <Title>

> Design: [对应 design 文档](../design/YYYY-MM-DD-<topic>-design.md)

**Goal:** 一句话说明交付目标
**Tech Stack:** 说明本计划涉及的前端、后端、DataAgent 或基础设施技术栈

## Architecture Summary

## Task 1: <task title>

**Files:**
- path/a
- path/b

**Steps:**
1. ...
2. ...

**Expected Result:**
- ...

## Verification

## Rollout / Backout
```

## 编写规则

- plan 必须引用对应 design
- 每个任务必须写清 `Files`、`Steps`、`Expected Result`
- 如果计划涉及跨前后端或基础设施联动，先在文首写清相关技术栈
- 计划风格以任务清单为主，不以时间排期或负责人分配代替实施说明
- 如果实施中出现范围变化，先回写 design 和 plan，再继续改代码

## 当前样板

- [2026-03-12-nl2sql-async-background-plan.md](2026-03-12-nl2sql-async-background-plan.md)
