"""Connector discovery must survive coach fallbacks and every distribution."""
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class JobDiscoveryTests(unittest.TestCase):
    def test_consumers_preserve_discovery_and_liveness(self):
        for relative in ('agents/career-coach.md', 'agents/role-prioritizer.md',
                         'skills/career-engine-intake/SKILL.md'):
            with self.subTest(relative=relative):
                text = (ROOT / 'plugin' / relative).read_text()
                self.assertIn('it is not a literal callable API', text)
                self.assertIn('never claim hidden connectors were checked', text)
                self.assertIn('company + exact title, then company alone', text)
                self.assertIn('Never query linkedin-mcp or fetch linkedin.com', text)
        coach = (ROOT / 'plugin/agents/career-coach.md').read_text()
        self.assertIn('current ladder before using the older numbered summary', coach)
        self.assertIn('match and liveness checks, closure rules', coach)
        prioritizer = (ROOT / 'plugin/agents/role-prioritizer.md').read_text()
        self.assertIn('without spawning nested agents', prioritizer)
        intake = (ROOT / 'plugin/skills/career-engine-intake/SKILL.md').read_text()
        self.assertIn('run the ladder’s search rungs', intake.replace("ladder's", 'ladder’s'))
        self.assertIn('(2, 3, 4, 5)', intake)

    def test_chatgpt_routes_receive_full_discovery_mapping(self):
        for archive, source in (
            ('career-engine-chatgpt.zip', 'knowledge/01-workflows-and-roles.txt'),
            ('career-engine-chatgpt-plugin.zip',
             'career-engine/skills/career-engine/references/01-workflows-and-roles.txt'),
        ):
            with self.subTest(archive=archive), zipfile.ZipFile(ROOT / archive) as z:
                text = z.read(source).decode()
                self.assertIn('current ladder before using the older numbered summary', text)
                self.assertIn('unexecuted search is never evidence', text)
                self.assertIn('Job-data connectors (2026-11-04', text)
