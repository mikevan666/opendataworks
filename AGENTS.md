# AGENTS.md

## Purpose

OpenDataWorks is a unified data portal for metadata management, workflow orchestration, lineage analysis, and intelligent query.

When working in this repository, optimize for:

- preserving clear boundaries between the main Java backend, the Vue frontend, and the Python-based DataAgent intelligent-query module
- keeping workflow, metadata, and intelligent-query behavior aligned with the current deployment model under `deploy/`
- preferring targeted, low-risk changes over broad refactors or speculative abstractions

## Tech Stack & Runtime

- `backend/`: main business backend for metadata, workflow, lineage, and platform APIs
- `frontend/`: main web application
- `dataagent/dataagent-backend/`: FastAPI-based intelligent-query backend
- `dataagent/.claude/skills/dataagent-nl2sql/`: intelligent-query skill bundle
- `deploy/`: Docker Compose, environment templates, and image/build assets

### Frontend stack

- `Vue 3` + `Vite 5`
- `Vue Router 4`
- `Pinia`
- `Element Plus` as the primary existing UI component library
- `Sass` for current style organization
- `Tailwind CSS` is an approved additive styling layer for new frontend work when utility-first styling improves implementation speed or consistency
- `ECharts`, `Vue Flow`, `CodeMirror`, `Axios`

### Backend stack

- Main backend:
  - `Java 8`
  - `Spring Boot 2.7`
  - `Spring MVC` + `WebFlux`
  - `MyBatis-Plus`
  - `MySQL 8`
  - `Flyway`
  - `Lombok`
  - `Hutool`
  - `JSqlParser`
  - `Apache POI`
- Intelligent-query backend:
  - `Python`
  - `FastAPI`
  - `Pydantic`
  - `PyMySQL`
  - `Alembic`
  - `AnyIO`

### Frontend stack rules

- Do not rewrite established `Element Plus` or `Sass` surfaces just to force Tailwind adoption.
- When introducing Tailwind CSS, do it incrementally and only for the touched UI area.
- Keep frontend changes aligned with the existing Vue component structure and routing/state patterns already in the repo.

### Node / nvm baseline

- This repository uses `nvm`.
- Before running any frontend command (`vite`, `npm --prefix frontend ...`, build/dev), load and switch Node from `.nvmrc`:
  - `export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && nvm use`
- If the target Node version is missing, install it first:
  - `nvm install`

### Frontend execution rule

- Always run `nvm use` successfully before frontend build/test/dev commands.
- If a frontend command fails with Node engine/runtime errors, retry only after `nvm use`.

## Architecture Overview

- `backend/src`: core platform logic for data assets, workflow orchestration, and lineage
- `frontend/src`: main UI for workflows, lineage, Data Studio, and intelligent-query entrypoints
- `dataagent/dataagent-backend`: NL2SQL runtime, session persistence, prompt assembly, and skill integration
- `docs/design`: active technical design documents for medium and large changes
- `docs/plans`: execution plans paired with design documents
- `docs/handbook`: long-lived handbook and feature documentation
- `docs/reports`: reports, validation notes, and post-change summaries

## Working Rules

- Prefer one verified primary path by default.
- Only add compatibility branches when real version or environment differences are confirmed.
- Keep fallback minimal, explicit, and single-layer.
- Avoid repeated or cascading fallback chains and duplicate guard branches.
- Prefer small, targeted changes that preserve existing module boundaries.
- When changing a public API, schema, runtime contract, or deployment behavior, update the related docs in the same change when the impact is medium or large.
- Do not move skill-specific behavior into shared runtime modules unless the behavior is genuinely generic.

## Design & Plan Workflow

- Change sizing:
  - Small changes: single-file or local fixes without schema, API, architecture, deployment, or cross-module impact may proceed directly.
  - Medium and large changes: anything involving architecture, data model, public interfaces, cross-frontend/backend coordination, deployment behavior, timeout strategy, or operational risk must start with design and plan documents.
- Active document directories:
  - design docs live in `docs/design/`
  - implementation plans live in `docs/plans/`
