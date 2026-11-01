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
            # The guard adapter now checks its traversal anchor. Model that
            # upstream structure rather than bypassing the generation gate.
            (source / 'scripts/block-personal-data-writes.sh').write_text(
                'def in_plugin_repo(p):\n'
                '    cur = os.path.dirname(os.path.abspath(p))\n'
                '    while True:\n'
                '        manifest = os.path.join(cur, ".claude-plugin", "plugin.json")\n'
                '        if os.path.isfile(manifest):\n'
                '            with open(manifest) as fh:\n'
                '                return cur if json.load(fh).get("name") == "career-engine" else None\n'
                '        parent = os.path.dirname(cur)\n'
                '        if parent == cur:\n'
                '            return None\n'
                '        cur = parent\n')
            needles = ['"log-token-usage.sh"', '\'"type": "prompt"\'', '"last_assistant_message"', "'ok", 'AskUserQuestion', 'gate-ask-user-question.sh']
            (source / 'scripts/qa-mechanical.sh').write_text('\n'.join('expect_ge "21t" "hooks/hooks.json" ' + n for n in needles))
            (source / 'hooks').mkdir()
            (source / 'hooks/hooks.json').write_text(json.dumps({'hooks': {'Stop': [{'hooks': [{'type': 'prompt', 'prompt': 'Synthetic queue-completion policy'}]}]}}))
            (source / 'scripts/qa-parity.json').write_text(json.dumps({'defined_terms': []}))
            (source / 'agents/role-prioritizer.md').write_text('Synthetic role fixture\n')
            # Model required LinkedIn-removal anchors without skipping their gate.
            linkedin_consumers = {'agents/career-coach.md': 'Take the company and title from the row and continue to step 1 (company careers page, ATS/board mirrors, exact-title search).\nTry the Job URL directly. If blocked (LinkedIn login wall, gated portal, 403/redirect)\nincluding JavaScript-rendered career pages and LinkedIn auth-walled postings. Call the strongest available on the Job URL.\n', 'skills/career-coach/coach-research.md': '## Research Phase\nConfirm they are reachable on LinkedIn (public profile, accepts connections). Action: Connect + short note.\nAction: Connect + note. Selection criteria in priority order: (a) 2nd degree with mutual connections; (b) same country as the user (`my_location` from `pipeline-preferences.json`); (c) active on LinkedIn (recent posts or activity visible); (d) function adjacent to the role (PMM for PM roles; BI/Analytics for data roles; etc.).\n', 'skills/career-coach/coach-analysis.md': '**Search LinkedIn for the company** and scan **all** people with {{USER_PROFESSION}} titles — not just the most senior one.\n', 'skills/career-coach/coach-output.md': '| <Name, Title> | Connect + short note | <1 sentence: role relationship + one specific engagement hook> | LinkedIn | [HIGH/MEDIUM/LOW] |\n| <Name, Title> | Connect + note | <1 sentence: advocate rationale + hook> | LinkedIn | [HIGH/MEDIUM/LOW] |\n'}
            linkedin_consumers["skills/career-coach/coach-analysis.md"] += "Review their LinkedIn posts, company blog articles, X/Twitter if public, and any published interviews\nSearch LinkedIn for the company's recruiter or talent team — cross-reference any name visible on the job posting.\n"
            for relative, content in linkedin_consumers.items():
                consumer = source / relative
                consumer.parent.mkdir(parents=True, exist_ok=True)
                consumer.write_text(content + "FUTURE CONSUMER GATE\n")
            intake = source / 'skills/career-engine-intake/SKILL.md'
            intake.parent.mkdir()
            intake.write_text("**Confirmation pass — run immediately after this role's writes, before moving to the next role (this closes the past silent-drop; see the per-role sequencing rule above).**\nFUTURE CONFIRMATION GATE\n")
            database = source / 'skills/database/SKILL.md'
            database.parent.mkdir()
            database.write_text('**Pipeline reads:**\nFUTURE DATABASE GATE\n')
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
                self.assertIn('FUTURE CONFIRMATION GATE', (root / 'plugin' / intake.relative_to(source)).read_text())
                self.assertIn('FUTURE DATABASE GATE', (root / 'plugin' / database.relative_to(source)).read_text())
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
        for path in ('codex/runtime.md', 'chatgpt/runtime.md', 'chatgpt/instructions.txt', 'chatgpt/plugin-skill.md'):
            self.assertIn('references/run-metrics-host.md', (ROOT / path).read_text())
