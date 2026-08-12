from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))

from eval_lib import (  # noqa: E402
    apply_mutation,
    copy_artifact_paths,
    hash_paths,
    install_skill,
    restore_mutation,
    run_command,
    sanitized_environment,
    select_cases,
)
from run_eval import (  # noqa: E402
    aggregate,
    baseline_fingerprint,
    build_agent_command,
    build_container_command,
    build_eval_prompt,
    build_test_environment,
    covered_risk_ids,
    evaluation_exit_code,
    planned_agent_calls,
    read_cached_baseline,
    restore_cached_baseline,
)


def result(
    agent: str,
    case: str,
    mode: str,
    score: float,
    critical: bool = True,
    repetition: int = 1,
) -> dict:
    return {
        "run_id": f"{agent}-{case}-{mode}-{repetition}",
        "agent": agent,
        "case": case,
        "mode": mode,
        "repetition": repetition,
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


class ArtifactTests(unittest.TestCase):
    def test_production_hash_ignores_python_runtime_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / "app" / "payment.py"
            source.parent.mkdir()
            source.write_text("enabled = True\n", encoding="utf-8")
            before = hash_paths(workspace, ["app/"])

            cache = workspace / "app" / "__pycache__"
            cache.mkdir()
            (cache / "payment.cpython-313.pyc").write_bytes(b"generated")

            self.assertEqual(before, hash_paths(workspace, ["app/"]))
            source.write_text("enabled = False\n", encoding="utf-8")
            self.assertNotEqual(before, hash_paths(workspace, ["app/"]))

    def test_production_hash_allows_colocated_tests_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / "src" / "PasswordReset.tsx"
            source.parent.mkdir()
            source.write_text("export const value = true;\n", encoding="utf-8")
            before = hash_paths(workspace, ["src/"], ignore_test_artifacts=True)

            colocated = workspace / "src" / "PasswordReset.test.tsx"
            colocated.write_text("test('feature', () => {});\n", encoding="utf-8")
            self.assertEqual(
                before,
                hash_paths(workspace, ["src/"], ignore_test_artifacts=True),
            )

            source.write_text("export const value = false;\n", encoding="utf-8")
            self.assertNotEqual(
                before,
                hash_paths(workspace, ["src/"], ignore_test_artifacts=True),
            )

    def test_production_hash_does_not_treat_contest_class_as_a_test(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / "src" / "Contest.java"
            source.parent.mkdir()
            source.write_text("class Contest {}\n", encoding="utf-8")

            hashes = hash_paths(workspace, ["src/"], ignore_test_artifacts=True)

            self.assertIn("src/Contest.java", hashes)

    def test_copies_only_requested_workspace_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            artifacts = root / "artifacts"
            (workspace / "tests").mkdir(parents=True)
            (workspace / "tests" / "feature.test.ts").write_text("test()\n", encoding="utf-8")
            (workspace / "src").mkdir()
            (workspace / "src" / "feature.spec.ts").write_text("test()\n", encoding="utf-8")
            (workspace / "tests" / "__pycache__").mkdir()
            (workspace / "tests" / "__pycache__" / "test.pyc").write_bytes(b"generated")
            (workspace / "test-evidence.json").write_text("{}\n", encoding="utf-8")

            copy_artifact_paths(workspace, artifacts, ["tests", "test-evidence.json"])

            output = artifacts / "workspace-output"
            self.assertTrue((output / "tests" / "feature.test.ts").is_file())
            self.assertTrue((output / "src" / "feature.spec.ts").is_file())
            self.assertTrue((output / "test-evidence.json").is_file())
            self.assertFalse((output / "tests" / "__pycache__" / "test.pyc").exists())


class RiskCoverageTests(unittest.TestCase):
    def test_matches_hidden_compound_risk_without_exposing_id(self) -> None:
        case = {
            "required_risks": ["ordering-correlation"],
            "risk_signal_groups": {
                "ordering-correlation": [
                    ["ordering", "sequencia"],
                    ["correlation", "correlacao"],
                ]
            },
        }

        covered = covered_risk_ids(
            case,
            "Evita sobrescrever uma sequência nova e preserva a correlação da mensagem.",
        )

        self.assertEqual(["ordering-correlation"], covered)

    def test_rejects_partial_compound_risk(self) -> None:
        case = {
            "required_risks": ["ordering-correlation"],
            "risk_signal_groups": {
                "ordering-correlation": [["ordering", "ordem"], ["correlation", "correlacao"]]
            },
        }

        self.assertEqual([], covered_risk_ids(case, "Valida apenas a ordem dos eventos."))

    def test_baseline_and_treatment_receive_same_request_without_hidden_risk_ids(self) -> None:
        case = {
            "prompt": "Crie testes guiados por risco para o pagamento.",
            "required_risks": ["idempotency", "concurrency", "rollback"],
        }

        baseline = build_eval_prompt(case, "codex", "baseline")
        treatment = build_eval_prompt(case, "codex", "skill")

        self.assertEqual("Use $skill-suite-tests. " + baseline, treatment)
        self.assertTrue(all(risk not in baseline for risk in case["required_risks"]))


class CommandTests(unittest.TestCase):
    def test_run_command_resolves_executable_cross_platform(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            command = run_command([sys.executable, "-c", "print('ok')"], Path(directory))
        self.assertTrue(command.passed)
        self.assertEqual(command.stdout.strip(), "ok")

    def test_run_command_passes_stdin_without_adding_it_to_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            command = run_command(
                [sys.executable, "-c", "import sys; print(len(sys.stdin.read()))"],
                Path(directory),
                input_text="sensitive-value\n",
            )
        self.assertTrue(command.passed)
        self.assertEqual("16", command.stdout.strip())
        self.assertNotIn("sensitive-value", " ".join(command.command))

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

    def test_grader_keeps_browser_path_without_agent_credentials(self) -> None:
        environment = {
            "PATH": "runtime-path",
            "PLAYWRIGHT_BROWSERS_PATH": "/tmp/browsers",
            "OPENAI_API_KEY": "openai-secret",
            "CURSOR_API_KEY": "cursor-secret",
        }

        test_environment = build_test_environment(environment)

        self.assertEqual("/tmp/browsers", test_environment["PLAYWRIGHT_BROWSERS_PATH"])
        self.assertNotIn("OPENAI_API_KEY", test_environment)
        self.assertNotIn("CURSOR_API_KEY", test_environment)

    def test_codex_home_exists_before_cli_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            runtime_home = root / "agent-home"
            with (
                mock.patch("run_eval.shutil.which", return_value="codex"),
                mock.patch.dict(
                    "os.environ",
                    {"PATH": "runtime-path", "OPENAI_API_KEY": "agent-key"},
                    clear=True,
                ),
            ):
                command, environment = build_agent_command(
                    "codex",
                    "Create tests",
                    workspace,
                    runtime_home,
                    "test-model",
                )

            self.assertTrue(Path(environment["CODEX_HOME"]).is_dir())
            self.assertTrue(Path(environment["HOME"]).is_dir())
            self.assertIn("--ignore-user-config", command)
            self.assertIn("--skip-git-repo-check", command)
            self.assertNotIn("CURSOR_API_KEY", environment)

    def test_containerized_codex_uses_controlled_full_access(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            command, _ = build_agent_command(
                "codex",
                "Create tests",
                workspace,
                root / "runtime",
                "test-model",
                containerized=True,
            )

        sandbox_index = command.index("--sandbox")
        self.assertEqual("danger-full-access", command[sandbox_index + 1])

    def test_container_mounts_only_fixture_and_agent_home(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            workspace.mkdir()
            runtime = root / "runtime"
            with (
                mock.patch("run_eval.shutil.which", return_value="/usr/bin/docker"),
                mock.patch("run_eval.os.getuid", return_value=1001, create=True),
                mock.patch("run_eval.os.getgid", return_value=1001, create=True),
            ):
                command, environment = build_container_command(
                    "eval-agent:test",
                    ["codex", "--version"],
                    workspace,
                    runtime,
                    {"PATH": "runtime-path", "OPENAI_API_KEY": "secret-value"},
                )
                codex_home_created = (runtime / "container-home" / ".codex").is_dir()

        rendered = " ".join(command)
        self.assertIn(f"source={workspace.resolve()},target=/workspace", rendered)
        self.assertIn("target=/home/eval", rendered)
        self.assertNotIn("secret-value", rendered)
        self.assertEqual("secret-value", environment["OPENAI_API_KEY"])
        self.assertIn("--read-only", command)
        self.assertIn("--cap-drop=ALL", command)
        self.assertIn("PYTHONPATH=/home/eval/python-site", rendered)
        self.assertTrue(codex_home_created)


class AggregateTests(unittest.TestCase):
    def test_partial_certification_accepts_a_later_repetition_label(self) -> None:
        results = [
            result("codex", "web", "baseline", 20, repetition=2),
            result("codex", "web", "skill", 100, repetition=2),
        ]

        report = aggregate(results, repetitions=1, repetition_start=2)

        self.assertTrue(report["passed"])
        self.assertEqual([], report["matrix_errors"])

    def test_release_gate_passes_with_required_gain(self) -> None:
        results = []
        for agent in ("codex", "cursor"):
            for case in ("web", "api", "events"):
                for repetition in range(1, 4):
                    baseline = result(agent, case, "baseline", 80, repetition=repetition)
                    skill = result(agent, case, "skill", 90, repetition=repetition)
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

    def test_gate_rejects_a_missing_mode_without_crashing(self) -> None:
        results = [result("codex", "web", "skill", 90)]

        report = aggregate(
            results,
            repetitions=1,
            expected_agents=["codex"],
            expected_cases=["web"],
        )

        self.assertFalse(report["passed"])
        self.assertIn("codex/web/baseline", report["matrix_errors"][0])

    def test_single_case_gate_requires_improvement_in_that_case(self) -> None:
        results = [
            result("codex", "web", "baseline", 80),
            result("codex", "web", "skill", 90),
        ]

        report = aggregate(
            results,
            repetitions=1,
            expected_agents=["codex"],
            expected_cases=["web"],
        )

        self.assertTrue(report["passed"])
        self.assertEqual(1, report["required_improved_cases"])

    def test_gate_rejects_a_completely_missing_case(self) -> None:
        results = [
            result("codex", "web", "baseline", 80),
            result("codex", "web", "skill", 90),
        ]

        report = aggregate(
            results,
            repetitions=1,
            expected_agents=["codex"],
            expected_cases=["web", "api"],
        )

        self.assertFalse(report["passed"])
        self.assertTrue(any("codex/api/baseline" in error for error in report["matrix_errors"]))
        self.assertTrue(any("codex/api/skill" in error for error in report["matrix_errors"]))

    def test_gate_rejects_a_completely_missing_agent(self) -> None:
        results = [
            result("codex", "web", "baseline", 80),
            result("codex", "web", "skill", 90),
        ]

        report = aggregate(
            results,
            repetitions=1,
            expected_agents=["codex", "cursor"],
            expected_cases=["web"],
        )

        self.assertFalse(report["passed"])
        self.assertTrue(any("cursor/web/baseline" in error for error in report["matrix_errors"]))
        self.assertTrue(any("cursor/web/skill" in error for error in report["matrix_errors"]))

    def test_release_gate_rejects_duplicate_or_missing_repetitions(self) -> None:
        results = []
        for case in ("web", "api", "events"):
            for mode, score in (("baseline", 80), ("skill", 90)):
                for repetition in (1, 2, 2):
                    run = result("codex", case, mode, score, repetition=repetition)
                    results.append(run)

        report = aggregate(
            results,
            repetitions=3,
            expected_agents=["codex"],
            expected_cases=["web", "api", "events"],
        )

        self.assertFalse(report["passed"])
        self.assertEqual(7, len(report["matrix_errors"]))
        self.assertTrue(any("duplicate run IDs" in error for error in report["matrix_errors"]))

    def test_agent_process_failure_is_reported_and_fails_job(self) -> None:
        results = []
        for case in ("web", "api", "events"):
            results.extend((result("codex", case, "baseline", 80), result("codex", case, "skill", 90)))
        results[0]["agent_exit_code"] = 1

        report = aggregate(results, repetitions=1)

        self.assertEqual(["codex-web-baseline-1"], report["execution_failures"])
        self.assertFalse(report["passed"])
        self.assertEqual(1, evaluation_exit_code(report, enforce_gate=False))


class PaidCallGuardTests(unittest.TestCase):
    def test_counts_paired_calls_and_cached_baselines(self) -> None:
        self.assertEqual(6, planned_agent_calls(1, 3, 1))
        self.assertEqual(3, planned_agent_calls(1, 3, 1, cached_baselines=3))
        self.assertEqual(36, planned_agent_calls(2, 3, 3))

    def test_rejects_impossible_cache_count(self) -> None:
        with self.assertRaises(ValueError):
            planned_agent_calls(1, 1, 1, cached_baselines=2)

    def test_baseline_cache_requires_matching_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_id = "codex-web-baseline-1"
            cached = root / "fingerprint" / run_id
            cached.mkdir(parents=True)
            document = {
                "run_id": run_id,
                "agent": "codex",
                "case": "web",
                "mode": "baseline",
                "repetition": 1,
                "model": "model-a",
                "dry_run": False,
                "agent_exit_code": 0,
            }
            (cached / "result.json").write_text(json.dumps(document), encoding="utf-8")

            self.assertIsNotNone(
                read_cached_baseline(root, "fingerprint", "codex", "web", 1, "model-a")
            )
            self.assertIsNone(
                read_cached_baseline(root, "fingerprint", "codex", "web", 1, "model-b")
            )

    def test_restored_baseline_is_marked_and_copied(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cached = root / "cache" / "run"
            cached.mkdir(parents=True)
            result_document = {"run_id": "run", "agent_exit_code": 0}
            (cached / "result.json").write_text(json.dumps(result_document), encoding="utf-8")
            (cached / "evidence.txt").write_text("kept", encoding="utf-8")

            restored = restore_cached_baseline((result_document, cached), root / "artifacts")

            self.assertTrue(restored["baseline_reused"])
            self.assertEqual("kept", (root / "artifacts" / "run" / "evidence.txt").read_text())

    def test_fingerprint_changes_with_agent_or_model(self) -> None:
        case = select_cases(["web-password-reset"])[0]
        codex = baseline_fingerprint(case, "codex", "model-a")
        cursor = baseline_fingerprint(case, "cursor", "model-a")
        other_model = baseline_fingerprint(case, "codex", "model-b")

        self.assertNotEqual(codex, cursor)
        self.assertNotEqual(codex, other_model)


class SkillPackagingTests(unittest.TestCase):
    def test_runtime_package_excludes_graders_and_docs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "skill-suite-tests"
            install_skill(destination)
            self.assertTrue((destination / "SKILL.md").is_file())
            self.assertTrue((destination / "scripts" / "detect_test_context.py").is_file())
            self.assertTrue((destination / "scripts" / "prove_test_sensitivity.py").is_file())
            self.assertTrue((destination / "examples" / "test-evidence.example.json").is_file())
            self.assertFalse((destination / "scripts" / "validate_repository.py").exists())
            self.assertFalse((destination / "evals").exists())
            self.assertFalse((destination / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
