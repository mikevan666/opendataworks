---
name: "OpenDataWorks Readonly SQL"
description: "Use this built-in skill to execute readonly SQL through the OpenDataWorks agent API and shared odw-cli. Guardrails such as readonly checks, datasource scope, default limit, and timeout are enforced by CLI and API."
category: "Platform"
version: "v1"
---

# OpenDataWorks Readonly SQL Skill

Use this skill when the user needs SQL execution against OpenDataWorks platform data or metadata-resolved business databases.

Execution contract:

- Always use `python3 scripts/run_readonly_sql.py`.
- The real boundary is enforced by `odw-cli + backend-agent-api`.
- Do not duplicate read-only policy logic in prompt text or hand-written SQL wrappers.

What the API and CLI guarantee:

- only readonly SQL
- platform database `opendataworks` is allowed
- business databases resolved by metadata are allowed
- default row limit is `200`
- default timeout is `30s`

Recommended flow:

1. If the target table or database is unclear, first use `OpenDataWorks Platform Skill`.
2. Once the database and SQL are clear, execute:
   - `python3 scripts/run_readonly_sql.py --database "<db>" --sql "<sql>"`
3. Summarize the result before proposing any further analysis or charting.
