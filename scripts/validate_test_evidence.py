#!/usr/bin/env python3
"""Validate the semantic contract of a Skill Suite Tests evidence report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CLASSIFICATION_FIELDS = ("purpose", "level", "quality_attributes", "techniques")
COMMAND_STATUSES = {"passed", "failed", "not_run"}
SUPPORT_STATUSES = {"validated", "adaptable"}
BOUNDARY_MODES = {"real", "containerized", "virtualized", "simulated"}


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(value: Any, *, allow_empty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(non_empty_string(item) for item in value)
    )


def validate(document: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["report must be a JSON object"]

    if document.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")
    if not non_empty_string(document.get("target")):
        errors.append("target must be a non-empty string")
    if document.get("support_status") not in SUPPORT_STATUSES:
        errors.append("support_status must be 'validated' or 'adaptable'")

    classification = document.get("classification")
    if not isinstance(classification, dict):
        errors.append("classification must be an object")
    else:
        for field in CLASSIFICATION_FIELDS:
            if not string_list(classification.get(field)):
                errors.append(f"classification.{field} must be a non-empty string array")

    basis = document.get("basis")
    if not isinstance(basis, list) or not basis:
        errors.append("basis must contain at least one traceable source")
    else:
        for index, item in enumerate(basis):
            if not isinstance(item, dict) or not non_empty_string(item.get("type")) or not non_empty_string(item.get("reference")):
                errors.append(f"basis[{index}] must contain non-empty type and reference")

    risks = document.get("risks")
    risk_ids: set[str] = set()
    if not isinstance(risks, list) or not risks:
        errors.append("risks must contain at least one risk")
    else:
        for index, risk in enumerate(risks):
            if not isinstance(risk, dict):
                errors.append(f"risks[{index}] must be an object")
                continue
            risk_id = risk.get("id")
            if not non_empty_string(risk_id):
                errors.append(f"risks[{index}].id must be a non-empty string")
            elif risk_id in risk_ids:
                errors.append(f"risks[{index}].id duplicates '{risk_id}'")
            else:
                risk_ids.add(risk_id)
            if not non_empty_string(risk.get("description")):
                errors.append(f"risks[{index}].description must be a non-empty string")
            if not non_empty_string(risk.get("impact")):
                errors.append(f"risks[{index}].impact must be a non-empty string")

    scenarios = document.get("scenarios")
    referenced_risk_ids: set[str] = set()
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("scenarios must contain at least one scenario")
    else:
        scenario_ids: set[str] = set()
        for index, scenario in enumerate(scenarios):
            if not isinstance(scenario, dict):
                errors.append(f"scenarios[{index}] must be an object")
                continue
            scenario_id = scenario.get("id")
            if not non_empty_string(scenario_id):
                errors.append(f"scenarios[{index}].id must be a non-empty string")
            elif scenario_id in scenario_ids:
                errors.append(f"scenarios[{index}].id duplicates '{scenario_id}'")
            else:
                scenario_ids.add(scenario_id)
            linked_risks = scenario.get("risk_ids")
            if not string_list(linked_risks):
                errors.append(f"scenarios[{index}].risk_ids must be a non-empty string array")
            elif risk_ids:
                referenced_risk_ids.update(linked_risks)
                unknown = sorted(set(linked_risks) - risk_ids)
                if unknown:
                    errors.append(f"scenarios[{index}].risk_ids references unknown risks: {', '.join(unknown)}")
            for field in ("name", "preconditions", "stimulus", "oracle", "isolation", "cleanup"):
                if not non_empty_string(scenario.get(field)):
                    errors.append(f"scenarios[{index}].{field} must be a non-empty string")
        unreferenced = sorted(risk_ids - referenced_risk_ids)
        if unreferenced:
            errors.append(f"risks without a scenario: {', '.join(unreferenced)}")

    boundaries = document.get("boundaries")
    if not isinstance(boundaries, list) or not boundaries:
        errors.append("boundaries must contain at least one boundary")
    else:
        for index, boundary in enumerate(boundaries):
            if not isinstance(boundary, dict):
                errors.append(f"boundaries[{index}] must be an object")
                continue
            if not non_empty_string(boundary.get("name")):
                errors.append(f"boundaries[{index}].name must be a non-empty string")
            if boundary.get("mode") not in BOUNDARY_MODES:
                errors.append(f"boundaries[{index}].mode is invalid")
            if not non_empty_string(boundary.get("rationale")):
                errors.append(f"boundaries[{index}].rationale must be a non-empty string")

    if not string_list(document.get("files_changed")):
        errors.append("files_changed must contain at least one path")

    commands = document.get("commands")
    if not isinstance(commands, list) or not commands:
        errors.append("commands must contain at least one command")
    else:
        executed = False
        for index, command in enumerate(commands):
            if not isinstance(command, dict):
                errors.append(f"commands[{index}] must be an object")
                continue
            if not non_empty_string(command.get("command")):
                errors.append(f"commands[{index}].command must be a non-empty string")
            status = command.get("status")
            if status not in COMMAND_STATUSES:
                errors.append(f"commands[{index}].status is invalid")
            exit_code = command.get("exit_code")
            if status == "not_run":
                if exit_code is not None:
                    errors.append(f"commands[{index}].exit_code must be null when not_run")
            else:
                executed = True
                if not isinstance(exit_code, int):
                    errors.append(f"commands[{index}].exit_code must be an integer when executed")
                elif status == "passed" and exit_code != 0:
                    errors.append(f"commands[{index}] passed with non-zero exit_code")
                elif status == "failed" and exit_code == 0:
                    errors.append(f"commands[{index}] failed with zero exit_code")
            if not non_empty_string(command.get("evidence")):
                errors.append(f"commands[{index}].evidence must be a non-empty string")
        if not executed:
            errors.append("at least one command must have been executed")

    evidence = document.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("evidence must contain at least one item")
    else:
        for index, item in enumerate(evidence):
            if not isinstance(item, dict) or not non_empty_string(item.get("type")) or not non_empty_string(item.get("summary")):
                errors.append(f"evidence[{index}] must contain non-empty type and summary")

    if not string_list(document.get("limitations"), allow_empty=True):
        errors.append("limitations must be an array of strings")

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Path to test-evidence.json")
    parser.add_argument("--json", action="store_true", help="Emit validation result as JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        document = json.loads(args.report.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors = [f"report not found: {args.report}"]
    except json.JSONDecodeError as exc:
        errors = [f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"]
    except OSError as exc:
        errors = [f"unable to read report: {exc}"]
    else:
        errors = validate(document)

    result = {"valid": not errors, "errors": errors}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
    else:
        print("Test evidence is valid.")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
