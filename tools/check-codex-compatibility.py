#!/usr/bin/env python3
"""Check native component resolution, optionally exercising real CLI installation."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]

def native_path(root,value):
    if not isinstance(value,str) or not value.startswith('./'):
        raise ValueError('Native component paths must start with ./')
    path=(root/value).resolve()
    if not path.is_relative_to(root.resolve()) or not path.exists():
        raise ValueError('Native component missing or escapes plugin root: '+value)
    return path

def check(root):
    manifest=json.loads((root/'.codex-plugin/plugin.json').read_text())
    if manifest['name']!='career-engine' or any(k in manifest for k in ('agents','commands','model','tools')):
        raise ValueError('Unsupported native manifest metadata')
    skill_root=native_path(root,manifest['skills'])
    hooks=json.loads(native_path(root,manifest['hooks']).read_text())
    for group in hooks['hooks']['PreToolUse']:
        for hook in group['hooks']:
            command=hook['command']
            if hook['type']!='command' or not command.startswith('python3 "${PLUGIN_ROOT}/scripts/'):
                raise ValueError('Unsupported Codex hook command: '+command)
            path=command.removeprefix('python3 "${PLUGIN_ROOT}/').removesuffix('"')
            native_path(root,'./'+path)
    for doc in (root/'CODEX-RUNTIME.md',root/'CODEX-QA.md'):
        if not doc.is_file():
            raise ValueError('Missing native runtime/QA contract: '+str(doc))
    for agent in (root/'agents').glob('*.md'):
        role=skill_root/('role-'+agent.stem)/'SKILL.md'
        if not role.is_file():
            raise ValueError('Unresolved native role skill: '+agent.stem)
    qa=(skill_root/'role-qa-plugin/SKILL.md').read_text()
    if 'CODEX-QA.md' not in qa or 'compatibility' not in qa:
        raise ValueError('QA role is not routed to Codex compatibility review')
    print('Native manifest, hook commands, role paths, and compatibility QA resolve')

def install():
    if not shutil.which('codex'):
        raise SystemExit('Codex CLI installation gate NOT RUN: codex is unavailable')
    version=subprocess.check_output(['codex','--version'],text=True).strip()
    with tempfile.TemporaryDirectory(prefix='career-codex-install-') as tmp:
        runtime_env=dict(os.environ)
        runtime_env['CODEX_HOME']=tmp
        commands=[['codex','plugin','marketplace','add',str(ROOT),'--json'],['codex','plugin','add','career-engine@cheyfitz-codex','--json']]
        for command in commands:
            result=subprocess.run(command,env=runtime_env,capture_output=True,text=True,check=True)
            outcome=json.loads(result.stdout)
        installed=Path(outcome['installedPath'])
        check(installed)
        lock=json.loads((ROOT/'upstream-lock.json').read_text())
        for name in lock['generated_sha256']:
            if (installed/name).read_bytes()!=(ROOT/'plugin'/name).read_bytes():
                raise ValueError('Installed bundle differs from validated source: '+name)
        print('Actual native CLI installation passed:',version)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--install',action='store_true')
    args=ap.parse_args()
    check(ROOT/'plugin')
    if args.install:
        install()
