# 文档索引

OpenDataWorks 的文档按用途收敛到以下目录：

1. `docs/design` —— 中大型变更的设计文档
2. `docs/plans` —— 与设计文档配套的实施计划
3. `docs/handbook` —— 长期维护的手册、特性专题与内部指南
4. `docs/guide` —— 面向使用者和部署者的指南内容
5. `docs/reports` —— 修复报告、测试结果、阶段总结

## 🧭 设计 (Design)

| 文档 | 内容 |
| --- | --- |
| [README.md](design/README.md) | design 文档命名规则、模板与编写要求 |
| [2026-03-12-nl2sql-async-background-design.md](design/2026-03-12-nl2sql-async-background-design.md) | 智能问数异步后台任务模式设计样板 |

## 🗂️ 计划 (Plans)

| 文档 | 内容 |
| --- | --- |
| [README.md](plans/README.md) | plan 文档命名规则、模板与执行要求 |
| [2026-03-12-nl2sql-async-background-plan.md](plans/2026-03-12-nl2sql-async-background-plan.md) | 智能问数异步后台任务模式实施计划样板 |

## 📚 手册 (Handbook)

| 分类 | 说明 |
| --- | --- |
| [overview.md](handbook/overview.md) | 品牌、价值、术语、路线图 |
| [architecture.md](handbook/architecture.md) | 系统组件、数据流、运行态 |
| [data-model-and-sql.md](handbook/data-model-and-sql.md) | 命名规范、核心表、脚本位置、SQL 策略 |
| [development-guide.md](handbook/development-guide.md) | 本地开发环境、数据库初始化、服务启动 |
| [operations-guide.md](handbook/operations-guide.md) | Docker Compose、离线包、systemd、镜像构建 |
| [testing-guide.md](handbook/testing-guide.md) | 手工/自动测试、巡检脚本、缺陷记录 |
| [features/](handbook/features) | 特性专题、技术设计与实现说明 |

## 📘 指南 (Guide)

| 文档 | 内容 |
| --- | --- |
| [guide/start/quick-start.md](guide/start/quick-start.md) | 快速开始与环境拉起 |
| [guide/deployment.md](guide/deployment.md) | 部署说明 |
| [guide/manual/features.md](guide/manual/features.md) | 功能概览 |
| [guide/faq/faq.md](guide/faq/faq.md) | 常见问题 |

## 🧪 报告 (Reports)

| 文档 | 内容 |
| --- | --- |
| [COMPLETION_REPORT.md](reports/COMPLETION_REPORT.md) | 里程碑交付清单 |
| [FIX_SUMMARY.md](reports/FIX_SUMMARY.md) | 关键缺陷修复记录 |
| [TEST_REPORT.md](reports/TEST_REPORT.md) | 综合测试报告 |
| [WORKFLOW_CODE_MISMATCH_FIX.md](reports/WORKFLOW_CODE_MISMATCH_FIX.md) | 工作流编码修复说明 |

## 使用约定

- 中大型变更先写 `docs/design`，再写 `docs/plans`。
- `docs/handbook` 继续承载稳定手册和专题说明，不再作为新设计规范的主目录。
- `docs/reports` 用于记录执行结果、问题复盘和阶段性总结，不替代 design 或 plan。
