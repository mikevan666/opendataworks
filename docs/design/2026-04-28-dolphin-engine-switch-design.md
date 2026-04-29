# Dolphin Engine Switch Design

**Date:** 2026-04-28
**Goal:** 支持管理员维护多个 DolphinScheduler 环境，并允许已发布工作流切换目标 Dolphin 后重新发布。
**Tech Stack:** Java 8 + Spring Boot 2.7 backend, MySQL + Flyway, Vue 3 + Element Plus frontend

## Current State

- DolphinScheduler 配置存储在单表 `dolphin_config`，服务层通过 `getActiveConfig()` 读取一个全局配置。
- 工作流只保存 `workflow_code`、`project_code`、`dolphin_schedule_id`，没有记录这些运行态字段属于哪个 Dolphin 环境。
- 发布预检、发布、上线、下线、执行、补数、调度和 WebUI 跳转都默认使用当前全局 Dolphin 配置。
- 如果发布后把全局 Dolphin 地址改为新集群，平台仍拿旧集群的 `workflow_code` 到新集群读取运行态定义，容易出现“找不到运行态工作流”。

## Solution

- 将 Dolphin 配置从单全局配置升级为多环境配置：
  - `dolphin_config` 增加环境名称、说明、默认标记和逻辑删除字段。
  - `is_active` 继续表示启停状态。
  - 默认环境用于兼容未绑定工作流和旧接口。
- 在工作流与发布记录上保存 `dolphin_config_id`：
  - 工作流所有运行态调用都优先使用自身绑定的 Dolphin 环境。
  - 发布记录写入当次目标环境，保证审计可追溯。
- 工作流详情提供“切换调度引擎”操作：
  - 目标 Dolphin 必须启用且连接测试通过。
  - 切换后清空旧运行态绑定，下一次发布在新 Dolphin 新建运行态工作流。
  - 平台保留工作流任务、版本、调度表达式等定义，不自动修改旧 Dolphin。
- Dolphin 客户端支持按配置显式调用：
  - `DolphinSchedulerService` 增加以 `dolphinConfigId` 为参数的重载。
  - 项目编码缓存按配置隔离，避免切换后复用旧项目编码。
  - 元数据目录、发布预检、修复元数据等路径使用工作流绑定配置。

## Interfaces

- 保留旧接口：
  - `GET /v1/settings/dolphin` 返回默认 Dolphin 配置。
  - `PUT /v1/settings/dolphin` 更新默认 Dolphin 配置。
  - `POST /v1/settings/dolphin/test` 测试传入配置。
- 新增接口：
  - `GET /v1/settings/dolphin/configs`
  - `GET /v1/settings/dolphin/configs/{id}`
  - `POST /v1/settings/dolphin/configs`
  - `PUT /v1/settings/dolphin/configs/{id}`
  - `DELETE /v1/settings/dolphin/configs/{id}`
  - `POST /v1/settings/dolphin/configs/{id}/default`
  - `POST /v1/settings/dolphin/configs/{id}/test`
  - `PUT /v1/workflows/{id}/scheduler-engine`
- Dolphin 元数据接口新增可选 `dolphinConfigId` 查询参数，旧调用不带参数时继续使用默认环境。

## Tradeoffs

- 采用“新建绑定”而不是按名称自动匹配，是为了避免跨集群误绑定已有生产工作流。
- 切换时不自动下线或删除旧 Dolphin 工作流，避免平台在不确定旧集群权限和业务影响时做破坏性动作。
- 本轮不抽象 Dinky 或通用调度引擎，只把现有 Dolphin 集成升级为多环境绑定，降低改动范围。

## Verification

- 后端单测覆盖 Dolphin 多配置管理、工作流切换字段重置、发布记录环境追溯、发布/执行/调度调用使用绑定环境。
- 前端测试覆盖配置管理 UI、工作流切换弹窗和切换后发布预检首次部署提示。
- 环境可用时用两个 Dolphin 配置做本地 smoke：A 发布成功，切换 B，B 首次发布成功，旧 A 不被自动修改。
