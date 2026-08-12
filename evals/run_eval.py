#!/usr/bin/env python3
"""Run paired agent evaluations and grade the generated tests deterministically."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

from eval_lib import (
    EVAL_ROOT,
    REPO_ROOT,
    apply_mutation,
    copy_eval_contract,
    copy_workspace,
    hash_paths,
    install_skill,
    manifest_hashes,
    restore_mutation,
    run_command,
    sanitized_environment,
    select_cases,
    write_command_log,
)

import sys

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from validate_test_evidence import validate as validate_evidence  # noqa: E402


def build_agent_command(
    agent: str,
    prompt: str,
    workspace: Path,
    runtime_home: Path,
    model: str | None,
) -> tuple[list[str], dict[str, str]]:
    isolated_home = runtime_home / "home"
    isolated_home.mkdir(parents=True, exist_ok=True)
    playwright_browsers = Path(tempfile.gettempdir()) / "skill-suite-tests-playwright"
    isolated_paths = {
        "APPDATA": str(isolated_home / "appdata"),
        "HOME": str(isolated_home),
        "LOCALAPPDATA": str(isolated_home / "localappdata"),
        "PLAYWRIGHT_BROWSERS_PATH": str(playwright_browsers),
        "USERPROFILE": str(isolated_home),
        "XDG_CACHE_HOME": str(isolated_home / ".cache"),
        "XDG_CONFIG_HOME": str(isolated_home / ".config"),
        "XDG_DATA_HOME": str(isolated_home / ".local" / "share"),
    }
    for name, value in isolated_paths.items():
        if name != "PLAYWRIGHT_BROWSERS_PATH":
            Path(value).mkdir(parents=True, exist_ok=True)

    if agent == "codex":
        executable = shutil.which("codex")
        if not executable:
            raise RuntimeError("codex CLI is not available")
        codex_home = runtime_home / "codex-home"
        codex_home.mkdir(parents=True, exist_ok=True)
        command = [
            executable,
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            "workspace-write",
            "--json",
        ]
        if model:
            command.extend(["--model", model])
        command.append(prompt)
        environment = sanitized_environment(
            {**isolated_paths, "CODEX_HOME": str(codex_home)}
        )
        environment.pop("CURSOR_API_KEY", None)
        return command, environment

    executable = shutil.which("cursor-agent") or shutil.which("agent")
    if not executable:
        raise RuntimeError("cursor-agent CLI is not available")
    command = [
        executable,
        "--print",
        "--force",
        "--output-format",
        "stream-json",
        "--sandbox",
        "enabled",
        "--trust",
        "--workspace",
        str(workspace),
    ]
    if model:
        command.extend(["--model", model])
    command.append(prompt)
    environment = sanitized_environment(isolated_paths)
    environment.pop("OPENAI_API_KEY", None)
    return command, environment


def grade_workspace(
    case: dict[str, Any],
    workspace: Path,
    production_before: dict[str, str],
    manifests_before: dict[str, str],
    artifacts: Path,
) -> dict[str, Any]:
    production_unchanged = production_before == hash_paths(workspace, case["production_paths"])
    manifests_unchanged = manifests_before == manifest_hashes(workspace)

    correct = run_command(case["test_command"], workspace, timeout=600)
    write_command_log(artifacts / "correct-tests.json", correct)
    if correct.passed and case.get("extended_test_command"):
        extended = run_command(case["extended_test_command"], workspace, timeout=900)
        write_command_log(artifacts / "extended-tests.json", extended)
        if not extended.passed:
            correct = extended

    mutation_results = []
    if correct.passed:
        for mutation in case["mutations"]:
            original = apply_mutation(workspace, mutation)
            try:
                result = run_command(case["test_command"], workspace, timeout=600)
            finally:
                restore_mutation(workspace, mutation, original)
            write_command_log(artifacts / f"mutation-{mutation['id']}.json", result)
            mutation_results.append({"id": mutation["id"], "killed": not result.passed})
    else:
        mutation_results = [{"id": mutation["id"], "killed": False} for mutation in case["mutations"]]

    mutation_score = sum(item["killed"] for item in mutation_results) / len(mutation_results)
    production_unchanged = production_unchanged and production_before == hash_paths(workspace, case["production_paths"])
    manifests_unchanged = manifests_unchanged and manifests_before == manifest_hashes(workspace)
    evidence_path = workspace / "test-evidence.json"
    if evidence_path.is_file():
        try:
            evidence_document = json.loads(evidence_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            evidence_errors = [f"invalid JSON: {error}"]
            evidence_text = ""
        else:
            evidence_errors = validate_evidence(evidence_document)
            evidence_text = json.dumps(evidence_document, ensure_ascii=False).lower()
    else:
        evidence_errors = ["test-evidence.json was not created"]
        evidence_text = ""

    covered_risks = [risk for risk in case["required_risks"] if risk.lower() in evidence_text]
    coverage_ratio = len(covered_risks) / len(case["required_risks"])

    score = round(
        (30 if correct.passed else 0)
        + 35 * mutation_score
        + 15 * coverage_ratio
        + (10 if production_unchanged and manifests_unchanged else 0)
        + (10 if not evidence_errors else 0),
        2,
    )
    critical_pass = (
        correct.passed
        and production_unchanged
        and mutation_score >= 0.8
        and not evidence_errors
        and score >= 80
    )
    return {
        "score": score,
        "critical_pass": critical_pass,
        "correct_tests_passed": correct.passed,
        "mutation_score": mutation_score,
        "mutations": mutation_results,
        "covered_risks": covered_risks,
        "required_risks": case["required_risks"],
        "production_unchanged": production_unchanged,
        "manifests_unchanged": manifests_unchanged,
        "evidence_valid": not evidence_errors,
        "evidence_errors": evidence_errors,
    }


def run_once(
    case: dict[str, Any],
    agent: str,
    mode: str,
    repetition: int,
    model: str | None,
    artifact_root: Path,
    dry_run: bool,
) -> dict[str, Any]:
    run_id = f"{agent}-{case['id']}-{mode}-{repetition}"
    artifacts = artifact_root / run_id
    artifacts.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=f"skill-suite-{run_id}-") as directory:
        runtime_root = Path(directory)
        workspace = runtime_root / "workspace"
        runtime_home = runtime_root / "agent-home"
        copy_workspace(case, workspace)
        copy_eval_contract(workspace)

        if mode == "skill":
            install_skill(workspace / ".agents" / "skills" / "skill-suite-tests")

        risk_ids = ", ".join(case["required_risks"])
        invocation = "Use $skill-suite-tests. " if agent == "codex" else "/skill-suite-tests "
        prompt = (
            (invocation if mode == "skill" else "")
            + case["prompt"]
            + f" Use exatamente estes IDs em risks[].id: {risk_ids}."
            + " Siga .eval-contract/test-evidence.v1.json e valide o relatório com .eval-contract/validate_test_evidence.py."
            + " Trabalhe apenas neste workspace e limite conclusões ao que executar."
        )
        command, environment = build_agent_command(agent, prompt, workspace, runtime_home, model)
        version_result = run_command([command[0], "--version"], workspace, env=environment, timeout=30)
        agent_version = (version_result.stdout or version_result.stderr).strip() or "unknown"
        if not dry_run and not version_result.passed:
            raise RuntimeError(f"unable to execute {agent} CLI: {agent_version}")
        if dry_run:
            result = {
                "run_id": run_id,
                "agent": agent,
                "case": case["id"],
                "mode": mode,
                "repetition": repetition,
                "model": model or "agent-default",
                "agent_version": agent_version,
                "dry_run": True,
                "command": command,
            }
            (artifacts / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
            return result

        required_secret = "OPENAI_API_KEY" if agent == "codex" else "CURSOR_API_KEY"
        if not environment.get(required_secret):
            raise RuntimeError(f"{required_secret} is required for {agent} evals")

        if agent == "codex":
            authentication = run_command(
                [command[0], "login", "--with-api-key"],
                workspace,
                env=environment,
                input_text=environment[required_secret] + "\n",
                timeout=30,
            )
            authentication_log = artifacts / "agent-auth.json"
            write_command_log(authentication_log, authentication)
            if not authentication.passed:
                raise RuntimeError(f"authentication failed for {run_id}; see {authentication_log}")

        for index, setup_command in enumerate(case["setup_commands"], start=1):
            setup = run_command(setup_command, workspace, env=environment, timeout=900)
            setup_log = artifacts / f"setup-{index}.json"
            write_command_log(setup_log, setup)
            if not setup.passed:
                raise RuntimeError(f"setup failed for {run_id}; see {setup_log}")

        production_before = hash_paths(workspace, case["production_paths"])
        manifests_before = manifest_hashes(workspace)
        started = time.monotonic()
        agent_result = run_command(command, workspace, env=environment, timeout=1800)
        duration_seconds = round(time.monotonic() - started, 2)
        write_command_log(artifacts / "agent.json", agent_result)

        grade = grade_workspace(case, workspace, production_before, manifests_before, artifacts)
        grade["critical_pass"] = grade["critical_pass"] and agent_result.passed
        result = {
            "run_id": run_id,
            "agent": agent,
            "case": case["id"],
            "mode": mode,
            "repetition": repetition,
            "model": model or "agent-default",
            "agent_version": agent_version,
            "dry_run": False,
            "agent_exit_code": agent_result.exit_code,
            "duration_seconds": duration_seconds,
            **grade,
        }
        (artifacts / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return result


def aggregate(results: list[dict[str, Any]], *, repetitions: int) -> dict[str, Any]:
    if any(result.get("dry_run") for result in results):
        return {"dry_run": True, "passed": True, "results": results}

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault((result["agent"], result["case"], result["mode"]), []).append(result)

    summaries = []
    for (agent, case, mode), runs in sorted(grouped.items()):
        summaries.append(
            {
                "agent": agent,
                "case": case,
                "mode": mode,
                "median_score": statistics.median(run["score"] for run in runs),
                "critical_passes": sum(run["critical_pass"] for run in runs),
                "runs": len(runs),
            }
        )

    comparisons = []
    agents = sorted({result["agent"] for result in results})
    cases = sorted({result["case"] for result in results})
    required_passes = 2 if repetitions >= 3 else repetitions
    for agent in agents:
        for case in cases:
            baseline = next(item for item in summaries if item["agent"] == agent and item["case"] == case and item["mode"] == "baseline")
            treatment = next(item for item in summaries if item["agent"] == agent and item["case"] == case and item["mode"] == "skill")
            comparisons.append(
                {
                    "agent": agent,
                    "case": case,
                    "baseline": baseline["median_score"],
                    "skill": treatment["median_score"],
                    "gain": treatment["median_score"] - baseline["median_score"],
                    "critical_gate": treatment["critical_passes"] >= required_passes,
                }
            )

    skill_scores = [item["skill"] for item in comparisons]
    gains = [item["gain"] for item in comparisons]
    execution_failures = [
        result["run_id"]
        for result in results
        if result.get("agent_exit_code", 0) != 0
    ]
    passed = (
        not execution_failures
        and statistics.median(skill_scores) >= 85
        and statistics.median(gains) >= 8
        and all(
            sum(item["gain"] > 0 for item in comparisons if item["agent"] == agent) >= 2
            for agent in agents
        )
        and all(gain >= -5 for gain in gains)
        and all(item["critical_gate"] for item in comparisons)
    )
    return {
        "dry_run": False,
        "passed": passed,
        "execution_failures": execution_failures,
        "median_skill_score": statistics.median(skill_scores),
        "median_gain": statistics.median(gains),
        "summaries": summaries,
        "comparisons": comparisons,
    }


def evaluation_exit_code(report: dict[str, Any], *, enforce_gate: bool) -> int:
    if report.get("execution_failures"):
        return 1
    return 1 if enforce_gate and not report["passed"] else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", action="append", choices=("codex", "cursor"), required=True)
    parser.add_argument("--case", action="append", dest="cases")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--model")
    parser.add_argument("--artifacts", type=Path, default=EVAL_ROOT / "artifacts")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--enforce-gate", action="store_true")
    return parser


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    if args.repetitions < 1:
        raise SystemExit("--repetitions must be at least 1")
    if not args.dry_run and not args.model:
        raise SystemExit("--model is required for comparable eval runs")
    cases = select_cases(args.cases)
    results = []
    for agent in args.agent:
        for case in cases:
            for repetition in range(1, args.repetitions + 1):
                for mode in ("baseline", "skill"):
                    results.append(
                        run_once(
                            case,
                            agent,
                            mode,
                            repetition,
                            args.model,
                            args.artifacts,
                            args.dry_run,
                        )
                    )
    report = aggregate(results, repetitions=args.repetitions)
    args.artifacts.mkdir(parents=True, exist_ok=True)
    (args.artifacts / "summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return evaluation_exit_code(report, enforce_gate=args.enforce_gate)


if __name__ == "__main__":
    raise SystemExit(main())
