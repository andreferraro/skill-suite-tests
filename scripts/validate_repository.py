#!/usr/bin/env python3
"""Validate the skill package, local links, schemas, and obvious secret leaks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_PATTERN = re.compile(r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)$")
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SECRET_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("OpenAI API key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("GitHub token", re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b")),
    (
        "assigned API secret",
        re.compile(
            r"(?m)^\s*(?:export\s+|\$env:)?[A-Z][A-Z0-9_]*(?:API_KEY|TOKEN|SECRET)\s*[:=]\s*[\"']?([^\s\"']+)"
        ),
    ),
)
PLACEHOLDERS = {
    "<redacted>",
    "changeme",
    "example",
    "placeholder",
    "secret",
    "your_api_key",
    "your_api_key_here",
}
IGNORED_PARTS = {".git", ".venv", "node_modules", "artifacts", "workspaces"}


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return {}, [f"unable to read {path}: {error}"]
    if not lines or lines[0] != "---":
        return {}, ["SKILL.md must start with YAML frontmatter"]
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}, ["SKILL.md frontmatter is not closed"]

    values: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            errors.append(f"invalid frontmatter line: {line}")
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"\'')
    return values, errors


def validate_skill(root: Path) -> list[str]:
    errors: list[str] = []
    frontmatter, parse_errors = parse_frontmatter(root / "SKILL.md")
    errors.extend(parse_errors)
    unknown = sorted(set(frontmatter) - {"name", "description"})
    if unknown:
        errors.append(f"SKILL.md frontmatter has unsupported fields: {', '.join(unknown)}")
    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")
    if not NAME_PATTERN.fullmatch(name) or len(name) > 64:
        errors.append("SKILL.md name must be lowercase kebab-case with at most 64 characters")
    if not description or len(description) > 1024 or any(character in description for character in "<>"):
        errors.append("SKILL.md description must contain 1-1024 characters and no angle brackets")

    agent_path = root / "agents" / "openai.yaml"
    try:
        agent_text = agent_path.read_text(encoding="utf-8")
    except OSError as error:
        errors.append(f"unable to read agents/openai.yaml: {error}")
    else:
        for field in ("display_name:", "short_description:", "default_prompt:"):
            if field not in agent_text:
                errors.append(f"agents/openai.yaml is missing {field[:-1]}")
        if "$skill-suite-tests" not in agent_text:
            errors.append("agents/openai.yaml default_prompt must invoke $skill-suite-tests")
    return errors


def read_json(path: Path) -> tuple[dict, list[str]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {}, [f"unable to read {path}: {error}"]
    if not isinstance(value, dict):
        return {}, [f"{path} must contain a JSON object"]
    return value, []


def validate_plugin(root: Path) -> list[str]:
    errors: list[str] = []
    manifest, manifest_errors = read_json(root / ".codex-plugin" / "plugin.json")
    errors.extend(manifest_errors)
    if manifest_errors:
        return errors

    if manifest.get("name") != "skill-suite-tests":
        errors.append("plugin name must be skill-suite-tests")
    if not SEMVER_PATTERN.fullmatch(str(manifest.get("version", ""))):
        errors.append("plugin version must use strict semver")
    if manifest.get("skills") != "./skills/":
        errors.append("plugin skills path must be ./skills/")

    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("plugin interface must be an object")
    else:
        for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
            if not interface.get(field):
                errors.append(f"plugin interface is missing {field}")

    skill_root = root / "skills" / "skill-suite-tests"
    if not skill_root.is_dir():
        errors.append("plugin must contain skills/skill-suite-tests")

    marketplace, marketplace_errors = read_json(root / ".agents" / "plugins" / "marketplace.json")
    errors.extend(marketplace_errors)
    if marketplace_errors:
        return errors
    entries = marketplace.get("plugins")
    if not isinstance(entries, list) or len(entries) != 1:
        errors.append("marketplace must expose exactly one plugin")
        return errors
    entry = entries[0]
    if entry.get("name") != manifest.get("name"):
        errors.append("marketplace plugin name must match the manifest")
    source = entry.get("source", {})
    if source.get("source") != "url" or source.get("ref") != "main":
        errors.append("marketplace must install the repository root from main")
    repository = str(manifest.get("repository", "")).removesuffix(".git")
    if str(source.get("url", "")).removesuffix(".git") != repository:
        errors.append("marketplace URL must match the manifest repository")
    return errors


def validate_local_links(root: Path) -> list[str]:
    errors: list[str] = []
    for document in root.rglob("*.md"):
        if any(part in IGNORED_PARTS for part in document.relative_to(root).parts):
            continue
        text = document.read_text(encoding="utf-8", errors="replace")
        for raw_target in MARKDOWN_LINK.findall(text):
            target = raw_target.strip().strip("<>").split(maxsplit=1)[0]
            if target.startswith(("http://", "https://", "mailto:", "#", "plugin://")):
                continue
            path_text = unquote(target.split("#", 1)[0])
            if not path_text:
                continue
            resolved = (document.parent / path_text).resolve()
            if not resolved.exists():
                relative_document = document.relative_to(root).as_posix()
                errors.append(f"broken local link in {relative_document}: {target}")
    return errors


def validate_schemas(root: Path) -> list[str]:
    errors: list[str] = []
    for schema_path in (root / "schemas").glob("*.json"):
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"invalid JSON schema {schema_path.name}: {error}")
            continue
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append(f"{schema_path.name} must use JSON Schema draft 2020-12")
        if schema.get("type") != "object" or not schema.get("required"):
            errors.append(f"{schema_path.name} must define an object with required fields")
    return errors


def scan_secrets(root: Path) -> list[str]:
    errors: list[str] = []
    text_suffixes = {".json", ".md", ".py", ".toml", ".ts", ".tsx", ".yaml", ".yml"}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in text_suffixes:
            continue
        relative = path.relative_to(root)
        if any(part in {".git", ".venv", "node_modules", "artifacts", "workspaces"} for part in relative.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                if label == "assigned API secret":
                    value = match.group(1).strip().lower()
                    if value in PLACEHOLDERS or value.startswith("${{"):
                        continue
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"possible {label} in {relative.as_posix()}:{line}")
    return errors


def validate_repository(root: Path) -> list[str]:
    skill_root = root / "skills" / "skill-suite-tests"
    return [
        *validate_plugin(root),
        *validate_skill(skill_root),
        *validate_local_links(root),
        *validate_schemas(skill_root),
        *scan_secrets(root),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate_repository(args.root.resolve())
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
