#!/usr/bin/env python3
"""Scan every publishable repository file, including Office XML, for user data."""
import importlib.util
import io
from pathlib import Path
import re
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def scan():
    spec=importlib.util.spec_from_file_location('pdd',ROOT/'plugin/scripts/personal_data_detect.py')
    pdd=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pdd)
    # Git's ignore rules define publishable files; include new untracked source.
    names=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).decode().split('\0')
    hits=[]
    def inspect(blob,name,rel,depth=0):
        if depth>4:
            hits.append(name+': archive nesting exceeds inspection limit')
            return
        suffix=Path(name).suffix.lower()
        if suffix in ('.zip','.plugin','.skill'):
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                for member in z.namelist():
                    if member.endswith('/'):
                        continue
                    if 'career-data' in Path(member).parts or Path(member).name=='career-data-marker.json':
                        hits.append(name+'!'+member+': external career-data bundled')
                    if pdd.is_stray_output_file(Path(member).name):
                        hits.append(name+'!'+member+': stray career-data output')
                    inspect(z.read(member),name+'!'+member,member,depth+1)
            return
        if suffix in ('.dotx','.dotm','.docx','.xlsx','.pptx'):
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                text='\n'.join(re.sub('<[^>]+>',' ',z.read(n).decode()) for n in z.namelist() if n.endswith('.xml'))
        else:
            try:
                text=blob.decode('utf-8')
            except UnicodeDecodeError:
                return
        for line,det,match,why in pdd.scan_text(text,rel,max_hits=3):
            hits.append(f'{name}:{line}: {det}: {why}')
    for name in dict.fromkeys(n for n in names if n):
        path=ROOT/name
        if not path.is_file():
            continue
        if pdd.is_stray_output_file(path.name):
            hits.append(name+': stray career-data output')
        blob=path.read_bytes()
        rel=name.removeprefix('plugin/')
        inspect(blob,name,rel)
    if hits:
        raise SystemExit('Repository scan blocked publication:\n'+'\n'.join(hits))
    print('Repository personal-data scan passed (text and Office XML)')

if __name__=='__main__':
    scan()
