---
name: "OpenDataWorks Platform"
description: "Use this built-in skill for OpenDataWorks platform metadata, lineage, datasource resolution, and DDL lookup. This skill does not execute SQL for data analysis."
category: "Platform"
version: "v1"
---

# OpenDataWorks Platform Skill

Use this skill when the user asks about OpenDataWorks platform objects or needs platform context before any analysis.

Scope:

- metadata inspect
- lineage lookup
- datasource resolution
- DDL lookup

Do not use this skill to execute analytical SQL. SQL execution belongs to `OpenDataWorks Readonly SQL Skill`.

Execution contract:

- Always call the local shared `odw-cli`.
- Prefer the helper scripts in `scripts/`.
- Do not call `portal-mcp` for OpenDataWorks platform capabilities.

Preferred scripts:

- `python3 scripts/inspect_metadata.py --keyword "<keyword>"`
- `python3 scripts/query_lineage.py --table "<table>" --db-name "<db>"`

Working rules:

1. If the user asks about tables, fields, databases, or datasource ownership, start with metadata inspect or datasource resolve.
2. If the user asks about upstream/downstream relationships, lineage impact, or where a table comes from, use lineage lookup.
3. If SQL is needed to answer the question, hand off to the readonly SQL skill instead of embedding execution logic here.
