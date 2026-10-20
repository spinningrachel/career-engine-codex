import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load():
    spec = importlib.util.spec_from_file_location('runtime', ROOT / 'tools/ci-runtime.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class CIRuntimeTests(unittest.TestCase):
    def test_reset_path_uses_prepared_python_and_action_cli_without_downloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'tools').mkdir()
            shutil.copy2(ROOT / 'tools/ci-runtime.py', root / 'tools/ci-runtime.py')
            (root / '.sync-work').mkdir()
            poison = root / 'system-bin'
            poison.mkdir()
            (poison / 'python3').write_text('#!/bin/sh\nexit 77\n')
            (poison / 'python3').chmod(0o755)
            codex = root / 'cache/node/24.1.0/x64/bin/codex'
            codex.parent.mkdir(parents=True)
            codex.write_text('#!/bin/sh\necho codex-test-fixture\n')
            codex.chmod(0o755)
            data = {'python': sys.executable, 'path': str(poison) + ':/usr/bin:/bin', 'tool_cache': str(root / 'cache')}
            (root / '.sync-work/review-runtime.json').write_text(json.dumps(data))
            env = dict(os.environ, PATH=data['path'])
            launcher = root / 'tools/ci-runtime.py'
            # A system interpreter can start the launcher; child commands must
            # use the recorded prepared interpreter rather than the poison PATH.
            system_python = '/usr/bin/python3' if Path('/usr/bin/python3').is_file() else sys.executable
            result = subprocess.run([system_python, str(launcher), 'run', 'python3', '-c', 'import sys; print(sys.executable)'], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(Path(result.stdout.strip()).resolve(), Path(sys.executable).resolve())
            result = subprocess.run([system_python, str(launcher), 'check'], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('codex-test-fixture', result.stdout)

    def test_missing_tools_fail_explicitly(self):
        runtime = load()
        with self.assertRaisesRegex(RuntimeError, 'Prepared Python'):
            runtime.environment({'python': '/nonexistent/prepared/python', 'path': '/nonexistent'})
        with self.assertRaisesRegex(RuntimeError, 'Codex CLI unavailable'):
            runtime.environment({'python': sys.executable, 'path': '/nonexistent'})

    def test_workflow_records_runtime_before_the_review_and_protects_launcher(self):
        import yaml
        flow = yaml.load((ROOT / '.github/workflows/sync-upstream.yml').read_text(), Loader=yaml.BaseLoader)
        steps = flow['jobs']['review']['steps']
        setup = next(i for i,s in enumerate(steps) if 'tools/ci-runtime.py record' in s.get('run', ''))
        review = next(i for i,s in enumerate(steps) if s.get('name') == 'Review and adapt with Codex')
        self.assertLess(setup, review)
        final = next(s for s in steps if s.get('name') == 'Require review and rerun validation')
        self.assertIn('git diff --exit-code -- tools/ci-runtime.py', final['run'])
