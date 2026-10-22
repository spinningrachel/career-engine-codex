"""Guard changed doctrine at its writeback and closure consumers."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('intake_port', ROOT / 'tools/port.py')
port = importlib.util.module_from_spec(spec)
spec.loader.exec_module(port)


class IntakeCorrectionTests(unittest.TestCase):
    def test_confirmation_and_closure_precedence_preserve_gates(self):
        intake = (ROOT / 'plugin/skills/career-engine-intake/SKILL.md').read_text()
        database = (ROOT / 'plugin/skills/database/SKILL.md').read_text()
        self.assertIn('exclude coach fields skipped under the no-matching-text-property rule from confirmation, retry, and unwritten-field reporting', intake)
        self.assertIn('Still require their coach output and the outreach-map details', intake)
        self.assertIn('attempt the write once more', intake)
        self.assertIn('Every selected role', intake)
        self.assertIn('a mirror cannot reopen the official posting', database)
        self.assertIn('never claim an index check occurred if it did not', database)
        self.assertIn('as `NOT WRITTEN`, with prior Status, URL, and evidence', database)

    def test_changed_anchor_blocks_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            path = target / 'skills/career-engine-intake/SKILL.md'
            path.parent.mkdir(parents=True)
            path.write_text('Changed upstream confirmation contract\n')
            with self.assertRaisesRegex(RuntimeError, 'Intake correction anchor changed'):
                port.adapt_intake_corrections(target)
