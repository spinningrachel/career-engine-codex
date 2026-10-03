#!/usr/bin/env python3
"""Normalize Codex tool inputs; preserve the upstream personal-data detector."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent

def payloads(data):
    tool = data.get('tool_name','').split('.')[-1]
    args = data.get('tool_input', {})
    if isinstance(args,str):
        if tool == 'apply_patch':
            args = {'patch':args}
        else:
            try:
                args=json.loads(args)
            except ValueError:
                return
    if not isinstance(args,dict):
        return
    cwd = data.get('cwd') or os.getcwd()
    if tool in ('exec_command','shell_command','shell','Bash'):
        cmd=args.get('cmd',args.get('command',''))
        if isinstance(cmd,list):
            cmd=' '.join(cmd)
        yield {'tool_name':'Bash','tool_input':{'command':cmd},'cwd':args.get('workdir') or cwd}
    elif tool == 'apply_patch':
        patch=args.get('patch') or args.get('input') or ''
        chunks=re.split(r'(?m)^\*\*\* (Add|Update|Delete) File: (.+)\n',patch)
        for i in range(1,len(chunks),3):
            kind,path,body=chunks[i:i+3]
            if kind=='Delete':
                continue
            moved=re.search(r'(?m)^\*\*\* Move to: (.+)$',body)
            if moved:
                path=moved.group(1)
            path=str(Path(cwd,path).resolve())
            new='\n'.join(line[1:] for line in body.splitlines() if line.startswith('+') and not line.startswith('+++'))
            yield {'tool_name':'Write','tool_input':{'file_path':path,'content':new},'cwd':cwd}
    else:
        # File-writing connectors retain upstream path/content handling.
        path=args.get('file_path') or args.get('path')
        if path:
            args=dict(args)
            args['file_path']=str(Path(cwd,path).resolve())
        yield {'tool_name':tool,'tool_input':args,'cwd':cwd}

def main():
    try:
        data=json.load(sys.stdin)
    except (ValueError,TypeError):
        return 0
    if not isinstance(data,dict):
        return 0
    for item in payloads(data):
        p=subprocess.run(['bash',str(HERE/'block-personal-data-writes.sh')],input=json.dumps(item),text=True,capture_output=True)
        if p.returncode:
            sys.stderr.write(p.stderr)
            return p.returncode
    return 0

if __name__=='__main__':
    sys.exit(main())
