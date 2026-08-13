from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "skill-suite-tests" / "scripts"))

from analyze_test_target import analyze  # noqa: E402


class AnalyzeTestTargetTests(unittest.TestCase):
    def test_reports_states_actions_and_repeated_guards(self) -> None:
        source = """
const [value, setValue] = useState({ state: "idle" });
const reset = () => { generation.current += 1; setValue({ state: "idle" }); };
async function run() {
  setValue({ state: "parsing" });
  if (generation.current !== currentGeneration) {
    return;
  }
  setValue({ state: "running" });
  await processBatch();
  if (generation.current !== currentGeneration) {
    return;
  }
}
"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.ts"
            target.write_text(source, encoding="utf-8")

            report = analyze(root, Path("target.ts"))

        self.assertEqual(["idle", "parsing", "running"], report["states"])
        self.assertEqual("reset", report["lifecycle_actions"][0]["action"])
        self.assertEqual(2, report["protective_guards"][0]["occurrences"])
        self.assertEqual(2, len(report["protective_guards"][0]["lines"]))

    def test_rejects_target_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            root.mkdir()
            outside = Path(directory) / "outside.ts"
            outside.write_text("export {};", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "inside root"):
                analyze(root, Path("../outside.ts"))


if __name__ == "__main__":
    unittest.main()
