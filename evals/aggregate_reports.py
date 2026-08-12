#!/usr/bin/env python3
"""Aggregate eval result shards and enforce the release gate."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from run_eval import aggregate


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, required=True)
    parser.add_argument("--agent", action="append", dest="agents", required=True)
    parser.add_argument("--case", action="append", dest="cases", required=True)
    parser.add_argument("--enforce-gate", action="store_true")
    args = parser.parse_args()

    results = []
    for path in sorted(args.input.rglob("result.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        if {"agent", "case", "mode", "repetition"}.issubset(document):
            results.append(document)
    if not results:
        raise SystemExit("no eval result shards found")

    report = aggregate(
        results,
        repetitions=args.repetitions,
        expected_agents=args.agents,
        expected_cases=args.cases,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        lines = [
            "## Skill Suite Tests eval",
            "",
            f"Gate: **{'PASS' if report['passed'] else 'FAIL'}**",
            "",
            "| Agente | Caso | Baseline | Skill | Ganho | Gate crítico |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
        if report.get("matrix_errors"):
            lines.extend(
                ["", "### Erros de matriz", "", *[f"- {error}" for error in report["matrix_errors"]]]
            )
        for comparison in report.get("comparisons", []):
            lines.append(
                f"| {comparison['agent']} | {comparison['case']} | {comparison['baseline']} | "
                f"{comparison['skill']} | {comparison['gain']} | "
                f"{'PASS' if comparison['critical_gate'] else 'FAIL'} |"
            )
        Path(summary_path).open("a", encoding="utf-8").write("\n".join(lines) + "\n")

    return 1 if args.enforce_gate and not report["passed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
