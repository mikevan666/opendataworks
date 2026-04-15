from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean


def load_rows(path: Path):
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        raise ValueError("JSON 文件必须是对象数组")
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    raise ValueError("仅支持 .json 或 .csv")


def maybe_float(value):
    try:
        return float(value)
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="Profile a local CSV or JSON dataset")
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    path = Path(args.input).expanduser()
    rows = load_rows(path)
    numeric_columns = {}
    for row in rows:
        for key, value in row.items():
            number = maybe_float(value)
            if number is None:
                continue
            numeric_columns.setdefault(key, []).append(number)

    summary = {
        "kind": "python_analysis",
        "input": str(path),
        "row_count": len(rows),
        "columns": sorted({key for row in rows for key in row.keys()}),
        "numeric_summary": {
            key: {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": round(mean(values), 4),
            }
            for key, values in sorted(numeric_columns.items())
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
