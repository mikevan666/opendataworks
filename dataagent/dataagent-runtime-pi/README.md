# dataagent-runtime-pi

DataAgent 的 Pi 数据面：一个 Node 子进程，在 `@earendil-works/pi-agent-core` 的
官方 Agent 循环上执行一轮 NL2SQL，通过 stdio 上的 NDJSON 与 Python 控制面通信。

配套设计：`docs/design/2026-09-08-dataagent-runtime-plane-split-design.md`

## 本包不产出独立镜像

这里**没有 Dockerfile，也不在 CI 的镜像构建矩阵里**，这是刻意的。

Cell 是子进程，不是网络服务。它的构建产物由 `dataagent-backend` 与
`dataagent-runner` 两个镜像的多阶段构建吸收：

```dockerfile
# dataagent-backend/Dockerfile 与 Dockerfile.runner
FROM node:22-bookworm-slim AS pi-cell
...
COPY --from=pi-cell /build/dist        /opt/dataagent-runtime-pi/dist
COPY --from=pi-cell /build/node_modules /opt/dataagent-runtime-pi/node_modules
ENV DATAAGENT_RUNTIME_PI_DIR=/opt/dataagent-runtime-pi
```

隔离由平台既有的机制提供，不由本包自己发明：

| 隔离拓扑 | 由谁决定 | Cell 在哪运行 |
|---|---|---|
| 进程内 | `DATAAGENT_SANDBOX_MODE` 未设置 | `dataagent-backend` 容器内的子进程 |
| 子容器 | `DATAAGENT_SANDBOX_MODE` 已设置 | sandbox runner 拉起的子容器内的子进程 |

两种拓扑下 Cell 都是子进程。引擎选择（`DATAAGENT_RUNTIME_KIND`）与隔离拓扑
正交——分叉点在 `core/task_executor._execute_task_stream_local` 内部，而不是
和 `_should_use_sandbox_runner` 并列，这样切到 Pi 不会静默丢失容器隔离。

曾经短暂存在过一个独立的 `opendataworks-dataagent-runtime-pi` 镜像。它被移除是
因为没有任何地方部署它：compose 里没有对应 service，却每次提交都要构建推送。
若将来真需要「Cell 独立成容器」这种拓扑，应当连同 compose service、离线包
（`scripts/create-offline-package.sh`、`scripts/load-images.sh`）和发布说明一起
在同一次改动里加回，而不是只留一个无人拉取的镜像。

## 开发

```bash
nvm use                 # .nvmrc 指定 22.19.0
npm ci
npm run typecheck
npm test                # tsc 后跑 node --test
npm run build
```

Python 侧的 `core/pi_runtime.resolve_cell_command` 需要 `dist/src/main.js` 存在，
否则会以 `pi_runtime_missing` 报错并给出构建提示。跨进程契约测试
（`dataagent-backend/tests/test_pi_runtime_e2e.py`）也依赖它，未构建时会跳过。

## 与 Python 侧共享的契约

- 帧协议与中立事件：`core/pi_runtime.py` 顶部注释，以及本包 `src/protocol/frames.ts`
- 工作区边界：策略由 Python 生成（`core/boundary_policy.py`），本包执行
  （`src/policy/workspace-boundary-enforcer.ts`）。两套实现由共享用例表
  `dataagent/contracts/boundary/v1/conformance-cases.json` 约束，任一侧漂移即测试失败。
