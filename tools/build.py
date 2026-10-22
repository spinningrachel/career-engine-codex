#!/usr/bin/env python3
"""Build a Codex plugin archive, refusing personal data in text or Office XML."""
import argparse
import importlib.util
import io
from pathlib import Path
import re
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def package(output):
    plugin=ROOT/'plugin'
    spec=importlib.util.spec_from_file_location('pdd',plugin/'scripts/personal_data_detect.py')
    pdd=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pdd)
    members=[]
    hits=[]
    for path in sorted(plugin.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts or path.suffix=='.pyc':
            continue
        rel=path.relative_to(plugin).as_posix()
        if pdd.is_stray_output_file(path.name):
            hits.append(rel+': personal output file')
            continue
        blob=path.read_bytes()
        if path.suffix in ('.dotx','.docx','.dotm','.xlsx','.pptx'):
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                text='\n'.join(re.sub('<[^>]+>',' ',z.read(n).decode('utf-8')) for n in z.namelist() if n.endswith('.xml'))
        else:
            try:
                text=blob.decode('utf-8')
            except UnicodeDecodeError:
                text=''
        for line,name,match,why in pdd.scan_text(text,rel,max_hits=3):
            hits.append(f'{rel}:{line}: {name}: {why}')
        # Test harnesses are validated in source and omitted from product packaging.
        if path.name.startswith(('test-','test_')) or 'test-fixtures' in path.parts:
            continue
        # These documents are inputs to shipped doctrine QA. CODEX-RUNTIME.md
        # supplies the host mapping for their upstream installation procedures.
        mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
        members.append((rel,blob,mode))
    if hits:
        raise SystemExit('Packaging blocked:\n'+'\n'.join(hits))
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for rel,blob,mode in members:
            info=zipfile.ZipInfo(rel,date_time=(2026,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3
            info.external_attr=(0o100000 | mode)<<16
            z.writestr(info,blob)
    print('Built',output,'with',len(members),'files; personal-data scan passed')

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,help='Build only the Codex archive at this path; omission builds both published packages')
    args=ap.parse_args()
    package(args.output or ROOT/'career-engine-codex.zip')
    if args.output is None:
        spec=importlib.util.spec_from_file_location('chatgpt_builder',ROOT/'tools/build-chatgpt.py')
        builder=importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
        builder.build(ROOT/'career-engine-chatgpt.zip')

        spec=importlib.util.spec_from_file_location("chatgpt_plugin_builder",ROOT/"tools/build-chatgpt-plugin.py")
        plugin_builder=importlib.util.module_from_spec(spec); spec.loader.exec_module(plugin_builder)
        plugin_builder.build(ROOT/"career-engine-chatgpt-plugin.zip")
