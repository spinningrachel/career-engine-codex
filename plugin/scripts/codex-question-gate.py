#!/usr/bin/env python3
"""Adapt Codex question/transcript payloads to the canonical upstream gate."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent

def main():
    try:
        data=json.load(sys.stdin)
    except (ValueError,TypeError):
        return 0
    name=str(data.get('tool_name','')).split('.')[-1]
    if name not in ('request_user_input','request_user_input_async','AskUserQuestion'):
        return 0
    args=data.get('tool_input') or {}
    if isinstance(args,str):
        args=json.loads(args)
    questions=[]
    for q in args.get('questions',[]):
        if not isinstance(q,dict):
            continue
        questions.append({'question':q.get('question',q.get('title','')),'header':q.get('header',''),'options':[o if isinstance(o,dict) else {'label':o} for o in q.get('options',[])]})
    path=data.get('transcript_path')
    if not path or not Path(path).is_file():
        return 0
    spec=importlib.util.spec_from_file_location('adapter',HERE/'codex-personal-data-hook.py')
    adapter=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    events=[]
    for line in Path(path).read_text(errors='replace').splitlines():
        try:
            event=json.loads(line)
        except ValueError:
            continue
        if event.get('type')=='assistant':
            events.append(event)
            continue
        if event.get('type')!='response_item':
            continue
        item=event.get('payload') or {}
        if item.get('type') not in ('function_call','custom_tool_call'):
            continue
        call={'tool_name':item.get('name',''),'tool_input':item.get('arguments',item.get('input',{})),'cwd':data.get('cwd')}
        for normalized in adapter.payloads(call):
            events.append({'type':'assistant','message':{'content':[{'type':'tool_use','name':normalized['tool_name'],'input':normalized['tool_input']}]}})
    with tempfile.NamedTemporaryFile(mode='w',suffix='.jsonl') as transcript:
        for e in events:
            transcript.write(json.dumps(e)+'\n')
        transcript.flush()
        adapted={'tool_name':'AskUserQuestion','tool_input':{'questions':questions},'transcript_path':transcript.name}
        result=subprocess.run(['bash',str(HERE/'gate-ask-user-question.sh')],input=json.dumps(adapted),text=True,capture_output=True)
        # The upstream gate uses permissionDecision deny on stdout, not exit 2.
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        return result.returncode

if __name__=='__main__':
    try:
        sys.exit(main())
    except (OSError,ValueError,TypeError):
        # Match the upstream question gate's fail-open behavior.
        sys.exit(0)
