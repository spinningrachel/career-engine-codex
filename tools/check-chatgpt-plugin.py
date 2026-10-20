#!/usr/bin/env python3
"""Fail closed on stale, incomplete, or malformed ChatGPT Plugins packages."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import zipfile
import yaml

ROOT = Path(__file__).resolve().parents[1]

def check():
    spec = importlib.util.spec_from_file_location('chat_plugin', ROOT/'tools/build-chatgpt-plugin.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    with zipfile.ZipFile(ROOT/'career-engine-chatgpt-plugin.zip') as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)), 'Duplicate plugin entries'
        assert all(n.startswith('career-engine/') and '..' not in Path(n).parts for n in names)
        data = {n.removeprefix('career-engine/'): archive.read(n) for n in names}
        assert data == builder.members(), 'ChatGPT plugin stale/incomplete; rebuild all packages'
        assert all((i.external_attr >> 16) == 0o100644 for i in archive.infolist())
    manifest = json.loads(data['plugin.json'])
    assert manifest['$schema'] == builder.SCHEMA and manifest['name'] == 'career-engine'
    assert re.fullmatch(r'\d+\.\d+\.\d+\+[A-Za-z0-9.-]+', manifest['version'])
    assert not {'skills','interface','apps','mcpServers'} & manifest.keys()
    interface = manifest['extensions']['com.openai']['interface']
    assert 0 < len(interface['shortDescription']) <= 30
    assert isinstance(interface['capabilities'], list)
    skill = data['skills/career-engine/SKILL.md'].decode()
    assert skill.startswith('---\n') and len(skill.encode()) <= 1024*1024
    front = yaml.safe_load(skill.split('---',2)[1])
    assert front['name'] == 'career-engine' and front['description'].strip()
    provenance = json.loads(data['provenance.json'])
    lock = json.loads((ROOT/'upstream-lock.json').read_text())
    assert provenance['upstream_commit'] == lock['commit']
    assert provenance['sha256'] == {n: hashlib.sha256(b).hexdigest() for n,b in data.items() if n!='provenance.json'}
    index = json.loads(data['skills/career-engine/references/source-index.json'])
    for path, info in index.items():
        content = data['skills/career-engine/'+info['knowledge_file']].decode()
        marker = '=== SOURCE: '+path+' ===\n'
        assert content.count(marker) == 1, 'Missing/duplicate source: '+path
    print('ChatGPT plugin offline PASS: portable manifest, skill, complete doctrine, runtime, templates and provenance. Live install: NOT RUN.')

if __name__ == '__main__':
    check()
