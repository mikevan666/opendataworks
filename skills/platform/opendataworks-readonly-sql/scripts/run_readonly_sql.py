from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from odw_skill_runtime import call_metadata_cli, error_payload, print_json  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Execute readonly SQL through OpenDataWorks agent API")
    parser.add_argument("--database", required=True)
    parser.add_argument("--sql", required=True)
    parser.add_argument("--preferred-engine", default="")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()

    try:
        payload = call_metadata_cli(
            "read-query",
            database=args.database,
            sql=args.sql,
            preferred_engine=args.preferred_engine,
            limit=args.limit,
            timeout_seconds=args.timeout_seconds,
        )
        print_json(payload)
    except Exception as exc:
        print_json(
            error_payload(
                "query_result",
                str(exc),
                database=args.database,
                sql=args.sql,
            )
        )


if __name__ == "__main__":
    main()
