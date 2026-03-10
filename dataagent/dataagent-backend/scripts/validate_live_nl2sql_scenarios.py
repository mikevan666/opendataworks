#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    category: str
    question: str
    expected_kinds: tuple[str, ...] = ()
    expected_chart_types: tuple[str, ...] = ()
    require_sql: bool = False
    require_nonempty_content: bool = True


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        scenario_id="term_explanation",
        category="term",
        question="什么是数据表血缘？",
    ),
    Scenario(
        scenario_id="statistics",
        category="statistics",
        question="当前 active 状态的数据表数量",
        expected_kinds=("sql_execution",),
        require_sql=True,
    ),
    Scenario(
        scenario_id="comparison",
        category="comparison",
        question="各数据层表数量对比",
        expected_kinds=("chart_spec",),
        expected_chart_types=("bar",),
    ),
    Scenario(
        scenario_id="trend",
        category="trend",
        question="最近 30 天工作流发布次数趋势",
        expected_kinds=("chart_spec",),
        expected_chart_types=("line",),
    ),
    Scenario(
        scenario_id="share",
        category="share",
        question="各工作流发布操作类型占比",
        expected_kinds=("chart_spec",),
        expected_chart_types=("pie",),
    ),
    Scenario(
        scenario_id="detail",
        category="detail",
        question="最近工作流发布记录",
        expected_kinds=("sql_execution",),
        require_sql=True,
    ),
    Scenario(
        scenario_id="diagnosis",
        category="diagnosis",
        question="查看 dwd_tech_dev_inspection_rule_cnt_di 的上下游血缘",
        expected_kinds=("sql_execution",),
        require_sql=True,
    ),
    Scenario(
        scenario_id="sql_example",
        category="sql_example",
        question="给我一个查询最近 7 天工作流发布记录的 SQL 示例",
    ),
)


