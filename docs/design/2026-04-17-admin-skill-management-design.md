# Admin Skill Management Design

## Current State

The admin UI now models Skills as list and detail pages, but the runtime state still came from a single `skills_output_dir`. That made `enabled` mean “the one current skill”, not “this skill is available to runtime”.

`opendataagent` keeps a runtime enabled map per Skill and injects all enabled Skills into execution. OpenDataWorks should follow that model while keeping its existing `skills_output_dir` compatibility contract for the DataAgent semantic layer and scripts.

## Problem

Administrators need to enable multiple Skills at the same time. A single “current running Skill” model is misleading in the UI and limits runtime discovery. The UI should use concise `已启用 / 未启用` language and the runtime should only expose enabled Skills to the Claude Skill tool.

## Solution

- Store Skill enablement in `da_agent_settings.raw_json.skill_runtime` as `{ "<folder>": { "enabled": true|false } }`.
- Keep `skills_output_dir` as the primary compatibility Skill. On first migration, only the current `skills_output_dir` folder is enabled.
- Update `PUT /api/v1/dataagent/skills/runtime/{folder}` to enable or disable one Skill without affecting the others.
- Reject disabling the last enabled Skill. If disabling the current primary Skill, move `skills_output_dir` to the first remaining enabled Skill.
- Resolve document `enabled` from `skill_runtime`, not from `skills_output_dir`.
- During background NL2SQL execution, `core/task_executor.py` uses shared helpers in `core/agent_runtime.py` to create a runtime project under `dataagent/dataagent-backend/.runtime/enabled-skills` and expose only enabled Skills through `.claude/skills` symlinks.
- Keep `DATAAGENT_SKILL_ROOT` pointed at the primary Skill and add `DATAAGENT_ENABLED_SKILLS` plus `DATAAGENT_ENABLED_SKILL_ROOTS` for multi-Skill-aware scripts.
- Remove the unused legacy direct stream executor path; task execution is the runtime entrypoint for interactive, async, queue, and schedule flows.
- Simplify the admin UI: list cards show only core state, detail header is custom, file tree puts `SKILL.md` first, and wording uses `启用 / 已启用 / 未启用`.

## Interfaces

Existing document APIs remain:

- `GET /api/v1/dataagent/skills/documents`
- `GET /api/v1/dataagent/skills/documents/{document_id}`

Document fields keep the same shape, but `enabled` now means the owning Skill folder is enabled.

Runtime update API remains:

- `PUT /api/v1/dataagent/skills/runtime/{folder}`

Request:

- `{ "enabled": true | false }`

Response:

- `{ "skill_id": "<folder>", "enabled": true | false }`

Failure:

- `400` when the folder does not exist or disabling would leave zero enabled Skills.

## Data Notes

- No new table is added.
- `da_skill_document.relative_path` remains discovery-root relative, for example `dataagent-nl2sql/reference/40-runtime-metadata.md`.
- Existing settings without `skill_runtime` are interpreted as `{ current_skills_output_dir_folder: { enabled: true } }`.
- `.runtime/` is generated local runtime state and is gitignored.

## Tradeoffs

The semantic layer still reads the primary Skill from `skills_output_dir`. Multi-Skill activation controls Claude Skill discovery for execution, while existing script compatibility stays anchored on the primary Skill until the semantic layer is made fully multi-Skill-aware.

The runtime helper extraction keeps prompt/env/provider assembly shared without keeping a second agent execution path alive.
