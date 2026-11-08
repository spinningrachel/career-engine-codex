"""Keep the new research contract intact across host packaging boundaries."""
import json
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class CompanyFactsTests(unittest.TestCase):
    def test_optional_tracker_column_does_not_make_coach_output_optional(self):
        intake = (ROOT / 'plugin/skills/career-engine-intake/SKILL.md').read_text()
        gates = (ROOT / 'plugin/skills/gatekeeper-checks/coach-gates.md').read_text()
        self.assertIn('whether or not the tracker has the property; intake decides whether it can be written', gates)
        self.assertIn('add a text property named exactly `Core Company Facts`', intake)
        confirmation = intake.split('**Confirmation pass', 1)[1].split('Confirm in chat:', 1)[0]
        self.assertIn('`Core Company Facts` (only when the DB has a `Core Company Facts` property)', confirmation)
        self.assertIn('Compare the re-read value', confirmation)
        self.assertIn('attempt the write once more', confirmation)

    def test_changed_research_and_title_gates_reach_both_chatgpt_distributions(self):
        paths = (
            'skills/career-coach/coach-research.md',
            'skills/career-coach/coach-analysis.md',
            'skills/career-coach/coach-output.md',
            'skills/gatekeeper-checks/coach-gates.md',
            'skills/gatekeeper-checks/cv-gates.md',
        )
        with zipfile.ZipFile(ROOT / 'career-engine-chatgpt.zip') as kit, zipfile.ZipFile(
            ROOT / 'career-engine-chatgpt-plugin.zip'
        ) as plugin:
            kit_index = json.loads(kit.read('manifest.json'))['source_index']
            prefix = 'career-engine/skills/career-engine/'
            plugin_index = json.loads(plugin.read(prefix + 'references/source-index.json'))
            for path in paths:
                with self.subTest(path=path):
                    marker = '=== SOURCE: ' + path + ' ===\n'
                    def section(archive, name):
                        return archive.read(name).decode().split(marker, 1)[1].split('=== END SOURCE ===', 1)[0]
                    kit_text = section(kit, kit_index[path]['knowledge_file'])
                    plugin_text = section(plugin, prefix + plugin_index[path]['knowledge_file'])
                    self.assertEqual(kit_text, plugin_text)
                    # Knowledge resolves source labels rather than installed-root paths.
                    native = (ROOT / 'plugin' / path).read_text()
                    portable = native.replace('${CAREER_ENGINE_ROOT}/', '').replace('$CAREER_ENGINE_ROOT/', '')
                    self.assertEqual(kit_text.rstrip(), portable.rstrip())

    def test_coach_led_cannot_claim_saved_title_exemption(self):
        analysis = (ROOT / 'plugin/skills/career-coach/coach-analysis.md').read_text()
        gates = (ROOT / 'plugin/skills/gatekeeper-checks/coach-gates.md').read_text()
        self.assertIn('has NO rule: the coach decides per role', analysis)
        self.assertIn('such a line never carries the preferences-file label', analysis)
        self.assertIn('entry for that exact employer saying the same thing', gates)
        self.assertIn('A line failing this check is judged as if unlabeled', gates)
