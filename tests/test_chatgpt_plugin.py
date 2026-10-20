import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT/path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

class ChatGPTPluginTests(unittest.TestCase):
    def test_packaging_is_reproducible_and_rejects_missing_skill(self):
        builder = module('chat_plugin_builder', 'tools/build-chatgpt-plugin.py')
        checker = module('chat_plugin_checker', 'tools/check-chatgpt-plugin.py')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root/'career-engine-chatgpt-plugin.zip'
            builder.build(output)
            self.assertEqual(output.read_bytes(), (ROOT/output.name).read_bytes())
            (root/'tools').symlink_to(ROOT/'tools', target_is_directory=True)
            (root/'upstream-lock.json').symlink_to(ROOT/'upstream-lock.json')
            checker.ROOT = root
            checker.check()
            data = builder.members()
            del data['skills/career-engine/SKILL.md']
            with zipfile.ZipFile(output, 'w') as archive:
                for name, content in data.items():
                    archive.writestr('career-engine/'+name, content)
            with self.assertRaisesRegex(AssertionError, 'stale/incomplete'):
                checker.check()

    def test_checkpoint_and_publisher_include_plugin_artifact(self):
        checkpoint = module('chat_plugin_checkpoint','tools/checkpoint-sync.py')
        self.assertTrue(checkpoint.allowed('career-engine-chatgpt-plugin.zip'))
        self.assertIn("'career-engine-chatgpt-plugin.zip'", (ROOT/'tools/publish-sync.py').read_text())
        workflow = (ROOT/'.github/workflows/sync-upstream.yml').read_text()
        self.assertIn('tools/build-chatgpt-plugin.py tools/check-chatgpt-plugin.py chatgpt/plugin-skill.md', workflow)
