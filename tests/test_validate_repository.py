from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_repository import scan_secrets, validate_local_links  # noqa: E402


class RepositoryValidationTests(unittest.TestCase):
    def test_local_link_validator_detects_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("[missing](docs/missing.md)\n", encoding="utf-8")
            self.assertEqual(
                validate_local_links(root),
                ["broken local link in README.md: docs/missing.md"],
            )

    def test_secret_scanner_allows_placeholder_and_rejects_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "safe.md").write_text("OPENAI_API_KEY=your_api_key_here\n", encoding="utf-8")
            self.assertEqual(scan_secrets(root), [])
            (root / "unsafe.md").write_text("SERVICE_API_KEY=concrete-sensitive-value\n", encoding="utf-8")
            errors = scan_secrets(root)
            self.assertEqual(len(errors), 1)
            self.assertIn("unsafe.md:1", errors[0])


if __name__ == "__main__":
    unittest.main()
