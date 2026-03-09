from __future__ import annotations

import argparse
from datetime import datetime
from typing import Any

from _opendataworks_runtime import error_payload, load_json_input, print_json


def is_time_like(field: str, values: list[Any]) -> bool:
    lower = str(field or "").lower()
    if any(token in lower for token in ("dt", "date", "day", "time", "month", "hour")):
        return True
    if not values:
        return False
    matched = 0
    for value in values[:5]:
        text = str(value or "").strip()
        if not text:
            continue
        try:
            datetime.fromisoformat(text.replace("Z", "+00:00"))
            matched += 1
        except ValueError:
            continue
    return matched >= max(1, min(3, len(values[:5])))


def is_numeric(value: Any) -> bool:
    if isinstance(value, (int, float)):
        return True
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def choose_chart(
    rows: list[dict[str, Any]],
    preferred_chart_type: str = "",
    category_field: str = "",
    value_field: str = "",
) -> tuple[str | None, str | None, list[str]]:
    if not rows:
        return None, None, []

    first_row = rows[0]
    fields = list(first_row.keys())
    numeric_fields = [field for field in fields if any(is_numeric(row.get(field)) for row in rows)]
    dimension_fields = [field for field in fields if field not in numeric_fields]

    time_field = next((field for field in dimension_fields if is_time_like(field, [row.get(field) for row in rows])), None)
    preferred = str(preferred_chart_type or "").strip().lower()
    preferred_category = str(category_field or "").strip()
    preferred_value = str(value_field or "").strip()

    if preferred_category and preferred_category in dimension_fields:
        dimension_fields = [preferred_category] + [field for field in dimension_fields if field != preferred_category]
    if preferred_value and preferred_value in numeric_fields:
        numeric_fields = [preferred_value] + [field for field in numeric_fields if field != preferred_value]

    if preferred == "line":
        x_field = time_field or (dimension_fields[0] if dimension_fields else None)
        if x_field and numeric_fields:
            return "line", x_field, numeric_fields[: min(3, len(numeric_fields))]
        return None, None, []

    if preferred == "bar":
        if dimension_fields and numeric_fields:
            return "bar", dimension_fields[0], numeric_fields[: min(3, len(numeric_fields))]
        return None, None, []

    if preferred == "pie":
        if dimension_fields and numeric_fields and 2 <= len(rows) <= 8:
            return "pie", dimension_fields[0], numeric_fields[:1]
        return None, None, []

    if time_field and numeric_fields:
        return "line", time_field, numeric_fields[: min(3, len(numeric_fields))]

    if dimension_fields and numeric_fields:
        return "bar", dimension_fields[0], numeric_fields[: min(3, len(numeric_fields))]

    return None, None, []


def main():
    parser = argparse.ArgumentParser(description="Build a chart spec from SQL execution JSON")
    parser.add_argument("--input", default="")
    parser.add_argument("--input-file", default="")
    parser.add_argument("--chart-type", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--data", default="")
    parser.add_argument("--category-field", default="")
    parser.add_argument("--value-field", default="")
    args = parser.parse_args()

    try:
        raw_input = str(args.input or "").strip()
        input_file = str(args.input_file or "").strip() or None
        payload: dict[str, Any] = {}
        if raw_input or input_file:
            loaded_payload = load_json_input(raw=raw_input, file_path=input_file)
            payload = loaded_payload if isinstance(loaded_payload, dict) else {}
        rows = payload.get("rows") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raw_data = str(args.data or "").strip()
            if raw_data:
                rows = load_json_input(raw=raw_data)
            if not isinstance(rows, list):
                raise ValueError("输入中缺少 rows")

        chart_type, x_field, series_fields = choose_chart(
            rows,
            preferred_chart_type=str(args.chart_type or "").strip(),
            category_field=str(args.category_field or "").strip(),
            value_field=str(args.value_field or "").strip(),
        )
        if not chart_type or not x_field or not series_fields:
            print_json(
                {
                    "kind": "chart_spec",
                    "chart_type": "",
                    "title": "",
                    "description": "结果更适合以表格展示，未生成图表。",
                    "dataset": [],
                    "series": [],
                    "error": None,
                }
            )
            return

        title = str(args.title or "").strip() or payload.get("summary") or "查询结果图表"
        series = [
            {"name": field, "field": field, "type": chart_type}
            for field in series_fields
        ]
        print_json(
            {
                "kind": "chart_spec",
                "chart_type": chart_type,
                "title": title,
                "description": f"基于 {x_field} 绘制 {chart_type} 图",
                "x_field": x_field,
                "series": series,
                "dataset": rows[:20],
                "error": None,
            }
        )
    except Exception as exc:
        print_json(error_payload("chart_spec", str(exc), chart_type="", dataset=[], series=[]))


if __name__ == "__main__":
    main()
