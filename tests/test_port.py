import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile
import importlib.util
import io
import shutil

ROOT=Path(__file__).resolve().parents[1]
PLUGIN=ROOT/'plugin'

class PortTests(unittest.TestCase):
    def test_generated_provenance(self):
        lock=json.loads((ROOT/'upstream-lock.json').read_text())
        self.assertRegex(lock['commit'],r'^[0-9a-f]{40}$')
        actual={str(p.relative_to(PLUGIN)):hashlib.sha256(p.read_bytes()).hexdigest() for p in PLUGIN.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
        self.assertEqual(lock['generated_sha256'],actual)

    def test_skills_have_runtime_and_role_documents(self):
        skills=list((PLUGIN/'skills').glob('*/SKILL.md'))
        self.assertGreaterEqual(len(skills),40)
        for p in skills:
            text=p.read_text()
            self.assertTrue(text.startswith('---\n'),p)
            self.assertIn('description:',text.split('\n---',1)[0],p)
            self.assertIn('CODEX-RUNTIME.md',text,p)
        for p in (PLUGIN/'agents').glob('*.md'):
            self.assertTrue((PLUGIN/'skills'/('role-'+p.stem)/'SKILL.md').is_file(),p)

    def test_native_hook_adapts_real_tool_inputs(self):
        hook=PLUGIN/'scripts/codex-personal-data-hook.py'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'.codex-plugin').mkdir()
            (root/'.codex-plugin/plugin.json').write_text('{"name":"test"}')
            content='output_folder: /U'+'sers/fixture/Documents/out'
            cases=[
                ('apply_patch',f'*** Begin Patch\n*** Add File: references/profile.md\n+{content}\n*** End Patch',2),
                ('functions.apply_patch',{'input':f'*** Begin Patch\n*** Update File: references/profile.md\n@@\n+{content}\n*** End Patch'},2),
                ('functions.exec_command',{'cmd':f'echo "{content}" > references/profile.md','workdir':tmp},2),
                ('exec_command',{'cmd':'git status','workdir':tmp},0),
                ('apply_patch',f'*** Begin Patch\n*** Add File: references/profile.md\n+{{{{USER_FULL_NAME}}}}\n*** End Patch',0),
                ('apply_patch',f'*** Begin Patch\n*** Add File: /tmp/outside-career-fixture.md\n+{content}\n*** End Patch',0),
            ]
            for tool,args,expected in cases:
                with self.subTest(tool=tool,args=args):
                    result=subprocess.run(['python3',str(hook)],input=json.dumps({'tool_name':tool,'tool_input':args,'cwd':tmp}),text=True,capture_output=True)
                    self.assertEqual(result.returncode,expected,result.stderr)

    def test_archive_contains_native_plugin_and_no_test_harness(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive=Path(tmp)/'plugin.zip'
            subprocess.run(['python3',str(ROOT/'tools/build.py'),'--output',str(archive)],check=True)
            with zipfile.ZipFile(archive) as z:
                names=z.namelist()
                self.assertIn('.codex-plugin/plugin.json',names)
                self.assertIn('CODEX-RUNTIME.md',names)
                self.assertIn('CODEX-QA.md',names)
                self.assertFalse(any(Path(n).name.startswith(('test-','test_')) for n in names))
                self.assertFalse(any('.claude' in n for n in names))

    def test_committed_archive_matches_reproducible_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive=Path(tmp)/'plugin.zip'
            subprocess.run(['python3',str(ROOT/'tools/build.py'),'--output',str(archive)],check=True)
            self.assertEqual(archive.read_bytes(),(ROOT/'career-engine-codex.zip').read_bytes(),'Plugin archive is stale; rebuild and commit it with the source')

    def test_native_path_rejects_missing_and_escaping_components(self):
        spec=importlib.util.spec_from_file_location('native_qa',ROOT/'tools/check-codex-compatibility.py')
        native_qa=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(native_qa)
        self.assertEqual(native_qa.native_path(PLUGIN,'./skills'),PLUGIN/'skills')
        for value in ('skills','./missing-component','./../README.md'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                native_qa.native_path(PLUGIN,value)

    def test_qa_entrypoints_focus_on_codex_compatibility(self):
        for p in [PLUGIN/'skills/role-qa-plugin/SKILL.md',PLUGIN/'agents/qa-plugin.md']:
            text=p.read_text()
            self.assertIn('CODEX-QA.md',text,p)
            self.assertIn('Codex compatibility',text,p)
        self.assertIn('CODEX-QA.md',(ROOT/'codex/sync-review.md').read_text())

    def test_repository_scan_rejects_user_data_inside_archived_office_xml(self):
        spec=importlib.util.spec_from_file_location('repo_scan',ROOT/'tools/scan-repo.py')
        repo_scan=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(repo_scan)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            subprocess.run(['git','init','-q',str(root)],check=True)
            (root/'plugin/scripts').mkdir(parents=True)
            shutil.copy2(PLUGIN/'scripts/personal_data_detect.py',root/'plugin/scripts/personal_data_detect.py')
            office=io.BytesIO()
            with zipfile.ZipFile(office,'w') as z:
                z.writestr('word/document.xml','<p>output_folder: /U'+'sers/fixture/Documents/out</p>')
            with zipfile.ZipFile(root/'product.zip','w') as z:
                z.writestr('references/template.docx',office.getvalue())
            repo_scan.ROOT=root
            with self.assertRaises(SystemExit) as failure:
                repo_scan.scan()
            self.assertIn('product.zip!references/template.docx',str(failure.exception))

    def test_question_gate_understands_codex_transcript(self):
        hook=PLUGIN/'scripts/codex-question-gate.py'
        with tempfile.TemporaryDirectory() as tmp:
            transcript=Path(tmp)/'transcript.jsonl'
            patch='*** Begin Patch\n*** Add File: /tmp/run/_pipeline/state.json\n+{}\n*** End Patch'
            call={'type':'response_item','payload':{'type':'custom_tool_call','name':'apply_patch','input':patch}}
            for event,question,deny in [
                (call,'Should I continue with the remaining roles?',True),
                (call,'The output_folder is missing. How should I proceed?',False),
                ({'type':'response_item','payload':{'type':'message','role':'user','content':'I wrote /tmp/run/_pipeline/state.json'}},'Should I continue?',False),
                (call,'Which of these career facts is accurate?',False),
            ]:
                with self.subTest(question=question,event=event):
                    transcript.write_text(json.dumps(event)+'\n')
                    payload={'tool_name':'request_user_input_async','tool_input':{'questions':[{'title':question}]},'cwd':tmp,'transcript_path':str(transcript)}
                    result=subprocess.run(['python3',str(hook)],input=json.dumps(payload),text=True,capture_output=True,check=True)
                    if deny:
                        self.assertEqual(json.loads(result.stdout)['hookSpecificOutput']['permissionDecision'],'deny')
                    else:
                        self.assertEqual(result.stdout,'')
