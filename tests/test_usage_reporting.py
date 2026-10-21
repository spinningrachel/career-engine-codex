"""Synthetic doctrine fixtures exercise the real generator, not installed caches."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('usage_port', ROOT / 'tools/port.py')
port = importlib.util.module_from_spec(spec)
spec.loader.exec_module(port)


class UsageReportingTests(unittest.TestCase):
    def test_regeneration_preserves_adapter_and_future_doctrine(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'upstream'
            for folder in port.INCLUDE:
                (source / folder).mkdir(parents=True)
            for name in ('LICENSE', 'README.md', 'CLAUDE.md', 'CONNECTORS.md'):
                (source / name).write_text('Synthetic fixture\n')
            for name in ('block-personal-data-writes.sh', 'test-personal-data-guard.sh'):
                (source / 'scripts' / name).write_text('# synthetic fixture\n')
            needles = ['"log-token-usage.sh"', '\'"type": "prompt"\'', '"last_assistant_message"', "'ok", 'AskUserQuestion', 'gate-ask-user-question.sh']
            (source / 'scripts/qa-mechanical.sh').write_text('\n'.join('expect_ge "21t" "hooks/hooks.json" ' + n for n in needles))
            post = source / 'skills/career-engine-orchestrator/orchestrator-post-run.md'
            post.parent.mkdir()
            post.write_text('Actual token counts are appended by a Stop hook configured during setup — the hook writes to this same file when the session ends.\n"token_counts": "pending — written by Stop hook at session end"\nSet each agent count from the actual invocations this run. Leave `token_counts` as the literal string `"pending — written by Stop hook at session end"` — the hook replaces this value when the session closes.\n## Final Chat Delivery\nFUTURE REQUIRED GATE\n')
            setup = source / 'skills/career-engine-setup/SKILL.md'
            setup.parent.mkdir()
            setup.write_text('**Token usage tracking (optional but recommended):**\nlegacy\nConfirm: "Phase 6 complete.\n')
            subprocess.run(['git', 'init', '-q', str(source)], check=True)
            subprocess.run(['git', '-C', str(source), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(source), '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.com', 'commit', '-qm', 'synthetic'], check=True)
            shutil.copytree(ROOT / 'codex', root / 'codex')
            (root / "tools").mkdir()
            shutil.copy2(ROOT / "tools/port.py", root / "tools/port.py")
            old_file = port.__file__
            port.__file__ = str(root / "tools/port.py")
            old = port.ROOT
            try:
                port.ROOT = root
                port.generate(source)
                first = (root / 'upstream-lock.json').read_bytes()
                (root / 'plugin/references/run-metrics-host.md').write_text('cache-only damage')
                port.generate(source)
                self.assertEqual(first, (root / 'upstream-lock.json').read_bytes())
                self.assertIn('FUTURE REQUIRED GATE', (root / 'plugin' / post.relative_to(source)).read_text())
                self.assertEqual((ROOT / 'codex/overrides/references/run-metrics-host.md').read_bytes(), (root / 'plugin/references/run-metrics-host.md').read_bytes())
                post.write_text(post.read_text().replace('## Final Chat Delivery', '## Changed delivery'))
                with self.assertRaisesRegex(RuntimeError, 'anchor changed'):
                    port.generate(source)
            finally:
                port.ROOT = old
                port.__file__ = old_file

    def test_generated_reporting_contract(self):
        text = (ROOT / 'plugin/references/run-metrics-host.md').read_text()
        for required in ('run-metrics-YYYY-MM-DD.json', 'interrupted runs', 'state.json', 'halted-roles.json', 'sequential_role_passes', 'spawned_agent_invocations', 'retry once', 'parse JSON', 'absolute external output path', 'sandbox download link', 'content follows'):
            self.assertIn(required, text)
        example = text.split('```json\n', 1)[1].split('```', 1)[0]
        accounting = json.loads(example)
        for key in ('token_counts', 'cost'):
            self.assertEqual(accounting[key]['status'], 'unavailable')
            self.assertTrue(accounting[key]['reason'])
        post = (ROOT / 'plugin/skills/career-engine-orchestrator/orchestrator-post-run.md').read_text()
        self.assertNotIn('pending — written by Stop hook', post)
        self.assertIn('roles_processed', post)
        self.assertIn('on an interrupted run all three block', post)
        setup = (ROOT / 'plugin/skills/career-engine-setup/SKILL.md').read_text()
        self.assertNotIn('The hook ships with the plugin and **registers itself**', setup)
        for path in ('codex/runtime.md', 'chatgpt/runtime.md', 'chatgpt/instructions.txt'):
            self.assertIn('references/run-metrics-host.md', (ROOT / path).read_text())
