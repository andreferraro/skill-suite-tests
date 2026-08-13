#!/usr/bin/env python3
"""Prove that a test command detects one temporary, exactly matched local mutation."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def prove(
    root: Path,
    relative_file: str,
    search: str,
    replace: str,
    command: list[str],
    timeout: int,
    occurrence: int | None = None,
) -> tuple[int, dict[str, object]]:
    root = root.resolve()
    target = (root / relative_file).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return 2, {"proved": False, "error": "mutation target is outside project root"}
    if not target.is_file():
        return 2, {"proved": False, "error": "mutation target is not a file"}
    if not search or search == replace:
        return 2, {"proved": False, "error": "mutation must replace non-empty text with a different value"}
    if not command:
        return 2, {"proved": False, "error": "test command is required after --"}

    original = target.read_bytes()
    original_hash = hashlib.sha256(original).hexdigest()
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError:
        return 2, {"proved": False, "error": "mutation target must be UTF-8 text"}
    match_count = text.count(search)
    if occurrence is None and match_count != 1:
        return 2, {
            "proved": False,
            "error": "mutation search must match exactly once or --occurrence must be provided",
        }
    if occurrence is not None and (occurrence < 1 or occurrence > match_count):
        return 2, {
            "proved": False,
            "error": f"mutation occurrence must be between 1 and {match_count}",
        }

    if occurrence is None:
        mutated_text = text.replace(search, replace)
    else:
        parts = text.split(search)
        index = occurrence - 1
        mutated_text = search.join(parts[: index + 1]) + replace + search.join(parts[index + 1 :])

    result: dict[str, object] = {"proved": False}
    exit_code = 2
    try:
        try:
            target.write_text(mutated_text, encoding="utf-8", newline="")
        except OSError as error:
            result = {"proved": False, "error": f"unable to apply mutation: {error}"}
        else:
            try:
                process = subprocess.run(
                    command,
                    cwd=root,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                result = {"proved": False, "error": f"test command timed out after {timeout} seconds"}
            except OSError as error:
                result = {"proved": False, "error": f"unable to execute test command: {error}"}
            else:
                proved = process.returncode != 0
                exit_code = 0 if proved else 1
                result = {
                    "proved": proved,
                    "command": command,
                    "mutated_exit_code": process.returncode,
                    "stdout_tail": process.stdout[-4000:],
                    "stderr_tail": process.stderr[-4000:],
                }
    finally:
        try:
            target.write_bytes(original)
        except OSError as error:
            result = {"proved": False, "error": f"unable to restore mutation target: {error}"}
            exit_code = 2

    try:
        restored = hashlib.sha256(target.read_bytes()).hexdigest() == original_hash
    except OSError:
        restored = False
    result["restored"] = restored
    if not restored:
        result["proved"] = False
        result["error"] = "mutation target was not restored exactly"
        exit_code = 2
    return exit_code, result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--file", required=True, dest="relative_file")
    parser.add_argument("--search", required=True)
    parser.add_argument("--replace", required=True)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--occurrence", type=int)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    exit_code, result = prove(
        args.root,
        args.relative_file,
        args.search,
        args.replace,
        command,
        args.timeout,
        args.occurrence,
    )
    # Keep CLI output encodable on Windows consoles configured with cp1252.
    # Captured test runners commonly emit symbols such as ✓ and ❯.
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
