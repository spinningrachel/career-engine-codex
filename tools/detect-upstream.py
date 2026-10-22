#!/usr/bin/env python3
"""Fetch upstream and emit GitHub output; no-op if already ported/pending."""
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def git(*args,cwd=ROOT):
    return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()

def detect():
    old=json.loads((ROOT/'upstream-lock.json').read_text())['commit']
    work=ROOT/'.sync-work'
    work.mkdir(exist_ok=True)
    upstream=work/'upstream'
    if not upstream.exists():
        subprocess.run(['git','clone','--depth','1','https://github.com/spinningrachel/career-engine-claude.git',str(upstream)],check=True)
    else:
        subprocess.run(['git','fetch','--depth','1','origin','main'],cwd=upstream,check=True)
        subprocess.run(['git','checkout','--detach','FETCH_HEAD'],cwd=upstream,check=True)
    new=git('rev-parse','HEAD',cwd=upstream)
    changed=new!=old
    # A branch alone is not delivery: publication may have failed after push.
    # Skip paid review only for an actual open PR against this same main base.
    pending=subprocess.run(['git','fetch','origin','refs/heads/sync/upstream'],cwd=ROOT,capture_output=True,text=True)
    if pending.returncode==0:
        pending_lock=json.loads(git('show','FETCH_HEAD:upstream-lock.json'))
        based_on_main = subprocess.run(['git','merge-base','--is-ancestor','HEAD','FETCH_HEAD'],cwd=ROOT).returncode == 0
        if pending_lock['commit']==new and based_on_main and pending_pr_matches(git('rev-parse','FETCH_HEAD'), git('rev-parse','HEAD')):
            changed=False
            print('An open sync PR already contains this upstream version on the current base.')
    if changed:
        subprocess.run(['git','fetch','--depth','1','origin',old],cwd=upstream,check=True)
        (work/'upstream.diff').write_text(git('diff',old,new,'--',cwd=upstream)+'\n')
    output=f'changed={str(changed).lower()}\nupstream_sha={new}\n'
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a') as f:
            f.write(output)
    print(output,end='')

def pending_pr_matches(head, base):
    result = subprocess.run(['gh','pr','list','--repo','spinningrachel/career-engine-codex',
                             '--head','sync/upstream','--base','main','--state','open',
                             '--json','headRefOid,baseRefOid'], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Cannot determine whether sync has an open PR: ' + result.stderr)
    return any(pr['headRefOid'] == head and pr['baseRefOid'] == base for pr in json.loads(result.stdout))

if __name__=='__main__':
    detect()
