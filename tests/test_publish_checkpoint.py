import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

class CheckpointTests(unittest.TestCase):
    def fixture(self, root):
        checkpoint = module('checkpoint-sync')
        checkpoint.ROOT = root
        (root / '.sync-work').mkdir()
        (root / '.sync-work/review-result.json').write_text(json.dumps({'status': 'passed', 'unresolved': []}))
        (root / 'plugin/.codex-plugin').mkdir(parents=True)
        (root / 'plugin/.codex-plugin/plugin.json').write_text('{"version":"fixture"}')
        (root / 'upstream-lock.json').write_text('{"commit":"fixture-upstream"}')
        (root / 'README.md').write_text('reviewed')
        return checkpoint

    def test_retry_restores_reviewed_files_and_deletions_without_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint = self.fixture(root)
            archive = root / 'saved.tar.gz'
            with patch.object(checkpoint.subprocess, 'check_output', return_value='base\n'):
                checkpoint.pack(archive, 'base')
            (root / 'README.md').write_text('stale checkout')
            (root / 'plugin/removed.md').write_text('not in reviewed snapshot')
            checkpoint.restore(archive, 'base')
            self.assertEqual((root / 'README.md').read_text(), 'reviewed')
            self.assertFalse((root / 'plugin/removed.md').exists())
            self.assertTrue((root / 'plugin/.codex-plugin/plugin.json').is_file())
            with self.assertRaisesRegex(ValueError, 'different workflow base'):
                checkpoint.restore(archive, 'advanced-main')

    def test_checkpoint_rejects_failed_review_before_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint = self.fixture(root)
            (root / '.sync-work/review-result.json').write_text('{"status":"blocked","unresolved":[]}')
            with self.assertRaises(ValueError):
                checkpoint.pack(root / 'saved.tar.gz', 'base')

    def test_restore_rejects_protected_paths_links_and_tampering_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkpoint = self.fixture(root)
            original = root / 'saved.tar.gz'
            with patch.object(checkpoint.subprocess, 'check_output', return_value='base\n'):
                checkpoint.pack(original, 'base')
            with tarfile.open(original) as saved:
                files = {m.name: saved.extractfile(m).read() for m in saved.getmembers()}
            for name in ['../escape', '.git/config', 'tools/publish-sync.py', 'README.md']:
                broken = root / 'broken.tar.gz'
                modified = dict(files)
                modified[name] = b'changed'
                with tarfile.open(broken, 'w:gz') as out:
                    for path, data in modified.items():
                        info = tarfile.TarInfo(path)
                        info.size = len(data)
                        out.addfile(info, io.BytesIO(data))
                with self.assertRaises(ValueError):
                    checkpoint.restore(broken, 'base')
                self.assertEqual((root / 'README.md').read_text(), 'reviewed')
            with tarfile.open(root / 'link.tar.gz', 'w:gz') as out:
                info = tarfile.TarInfo('plugin/linked')
                info.type = tarfile.SYMTYPE
                info.linkname = '/tmp/elsewhere'
                out.addfile(info)
            with self.assertRaises(ValueError):
                checkpoint.restore(root / 'link.tar.gz', 'base')

class PublisherTests(unittest.TestCase):
    def test_transient_read_retries_but_push_never_blindly_retries(self):
        publisher = module('publish-sync')
        failure = subprocess.CalledProcessError(128, ['git'], stderr='Could not resolve host: github.com')
        success = subprocess.CompletedProcess([], 0, 'sha refs/heads/main\n', '')
        with patch.object(publisher.subprocess, 'run', side_effect=[failure, success]) as run, patch.object(publisher.time, 'sleep'):
            self.assertEqual(publisher.run('git', 'ls-remote', 'origin', capture_output=True), success)
            self.assertEqual(run.call_count, 2)
        with patch.object(publisher.subprocess, 'run', side_effect=failure) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                publisher.run('git', 'push', 'origin')
            self.assertEqual(run.call_count, 1)
