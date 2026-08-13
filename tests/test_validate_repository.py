from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_repository import scan_secrets, validate_local_links  # noqa: E402


class RepositoryValidationTests(unittest.TestCase):
    def test_skill_requires_lifecycle_state_traceability(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn(
            "risco -> mecanismo protetivo -> estado ou fase -> cenário -> oráculo",
            skill,
        )
        self.assertIn(
            "Não tratar um cenário representativo como cobertura de todo o ciclo de vida.",
            skill,
        )
        self.assertIn(
            "Proteções distintas para estados ou fases distintas exigem provas distintas.",
            skill,
        )
        self.assertIn(
            "Primeiro executar a ação e aguardar o estado pós-cancelamento observável.",
            skill,
        )
        self.assertIn(
            "disparar `reset` e callback obsoleto no mesmo ciclo pode esconder a regressão",
            skill,
        )

    def test_paid_agent_jobs_enforce_the_case_gate(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "agent-evals.yml").read_text(
            encoding="utf-8"
        )
        paired_commands = workflow.split("name: Run paired eval within the approved ceiling")[1:]

        self.assertEqual(2, len(paired_commands))
        for command in paired_commands:
            paired_command = command.split("- name: Save new comparable baseline", 1)[0]
            self.assertIn("--enforce-critical-gate", paired_command)
        cache_key = "baseline-${{ steps.fingerprint.outputs.value }}-r${{ inputs.repetition }}"
        self.assertEqual(4, workflow.count(cache_key))
        self.assertNotIn("steps.fingerprint.outputs.value }}-r1", workflow)

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
