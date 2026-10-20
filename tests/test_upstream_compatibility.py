"""Negative cases for the October upstream install and unattended-run fixes."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugin'


class UpstreamCompatibilityTests(unittest.TestCase):
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

