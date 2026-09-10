# DataAgent Pi 运行时长上下文治理与空闲超时根治方案 — 执行计划

- 日期：2026-09-09
- 关联设计：`docs/design/2026-09-09-pi-agent-context-governance-design.md`
- 受影响栈：
  - `dataagent-runtime-pi`（Node.js / TypeScript 运行时内核）
  - `dataagent-backend`（Python 控制面、配置与任务执行器）

---

## 1. 任务分解与触达文件

### 阶段 1：两级超时治理与长任务心跳维持（立即止血）

1. **Python 配置与控制面参数打通**
   - 触达文件：
     - `dataagent/dataagent-backend/core/config.py`：新增配置项 `dataagent_run_idle_timeout_seconds`（默认 300）与 `dataagent_run_total_timeout_seconds`（默认 600）。
     - `dataagent/dataagent-backend/core/task_executor.py`：在构造 `PiRunContext` 时显式传入 `idle_timeout_seconds` 与 `total_timeout_seconds`，打通平台配置。
     - `dataagent/dataagent-backend/core/pi_runtime.py`：`PiRunContext.to_init_payload()` 确保将超时参数下发至 `cell.init` 协议帧。

2. **Node.js 协议与长工具心跳支持**
   - 触达文件：
     - `dataagent/dataagent-runtime-pi/src/protocol/frames.ts`：完善 `limits` 契约（显式声明 `idle_timeout_seconds` 等）。
     - `dataagent/dataagent-runtime-pi/src/tools/tool-registry.ts`：在长工具执行（慢 SQL、网络请求）期间，注入心跳上报机制，每 15s 产生一次轻量级进度更新。

### 阶段 2：Layer 1 工具结果即时折叠与落盘（Ingestion Guard & ResultStore）

1. **本地结果存储管理（`ResultStore`）**
   - 新建文件：
     - `dataagent/dataagent-runtime-pi/src/context/result-store.ts`：
       负责将超出阈值的大输出保存到 `${workspaceRoot}/.dataagent/results/${result_ref}.json`；
       提供结果切片读取 API。

2. **确定性表格指纹抽取（`TabularDigest`）**
   - 新建文件：
     - `dataagent/dataagent-runtime-pi/src/context/tabular-digest.ts`：
       解析 SQL 查询结果或 JSON 列表；
       提取 Schema 列信息、总行数；
       提取 Head 5 行与 Tail 5 行样本；
       计算数值列和日期列的空值率与极值；
       构建紧凑的 Compact Representation。

3. **内置召回工具（`fetch_tool_result`）**
   - 新建文件：
     - `dataagent/dataagent-runtime-pi/src/tools/fetch-tool-result.ts`：
       实现模型按需获取完整结果分页的内置工具；
   - 触达文件：
     - `dataagent/dataagent-runtime-pi/src/tools/tool-registry.ts`：注册该工具。

4. **`cell.ts` 接入 `afterToolCall` 拦截**
   - 触达文件：
     - `dataagent/dataagent-runtime-pi/src/kernel/cell.ts`：
       在 Agent 实例化中配置 `afterToolCall`；
       超过 16KB 时自动持久化并替换为结构化 Compact 视图。

### 阶段 3：Layer 2 & Layer 3 上下文工作集保护与动态裁剪（`transformContext`）

1. **动态裁剪核心纯函数（`ContextPruner`）**
   - 新建文件：
     - `dataagent/dataagent-runtime-pi/src/context/context-pruner.ts`：
       定义锚点保护逻辑：保留 System Prompt、首个 User Prompt、最近 N 轮（默认 6 轮）消息、最后一条 SQL/工具证据；
       实现非破坏性去重（相同参数查询旧输出置换为占位符）；
       实现历史已修复错误堆栈收敛（压缩为单行摘要）；
       严格包裹在 Fail-Open 结构中，确保发生任何不可预期异常时安全降级。

2. **`cell.ts` 替换粗暴滑动窗口**
   - 触达文件：
     - `dataagent/dataagent-runtime-pi/src/kernel/cell.ts`：
       移除简陋的 `messages.slice(-40)`，替换为 `ContextPruner` 流水线调用。

---

## 2. 验证方案

### 自动化单测与组件测试

1. **超时与控制面测试**：
   - 命令：`pytest dataagent/dataagent-backend/tests/test_pi_runtime.py`
   - 断言：`PiRunContext` 正确继承并透传 300s/600s 超时配置；心跳帧能持续刷新活跃时间戳。

2. **ResultStore 与 TabularDigest 单元测试**：
   - 新建测试：`dataagent/dataagent-runtime-pi/test/result_store.test.ts`
   - 测试内容：
     - 大体积 JSON 表格数据成功落盘并生成唯一 `result_ref`；
     - 准确提取 Schema 列名与数据类型；
     - 正确切取 Head 5 与 Tail 5 行，大结果被压缩至 < 2KB；
     - `fetch_tool_result` 工具正确根据 offset/limit 分页返回，支持列过滤。

3. **ContextPruner 单元测试**：
   - 新建测试：`dataagent/dataagent-runtime-pi/test/context_pruner.test.ts`
   - 测试内容：
     - 保护集验证：System Prompt、首条提问、最近 6 条消息完整无损；
     - 去重验证：重复查询相同元数据，旧结果被标记为 `[Superseded]`；
     - 错误收敛验证：历史已被解决的 SQL 语法错误堆栈被压缩；
     - Fail-Open 验证：传入异常格式消息时，安全返回原数组，不抛出异常。

4. **Runtime 全量单测**：
   - 命令：`npm --prefix dataagent/dataagent-runtime-pi test`
   - 确保既有 64 项测试与新增测试全部保持绿色。

### 本地端到端冒烟验证（按照 AGENTS.md 本地冒烟法）

1. **环境准备**：
   - 启动本地 MySQL (`127.0.0.1:3306`) 与 Redis (`127.0.0.1:6379`)；
   - 启动本地 Java 后端 (`127.0.0.1:8080`) 与 portal-mcp (`127.0.0.1:8801`)；
   - 启动 `dataagent-backend`（`main.py`）。
2. **多轮问数与大表查询冒烟**：
   - 发起查询大表（返回 1000+ 行数据）的业务问数请求；
   - 观察：
     - 工具返回未溢出内存，工作区生成 `.dataagent/results/res_xxx.json`；
     - 注入到模型的上下文为结构化预览指纹；
     - 模型依据预览正常分析得出数据结论，未发生 120s 空闲超时；
     - 进行连续 5 轮追问，上下文平稳维持在健康水位，无雪崩现象。

---

## 3. 回滚与风险预案

1. **配置级回退**：
   - 若特定模型对结构化折叠输出不敏感，可通过环境变量 `DATAAGENT_CONTEXT_FOLD_ENABLED=false` 一键关闭折叠，退回原始直接传递；
2. **Fail-Open 托底**：
   - `ContextPruner` 内部全部采用 `try-catch` 托底，运行期发生任何解析异常均静默降级为直通模式，绝不中断任务流；
3. **磁盘空间保障**：
   - `.dataagent/results/` 下的缓存文件随任务会话生命周期绑定，在任务或会话清理时联动回收，单任务上限 100MB。
