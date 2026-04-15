---
name: "Python Analysis"
description: "Use this built-in skill for lightweight Python-based data exploration, profiling, aggregation, and file-based analysis. It does not fetch OpenDataWorks metadata on its own."
category: "Generic"
version: "v1"
---

# Python Analysis Skill

Use this skill when the user needs local Python-based analysis on files, tabular results, or intermediate data artifacts.

Typical tasks:

- inspect CSV or JSON files
- compute descriptive statistics
- aggregate or pivot local result sets
- reshape data before chart generation

Execution contract:

- Prefer `python3 scripts/profile_dataset.py --input <file>`
- Work on explicit local files or prior tool outputs
- Do not assume OpenDataWorks metadata access here; use the platform skill or readonly SQL skill first if upstream data needs to be fetched
