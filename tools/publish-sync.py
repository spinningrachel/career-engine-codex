#!/usr/bin/env python3
"""Publish a reviewed sync branch and create/update its pull request."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]

def run(*args,**kwargs):
    captured = kwargs.pop('capture_output', False)
    read_remote = args[:2] == ('git','ls-remote') or args[:3] in (('gh','pr','list'), ('gh','pr','view'))
    transient = ('could not resolve host', 'temporary failure in name resolution',
                 'eai_again', 'connection timed out', 'failed to connect', 'connection reset')
    for attempt in range(3):
        try:
            result = subprocess.run(args,cwd=ROOT,check=True,text=True,capture_output=True,timeout=120,**kwargs)
        except subprocess.CalledProcessError as exc:
            message = exc.stderr or ''
            token = os.environ.get('GH_TOKEN')
            if token:
                message = message.replace(token, '***')
            print(message, file=sys.stderr)
            if read_remote and attempt < 2 and any(term in message.lower() for term in transient):
                time.sleep(2 ** (attempt + 1))
                continue
            raise
        except subprocess.TimeoutExpired:
            print('Command exceeded the 120-second publishing limit.', file=sys.stderr)
            raise
        if not captured:
            print(result.stdout, end='')
            print(result.stderr, end='', file=sys.stderr)
        return result


def wait_for_validation(head, timeout=1200):
    """Require the PR validation workflow and its validate job on this exact head."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        runs = json.loads(run(
            'gh', 'run', 'list', '--workflow', 'validate.yml',
            '--branch', 'sync/upstream', '--commit', head, '--event', 'pull_request',
            '--limit', '20', '--json', 'databaseId,status,conclusion,headSha',
            capture_output=True).stdout)
        matching = [item for item in runs if item['headSha'] == head]
        if matching:
            latest = max(matching, key=lambda item: item['databaseId'])
            if latest['status'] == 'completed':
                if latest['conclusion'] != 'success':
                    raise SystemExit('PR validation did not pass; leaving the PR open. '
                                     'Inspect the run and approve workflows if required.')
                details = json.loads(run(
                    'gh', 'run', 'view', str(latest['databaseId']),
                    '--json', 'jobs', capture_output=True).stdout)
                jobs = [job for job in details['jobs'] if job['name'] == 'validate']
                if len(jobs) != 1 or jobs[0]['conclusion'] != 'success':
                    raise SystemExit('Validation job did not succeed; leaving the PR open.')
                return
            if latest['status'] in ('waiting', 'action_required'):
                raise SystemExit('PR validation requires approval; leaving the PR open. '
                                 'Approve workflows in GitHub, then rerun the sync.')
        time.sleep(10)
    raise SystemExit('Timed out waiting for PR validation; leaving the PR open. '
                     'Check GitHub for a pending workflow approval.')

def main():
    result=json.loads((ROOT/'.sync-work/review-result.json').read_text())
    if result['status']!='passed' or result['unresolved']:
        raise SystemExit('Codex review blocked this update; inspect review-result.json')
    sha=json.loads((ROOT/'upstream-lock.json').read_text())['commit']
    title='Sync career-engine upstream '+sha[:12]
    body=result['summary']+'\n\nUpstream commit: `'+sha+'`.\n\nValidation: native installation/package checks, ChatGPT kit and portable export fixtures, upstream export fixtures, personal-data guard, mechanical/parity QA, and archive scan passed. Live ChatGPT UI, personal-data, and connector workflows were not exercised.\n\nGenerated and reviewed by Codex; merge follows the configured automatic-merge policy and repository protections.\n'
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
    run('git','add','plugin','codex/overrides','tools/port.py','tests','upstream-lock.json','LICENSE','career-engine-codex.zip','career-engine-chatgpt.zip', 'career-engine-chatgpt-plugin.zip', 'chatgpt-plugin-version.json','chatgpt','README.md')
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
        wait_for_validation(head)
        if run('git','ls-remote','origin','refs/heads/main',capture_output=True).stdout.split()[0]!=base:
            raise SystemExit('main changed during PR validation; leaving the PR open')
        current=json.loads(run('gh','pr','view',str(number),'--json','headRefOid,state',capture_output=True).stdout)
        if current['state']!='OPEN' or current['headRefOid']!=head:
            raise SystemExit('PR changed during validation; refusing to merge')
        # GitHub enforces branch protections; never use --admin or bypass checks.
        run('gh','pr','merge',str(number),'--squash','--match-head-commit',head)

if __name__=='__main__':
    main()
