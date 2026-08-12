#!/usr/bin/env python3
"""Run paired agent evaluations and grade the generated tests deterministically."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import statistics
import tempfile
import time
import unicodedata
from pathlib import Path
from typing import Any

from eval_lib import (
    EVAL_ROOT,
    REPO_ROOT,
    apply_mutation,
    copy_artifact_paths,
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


BASELINE_CACHE_VERSION = "1"


def build_test_environment(environment: dict[str, str]) -> dict[str, str]:
    """Keep deterministic test runtime settings without exposing agent credentials."""
    result = environment.copy()
    result.pop("OPENAI_API_KEY", None)
    result.pop("CURSOR_API_KEY", None)
    return result


def normalize_evidence_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def planned_agent_calls(
    agent_count: int,
    case_count: int,
    repetitions: int,
    *,
    cached_baselines: int = 0,
) -> int:
    """Return the paid call count after valid baseline cache hits are applied."""
    total_pairs = agent_count * case_count * repetitions
    if cached_baselines < 0 or cached_baselines > total_pairs:
        raise ValueError("cached baseline count is outside the evaluation matrix")
    return total_pairs * 2 - cached_baselines


def baseline_fingerprint(case: dict[str, Any], agent: str, model: str) -> str:
    """Fingerprint everything that can change a baseline result."""
    digest = hashlib.sha256()
    digest.update(f"baseline-cache-v{BASELINE_CACHE_VERSION}\0{agent}\0{model}\0".encode())
    paths = [
        EVAL_ROOT / "agent.Dockerfile",
        EVAL_ROOT / "cases.json",
        EVAL_ROOT / "eval_lib.py",
        EVAL_ROOT / "run_eval.py",
        EVAL_ROOT / "validate_fixtures.py",
        EVAL_ROOT / case["workspace"],
        EVAL_ROOT / case["reference_tests"],
        REPO_ROOT / "schemas" / "test-evidence.v1.json",
        REPO_ROOT / "scripts" / "validate_test_evidence.py",
    ]
    files: list[Path] = []
    for path in paths:
        files.extend(sorted(item for item in path.rglob("*") if item.is_file()) if path.is_dir() else [path])
    for path in sorted(set(files), key=lambda item: item.as_posix()):
        digest.update(path.relative_to(REPO_ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def read_cached_baseline(
    cache_root: Path,
    fingerprint: str,
    agent: str,
    case_id: str,
    repetition: int,
    model: str,
) -> tuple[dict[str, Any], Path] | None:
    run_id = f"{agent}-{case_id}-baseline-{repetition}"
    cached_artifacts = cache_root / fingerprint / run_id
    result_path = cached_artifacts / "result.json"
    if not result_path.is_file():
        return None
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    expected = {
        "run_id": run_id,
        "agent": agent,
        "case": case_id,
        "mode": "baseline",
        "repetition": repetition,
        "model": model,
        "dry_run": False,
        "agent_exit_code": 0,
    }
    if any(result.get(key) != value for key, value in expected.items()):
        return None
    return result, cached_artifacts


def restore_cached_baseline(
    cached: tuple[dict[str, Any], Path],
    artifact_root: Path,
) -> dict[str, Any]:
    result, cached_artifacts = cached
    destination = artifact_root / result["run_id"]
    shutil.copytree(cached_artifacts, destination, dirs_exist_ok=True)
    restored = {**result, "baseline_reused": True}
    (destination / "result.json").write_text(
        json.dumps(restored, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return restored


def cache_baseline(
    result: dict[str, Any],
    artifact_root: Path,
    cache_root: Path,
    fingerprint: str,
) -> None:
    if result.get("agent_exit_code") != 0 or result.get("dry_run"):
        return
    source = artifact_root / result["run_id"]
    destination = cache_root / fingerprint / result["run_id"]
    if destination.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)


def covered_risk_ids(case: dict[str, Any], evidence_text: str) -> list[str]:
    """Match hidden risk concepts through deterministic groups of accepted signals."""
    normalized = normalize_evidence_text(evidence_text)
    covered: list[str] = []
    for risk in case["required_risks"]:
        groups = case["risk_signal_groups"][risk]
        if all(any(normalize_evidence_text(signal) in normalized for signal in group) for group in groups):
            covered.append(risk)
    return covered


def build_eval_prompt(case: dict[str, Any], agent: str, mode: str) -> str:
    invocation = "Use $skill-suite-tests. " if agent == "codex" else "/skill-suite-tests "
    return (
        (invocation if mode == "skill" else "")
        + case["prompt"]
        + " Siga .eval-contract/test-evidence.v1.json e valide o relatório com .eval-contract/validate_test_evidence.py."
        + " Trabalhe apenas neste workspace e limite conclusões ao que executar."
    )


def build_agent_command(
    agent: str,
    prompt: str,
    workspace: Path,
    runtime_home: Path,
    model: str | None,
    *,
    containerized: bool = False,
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
        executable = "codex" if containerized else shutil.which("codex")
        if executable is None:
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
            "danger-full-access" if containerized else "workspace-write",
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

    executable = "cursor-agent" if containerized else (shutil.which("cursor-agent") or shutil.which("agent"))
    if executable is None:
        raise RuntimeError("cursor-agent CLI is not available")
    command = [
        executable,
        "--print",
        "--force",
        "--output-format",
        "stream-json",
        "--trust",
    ]
    if not containerized:
        command.extend(["--sandbox", "enabled", "--workspace", str(workspace)])
    if model:
        command.extend(["--model", model])
    command.append(prompt)
    environment = sanitized_environment(isolated_paths)
    environment.pop("OPENAI_API_KEY", None)
    return command, environment


def build_container_command(
    image: str,
    inner_command: list[str],
    workspace: Path,
    runtime_home: Path,
    environment: dict[str, str],
) -> tuple[list[str], dict[str, str]]:
    """Wrap an agent command in a container that can only see its fixture and home."""
    docker = shutil.which("docker")
    if docker is None:
        raise RuntimeError("docker is required for isolated agent evals")

    workspace = workspace.resolve()
    runtime_home = runtime_home.resolve()
    container_home = runtime_home / "container-home"
    container_home.mkdir(parents=True, exist_ok=True)
    (container_home / ".codex").mkdir(exist_ok=True)
    (container_home / ".cache").mkdir(exist_ok=True)
    (container_home / "python-site").mkdir(exist_ok=True)
    uid = os.getuid() if hasattr(os, "getuid") else None
    gid = os.getgid() if hasattr(os, "getgid") else None

    command = [
        docker,
        "run",
        "--rm",
        "--interactive",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--pids-limit=512",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,size=1g",
        "--mount",
        f"type=bind,source={workspace},target=/workspace",
        "--mount",
        f"type=bind,source={container_home},target=/home/eval",
        "--workdir",
        "/workspace",
        "--env",
        "HOME=/home/eval",
        "--env",
        "CODEX_HOME=/home/eval/.codex",
        "--env",
        "PLAYWRIGHT_BROWSERS_PATH=/ms-playwright",
        "--env",
        "PYTHONPATH=/home/eval/python-site",
    ]
    if uid is not None and gid is not None:
        command.extend(["--user", f"{uid}:{gid}"])
    for name in ("CI", "CURSOR_API_KEY", "LANG", "LC_ALL", "OPENAI_API_KEY"):
        if environment.get(name):
            command.extend(["--env", name])
    command.extend([image, *inner_command])
    return command, environment


def prepare_container_workspace(
    image: str,
    workspace: Path,
    runtime_home: Path,
    environment: dict[str, str],
) -> None:
    requirements = workspace / "requirements.lock"
    if not requirements.is_file():
        return
    command, container_environment = build_container_command(
        image,
        [
            "python",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-deps",
            "--require-hashes",
            "--target",
            "/home/eval/python-site",
            "-r",
            "/workspace/requirements.lock",
        ],
        workspace,
        runtime_home,
        environment,
    )
    preparation = run_command(command, workspace, env=container_environment, timeout=900)
    if not preparation.passed:
        raise RuntimeError(f"unable to prepare isolated Python workspace: {preparation.stderr}")


def grade_workspace(
    case: dict[str, Any],
    workspace: Path,
    production_before: dict[str, str],
    manifests_before: dict[str, str],
    artifacts: Path,
    test_environment: dict[str, str] | None = None,
) -> dict[str, Any]:
    production_unchanged = production_before == hash_paths(
        workspace,
        case["production_paths"],
        ignore_test_artifacts=True,
    )
    manifests_unchanged = manifests_before == manifest_hashes(workspace)

    correct = run_command(case["test_command"], workspace, env=test_environment, timeout=600)
    write_command_log(artifacts / "correct-tests.json", correct)
    if correct.passed and case.get("extended_test_command"):
        extended = run_command(
            case["extended_test_command"],
            workspace,
            env=test_environment,
            timeout=900,
        )
        write_command_log(artifacts / "extended-tests.json", extended)
        if not extended.passed:
            correct = extended

    mutation_results = []
    if correct.passed:
        for mutation in case["mutations"]:
            original = apply_mutation(workspace, mutation)
            try:
                result = run_command(
                    case["test_command"],
                    workspace,
                    env=test_environment,
                    timeout=600,
                )
            finally:
                restore_mutation(workspace, mutation, original)
            write_command_log(artifacts / f"mutation-{mutation['id']}.json", result)
            mutation_results.append({"id": mutation["id"], "killed": not result.passed})
    else:
        mutation_results = [{"id": mutation["id"], "killed": False} for mutation in case["mutations"]]

    mutation_score = sum(item["killed"] for item in mutation_results) / len(mutation_results)
    production_unchanged = production_unchanged and production_before == hash_paths(
        workspace,
        case["production_paths"],
        ignore_test_artifacts=True,
    )
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

    covered_risks = covered_risk_ids(case, evidence_text)
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
    agent_container_image: str | None,
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

        prompt = build_eval_prompt(case, agent, mode)
        command, environment = build_agent_command(
            agent,
            prompt,
            workspace,
            runtime_home,
            model,
            containerized=bool(agent_container_image),
        )
        if agent_container_image:
            version_command, version_environment = build_container_command(
                agent_container_image,
                [command[0], "--version"],
                workspace,
                runtime_home,
                environment,
            )
        else:
            version_command, version_environment = [command[0], "--version"], environment
        version_result = run_command(
            version_command,
            workspace,
            env=version_environment,
            timeout=30,
        )
        agent_version = (version_result.stdout or version_result.stderr).strip() or "unknown"
        if not dry_run and not version_result.passed:
            raise RuntimeError(f"unable to execute {agent} CLI: {agent_version}")
        agent_command = command
        agent_environment = environment
        if agent_container_image:
            agent_command, agent_environment = build_container_command(
                agent_container_image,
                command,
                workspace,
                runtime_home,
                environment,
            )
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
                "command": agent_command,
            }
            (artifacts / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
            return result

        required_secret = "OPENAI_API_KEY" if agent == "codex" else "CURSOR_API_KEY"
        if not environment.get(required_secret):
            raise RuntimeError(f"{required_secret} is required for {agent} evals")

        if agent == "codex":
            authentication_command = [command[0], "login", "--with-api-key"]
            authentication_environment = environment
            if agent_container_image:
                authentication_command, authentication_environment = build_container_command(
                    agent_container_image,
                    authentication_command,
                    workspace,
                    runtime_home,
                    environment,
                )
            authentication = run_command(
                authentication_command,
                workspace,
                env=authentication_environment,
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

        if agent_container_image:
            prepare_container_workspace(
                agent_container_image,
                workspace,
                runtime_home,
                environment,
            )

        production_before = hash_paths(
            workspace,
            case["production_paths"],
            ignore_test_artifacts=True,
        )
        manifests_before = manifest_hashes(workspace)
        started = time.monotonic()
        agent_result = run_command(
            agent_command,
            workspace,
            env=agent_environment,
            timeout=1800,
        )
        duration_seconds = round(time.monotonic() - started, 2)
        write_command_log(artifacts / "agent.json", agent_result)

        test_environment = build_test_environment(environment)
        grade = grade_workspace(
            case,
            workspace,
            production_before,
            manifests_before,
            artifacts,
            test_environment,
        )
        grade["critical_pass"] = grade["critical_pass"] and agent_result.passed
        copy_artifact_paths(
            workspace,
            artifacts,
            case.get("artifact_paths", ["tests", "test-evidence.json"]),
        )
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


def aggregate(
    results: list[dict[str, Any]],
    *,
    repetitions: int,
    repetition_start: int = 1,
    expected_agents: list[str] | None = None,
    expected_cases: list[str] | None = None,
) -> dict[str, Any]:
    if any(result.get("dry_run") for result in results):
        return {"dry_run": True, "passed": True, "results": results}

    expected_agents = sorted(set(expected_agents or (result["agent"] for result in results)))
    expected_cases = sorted(set(expected_cases or (result["case"] for result in results)))
    expected_repetitions = set(range(repetition_start, repetition_start + repetitions))
    expected_modes = {"baseline", "skill"}
    matrix_errors: list[str] = []

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for result in results:
        grouped.setdefault((result["agent"], result["case"], result["mode"]), []).append(result)

    result_agents = {result["agent"] for result in results}
    result_cases = {result["case"] for result in results}
    result_modes = {result["mode"] for result in results}
    unexpected_agents = sorted(result_agents - set(expected_agents))
    unexpected_cases = sorted(result_cases - set(expected_cases))
    if unexpected_agents:
        matrix_errors.append(f"unexpected agents: {', '.join(unexpected_agents)}")
    if unexpected_cases:
        matrix_errors.append(f"unexpected cases: {', '.join(unexpected_cases)}")
    unexpected_modes = sorted(result_modes - expected_modes)
    if unexpected_modes:
        matrix_errors.append(f"unexpected modes: {', '.join(unexpected_modes)}")

    run_ids = [result["run_id"] for result in results]
    duplicate_run_ids = sorted({run_id for run_id in run_ids if run_ids.count(run_id) > 1})
    if duplicate_run_ids:
        matrix_errors.append(f"duplicate run IDs: {', '.join(duplicate_run_ids)}")

    for agent in expected_agents:
        for case in expected_cases:
            for mode in sorted(expected_modes):
                runs = grouped.get((agent, case, mode), [])
                repetitions_found = [run["repetition"] for run in runs]
                if len(runs) != repetitions or set(repetitions_found) != expected_repetitions:
                    matrix_errors.append(
                        f"incomplete matrix for {agent}/{case}/{mode}: "
                        f"expected repetitions {sorted(expected_repetitions)}, found {sorted(repetitions_found)}"
                    )

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
    required_passes = 2 if repetitions >= 3 else repetitions
    summary_index = {
        (item["agent"], item["case"], item["mode"]): item
        for item in summaries
    }
    for agent in expected_agents:
        for case in expected_cases:
            baseline = summary_index.get((agent, case, "baseline"))
            treatment = summary_index.get((agent, case, "skill"))
            if baseline is None or treatment is None:
                continue
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
    required_improved_cases = min(2, len(expected_cases))
    passed = (
        not matrix_errors
        and not execution_failures
        and bool(skill_scores)
        and statistics.median(skill_scores) >= 85
        and statistics.median(gains) >= 8
        and all(
            sum(item["gain"] > 0 for item in comparisons if item["agent"] == agent)
            >= required_improved_cases
            for agent in expected_agents
        )
        and all(gain >= -5 for gain in gains)
        and all(item["critical_gate"] for item in comparisons)
    )
    return {
        "dry_run": False,
        "passed": passed,
        "matrix_errors": matrix_errors,
        "execution_failures": execution_failures,
        "median_skill_score": statistics.median(skill_scores) if skill_scores else None,
        "median_gain": statistics.median(gains) if gains else None,
        "required_improved_cases": required_improved_cases,
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
    parser.add_argument(
        "--repetition-start",
        type=int,
        default=1,
        help="Label the first repetition, allowing a certification to continue without rerunning earlier samples",
    )
    parser.add_argument("--model")
    parser.add_argument(
        "--agent-container-image",
        help="Run the agent in this prebuilt container image with only the fixture mounted",
    )
    parser.add_argument("--artifacts", type=Path, default=EVAL_ROOT / "artifacts")
    parser.add_argument(
        "--baseline-cache",
        type=Path,
        help="Reuse valid baseline artifacts and save new baselines under this directory",
    )
    parser.add_argument(
        "--max-agent-calls",
        type=int,
        help="Required paid-call ceiling. The run is rejected before an agent starts if it would exceed this value",
    )
    parser.add_argument(
        "--print-baseline-fingerprint",
        action="store_true",
        help="Print the cache fingerprint for exactly one agent and case, then exit",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--enforce-gate", action="store_true")
    return parser


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args()
    if args.repetitions < 1:
        raise SystemExit("--repetitions must be at least 1")
    if args.repetition_start < 1:
        raise SystemExit("--repetition-start must be at least 1")
    if args.max_agent_calls is not None and args.max_agent_calls < 0:
        raise SystemExit("--max-agent-calls cannot be negative")
    if not args.dry_run and not args.model:
        raise SystemExit("--model is required for comparable eval runs")
    cases = select_cases(args.cases)
    if args.print_baseline_fingerprint:
        if not args.model:
            raise SystemExit("--model is required to calculate a baseline fingerprint")
        if len(args.agent) != 1 or len(cases) != 1:
            raise SystemExit("--print-baseline-fingerprint requires exactly one agent and one case")
        print(baseline_fingerprint(cases[0], args.agent[0], args.model))
        return 0

    cached: dict[tuple[str, str, int], tuple[dict[str, Any], Path]] = {}
    if args.baseline_cache and not args.dry_run:
        for agent in args.agent:
            for case in cases:
                fingerprint = baseline_fingerprint(case, agent, args.model)
                for repetition in range(
                    args.repetition_start,
                    args.repetition_start + args.repetitions,
                ):
                    hit = read_cached_baseline(
                        args.baseline_cache,
                        fingerprint,
                        agent,
                        case["id"],
                        repetition,
                        args.model,
                    )
                    if hit:
                        cached[(agent, case["id"], repetition)] = hit

    call_count = planned_agent_calls(
        len(args.agent),
        len(cases),
        args.repetitions,
        cached_baselines=len(cached),
    )
    if not args.dry_run:
        if args.max_agent_calls is None:
            raise SystemExit("--max-agent-calls is required for paid evals")
        if call_count > args.max_agent_calls:
            raise SystemExit(
                f"planned paid calls ({call_count}) exceed --max-agent-calls ({args.max_agent_calls})"
            )
    print(f"Paid agent calls planned: {call_count}; cached baselines: {len(cached)}")

    results = []
    for agent in args.agent:
        for case in cases:
            fingerprint = baseline_fingerprint(case, agent, args.model or "agent-default")
            for repetition in range(
                args.repetition_start,
                args.repetition_start + args.repetitions,
            ):
                for mode in ("baseline", "skill"):
                    cache_key = (agent, case["id"], repetition)
                    if mode == "baseline" and cache_key in cached:
                        results.append(restore_cached_baseline(cached[cache_key], args.artifacts))
                        continue
                    result = run_once(
                        case,
                        agent,
                        mode,
                        repetition,
                        args.model,
                        args.artifacts,
                        args.dry_run,
                        args.agent_container_image,
                    )
                    results.append(result)
                    if mode == "baseline" and args.baseline_cache:
                        cache_baseline(result, args.artifacts, args.baseline_cache, fingerprint)
    report = aggregate(
        results,
        repetitions=args.repetitions,
        repetition_start=args.repetition_start,
        expected_agents=args.agent,
        expected_cases=[case["id"] for case in cases],
    )
    args.artifacts.mkdir(parents=True, exist_ok=True)
    (args.artifacts / "summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return evaluation_exit_code(report, enforce_gate=args.enforce_gate)


if __name__ == "__main__":
    raise SystemExit(main())
