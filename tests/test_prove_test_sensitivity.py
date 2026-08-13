from __future__ import annotations

import sys
import tempfile
import unittest
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prove_test_sensitivity import prove  # noqa: E402


class ProveTestSensitivityTests(unittest.TestCase):
    def test_result_with_unicode_can_be_printed_on_cp1252_console(self) -> None:
        serialized = json.dumps({"stdout_tail": "✓ ❯"}, ensure_ascii=True, indent=2)

        serialized.encode("cp1252")
        self.assertIn(r"\u2713", serialized)
        self.assertIn(r"\u276f", serialized)

    def test_proves_failure_and_restores_source_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "feature.py"
            original = "enabled = True\n"
            source.write_text(original, encoding="utf-8", newline="")

            exit_code, result = prove(
                root,
                "feature.py",
                "enabled = True",
                "enabled = False",
                [
                    sys.executable,
                    "-c",
                    "from feature import enabled; raise SystemExit(0 if enabled else 1)",
                ],
                30,
            )

            self.assertEqual(0, exit_code)
            self.assertTrue(result["proved"])
            self.assertTrue(result["restored"])
            self.assertEqual(original, source.read_text(encoding="utf-8"))

    def test_rejects_an_insensitive_test_and_restores_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "feature.py"
            source.write_text("enabled = True\n", encoding="utf-8", newline="")

            exit_code, result = prove(
                root,
                "feature.py",
                "True",
                "False",
                [sys.executable, "-c", "raise SystemExit(0)"],
                30,
            )

            self.assertEqual(1, exit_code)
            self.assertFalse(result["proved"])
            self.assertTrue(result["restored"])
            self.assertEqual("enabled = True\n", source.read_text(encoding="utf-8"))

    def test_rejects_path_outside_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            root.mkdir()
            outside = root.parent / "outside.py"
            outside.write_text("enabled = True\n", encoding="utf-8")

            exit_code, result = prove(root, "../outside.py", "True", "False", [sys.executable], 30)

            self.assertEqual(2, exit_code)
            self.assertFalse(result["proved"])

    def test_mutates_selected_occurrence_and_restores_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "feature.py"
            original = "guard = True\nfirst = guard\nsecond = guard\n"
            source.write_text(original, encoding="utf-8", newline="")

            exit_code, result = prove(
                root,
                "feature.py",
                "guard",
                "disabled",
                [
                    sys.executable,
                    "-c",
                    "from pathlib import Path; text=Path('feature.py').read_text(); raise SystemExit(1 if 'second = disabled' in text and 'first = guard' in text else 0)",
                ],
                30,
                occurrence=3,
            )

            self.assertEqual(0, exit_code)
            self.assertTrue(result["proved"])
            self.assertTrue(result["restored"])
            self.assertEqual(original, source.read_text(encoding="utf-8"))

    def test_requires_occurrence_for_repeated_search(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "feature.py"
            source.write_text("guard\nguard\n", encoding="utf-8")

            exit_code, result = prove(
                root,
                "feature.py",
                "guard",
                "disabled",
                [sys.executable, "-c", "raise SystemExit(1)"],
                30,
            )

            self.assertEqual(2, exit_code)
            self.assertIn("--occurrence", result["error"])