def _http_json(method: str, url: str, *, payload: dict[str, Any] | None, timeout_seconds: int) -> Any:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=headers, method=method.upper())
    with urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _parse_sse_events(raw_text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for chunk in raw_text.split("\n\n"):
        lines = [line for line in chunk.splitlines() if line.startswith("data:")]
        if not lines:
            continue
        payload = "\n".join(line[5:].lstrip() for line in lines)
        try:
            events.append(json.loads(payload))
        except json.JSONDecodeError:
            continue
    return events


def _http_sse(url: str, *, payload: dict[str, Any], timeout_seconds: int) -> list[dict[str, Any]]:
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        raw = response.read().decode("utf-8")
    return _parse_sse_events(raw)


def _maybe_json(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return value
        if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return value
    return value


def _iter_outputs(value: Any):
    parsed = _maybe_json(value)
    if isinstance(parsed, dict):
        yield parsed
        for child in parsed.values():
            yield from _iter_outputs(child)
        return
    if isinstance(parsed, list):
        for item in parsed:
            yield from _iter_outputs(item)


def _analyze_response(data: dict[str, Any]) -> dict[str, Any]:
    blocks = data.get("blocks") or []
    kinds: list[str] = []
    chart_types: list[str] = []
    sql_count = 0
    tool_names: list[str] = []
    block_types = [str(block.get("type") or "") for block in blocks]

    for block in blocks:
        tool_name = str(block.get("tool_name") or "").strip()
        if tool_name:
            tool_names.append(tool_name)
        output = block.get("output")
        for item in _iter_outputs(output):
            if not isinstance(item, dict):
                continue
            kind = str(item.get("kind") or "").strip()
            if kind:
                kinds.append(kind)
                if kind == "sql_execution":
                    sql_count += 1
            chart_type = str(item.get("chart_type") or "").strip()
            if chart_type:
                chart_types.append(chart_type)

    return {
        "status": str(data.get("status") or ""),
        "content": str(data.get("content") or ""),
        "error": data.get("error"),
        "block_types": block_types,
        "tool_names": tool_names,
        "kinds": kinds,
        "chart_types": chart_types,
        "sql_count": sql_count,
        "block_count": len(blocks),
    }


def _validate_scenario(scenario: Scenario, analysis: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if analysis.get("status") != "success":
        reasons.append(f"status={analysis.get('status')}")
    if scenario.require_nonempty_content and not str(analysis.get("content") or "").strip():
        reasons.append("empty_content")

    actual_kinds = set(str(item) for item in analysis.get("kinds") or [])
    expected_kinds = set(scenario.expected_kinds)
    if expected_kinds and not (actual_kinds & expected_kinds):
        reasons.append(f"missing_expected_kind:{','.join(sorted(expected_kinds))}")

    if scenario.require_sql and int(analysis.get("sql_count") or 0) <= 0:
        reasons.append("missing_sql_execution")

    actual_chart_types = set(str(item) for item in analysis.get("chart_types") or [])
    expected_chart_types = set(scenario.expected_chart_types)
    if expected_chart_types and not (actual_chart_types & expected_chart_types):
        reasons.append(f"missing_expected_chart:{','.join(sorted(expected_chart_types))}")

    if scenario.category == "sql_example":
        content_lower = str(analysis.get("content") or "").lower()
        if "select" not in content_lower:
            reasons.append("sql_example_missing_select")

    return (not reasons, reasons)


def _run_non_stream(base_url: str, scenario: Scenario, provider_id: str, model: str, timeout_seconds: int) -> dict[str, Any]:
    session_id = f"live-{scenario.scenario_id}-{uuid.uuid4().hex[:8]}"
    url = f"{base_url}/api/v1/nl2sql/sessions/{session_id}/messages"
    start = time.perf_counter()
    payload = {
        "content": scenario.question,
        "stream": False,
        "provider_id": provider_id,
        "model": model,
    }
    data = _http_json("POST", url, payload=payload, timeout_seconds=timeout_seconds)
    elapsed = round(time.perf_counter() - start, 2)
    analysis = _analyze_response(data)
    passed, reasons = _validate_scenario(scenario, analysis)
    return {
        "mode": "non_stream",
        "session_id": session_id,
        "elapsed_seconds": elapsed,
        "passed": passed,
        "reasons": reasons,
        "response": analysis,
    }


def _run_stream(base_url: str, scenario: Scenario, provider_id: str, model: str, timeout_seconds: int) -> dict[str, Any]:
    session_id = f"live-{scenario.scenario_id}-{uuid.uuid4().hex[:8]}"
    url = f"{base_url}/api/v1/nl2sql/sessions/{session_id}/messages"
    start = time.perf_counter()
    payload = {
        "content": scenario.question,
        "stream": True,
        "provider_id": provider_id,
        "model": model,
    }
    events = _http_sse(url, payload=payload, timeout_seconds=timeout_seconds)
    elapsed = round(time.perf_counter() - start, 2)
    done = next((event for event in reversed(events) if str(event.get("type") or "") == "done"), {})
    analysis = _analyze_response(done.get("payload") or {})
    passed, reasons = _validate_scenario(scenario, analysis)
    if not events:
        reasons.append("no_stream_events")
        passed = False
    elif str(events[-1].get("type") or "") != "done":
        reasons.append("stream_missing_done")
        passed = False
    return {
        "mode": "stream",
        "session_id": session_id,
        "elapsed_seconds": elapsed,
        "passed": passed,
        "reasons": reasons,
        "event_count": len(events),
        "event_types": [str(event.get("type") or "") for event in events],
        "response": analysis,
    }


def _report_line(result: dict[str, Any]) -> str:
    response = result.get("response") or {}
    outcome = "PASS" if result.get("passed") else "FAIL"
    return (
        f"[{outcome}] {result.get('mode')} "
        f"elapsed={result.get('elapsed_seconds')}s "
        f"kinds={response.get('kinds')} chart_types={response.get('chart_types')} "
        f"reasons={result.get('reasons')}"
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate live NL2SQL scenarios against the local backend.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8900")
    parser.add_argument("--provider-id", default="")
    parser.add_argument("--model", default="")
    parser.add_argument(
        "--mode",
        choices=("non-stream", "stream", "both"),
        default="stream",
        help="Validation focus defaults to stream because the production frontend uses SSE.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--report", default="")
    parser.add_argument("--scenario", action="append", default=[], help="Only run the specified scenario_id. Repeatable.")
    args = parser.parse_args(argv)

    settings = _http_json("GET", f"{args.base_url}/api/v1/nl2sql/settings", payload=None, timeout_seconds=args.timeout_seconds)
    provider_id = args.provider_id or str(settings.get("default_provider_id") or "")
    model = args.model or str(settings.get("default_model") or "")
    if not provider_id or not model:
        print("missing default provider/model", file=sys.stderr)
        return 2

    report: dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "base_url": args.base_url,
        "provider_id": provider_id,
        "model": model,
        "mode": args.mode,
        "scenarios": [],
    }

    runners = []
    if args.mode in {"non-stream", "both"}:
        runners.append(_run_non_stream)
    if args.mode in {"stream", "both"}:
        runners.append(_run_stream)

    requested = {item.strip() for item in args.scenario if str(item or "").strip()}
    scenarios = [item for item in SCENARIOS if not requested or item.scenario_id in requested]
    if requested and not scenarios:
        print(f"unknown scenario ids: {sorted(requested)}", file=sys.stderr, flush=True)
        return 2

    for scenario in scenarios:
        scenario_entry = {
            "scenario_id": scenario.scenario_id,
            "category": scenario.category,
            "question": scenario.question,
            "results": [],
        }
        print(f"\n=== {scenario.scenario_id} | {scenario.question}", flush=True)
        for runner in runners:
            try:
                result = runner(args.base_url, scenario, provider_id, model, args.timeout_seconds)
            except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
                result = {
                    "mode": "stream" if runner is _run_stream else "non_stream",
                    "passed": False,
                    "reasons": [exc.__class__.__name__, str(exc)],
                    "response": {
                        "status": "failed",
                        "content": "",
                        "error": {"message": str(exc)},
                        "block_types": [],
                        "tool_names": [],
                        "kinds": [],
                        "chart_types": [],
                        "sql_count": 0,
                        "block_count": 0,
                    },
                }
            scenario_entry["results"].append(result)
            print(_report_line(result), flush=True)
        report["scenarios"].append(scenario_entry)

    total = sum(len(item["results"]) for item in report["scenarios"])
    passed = sum(1 for item in report["scenarios"] for result in item["results"] if result.get("passed"))
    report["summary"] = {
        "total_checks": total,
        "passed_checks": passed,
        "failed_checks": total - passed,
    }

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nSummary: passed={passed}/{total} failed={total - passed}")
    if args.report:
        print(f"Report: {args.report}", flush=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
