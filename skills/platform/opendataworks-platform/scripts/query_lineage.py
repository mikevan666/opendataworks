from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))

from odw_skill_runtime import call_metadata_cli, error_payload, print_json  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Query OpenDataWorks lineage")
    parser.add_argument("--table", default="")
    parser.add_argument("--db-name", default="")
    parser.add_argument("--table-id", type=int)
    parser.add_argument("--depth", type=int)
    args = parser.parse_args()

    try:
        payload = call_metadata_cli(
            "lineage",
            table=args.table,
            db_name=args.db_name,
            table_id=args.table_id,
            depth=args.depth,
        )
        print_json(payload)
    except Exception as exc:
        print_json(
            error_payload(
                "lineage_snapshot",
                str(exc),
                table=args.table or None,
                db_name=args.db_name or None,
                table_id=args.table_id,
            )
        )


if __name__ == "__main__":
    main()
