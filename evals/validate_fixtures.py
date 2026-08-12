#!/usr/bin/env python3
"""Prove that reference tests pass and kill every declared mutation."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from eval_lib import (
    apply_mutation,
    copy_reference_tests,
    copy_workspace,
    restore_mutation,
    run_command,
    select_cases,
)


def validate_case(case: dict, *, skip_setup: bool, infrastructure: bool) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"skill-suite-fixture-{case['id']}-") as directory:
        workspace = Path(directory) / "workspace"
        copy_workspace(case, workspace)
        copy_reference_tests(case, workspace)

        if not skip_setup:
            for index, setup_command in enumerate(case["setup_commands"], start=1):
                setup = run_command(setup_command, workspace, timeout=900)
                if not setup.passed:
                    return {
                        "case": case["id"],
                        "passed": False,
                        "stage": f"setup-{index}",
                        "exit_code": setup.exit_code,
                        "output": setup.stdout + setup.stderr,
                    }

        reference = run_command(case["test_command"], workspace, timeout=600)
        if not reference.passed:
            return {
                "case": case["id"],
                "passed": False,
                "stage": "reference",
                "exit_code": reference.exit_code,
                "output": reference.stdout + reference.stderr,
            }

        extended_result = None
        if infrastructure and case.get("extended_test_command"):
            extended_result = run_command(case["extended_test_command"], workspace, timeout=900)
            if not extended_result.passed:
                return {
                    "case": case["id"],
                    "passed": False,
                    "stage": "extended",
                    "exit_code": extended_result.exit_code,
                    "output": extended_result.stdout + extended_result.stderr,
                }

        mutations = []
        for mutation in case["mutations"]:
            original = apply_mutation(workspace, mutation)
            try:
                result = run_command(case["test_command"], workspace, timeout=600)
            finally:
                restore_mutation(workspace, mutation, original)
            mutations.append(
                {
                    "id": mutation["id"],
                    "killed": not result.passed,
                    "exit_code": result.exit_code,
                }
            )

        return {
            "case": case["id"],
            "passed": all(item["killed"] for item in mutations),
            "stage": "complete",
            "reference_exit_code": reference.exit_code,
            "extended_check": "passed" if extended_result is not None else "not_run",
            "mutations": mutations,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", dest="cases", help="Case id; repeat to select multiple")
    parser.add_argument("--skip-setup", action="store_true", help="Skip dependency installation")
    parser.add_argument("--infrastructure", action="store_true", help="Run RabbitMQ/PostgreSQL smoke test")
    parser.add_argument("--output", type=Path, help="Write JSON report to this path")
    return parser


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    results = [
        validate_case(case, skip_setup=args.skip_setup, infrastructure=args.infrastructure)
        for case in select_cases(args.cases)
    ]
    report = {"passed": all(result["passed"] for result in results), "results": results}
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
