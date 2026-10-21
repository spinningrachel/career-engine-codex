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
    def test_version_stamp_tracks_adapter_changes_and_published_archive(self):
        import json
        builder = module('version_builder', 'tools/build-chatgpt-plugin.py')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'career-engine-chatgpt.zip').symlink_to(ROOT/'career-engine-chatgpt.zip')
            (root/'chatgpt').mkdir()
            skill = root/'chatgpt/plugin-skill.md'
            original = (ROOT/'chatgpt/plugin-skill.md').read_text()
            skill.write_text(original)
            builder.ROOT = root
            first = builder.members()
            skill.write_text(original+'\nHost adapter changed.\n')
            second = builder.members()
            self.assertNotEqual(json.loads(first['plugin.json'])['version'], json.loads(second['plugin.json'])['version'])
            builder.build(root/'career-engine-chatgpt-plugin.zip')
            record = json.loads((root/'chatgpt-plugin-version.json').read_text())
            for name in ('career-engine', 'career-engine-version'):
                text = second['skills/'+name+'/SKILL.md'].decode()
                self.assertIn(record['package_version'], text)
                self.assertIn(record['upstream_commit'], text)
                self.assertIn('Never use the remote version as the loaded version', text)

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
            record = root/'chatgpt-plugin-version.json'
            original_record = record.read_text()
            record.write_text('{}')
            with self.assertRaisesRegex(AssertionError, 'Stale published version record'):
                checker.check()
            record.write_text(original_record)
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