- Naming rules:
  - design: `YYYY-MM-DD-<topic>-design.md`
  - plan: `YYYY-MM-DD-<topic>-plan.md`
  - design and plan for the same change must share the same `<topic>` slug
- Authoring order:
  - write design before plan
  - keep design focused on current state, problem, scope, solution, interfaces, and tradeoffs
  - keep plan focused on executable tasks, touched files, verification, rollout, and backout
  - identify the affected frontend, backend, DataAgent, and infrastructure stacks when that context matters for implementation
- Reuse rules:
  - if a matching active topic already exists, update it instead of creating a duplicate
  - if scope drifts during implementation, update design and plan before continuing code changes
- Applicability:
  - repository-wide rules apply to the whole repo
  - modules may define stricter local rules in addenda, but may not weaken the repository-wide rules

## Module Addenda

### Intelligent Query module rules

- Scope: these rules apply to the NL2SQL / intelligent-query flow under `dataagent/dataagent-backend` and the skill bundle under `dataagent/.claude/skills/dataagent-nl2sql`.
- Keep generic agent and runtime modules skill-agnostic. Do not hardcode skill-specific script names, CLI subcommands, prompt recipes, or deployment paths in shared modules such as `core/nl2sql_agent.py`.
- The skill bundle is the single source of truth for question-routing playbooks, script invocation patterns, exact required arguments, and recovery rules. If behavior is specific to intelligent-query, put it in `SKILL.md`, `reference/*`, or skill-local scripts.
- Never assume deployment-only absolute paths such as `/app/scripts/...`. Resolve from `skills_output_dir`, skill root, or another runtime-derived root.
- For intelligent-query, do not add an extra wrapper layer unless a verified runtime limitation requires it. Prefer direct execution of skill-local scripts via `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/<name>.py" ...`.
- The current canonical invocation contract is:
  - runtime exposes `DATAAGENT_PYTHON_BIN` and `DATAAGENT_SKILL_ROOT`
  - executable form is `"$DATAAGENT_PYTHON_BIN" "${DATAAGENT_SKILL_ROOT}/scripts/<name>.py" ...`
  - executable references in docs must use the full form above, not bare `run_sql.py` or guessed relative paths
- Avoid duplicating invocation contracts across layers. When changing script entrypoints or required parameters, update the skill docs, skill template or sync generator, and regression tests in the same change.
- Prefer one stable invocation contract. Do not keep multiple equivalent command forms unless a real environment difference has been verified.

### Intelligent Query timeout rules

- Treat intelligent-query timeouts as a chain, not a single knob. When changing one timeout, review backend agent timeout, SQL timeout, reverse-proxy stream timeout, and frontend streaming behavior together.
- For the current SSE chat flow, backend timeout is the primary model-run cutoff. Do not assume frontend axios timeout controls streaming requests without checking the actual streaming implementation.
- Reverse-proxy read and send timeout must be greater than the backend agent timeout, otherwise proxy timeout will hide the real backend failure mode.
- Before increasing timeout, first reduce unnecessary turns, duplicate reads, path guessing, and repeated tool retries. Raise timeout only after the execution path is already simplified.
- Distinguish conversation lifetime from single-run lifetime:
  - a chat session may stay alive for a long time
  - one NL2SQL run still needs bounded execution time
  - long-lived chat does not justify an unbounded single request
- Prefer a two-level timeout model for intelligent-query:
  - total run timeout for one request
  - idle or progress timeout for detecting stalled runs with no new stream or tool output
- For interactive NL2SQL, prefer a longer bounded run timeout over the current short default. As a rule of thumb, `300-420s` total is more appropriate than `180s` once the execution path is already simplified.
- For queries that may exceed interactive limits, prefer asynchronous or background execution instead of endlessly extending the synchronous request timeout.

### Intelligent Query verification rules

- For medium and large intelligent-query changes that span `frontend/`, `dataagent/dataagent-backend/`, worker execution, schema, or deployment wiring, targeted unit or contract tests are not enough on their own.
- Before claiming the change is fully validated, run at least one local end-to-end smoke flow when the environment is available.
- The minimum local intelligent-query smoke flow is:
  - start the required local services for the touched path, typically MySQL, `dataagent-backend`, `dataagent-worker`, and the frontend when UI behavior changed
  - submit one real NL2SQL request through the actual entrypoint affected by the change
  - verify run creation, event streaming or polling, terminal status persistence, and result rendering or session recovery for the changed path
