# 2026-03-26 NL2SQL SDK Session Resume Plan

## Goal

Make follow-up questions on an existing NL2SQL topic continue the prior Claude Agent SDK session when a real SDK session id is available.

## Tasks

1. Extend task execution input/output.
   - Add `resume_session_id` to `TaskExecutionInput`
   - Add returned `session_id` to `TaskExecutionResult`

2. Capture and persist SDK session ids.
   - Record `session_id` from SDK messages/results inside `task_executor`
   - Add topic-store update/read helpers for resumable conversation ids

3. Resume the SDK session from the coordinator.
   - Read topic-level resumable session id before execution
   - Pass it into `TaskExecutionInput`
   - After execution, persist the returned session id back to the topic

4. Preserve compatibility for legacy topics.
   - Treat placeholder topic bootstrap ids (`chat_conv_*`) as non-resumable
   - Keep prompt-history execution when no real SDK session id exists

5. Persist the SDK local session files across container recreation.
   - Mount a Docker volume into the DataAgent container `HOME`
   - Update deployment docs to explain persistence and the `down -v` caveat

6. Verify.
   - Update `dataagent/dataagent-backend/tests/test_task_executor.py`
   - Run targeted frontend NL2SQL chat tests for the summary-truncation change
   - Run targeted backend task executor tests for session resume behavior
   - Verify compose/doc changes are consistent

## Verification

- `npm --prefix frontend test -- src/views/intelligence/__tests__/NL2SqlChat.spec.js`
- `python3 -m pytest dataagent/dataagent-backend/tests/test_task_executor.py`

## Backout

- Stop passing `resume` to Claude Agent SDK
- Stop persisting returned SDK session ids into `chat_conversation_id`
- Revert the targeted task executor/coordinator/topic-store changes
