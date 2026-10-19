from pathlib import Path
import os
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]

class NativeDistributionTests(unittest.TestCase):
    def test_archive_retains_doctrine_and_executable_qa_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            archive = directory / 'native.zip'
            subprocess.run(['python3', str(ROOT / 'tools/build.py'), '--output', str(archive)], check=True, capture_output=True)
            with zipfile.ZipFile(archive) as bundle:
                for name in ('README.md', 'CLAUDE.md', 'CODEX-RUNTIME.md'):
                    self.assertEqual(bundle.read(name), (ROOT / 'plugin' / name).read_bytes())
                script = 'skills/gatekeeper-checks/scripts/pregate-lint.py'
                self.assertEqual((bundle.getinfo(script).external_attr >> 16) & 0o777, 0o755)
                self.assertEqual((bundle.getinfo('CLAUDE.md').external_attr >> 16) & 0o777, 0o644)
                bundle.extractall(directory / 'installed')
                # Python's extractor does not apply UNIX mode metadata; do what
                # an installer does, then execute a shipped entrypoint directly.
                installed = directory / 'installed' / script
                installed.chmod((bundle.getinfo(script).external_attr >> 16) & 0o777)
                self.assertTrue(os.access(installed, os.X_OK))
                result = subprocess.run([str(installed), '--selftest'], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unpacked_distribution_passes_shipped_mechanical_qa(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            with zipfile.ZipFile(ROOT / 'career-engine-codex.zip') as bundle:
                bundle.extractall(directory)
                for member in bundle.infolist():
                    (directory / member.filename).chmod((member.external_attr >> 16) & 0o777)
            result = subprocess.run(['bash', str(directory / 'scripts/qa-mechanical.sh'), str(directory)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, '\n'.join(line for line in result.stdout.splitlines() if 'FAIL' in line) + result.stderr)
