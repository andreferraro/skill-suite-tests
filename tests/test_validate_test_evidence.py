from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_test_evidence import validate  # noqa: E402


def valid_report() -> dict:
    return {
        "schema_version": "1.0",
        "target": "payment creation",
        "support_status": "validated",
        "classification": {
            "purpose": ["regression"],
            "level": ["integration"],
            "quality_attributes": ["concurrency"],
            "techniques": ["state transition"],
        },
        "basis": [{"type": "requirement", "reference": "Payment idempotency rule"}],
        "risks": [{"id": "R1", "description": "Duplicate charge", "impact": "Financial loss"}],
        "scenarios": [
            {
                "id": "S1",
                "risk_ids": ["R1"],
                "name": "Concurrent duplicate request",
                "preconditions": "Empty database",
                "stimulus": "Two requests with the same key",
                "oracle": "One persisted payment and one stable identifier",
                "isolation": "Unique database per test",
                "cleanup": "Temporary database removed",
            }
        ],
        "boundaries": [
            {"name": "SQLite", "mode": "real", "rationale": "Persistence is part of the risk"}
        ],
        "files_changed": ["tests/test_payment.py"],
        "commands": [
            {"command": "pytest -q", "status": "passed", "exit_code": 0, "evidence": "3 passed"}
        ],
        "evidence": [{"type": "test-output", "summary": "3 tests passed"}],
        "limitations": [],
    }


class ValidateTestEvidenceTests(unittest.TestCase):
    def test_accepts_complete_report(self) -> None:
        self.assertEqual([], validate(valid_report()))

    def test_rejects_unknown_risk_reference(self) -> None:
        report = valid_report()
        report["scenarios"][0]["risk_ids"] = ["R404"]

        errors = validate(report)

        self.assertTrue(any("unknown risks" in error for error in errors))

    def test_rejects_risk_without_scenario(self) -> None:
        document = valid_report()
        document["risks"].append(
            {"id": "uncovered", "description": "Risk without scenario", "impact": "Regression"}
        )

        errors = validate(document)

        self.assertIn("risks without a scenario: uncovered", errors)

    def test_rejects_report_without_executed_command(self) -> None:
        report = valid_report()
        report["commands"] = [
            {"command": "pytest -q", "status": "not_run", "exit_code": None, "evidence": "Missing environment"}
        ]

        errors = validate(report)

        self.assertIn("at least one command must have been executed", errors)

    def test_rejects_inconsistent_exit_code(self) -> None:
        report = valid_report()
        report["commands"][0]["exit_code"] = 1

        errors = validate(report)

        self.assertTrue(any("passed with non-zero" in error for error in errors))

    def test_rejects_duplicate_ids(self) -> None:
        report = valid_report()
        duplicate = copy.deepcopy(report["risks"][0])
        report["risks"].append(duplicate)

        errors = validate(report)

        self.assertTrue(any("duplicates 'R1'" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