- If the change specifically affects async or background execution, the smoke flow must cover:
  - request accepted with `run_id`
  - worker pickup and execution
  - `/runs/{run_id}` status transition
  - `/runs/{run_id}/events` or stream consumption
  - final assistant message persistence
- If a local full-flow test was not run, do not describe the change as fully verified. State exactly which layer was verified and which end-to-end path remains untested.

### Intelligent Query local smoke method

- Use the local Docker MySQL exposed on `127.0.0.1:3306` as the default smoke database when it is available.
- Prefer the dedicated session schema `dataagent` for local intelligent-query smoke tests. Do not mix smoke-session data into unrelated business schemas when a dedicated schema can be created.
- If `dataagent` schema or user is missing on a reused local MySQL volume, initialize it first with the repository-standard credentials:
  - database: `dataagent`
  - user: `dataagent`
  - password: `dataagent123`
  - privileges: `SELECT` on `opendataworks.*`, full privileges on `dataagent.*`
- For DataAgent full-flow smoke, prefer a dedicated Python `3.11` virtualenv instead of the host Python when local package versions are uncertain.
- Standard local intelligent-query smoke sequence:
  - create or reuse a local Python `3.11` virtualenv
  - install `dataagent/dataagent-backend/requirements.txt`
  - set runtime env to local MySQL:
    - `MYSQL_HOST=127.0.0.1`
    - `MYSQL_PORT=3306`
    - `MYSQL_USER=dataagent`
    - `MYSQL_PASSWORD=dataagent123`
    - `MYSQL_DATABASE=opendataworks`
    - `SESSION_MYSQL_DATABASE=dataagent`
  - run `alembic upgrade head` in `dataagent/dataagent-backend`
  - ensure `da_agent_settings` in `dataagent` contains a valid provider selection and runtime DB config before starting services
  - start `uvicorn main:app`
  - start `python worker_main.py`
  - drive the smoke through real HTTP requests, not mocked store calls
- Minimum smoke scenarios for async intelligent-query changes:
  - background run accepted: verify `POST /sessions/{session_id}/messages` returns `accepted=true` and a `run_id`
  - worker pickup: verify run status transitions `queued -> running -> success|failed|cancelled`
  - event persistence: verify `/runs/{run_id}/events` returns the expected terminal `done` event and any relevant `tool.*` events
  - message persistence: verify the final assistant message is present in `GET /sessions/{session_id}`
  - cancel path: stop or bypass worker pickup long enough to verify queued-run cancellation through `POST /runs/{run_id}/cancel`
- Recommended smoke prompts:
  - minimal run liveness check: `你好，请直接回复 smoke-ok。`
  - real NL2SQL path: `最近 30 天工作流发布次数趋势`
- Cleanup after smoke:
  - delete smoke sessions created during the test
  - stop local backend and worker processes
  - keep any schema or user bootstrap needed for repeatability unless the test explicitly requires cleanup
- Report the exact environment used in the verification note:
  - MySQL host and schema
  - Python interpreter or virtualenv
  - whether real provider credentials and real model execution were used
  - which smoke scenarios passed or were skipped

## Verification Expectations

- Run the narrowest relevant verification before claiming completion.
- Frontend changes:
  - run `nvm use` first
  - then run the smallest relevant frontend build, test, or lint command
- Backend or platform changes:
  - run the smallest relevant backend test or compile check for the touched area
- DataAgent changes:
  - prefer focused `pytest` coverage for the touched module or contract
  - if code paths are sensitive to prompt or runtime configuration, add or update a targeted regression test
- Cross-layer changes:
  - if a change crosses frontend, backend, worker, persistence, or deployment boundaries, add a local end-to-end smoke verification on top of targeted tests when the required environment can be started locally
  - if that smoke verification cannot be run, report the missing local full-flow coverage explicitly
- Docs-only changes:
  - verify directory placement, file naming, cross-links, and consistency with repository rules
- If verification was not run, say so explicitly.
