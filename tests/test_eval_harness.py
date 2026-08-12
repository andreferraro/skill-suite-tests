from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))

from eval_lib import apply_mutation, install_skill, restore_mutation, run_command, sanitized_environment  # noqa: E402
from run_eval import aggregate  # noqa: E402


def result(agent: str, case: str, mode: str, score: float, critical: bool = True) -> dict:
    return {
        "agent": agent,
        "case": case,
        "mode": mode,
        "repetition": 1,
        "score": score,
        "critical_pass": critical,
    }


class MutationTests(unittest.TestCase):
    def test_apply_and_restore_exact_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            path = workspace / "module.py"
            path.write_text("enabled = True\n", encoding="utf-8")
            mutation = {"id": "disable", "file": "module.py", "search": "True", "replace": "False"}

            original = apply_mutation(workspace, mutation)
            self.assertEqual(path.read_text(encoding="utf-8"), "enabled = False\n")
            restore_mutation(workspace, mutation, original)
            self.assertEqual(path.read_text(encoding="utf-8"), "enabled = True\n")

    def test_missing_mutation_target_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "module.py").write_text("enabled = True\n", encoding="utf-8")
            mutation = {"id": "missing", "file": "module.py", "search": "absent", "replace": "value"}
            with self.assertRaises(ValueError):
                apply_mutation(workspace, mutation)


class CommandTests(unittest.TestCase):
    def test_run_command_resolves_executable_cross_platform(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            command = run_command([sys.executable, "-c", "print('ok')"], Path(directory))
        self.assertTrue(command.passed)
        self.assertEqual(command.stdout.strip(), "ok")

    def test_agent_environment_uses_allowlist(self) -> None:
        with mock.patch.dict(
            "os.environ",
            {"PATH": "runtime-path", "OPENAI_API_KEY": "agent-key", "DATABASE_URL": "production"},
            clear=True,
        ):
            environment = sanitized_environment()
        self.assertEqual(environment["PATH"], "runtime-path")
        self.assertEqual(environment["OPENAI_API_KEY"], "agent-key")
        self.assertNotIn("DATABASE_URL", environment)


class AggregateTests(unittest.TestCase):
    def test_release_gate_passes_with_required_gain(self) -> None:
        results = []
        for agent in ("codex", "cursor"):
            for case in ("web", "api", "events"):
                for repetition in range(1, 4):
                    baseline = result(agent, case, "baseline", 80)
                    skill = result(agent, case, "skill", 90)
                    baseline["repetition"] = repetition
                    skill["repetition"] = repetition
                    results.extend((baseline, skill))
        report = aggregate(results, repetitions=3)
        self.assertTrue(report["passed"])

    def test_release_gate_rejects_redundant_skill(self) -> None:
        results = []
        for case in ("web", "api", "events"):
            results.extend((result("codex", case, "baseline", 90), result("codex", case, "skill", 90)))
        report = aggregate(results, repetitions=1)
        self.assertFalse(report["passed"])

    def test_release_gate_requires_two_improvements_per_agent(self) -> None:
        results = []
        for case in ("web", "api", "events"):
            results.extend((result("codex", case, "baseline", 80), result("codex", case, "skill", 90)))
        for case, skill_score in (("web", 90), ("api", 80), ("events", 80)):
            results.extend((result("cursor", case, "baseline", 80), result("cursor", case, "skill", skill_score)))

        report = aggregate(results, repetitions=1)

        self.assertFalse(report["passed"])


class SkillPackagingTests(unittest.TestCase):
    def test_runtime_package_excludes_graders_and_docs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "skill-suite-tests"
            install_skill(destination)
            self.assertTrue((destination / "SKILL.md").is_file())
            self.assertTrue((destination / "scripts" / "detect_test_context.py").is_file())
            self.assertTrue((destination / "examples" / "test-evidence.example.json").is_file())
            self.assertFalse((destination / "scripts" / "validate_repository.py").exists())
            self.assertFalse((destination / "evals").exists())
            self.assertFalse((destination / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
