"""Negative cases for the October upstream install and unattended-run fixes."""
import json
import os
import importlib.util
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugin'


class UpstreamCompatibilityTests(unittest.TestCase):
    def test_detailed_word_limit_counts_unicode_and_excludes_comments(self):
        spec = importlib.util.spec_from_file_location(
            'pregate_length_fixture', PLUGIN / 'skills/gatekeeper-checks/scripts/pregate-lint.py')
        lint = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = lint
        try:
            spec.loader.exec_module(lint)
            for word in ('word', 'שלום', '中文'):
                with self.subTest(word=word):
                    lines = [word + ' | -'] * 890
                    self.assertEqual(lint.count_cv_words(lines), 890)
                    self.assertEqual(lint.check_cv_length_limits(lines), [])
                    hits = lint.check_cv_length_limits(lines + [word])
                    self.assertEqual([hit.check_id for hit in hits], ['CV-TOTAL-WORDCOUNT'])
            self.assertEqual(lint.count_cv_words([
                'visible <!-- hidden', 'hidden', 'hidden --> visible',
                '## EDUCATION', 'excluded words', '## EXPERIENCE', 'counted']), 4)
        finally:
            sys.modules.pop(spec.name, None)

    def test_detailed_length_gate_runs_outside_plugin_directory(self):
        gate = (PLUGIN / 'skills/gatekeeper-checks/cv-gates.md').read_text()
        command = gate.split('Run `', 1)[1].split('`', 1)[0]
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / 'cv.md'
            # Avoid summary-specific limits: this checks the new whole-CV gate.
            draft.write_text('## EXPERIENCE\n' + 'word ' * 891 + '\n')
            result = subprocess.run(
                ['bash', '-c', command.replace('<staged CV>', '"' + str(draft) + '"')],
                cwd=tmp, env={**os.environ, 'CAREER_ENGINE_ROOT': str(PLUGIN)},
                capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('CV-TOTAL-WORDCOUNT', result.stdout + result.stderr)
            self.assertNotIn("can't open file", result.stderr)

    def test_frontmatter_gate_rejects_installer_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'agents').mkdir()
            agent = root / 'agents/fixture.md'
            cases = [
                ('---\nname: fixture\ndescription: "Use: the confirmed title"\n---\n', 0),
                ('---\nname: fixture\ndescription: "Use "this" title"\n---\n', 1),
                ('---\nname: fixture\ndescription: first\ndescription: second\n---\n', 1),
                ('Retired banner\n---\nname: fixture\ndescription: fixture\n---\n', 1),
                ('---\nname: fixture\n---\n', 1),
            ]
            for content, expected in cases:
                with self.subTest(content=content):
                    agent.write_text(content)
                    result = subprocess.run(
                        ['python3', str(PLUGIN / 'scripts/check-frontmatter.py'), tmp],
                        capture_output=True, text=True)
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)

    def test_native_question_gate_preserves_unattended_write_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            transcript = Path(tmp) / 'transcript.jsonl'
            run = {'type': 'response_item', 'payload': {
                'type': 'function_call', 'name': 'functions.exec_command',
                'arguments': json.dumps({'cmd': 'mkdir -p /tmp/fixture/_pipeline; '
                                              'touch /tmp/fixture/_pipeline/state.json'})}}
            pasted = {'type': 'response_item', 'payload': {
                'type': 'message', 'role': 'user', 'content': json.dumps(run)}}
            cases = [
                (run, 'I am holding off writing the score. Which number should I write?', True),
                (run, 'The role is not a job listing. Is it your call?', True),
                (run, 'Can you paste the three JDs so I can score them?', True),
                (run, 'database_id is missing. Where is the required config?', False),
                (pasted, 'Can you paste the three JDs so I can score them?', False),
            ]
            for event, question, deny in cases:
                with self.subTest(question=question, event=event):
                    transcript.write_text(json.dumps(event) + '\n')
                    payload = {'tool_name': 'request_user_input_async',
                               'tool_input': {'questions': [{'title': question}]},
                               'transcript_path': str(transcript), 'cwd': tmp}
                    result = subprocess.run(
                        ['python3', str(PLUGIN / 'scripts/codex-question-gate.py')],
                        input=json.dumps(payload), capture_output=True, text=True, check=True)
                    if deny:
                        self.assertEqual(json.loads(result.stdout)['hookSpecificOutput']
                                         ['permissionDecision'], 'deny')
                    else:
                        self.assertEqual(result.stdout, '')

