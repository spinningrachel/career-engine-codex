import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    spec = importlib.util.spec_from_file_location('fixture', ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class RecoveryTests(unittest.TestCase):
    def test_branch_without_open_matching_pr_does_not_suppress_update(self):
        detect = load('tools/detect-upstream.py')
        cases = [([], False),
                 ([{'headRefOid': 'head', 'baseRefOid': 'base'}], True),
                 ([{'headRefOid': 'other', 'baseRefOid': 'base'}], False),
                 ([{'headRefOid': 'head', 'baseRefOid': 'old'}], False)]
        for prs, expected in cases:
            with self.subTest(prs=prs), patch.object(detect.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(prs), '')):
                self.assertEqual(detect.pending_pr_matches('head', 'base'), expected)
        with patch.object(detect.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '', 'permission denied')):
            with self.assertRaisesRegex(RuntimeError, 'Cannot determine'):
                detect.pending_pr_matches('head', 'base')

    def test_native_version_rejects_stale_or_missing_cache_key(self):
        checker = load('codex/native-version.py')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '.codex-plugin').mkdir()
            (root / 'UPSTREAM.md').write_text('Commit: ' + 'a' * 40 + '\n')
            manifest = root / '.codex-plugin/plugin.json'
            version = '1.0.0+upstream.' + 'a' * 12 + '.codex.' + 'b' * 12
            manifest.write_text(json.dumps({'name': 'career-engine', 'version': version}))
            checker.check(root)
            for bad in ['', '1.0.0', version.replace('upstream.a', 'upstream.c')]:
                manifest.write_text(json.dumps({'name': 'career-engine', 'version': bad}))
                with self.assertRaises(ValueError):
                    checker.check(root)

    def test_repairable_preflight_keeps_final_validation_blocking(self):
        import yaml
        flow = yaml.load((ROOT / '.github/workflows/sync-upstream.yml').read_text(), Loader=yaml.BaseLoader)
        steps = flow['jobs']['sync']['steps']
        preflight = next(s for s in steps if s.get('id') == 'preflight')
        self.assertEqual(preflight['continue-on-error'], 'true')
        self.assertEqual(preflight['shell'], 'bash')  # GitHub's explicit bash enables pipefail for tee.
        final = next(s for s in steps if s.get('name') == 'Require review and rerun validation')
        self.assertNotIn('continue-on-error', final)
        self.assertIn('bash tools/validate.sh', final['run'])
        self.assertIn('git diff --exit-code', final['run'])
        self.assertLess(steps.index(final), next(i for i,s in enumerate(steps) if s.get('name') == 'Open the reviewed update PR'))
        review = next(s for s in steps if s.get('name') == 'Review and adapt with Codex')
        self.assertLess(int(review['timeout-minutes']), int(flow['jobs']['sync']['timeout-minutes']))
