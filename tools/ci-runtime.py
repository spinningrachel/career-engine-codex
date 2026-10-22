#!/usr/bin/env python3
"""Use prepared CI tools even when a review login shell resets PATH."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / '.sync-work/review-runtime.json'

def record():
    sites = set()
    for name in ('docx', 'lxml', 'yaml', 'typing_extensions'):
        spec = importlib.util.find_spec(name)
        if spec is None or spec.origin is None:
            raise RuntimeError('Required dependency missing during trusted setup: ' + name)
        origin = Path(spec.origin)
        sites.add(str(origin.parent.parent if spec.submodule_search_locations else origin.parent))
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    RECORD.write_text(json.dumps({'python': sys.executable, 'path': os.environ['PATH'],
                                  'library_path': os.environ.get('LD_LIBRARY_PATH', ''),
                                  'python_path': sorted(sites),
                                  'tool_cache': os.environ.get('RUNNER_TOOL_CACHE', '')}))

def environment(data):
    python = Path(data['python'])
    if not python.is_absolute() or not python.is_file():
        raise RuntimeError('Prepared Python is unavailable; do not reinstall in the review sandbox')
    path = data['path']
    codex = shutil.which('codex', path=path)
    cache = data.get('tool_cache')
    if not codex and cache:
        # The action installs its CLI after recording setup-python's runtime.
        # Discover that installation only within the configured runner tool cache.
        candidates = list((Path(cache) / 'node').glob('*/x64/bin/codex'))
        candidates.sort(key=lambda p: tuple(int(n) for n in re.findall(r'\d+', p.parents[2].name)), reverse=True)
        codex = next((str(p) for p in candidates if p.is_file() and os.access(p, os.X_OK)), None)
    if not codex:
        raise RuntimeError('Action-installed Codex CLI unavailable in recorded PATH/tool cache')
    env = dict(os.environ)
    env['PATH'] = os.pathsep.join([str(python.parent), str(Path(codex).parent), path])
    if data.get('library_path'):
        env['LD_LIBRARY_PATH'] = data['library_path']
    if data.get('python_path'):
        env['PYTHONPATH'] = os.pathsep.join(data['python_path'])
    return env

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['record', 'check', 'run'])
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.operation == 'record':
        record()
        return
    if not RECORD.is_file():
        raise SystemExit('CI runtime record missing; the trusted setup step must create it')
    data = json.loads(RECORD.read_text())
    env = environment(data)
    if args.operation == 'check':
        subprocess.run([data['python'], '-c', 'import docx, lxml, yaml; print("Prepared export dependencies import successfully")'], env=env, check=True)
        subprocess.run(['codex', '--version'], env=env, check=True)
    else:
        if not args.command:
            parser.error('run requires a command')
        os.execvpe(args.command[0], args.command, env)

if __name__ == '__main__':
    main()
