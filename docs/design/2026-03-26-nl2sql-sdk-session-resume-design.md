# 2026-03-26 NL2SQL SDK Session Resume Design

## Current State

The intelligent-query runtime executes Claude Agent SDK calls from `dataagent/dataagent-backend/core/task_executor.py`.

Today the runtime always calls `claude_agent_sdk.query()` as a fresh turn:

- it rebuilds prior UI history into a single prompt string
- it does not pass a saved SDK session identifier back into the SDK
- it does not persist the real SDK session id returned by the SDK

The topic model already contains `chat_conversation_id`, but the active execution path does not use it for resume.

## Problem

When a user returns to an existing NL2SQL topic and asks a follow-up question, the runtime does not continue the original Claude SDK session. This breaks the expected “resume previous conversation” behavior for historical topics and makes restart/re-entry semantics weaker than the SDK supports.

## Scope

In scope:

- DataAgent task execution path
- topic-level persistence of the real Claude SDK session id
- follow-up turns on an existing topic
- Docker Compose persistence for the local Claude SDK session files

Out of scope:

- reconstructing missing SDK session ids for already-finished legacy topics that never stored a real SDK session id
- redesigning frontend topic persistence
- changing prompt/tool rendering beyond the existing summary truncation fix

## Proposed Solution

Use topic-level SDK session resume in the active task path.

### Execution

- extend `TaskExecutionInput` with `resume_session_id`
- when a topic already has a real SDK conversation id, call `claude_agent_sdk.query()` with `ClaudeAgentOptions(resume=...)`
- when resuming a real SDK session, send only the current user question as the prompt instead of replaying the full reconstructed history
- when no real SDK session id exists, keep the current history-to-prompt fallback

### Persistence

- capture the SDK `session_id` from SDK messages/results in `task_executor`
- after task completion, write the returned session id back into `da_agent_topic.chat_conversation_id`
- ignore placeholder ids created by the current topic bootstrap (`chat_conv_*`) when deciding whether a topic is resumable
- persist the DataAgent container `HOME` directory with a Docker volume so SDK session files under `~/.claude/projects/<sanitized-cwd>/` survive container recreation on the same host

## Tradeoffs

Pros:

- historical topics can continue the actual Claude SDK session
- restart/re-entry behavior aligns with SDK capabilities
- old topics without a real stored SDK session still keep the current prompt-history fallback

Cons:

- already-finished legacy topics cannot be perfectly rebound to an old SDK session unless they run once after this change and store a real session id
- the topic table field now becomes an operational runtime contract, not just a placeholder identifier

## Affected Stacks

- DataAgent backend: `core/task_executor.py`, `core/task_coordinator.py`, `core/topic_task_store.py`
- Deployment: `deploy/docker-compose.dev.yml`, `deploy/docker-compose.prod.yml`, `deploy/README.md`
- Tests: `tests/test_task_executor.py`
