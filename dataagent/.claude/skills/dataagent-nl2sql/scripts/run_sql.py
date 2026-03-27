from __future__ import annotations

import argparse

from _opendataworks_runtime import (
    ensure_read_only,
    env_int,
    error_payload,
    print_json,
    query_readonly,
    serializable_rows,
)


def main():
    parser = argparse.ArgumentParser(description="Execute read-only SQL through the backend agent query path")
    parser.add_argument("--database", required=True)
    parser.add_argument("--engine", default="")
    parser.add_argument("--sql", required=True)
    parser.add_argument("--limit", type=int, default=env_int("DATAAGENT_QUERY_LIMIT", 100))
    args = parser.parse_args()

    database = str(args.database or "").strip()
    preferred_engine = str(args.engine or "").strip().lower() or None
    sql = str(args.sql or "").strip()
    limit = max(1, int(args.limit or 100))

    try:
        ensure_read_only(sql)
        result = query_readonly(
            database=database,
            sql=sql,
            preferred_engine=preferred_engine,
            limit=limit,
            timeout_seconds=max(1, env_int("DATAAGENT_SQL_READ_TIMEOUT_SECONDS", 60)),
        )

        preview_rows = list(result.get("rows") or [])[:limit]
        serialized_rows = serializable_rows(preview_rows)
        columns = list(serialized_rows[0].keys()) if serialized_rows else []

        print_json(
            {
                "kind": "sql_execution",
                "tool_label": "SQL 执行",
                "engine": result.get("engine"),
                "database": result.get("database"),
                "sql": sql,
                "columns": columns,
                "rows": serialized_rows,
                "row_count": len(serialized_rows),
                "has_more": bool(result.get("has_more")),
                "duration_ms": int(result.get("duration_ms") or 0),
                "summary": f"返回 {len(serialized_rows)} 行结果",
                "error": None,
            }
        )
    except Exception as exc:
        print_json(
            error_payload(
                "sql_execution",
                str(exc),
                tool_label="SQL 执行",
                database=database,
                engine=preferred_engine,
                sql=sql,
                columns=[],
                rows=[],
                row_count=0,
                has_more=False,
                duration_ms=0,
            )
        )


if __name__ == "__main__":
    main()
