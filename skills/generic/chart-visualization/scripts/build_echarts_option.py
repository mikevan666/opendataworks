from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_rows(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("输入必须是对象数组 JSON")
    return [item for item in data if isinstance(item, dict)]


def main():
    parser = argparse.ArgumentParser(description="Build a basic ECharts option from JSON rows")
    parser.add_argument("--input", required=True)
    parser.add_argument("--chart-type", choices=["line", "bar", "pie"], default="line")
    parser.add_argument("--title", default="")
    parser.add_argument("--x", default="")
    parser.add_argument("--y", default="")
    parser.add_argument("--name", default="")
    args = parser.parse_args()

    rows = load_rows(Path(args.input).expanduser())
    chart_type = args.chart_type
    title = args.title or "数据图表"

    if chart_type == "pie":
        name_key = args.name or args.x
        value_key = args.y
        series_data = [
            {"name": item.get(name_key), "value": item.get(value_key)}
            for item in rows
        ]
        option = {
            "title": {"text": title},
            "tooltip": {"trigger": "item"},
            "legend": {"bottom": 0},
            "series": [{"type": "pie", "radius": "60%", "data": series_data}],
        }
    else:
        x_key = args.x
        y_key = args.y
        option = {
            "title": {"text": title},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": [item.get(x_key) for item in rows]},
            "yAxis": {"type": "value"},
            "series": [
                {
                    "name": y_key,
                    "type": chart_type,
                    "data": [item.get(y_key) for item in rows],
                    "smooth": chart_type == "line",
                }
            ],
        }

    print(json.dumps({"kind": "chart_option", "option": option}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
