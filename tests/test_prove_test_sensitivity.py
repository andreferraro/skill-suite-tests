from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from prove_test_sensitivity import prove  # noqa: E402


class ProveTestSensitivityTests(unittest.TestCase):
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
