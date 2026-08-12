#!/usr/bin/env python3
"""Detect test-related project context without selecting or installing tools."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable


IGNORED_DIRS = {
    ".git",
    ".agents",
    ".agent-site",
    ".claude",
    ".codex",
    ".cursor",
    ".eval-contract",
    ".idea",
    ".next",
    ".pytest_cache",
    ".venv",
    ".vscode",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "venv",
}

MANIFEST_NAMES = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "poetry.lock",
    "uv.lock",
    "Pipfile",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Gemfile",
    "composer.json",
}

TEST_PATTERNS = (
    re.compile(r"(^|/)(tests?|specs?|__tests__)/", re.IGNORECASE),
    re.compile(r"(^|/)(test_|spec_).+\.(py|rb|php)$", re.IGNORECASE),
    re.compile(r"\.(test|spec)\.(js|jsx|ts|tsx|mjs|cjs)$", re.IGNORECASE),
    re.compile(r"(Test|Tests)\.(java|kt|cs)$"),
    re.compile(r"_test\.go$", re.IGNORECASE),
)

RISK_SIGNAL_PATTERNS = {
    "accessibility-semantics": (
        re.compile(r"\baria-[a-z-]+\b", re.IGNORECASE),
        re.compile(r"\brole\s*=", re.IGNORECASE),
        re.compile(r"\bhtmlfor\s*=", re.IGNORECASE),
    ),
    "concurrency-control": (
        re.compile(r"\bbegin\s+immediate\b", re.IGNORECASE),
        re.compile(r"\bfor\s+update\b", re.IGNORECASE),
        re.compile(r"\b(mutex|semaphore|lock)\b", re.IGNORECASE),
    ),
    "dead-letter-control": (
        re.compile(r"\bdlq\b", re.IGNORECASE),
        re.compile(r"dead[-_ ]?letter", re.IGNORECASE),
    ),
    "deduplication-control": (
        re.compile(r"\bdedup", re.IGNORECASE),
        re.compile(r"hasprocessed", re.IGNORECASE),
        re.compile(r"\bduplicate\b", re.IGNORECASE),
    ),
    "idempotency-control": (re.compile(r"\bidempoten", re.IGNORECASE),),
    "non-positive-validation": (
        re.compile(r"\b(amount|value|quantity|total)\s*<=\s*0\b", re.IGNORECASE),
        re.compile(r"\bgt\s*=\s*0\b", re.IGNORECASE),
    ),
    "ordering-correlation-control": (
        re.compile(r"\b(sequence|ordering)\b", re.IGNORECASE),
        re.compile(r"\bcorrelation(id|_id)?\b", re.IGNORECASE),
    ),
    "retry-control": (
        re.compile(r"\bretry\b", re.IGNORECASE),
        re.compile(r"\battempt\s*\+\s*1\b", re.IGNORECASE),
        re.compile(r"maxattempt", re.IGNORECASE),
    ),
    "stale-async-guard": (
        re.compile(r"latestrequest", re.IGNORECASE),
        re.compile(r"requestid\s*!==?", re.IGNORECASE),
        re.compile(r"abortcontroller", re.IGNORECASE),
    ),
    "transaction-rollback": (re.compile(r"\brollback\b", re.IGNORECASE),),
}


def iter_project_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if any(part in IGNORED_DIRS for part in relative_parts):
            continue
        yield path


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read_text(path: Path) -> str:
    try:
        if path.stat().st_size > 1_000_000:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def detect_risk_signals(relative_files: dict[str, Path]) -> dict[str, list[str]]:
    source_files = {
        name: path
        for name, path in relative_files.items()
        if name.endswith((".cs", ".go", ".java", ".js", ".jsx", ".kt", ".py", ".rb", ".ts", ".tsx"))
        and not any(pattern.search(name) for pattern in TEST_PATTERNS)
    }
    source_contents = {name: read_text(path) for name, path in source_files.items()}
    signals: dict[str, list[str]] = {}
    for signal, patterns in RISK_SIGNAL_PATTERNS.items():
        if signal == "ordering-correlation-control":
            matching_files = sorted(
                name
                for name, content in source_contents.items()
                if all(pattern.search(content) for pattern in patterns)
            )
        else:
            matching_files = sorted(
                name
                for name, content in source_contents.items()
                if any(pattern.search(content) for pattern in patterns)
            )
        if matching_files:
            signals[signal] = matching_files
    return signals


def package_dependencies(package_files: list[Path]) -> set[str]:
    dependencies: set[str] = set()
    for package_file in package_files:
        try:
            document = json.loads(package_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            values = document.get(section, {})
            if isinstance(values, dict):
                dependencies.update(str(name).lower() for name in values)
    return dependencies


def detect(root: Path) -> dict[str, object]:
    files = list(iter_project_files(root))
    relative_files = {relative(path, root): path for path in files}
    manifests = sorted(
        name
        for name in relative_files
        if Path(name).name in MANIFEST_NAMES
        or name.endswith((".csproj", ".sln", ".fsproj"))
    )
    package_files = [path for name, path in relative_files.items() if Path(name).name == "package.json"]
    dependencies = package_dependencies(package_files)

    searchable_files = [
        path
        for name, path in relative_files.items()
        if Path(name).name in MANIFEST_NAMES
        or name.endswith((".csproj", ".fsproj", ".config.js", ".config.ts", ".yaml", ".yml"))
    ]
    searchable_text = "\n".join(read_text(path).lower() for path in searchable_files)
    dependency_text = " ".join(sorted(dependencies)) + "\n" + searchable_text
    source_text = "\n".join(
        read_text(path).lower()
        for name, path in relative_files.items()
        if name.endswith((".cs", ".go", ".java", ".js", ".jsx", ".kt", ".py", ".rb", ".ts", ".tsx"))
    )

    technologies: set[str] = set()
    if package_files:
        technologies.add("nodejs")
    if "typescript" in dependencies or any(name.endswith((".ts", ".tsx")) for name in relative_files):
        technologies.add("typescript")
    if "react" in dependencies:
        technologies.add("react")
    if any(Path(name).name in {"pyproject.toml", "requirements.txt", "requirements-dev.txt", "Pipfile"} for name in relative_files):
        technologies.add("python")
    if "fastapi" in dependency_text:
        technologies.add("fastapi")
    if "go.mod" in {Path(name).name for name in relative_files}:
        technologies.add("go")
    if any(Path(name).name in {"pom.xml", "build.gradle", "build.gradle.kts"} for name in relative_files):
        technologies.add("jvm")
    if any(name.endswith((".csproj", ".sln")) for name in relative_files):
        technologies.add("dotnet")

    tool_signals = {
        "vitest": ("vitest",),
        "jest": ("jest",),
        "testing-library": ("@testing-library/",),
        "playwright": ("@playwright/test", "playwright.config"),
        "cypress": ("cypress",),
        "pytest": ("pytest", "pytest.ini"),
        "unittest": ("unittest",),
        "testcontainers": ("testcontainers", "testcontainers-"),
        "pact": ("pact",),
        "k6": ("k6",),
        "junit": ("junit",),
        "xunit": ("xunit",),
    }
    test_tools = []
    for tool, signals in tool_signals.items():
        dependency_match = (
            tool == "jest" and ("jest" in dependencies or any(name.startswith("@jest/") for name in dependencies))
        ) or (
            tool != "jest" and any(signal in dependency_text for signal in signals)
        )
        file_match = any(signal in name.lower() for signal in signals for name in relative_files)
        if dependency_match or file_match:
            test_tools.append(tool)
    test_tools.sort()

    database_patterns = {
        "postgresql": (r"postgres", r"psycopg", r"(^|[^a-z0-9])pg([^a-z0-9]|$)"),
        "mysql": (r"mysql", r"mariadb"),
        "sqlite": (r"sqlite",),
        "mongodb": (r"mongodb", r"mongoose"),
        "redis": (r"redis",),
    }
    databases = sorted(
        database
        for database, patterns in database_patterns.items()
        if any(re.search(pattern, dependency_text + "\n" + source_text) for pattern in patterns)
    )

    broker_signals = {
        "rabbitmq": ("amqplib", "rabbitmq"),
        "kafka": ("kafkajs", "kafka"),
        "nats": ("nats",),
        "sqs": ("@aws-sdk/client-sqs", "boto3"),
    }
    brokers = sorted(
        broker
        for broker, signals in broker_signals.items()
        if any(signal in dependency_text + "\n" + source_text for signal in signals)
    )

    test_files = sorted(
        name for name in relative_files if any(pattern.search(name) for pattern in TEST_PATTERNS)
    )
    fixture_dirs = sorted(
        {
            "/".join(Path(name).parts[: index + 1])
            for name in relative_files
            for index, part in enumerate(Path(name).parts)
            if part.lower() in {"fixture", "fixtures", "factory", "factories", "testdata", "test-data"}
        }
    )
    ci_files = sorted(
        name
        for name in relative_files
        if name.startswith(".github/workflows/")
        or Path(name).name in {".gitlab-ci.yml", "azure-pipelines.yml", "Jenkinsfile", "buildkite.yml"}
    )
    infrastructure_files = sorted(
        name
        for name in relative_files
        if Path(name).name.lower().startswith("dockerfile")
        or Path(name).name.lower() in {"compose.yml", "compose.yaml", "docker-compose.yml", "docker-compose.yaml"}
        or (Path(name).name in MANIFEST_NAMES and "testcontainers" in read_text(relative_files[name]).lower())
    )

    profiles: list[str] = []
    if {"react", "typescript"}.issubset(technologies):
        profiles.append("react-typescript-frontend")
    if {"fastapi", "python"}.issubset(technologies):
        profiles.append("fastapi-python-api")
    if {"nodejs", "typescript"}.issubset(technologies) and brokers:
        profiles.append("node-typescript-events")

    return {
        "root": str(root.resolve()),
        "support_status": "validated" if profiles else "adaptable",
        "validated_profiles": sorted(profiles),
        "technologies": sorted(technologies),
        "manifests": manifests,
        "test_tools": test_tools,
        "test_files": test_files,
        "fixture_directories": fixture_dirs,
        "ci_files": ci_files,
        "databases": databases,
        "brokers": brokers,
        "browser_automation": [tool for tool in test_tools if tool in {"playwright", "cypress"}],
        "infrastructure_files": infrastructure_files,
        "risk_signals": detect_risk_signals(relative_files),
        "notes": [
            "Detection reports project evidence and candidate risk signals only; it does not recommend or install tools.",
            "Confirm signals against source code before making test-design decisions.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project root to inspect")
    parser.add_argument("--json", action="store_true", help="Emit formatted JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.root.expanduser()
    if not root.is_dir():
        print(f"error: project root does not exist or is not a directory: {root}", file=sys.stderr)
        return 2
    result = detect(root)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"support_status: {result['support_status']}")
        print(f"technologies: {', '.join(result['technologies']) or 'none detected'}")
        print(f"test_tools: {', '.join(result['test_tools']) or 'none detected'}")
        print(f"test_files: {len(result['test_files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
