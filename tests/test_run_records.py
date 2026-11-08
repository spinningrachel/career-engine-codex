"""Exercise shipped workbook runtimes and the report/cleanup host contracts."""
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'plugin/skills/run-records/scripts/xlsx_log.py'


class RunRecordsTests(unittest.TestCase):
    def run_helper(self, helper, *args, success=True):
        result = subprocess.run([sys.executable, str(helper), *map(str, args)],
                                capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0)
        return result

    def test_all_shipped_helpers_initialize_update_and_read_back_without_duplicates(self):
        helpers = [('native', HELPER.read_bytes())]
        for archive, member in (
            ('career-engine-chatgpt.zip', 'runtime/xlsx_log.py.txt'),
            ('career-engine-chatgpt-plugin.zip', 'career-engine/skills/career-engine/runtime/xlsx_log.py.txt'),
        ):
            with zipfile.ZipFile(ROOT / archive) as package:
                helpers.append((archive, package.read(member)))
        for distribution, source in helpers:
            with self.subTest(distribution=distribution), tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(source, HELPER.read_bytes())
                root = Path(tmp)
                helper = root / 'xlsx_log.py'
                helper.write_bytes(source)
                book = root / 'log.xlsx'
                self.run_helper(helper, 'init', book)
                original = book.read_bytes()
                self.run_helper(helper, 'init', book, success=False)
                self.assertEqual(book.read_bytes(), original)
                heads = self.run_helper(helper, 'headers', book)
                self.assertIn('Roles processed', heads['Runs'])
                self.assertIn('Company', heads['Applications'])
                row = {'Run': 'Intake 2026-11-08', 'Mode': 'Intake', 'Roles processed': 2}
                for count, action in ((2, 'created'), (3, 'updated')):
                    row['Roles processed'] = count
                    response = self.run_helper(helper, 'upsert', book, 'Runs', '--key-cols', 'Run', '--row', json.dumps(row))
                    self.assertEqual(response['action'], action)
                app = {'Company': 'Fixture Company', 'Role': 'Fixture role', 'Run': row['Run'], 'Status': 'Needs Research'}
                for action in ('created', 'updated'):
                    response = self.run_helper(helper, 'upsert', book, 'Applications', '--key-cols', 'Company,Role,Run', '--row', json.dumps(app))
                    self.assertEqual(response['action'], action)
                wb = openpyxl.load_workbook(book)
                self.assertEqual(wb['Runs'].max_row, 2)
                self.assertEqual(wb['Applications'].max_row, 2)
                for sheet, expected in (('Runs', row), ('Applications', app)):
                    actual = dict(zip(heads[sheet], next(wb[sheet].iter_rows(min_row=2, max_row=2, values_only=True))))
                    for key, value in expected.items():
                        self.assertEqual(actual[key], value)
                wb.close()

    def test_flexible_schema_preserves_columns_unmapped_values_and_existing_cells(self):
        with tempfile.TemporaryDirectory() as tmp:
            book = Path(tmp) / 'custom.xlsx'
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = 'My runs'
            ws.append(['Notes', 'Run', None, 'Count'])
            ws.append(['Keep this note', 'Intake fixture', 'User-owned value', 1])
            wb.save(book)
            wb.close()
            response = self.run_helper(HELPER, 'upsert', book, 'My runs', '--key-cols', 'Run', '--row', json.dumps({'Run': 'Intake fixture', 'Count': 4, 'Unmapped': 'never add a column'}))
            self.assertEqual(response['unmapped'], ['Unmapped'])
            wb = openpyxl.load_workbook(book)
            self.assertEqual(wb.sheetnames, ['My runs'])
            self.assertEqual(list(wb.active.values), [('Notes', 'Run', None, 'Count'), ('Keep this note', 'Intake fixture', 'User-owned value', 4)])
            wb.close()
            before = book.read_bytes()
            self.run_helper(HELPER, 'upsert', book, 'My runs', '--key-cols', 'Missing key', '--row', '{}', success=False)
            self.assertEqual(book.read_bytes(), before)
            missing = Path(tmp) / 'missing.xlsx'
            self.run_helper(HELPER, 'upsert', missing, 'Runs', '--key-cols', 'Run', '--row', '{"Run":"fixture"}', success=False)
            self.assertFalse(missing.exists())
            self.run_helper(HELPER, 'upsert', missing, 'Runs', '--key-cols', 'Run', '--row', '{"Run":"fixture"}', '--create-default')
            wb = openpyxl.load_workbook(missing)
            self.assertEqual(wb['Runs'].cell(2, 1).value, 'fixture')
            wb.close()

    def test_chatgpt_can_import_packaged_helper_without_shell(self):
        with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(ROOT / 'career-engine-chatgpt.zip') as kit:
            helper = Path(tmp) / 'xlsx_log.py'
            helper.write_bytes(kit.read('runtime/xlsx_log.py.txt'))
            spec = importlib.util.spec_from_file_location('private_workbook_helper', helper)
            runtime = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(runtime)
            book = Path(tmp) / 'private.xlsx'
            runtime.cmd_init(str(book))
            runtime.cmd_upsert(str(book), 'Runs', ['Run'], {'Run': 'Synthetic run', 'Roles processed': 1}, False)
            wb = openpyxl.load_workbook(book)
            self.assertEqual(wb['Runs'].cell(2, 1).value, 'Synthetic run')
            self.assertEqual(wb['Runs'].cell(2, 5).value, 1)
            wb.close()

    def test_host_contract_preserves_report_destination_readback_and_interrupted_state(self):
        mapping = (ROOT / 'plugin/references/run-records-host.md').read_text()
        for required in ('Interrupted runs delete nothing', 'reopen the actual workbook', 'before removing that track', 'birth time is unavailable', 'no subdirectories', 'cmd_upsert', 'private Data Analysis'):
            self.assertIn(required, mapping)
        metrics = (ROOT / 'plugin/references/run-metrics-host.md').read_text()
        self.assertIn('directly in the private external `agent_data_folder`', metrics)
        self.assertNotIn('in the external run output folder', metrics)
        for consumer in ('skills/run-records/SKILL.md', 'skills/career-engine-setup/SKILL.md'):
            self.assertIn('references/run-records-host.md', (ROOT / 'plugin' / consumer).read_text())
        for consumer in ('skills/career-engine-orchestrator/orchestrator-post-run.md', 'skills/career-engine-edit/SKILL.md', 'skills/career-engine-intake/SKILL.md'):
            self.assertIn('skills/run-records/SKILL.md', (ROOT / 'plugin' / consumer).read_text())
        post = (ROOT / 'plugin/skills/career-engine-orchestrator/orchestrator-post-run.md').read_text()
        self.assertIn('only then run Step 10', post)
        self.assertNotIn('because the Stop hook finds the file', post)
        for path in ('codex/runtime.md', 'chatgpt/runtime.md'):
            self.assertIn('references/run-records-host.md', (ROOT / path).read_text())


if __name__ == '__main__':
    unittest.main()
