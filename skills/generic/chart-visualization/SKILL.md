---
name: "Chart Visualization"
description: "Use this built-in skill for chart construction and data storytelling from structured tabular results. The workflow is organized from the AntV chart-visualization playbook, but current default output is ECharts-compatible option JSON for local rendering."
category: "Generic"
version: "v1"
---

# Chart Visualization Skill

Use this skill when the user already has structured rows and needs a chart, trend view, or lightweight data story.

This built-in skill keeps the AntV chart-visualization workflow discipline:

- choose chart type from the question and data shape
- keep annotations and titles concise
- preserve readable axes and legend defaults
- prefer data storytelling over decorative chart output

Current default artifact:

- ECharts option JSON via `python3 scripts/build_echarts_option.py`

Typical flow:

1. Prepare or fetch rows with the platform or SQL skills.
2. If needed, reshape locally with `Python Analysis Skill`.
3. Generate a chart option:
   - `python3 scripts/build_echarts_option.py --input rows.json --chart-type line --x date --y count`
