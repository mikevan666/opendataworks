from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from odw_skill_runtime import call_metadata_cli, error_payload, print_json  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Inspect OpenDataWorks metadata")
    parser.add_argument("--database", default="")
    parser.add_argument("--table", default="")
    parser.add_argument("--keyword", default="")
    parser.add_argument("--table-limit", type=int, default=12)
    args = parser.parse_args()

    try:
        payload = call_metadata_cli(
            "inspect",
            database=args.database,
            table=args.table,
            keyword=args.keyword,
            table_limit=args.table_limit,
        )
        print_json(payload)
    except Exception as exc:
        print_json(
            error_payload(
                "metadata_snapshot",
                str(exc),
                database=args.database or None,
                table=args.table or None,
                keyword=args.keyword or None,
            )
        )


if __name__ == "__main__":
    main()
