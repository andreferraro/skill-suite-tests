from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from detect_test_context import detect  # noqa: E402


class DetectTestContextTests(unittest.TestCase):
    def test_detects_validated_react_typescript_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text(
                json.dumps(
                    {
                        "dependencies": {"react": "19.1.1"},
                        "devDependencies": {
                            "typescript": "5.9.2",
                            "vitest": "3.2.4",
                            "@testing-library/react": "16.3.0",
                            "@playwright/test": "1.54.2",
                        },
                    }
                ),
                encoding="utf-8",
            )
            (root / "src").mkdir()
            (root / "src" / "App.tsx").write_text("export const App = () => null;", encoding="utf-8")
            (root / "tests").mkdir()
            (root / "tests" / "App.test.tsx").write_text("", encoding="utf-8")
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / ".github" / "workflows" / "test.yml").write_text("name: test", encoding="utf-8")

            result = detect(root)

            self.assertEqual("validated", result["support_status"])
            self.assertIn("react-typescript-frontend", result["validated_profiles"])
            self.assertEqual(["playwright"], result["browser_automation"])
            self.assertIn("tests/App.test.tsx", result["test_files"])
            self.assertIn(".github/workflows/test.yml", result["ci_files"])

    def test_detects_fastapi_profile_and_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "requirements.txt").write_text(
                "fastapi==0.116.1\npytest==8.4.1\naiosqlite==0.21.0\n",
                encoding="utf-8",
            )
            (root / "tests").mkdir()
            (root / "tests" / "test_api.py").write_text("", encoding="utf-8")

            result = detect(root)

            self.assertEqual("validated", result["support_status"])
            self.assertIn("fastapi-python-api", result["validated_profiles"])
            self.assertIn("pytest", result["test_tools"])
            self.assertIn("sqlite", result["databases"])

    def test_reports_unknown_stack_as_adaptable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "go.mod").write_text("module example.test\n", encoding="utf-8")

            result = detect(root)

            self.assertEqual("adaptable", result["support_status"])
            self.assertEqual([], result["validated_profiles"])
            self.assertIn("go", result["technologies"])

    def test_ignores_dependency_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "node_modules" / "fake" / "tests").mkdir(parents=True)
            (root / "node_modules" / "fake" / "tests" / "fake.test.js").write_text("", encoding="utf-8")

            result = detect(root)

            self.assertEqual([], result["test_files"])

    def test_ignores_agent_skill_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / ".agents" / "skills" / "sample"
            skill.mkdir(parents=True)
            (skill / "package.json").write_text(
                json.dumps({"dependencies": {"react": "19.1.1", "typescript": "5.9.2"}}),
                encoding="utf-8",
            )

            result = detect(root)

            self.assertEqual("adaptable", result["support_status"])
            self.assertEqual([], result["technologies"])

    def test_ignores_agent_python_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dependency = root / ".agent-site" / "fake_package" / "tests"
            dependency.mkdir(parents=True)
            (dependency / "test_postgres.py").write_text("import redis\n", encoding="utf-8")

            result = detect(root)

            self.assertEqual([], result["test_files"])
            self.assertEqual([], result["databases"])

    def test_jest_dom_does_not_imply_jest_runner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text(
                json.dumps(
                    {
                        "devDependencies": {
                            "@testing-library/jest-dom": "6.6.4",
                            "vitest": "3.2.7",
                        }
                    }
                ),
                encoding="utf-8",
            )

            result = detect(root)

            self.assertIn("vitest", result["test_tools"])
            self.assertNotIn("jest", result["test_tools"])

    def test_detects_sqlite_from_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pyproject.toml").write_text("[project]\nname = 'sample'\n", encoding="utf-8")
            (root / "storage.py").write_text("import sqlite3\n", encoding="utf-8")

            result = detect(root)

            self.assertIn("sqlite", result["databases"])

    def test_reports_confirmable_risk_signals_from_production_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src" / "payment.py").write_text(
                """
def create(idempotency_key, amount, connection):
    if amount <= 0:
        raise ValueError()
    connection.execute('BEGIN IMMEDIATE')
    try:
        return idempotency_key
    except Exception:
        connection.rollback()
""",
                encoding="utf-8",
            )
            (root / "tests").mkdir()
            (root / "tests" / "test_noise.py").write_text("retry = 'DLQ'\n", encoding="utf-8")

            result = detect(root)

            signals = result["risk_signals"]
            self.assertEqual(["src/payment.py"], signals["concurrency-control"])
            self.assertEqual(["src/payment.py"], signals["idempotency-control"])
            self.assertEqual(["src/payment.py"], signals["non-positive-validation"])
            self.assertEqual(["src/payment.py"], signals["transaction-rollback"])
            self.assertNotIn("retry-control", signals)


if __name__ == "__main__":
    unittest.main()
