#!/usr/bin/env python3
"""Extract lifecycle and asynchronous risk signals from one test target."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


STATE_PATTERN = re.compile(r"\bstate\s*(?::|===?|!==?)\s*[\"']([A-Za-z0-9_-]+)[\"']")
ACTION_PATTERN = re.compile(
    r"\b(?:function\s+|const\s+)?(reset|cancel|abort|retry|disconnect|unmount|timeout)\b",
    re.IGNORECASE,
)
ASYNC_PATTERN = re.compile(r"\b(async|await)\b")
IF_PATTERN = re.compile(r"\bif\s*\((.+)\)\s*\{")
PROTECTION_PATTERN = re.compile(
    r"\b(id|token|generation|version|abort|cancel|stale|current|lock|retry)\w*\b",
    re.IGNORECASE,
)


def analyze(root: Path, relative_file: Path) -> dict[str, object]:
    root = root.resolve()
    target = (root / relative_file).resolve()
    try:
        target.relative_to(root)
    except ValueError as error:
        raise ValueError("target file must stay inside root") from error
    if not target.is_file():
        raise ValueError(f"target file does not exist: {relative_file.as_posix()}")

    text = target.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    states = sorted(set(STATE_PATTERN.findall(text)))
    actions: dict[str, list[int]] = defaultdict(list)
    async_lines: list[int] = []
    guards: dict[str, list[int]] = defaultdict(list)

    for number, line in enumerate(lines, start=1):
        for action in ACTION_PATTERN.findall(line):
            actions[action.lower()].append(number)
        if ASYNC_PATTERN.search(line):
            async_lines.append(number)
        condition = IF_PATTERN.search(line)
        if condition and PROTECTION_PATTERN.search(condition.group(1)):
            normalized = re.sub(r"\s+", " ", condition.group(1).strip())
            guards[normalized].append(number)

    return {
        "file": relative_file.as_posix(),
        "states": states,
        "lifecycle_actions": [
            {"action": action, "lines": numbers}
            for action, numbers in sorted(actions.items())
        ],
        "async_boundary_lines": async_lines,
        "protective_guards": [
            {
                "condition": condition,
                "lines": numbers,
                "occurrences": len(numbers),
            }
            for condition, numbers in sorted(guards.items())
        ],
        "notes": [
            "Signals are candidates; confirm their behavior in source before designing tests.",
            "Repeated guards can protect different lifecycle phases and require separate scenarios.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = analyze(args.root, args.file)
    except ValueError as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
