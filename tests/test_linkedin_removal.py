"""Trace LinkedIn-only roles and outreach through each packaged host."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('linkedin_port', ROOT / 'tools/port.py')
port = importlib.util.module_from_spec(spec)
spec.loader.exec_module(port)


class LinkedInRemovalTests(unittest.TestCase):
    def test_no_mirror_path_preserves_search_and_write_gates(self):
        coach = (ROOT / 'plugin/agents/career-coach.md').read_text()
        intake = (ROOT / 'plugin/skills/career-engine-intake/SKILL.md').read_text()
        prioritizer = (ROOT / 'plugin/agents/role-prioritizer.md').read_text()
        self.assertIn('go directly to steps 3–5', coach)
        self.assertIn('Skip steps 1–2', coach)
        self.assertNotIn('continue to step 1 (company careers page', coach)
        self.assertNotIn('LinkedIn auth-walled postings', coach)
        self.assertIn('once-per-run removal notice', coach)
        self.assertIn('LinkedIn-only listing with no public mirror found', intake)
        self.assertIn('No Priority, no Role Summary, no Location write, no Status promotion', prioritizer)
        self.assertIn('JD Fetch Status` is written for every skipped role', prioritizer)
        self.assertIn('liveness check', coach)

    def test_outreach_policy_reaches_both_chatgpt_packages(self):
        output = (ROOT / 'plugin/skills/career-coach/coach-output.md').read_text()
        self.assertEqual(output.count('LinkedIn (manual; reachability unverified) | [LOW]'), 2)
        for archive, source in [
            ('career-engine-chatgpt.zip', 'knowledge/01-workflows-and-roles.txt'),
            ('career-engine-chatgpt-plugin.zip', 'career-engine/skills/career-engine/references/01-workflows-and-roles.txt'),
        ]:
            with self.subTest(archive=archive), zipfile.ZipFile(ROOT / archive) as z:
                doctrine = z.read(source).decode()
                for term in ('Skip steps 1–2', 'never invent counts or reachability',
                             'Preserve every required research dimension',
                             'LinkedIn (manual; reachability unverified) | [LOW]'):
                    self.assertIn(term, doctrine)

    def test_changed_consumer_blocks_adaptation(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            agent = target / 'agents/career-coach.md'
            agent.parent.mkdir()
            agent.write_text('New upstream acquisition contract\n')
            with self.assertRaisesRegex(RuntimeError, 'LinkedIn removal consumer changed'):
                port.adapt_linkedin_removal(target)
