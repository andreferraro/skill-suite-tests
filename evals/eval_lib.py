from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


EVAL_ROOT = Path(__file__).resolve().parent
REPO_ROOT = EVAL_ROOT.parent


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


def load_cases() -> list[dict[str, Any]]:
    document = json.loads((EVAL_ROOT / "cases.json").read_text(encoding="utf-8"))
    if document.get("schema_version") != "1.0" or not isinstance(document.get("cases"), list):
        raise ValueError("evals/cases.json has an unsupported schema")
    return document["cases"]


def select_cases(case_ids: Iterable[str] | None = None) -> list[dict[str, Any]]:
    cases = load_cases()
    selected = set(case_ids or [])
    if not selected:
        return cases
    known = {case["id"] for case in cases}
    unknown = selected - known
    if unknown:
        raise ValueError(f"unknown eval case(s): {', '.join(sorted(unknown))}")
    return [case for case in cases if case["id"] in selected]


def copy_workspace(case: dict[str, Any], destination: Path) -> None:
    source = EVAL_ROOT / case["workspace"]
    if destination.exists():
        raise FileExistsError(f"workspace already exists: {destination}")
    shutil.copytree(source, destination)


def copy_reference_tests(case: dict[str, Any], workspace: Path) -> None:
    source = EVAL_ROOT / case["reference_tests"]
    for file in source.iterdir():
        if file.is_file():
            destination = (
                workspace / "tests" / "e2e" / "reference"
                if file.name.endswith(".e2e.spec.ts")
                else workspace / "tests" / "reference"
            )
            destination.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, destination / file.name)


def copy_eval_contract(workspace: Path) -> None:
    destination = workspace / ".eval-contract"
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / "schemas" / "test-evidence.v1.json", destination / "test-evidence.v1.json")
    shutil.copy2(
        REPO_ROOT / "scripts" / "validate_test_evidence.py",
        destination / "validate_test_evidence.py",
    )


def run_command(
    command: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
    timeout: int = 300,
) -> CommandResult:
    resolved = shutil.which(command[0], path=(env or os.environ).get("PATH"))
    if resolved is None:
        return CommandResult(command, 127, "", f"executable not found: {command[0]}")
    executable_command = [resolved, *command[1:]]
    input_options: dict[str, Any]
    if input_text is None:
        input_options = {"stdin": subprocess.DEVNULL}
    else:
        input_options = {"input": input_text}
    try:
        process = subprocess.run(
            executable_command,
            cwd=cwd,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            check=False,
            **input_options,
        )
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode("utf-8", errors="replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode("utf-8", errors="replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
        return CommandResult(command, 124, stdout, stderr + f"\ncommand timed out after {timeout} seconds")
    except OSError as error:
        return CommandResult(command, 126, "", f"unable to start command: {error}")
    return CommandResult(command, process.returncode, process.stdout, process.stderr)


def apply_mutation(workspace: Path, mutation: dict[str, str]) -> str:
    path = workspace / mutation["file"]
    original = path.read_text(encoding="utf-8")
    occurrences = original.count(mutation["search"])
    if occurrences == 0:
        raise ValueError(f"mutation {mutation['id']} no longer matches {mutation['file']}")
    path.write_text(original.replace(mutation["search"], mutation["replace"]), encoding="utf-8")
    return original


def restore_mutation(workspace: Path, mutation: dict[str, str], original: str) -> None:
    (workspace / mutation["file"]).write_text(original, encoding="utf-8")


def hash_paths(workspace: Path, prefixes: list[str]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for prefix in prefixes:
        base = workspace / prefix
        if not base.exists():
            continue
        paths = [base] if base.is_file() else list(base.rglob("*"))
        for path in paths:
            if path.is_file():
                relative = path.relative_to(workspace).as_posix()
                hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def manifest_hashes(workspace: Path) -> dict[str, str]:
    candidates = (
        "package.json",
        "package-lock.json",
        "requirements.txt",
        "requirements.lock",
        "pyproject.toml",
        "poetry.lock",
        "uv.lock",
    )
    return hash_paths(workspace, [name for name in candidates if (workspace / name).exists()])


def skill_runtime_files() -> list[Path]:
    files = [
        REPO_ROOT / "SKILL.md",
        REPO_ROOT / "agents" / "openai.yaml",
        REPO_ROOT / "scripts" / "detect_test_context.py",
        REPO_ROOT / "scripts" / "validate_test_evidence.py",
    ]
    for directory in ("examples", "references", "schemas"):
        files.extend(path for path in (REPO_ROOT / directory).rglob("*") if path.is_file() and "__pycache__" not in path.parts)
    return files


def install_skill(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for source in skill_runtime_files():
        relative = source.relative_to(REPO_ROOT)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def sanitized_environment(extra: dict[str, str] | None = None) -> dict[str, str]:
    allowed_names = {
        "APPDATA",
        "CI",
        "COMSPEC",
        "CURSOR_API_KEY",
        "DOCKER_CONFIG",
        "GITHUB_ACTIONS",
        "HOME",
        "HOMEDRIVE",
        "HOMEPATH",
        "LANG",
        "LC_ALL",
        "LOCALAPPDATA",
        "NODE_EXTRA_CA_CERTS",
        "NUMBER_OF_PROCESSORS",
        "OPENAI_API_KEY",
        "OS",
        "PATH",
        "PATHEXT",
        "PLAYWRIGHT_BROWSERS_PATH",
        "PROCESSOR_ARCHITECTURE",
        "PROGRAMDATA",
        "PYTHONUTF8",
        "SHELL",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "TMPDIR",
        "USER",
        "USERPROFILE",
        "WINDIR",
    }
    environment = {name: value for name, value in os.environ.items() if name.upper() in allowed_names}
    if extra:
        environment.update(extra)
    return environment


def write_command_log(path: Path, result: CommandResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "command": result.command,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
