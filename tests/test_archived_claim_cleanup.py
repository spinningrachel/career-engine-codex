from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ArchivedClaimCleanupTests(unittest.TestCase):
    def test_cleanup_preserves_liveness_gate_and_reports_unreleased_claims(self):
        role = (ROOT/'plugin/agents/role-prioritizer.md').read_text()
        cleanup = role.split('**First, release unfinished claims (2026-10-21):**', 1)[1].split('\n\n', 1)[0]
        self.assertIn('re-fetch the page immediately before cleanup', cleanup)
        self.assertIn('only for this run\'s own unfinished claim', cleanup)
        self.assertIn('not archived/trashed', cleanup)
        self.assertIn('Status still matches the target', cleanup)
        self.assertIn('make no write, never unarchive it', cleanup)
        self.assertIn('claim not released', cleanup)
        self.assertIn('Never write to an archived/trashed page', (ROOT/'plugin/skills/database-notion/SKILL.md').read_text())
