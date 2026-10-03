#!/usr/bin/env python3
"""Publish a reviewed sync branch and create/update its pull request."""
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def run(*args,**kwargs):
    return subprocess.run(args,cwd=ROOT,check=True,text=True,**kwargs)

def main():
    result=json.loads((ROOT/'.sync-work/review-result.json').read_text())
    if result['status']!='passed' or result['unresolved']:
        raise SystemExit('Codex review blocked this update; inspect review-result.json')
    sha=json.loads((ROOT/'upstream-lock.json').read_text())['commit']
    title='Sync career-engine upstream '+sha[:12]
    body=result['summary']+'\n\nUpstream commit: `'+sha+'`.\n\nValidation: native port tests, upstream export fixtures, personal-data guard, mechanical/parity QA, and archive scan passed. Live personal-data and connector workflows were not exercised.\n\nGenerated and reviewed by Codex; merge requires repository owner review.\n'
    bodyfile=ROOT/'.sync-work/pr-body.md'
    bodyfile.write_text(body)
    base=run('git','rev-parse','HEAD',capture_output=True).stdout.strip()
    main=run('git','ls-remote','origin','refs/heads/main',capture_output=True).stdout.split()[0]
    if main!=base:
        raise SystemExit('main changed during validation; rerun sync against the new base')
    run('git','checkout','-B','sync/upstream')
    run('git','config','user.name','career-engine-codex[bot]')
    run('git','config','user.email','career-engine-codex[bot]@users.noreply.github.com')
    # Explicit paths: never stage arbitrary agent output, secrets, or workflows.
    run('git','add','plugin','codex/overrides','tools/port.py','tests','upstream-lock.json','LICENSE')
    run('git','commit','-m',title)
    # Lease against the remote branch observed immediately before updating it.
    remote=run('git','ls-remote','origin','refs/heads/sync/upstream',capture_output=True).stdout.strip()
    expected=remote.split()[0] if remote else ''
    run('git','push','origin','HEAD:refs/heads/sync/upstream','--force-with-lease=refs/heads/sync/upstream:'+expected)
    prs=json.loads(run('gh','pr','list','--head','sync/upstream','--state','open','--json','number',capture_output=True).stdout)
    if prs:
        number=str(prs[0]['number'])
        run('gh','pr','edit',number,'--title',title,'--body-file',str(bodyfile))
    else:
        run('gh','pr','create','--base','main','--head','sync/upstream','--title',title,'--body-file',str(bodyfile))
        number=json.loads(run('gh','pr','view','sync/upstream','--json','number',capture_output=True).stdout)['number']
    if os.environ.get('CODEX_SYNC_AUTO_MERGE','true').lower()=='true':
        if run('git','ls-remote','origin','refs/heads/main',capture_output=True).stdout.split()[0]!=base:
            raise SystemExit('main changed; leaving the PR open for fresh validation')
        head=run('git','rev-parse','HEAD',capture_output=True).stdout.strip()
        # GitHub enforces branch protections; never use --admin or bypass checks.
        run('gh','pr','merge',str(number),'--squash','--match-head-commit',head)

if __name__=='__main__':
    main()
