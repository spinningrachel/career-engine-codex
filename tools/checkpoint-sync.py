#!/usr/bin/env python3
"""Transport only reviewed, publishable files between isolated CI jobs."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
PATHS = ('plugin', 'codex/overrides', 'tools/port.py', 'tests', 'upstream-lock.json',
         'LICENSE', 'career-engine-codex.zip', 'career-engine-chatgpt.zip', 'chatgpt', 'README.md')
DIRS = ('plugin', 'codex/overrides', 'tests', 'chatgpt')

def allowed(name):
    path = PurePosixPath(name)
    return (not path.is_absolute() and '..' not in path.parts
            and not any(p.startswith('.') or p == '__pycache__' for p in path.parts
                        if p != '.codex-plugin')
            and not name.endswith('.pyc')
            and (name in PATHS or any(name.startswith(p + '/') for p in DIRS)))

def review_passed(review):
    if review.get('status') != 'passed' or review.get('unresolved') != []:
        raise ValueError('Only a passed, resolved semantic review can be checkpointed')

def pack(destination, base):
    review = json.loads((ROOT / '.sync-work/review-result.json').read_text())
    review_passed(review)
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() != base:
        raise ValueError('Review changed HEAD; checkpoint must use the original workflow commit')
    files = {}
    for name in PATHS:
        path = ROOT / name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p.is_relative_to(ROOT)):
            raise ValueError('Checkpoint source contains a symlink: ' + name)
        candidates = path.rglob('*') if path.is_dir() else [path]
        for p in candidates:
            rel = p.relative_to(ROOT).as_posix()
            if p.is_symlink():
                raise ValueError('Checkpoint cannot contain symlinks: ' + rel)
            if p.is_file() and allowed(rel):
                files[rel] = p.read_bytes()
    metadata = {'base': base, 'review': review,
                'upstream': json.loads(files['upstream-lock.json'])['commit'],
                'sha256': {p: hashlib.sha256(b).hexdigest() for p, b in files.items()}}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(destination, 'w:gz') as archive:
        entries = dict(files, **{'checkpoint.json': json.dumps(metadata).encode()})
        for name, data in sorted(entries.items()):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o755 if name != 'checkpoint.json' and os.access(ROOT / name, os.X_OK) else 0o644
            archive.addfile(info, io.BytesIO(data))

def restore(source, base):
    # Validate the entire archive before writing anything; never extract its
    # paths directly. The checkout's protected workflow/tools remain trusted.
    with tarfile.open(source, 'r:gz') as archive:
        members = archive.getmembers()
        names = [m.name for m in members]
        if len(set(names)) != len(names) or any(not m.isfile() for m in members):
            raise ValueError('Duplicate or non-file checkpoint entry')
        if any(n != 'checkpoint.json' and not allowed(n) for n in names):
            raise ValueError('Checkpoint contains a protected or escaping path')
        metadata = json.load(archive.extractfile('checkpoint.json'))
        if metadata['base'] != base:
            raise ValueError('Checkpoint belongs to a different workflow base')
        review_passed(metadata['review'])
        files = {m.name: archive.extractfile(m).read() for m in members if m.name != 'checkpoint.json'}
        actual = {n: hashlib.sha256(b).hexdigest() for n, b in files.items()}
        if actual != metadata['sha256']:
            raise ValueError('Checkpoint content/hash inventory mismatch')
        if json.loads(files['upstream-lock.json'])['commit'] != metadata['upstream']:
            raise ValueError('Checkpoint upstream provenance mismatch')
        for name in files:
            path = ROOT / name
            if path.is_symlink() or any(p.is_symlink() for p in path.parents if p.is_relative_to(ROOT)):
                raise ValueError('Checkout path contains a symlink')
        for directory in DIRS:
            root = ROOT / directory
            if root.is_symlink() or (root.exists() and any(p.is_symlink() for p in root.rglob('*'))):
                raise ValueError('Checkout contains a symlink in a publishable directory')
        # Delete old tracked content omitted from the reviewed snapshot too.
        for directory in DIRS:
            root = ROOT / directory
            if root.exists():
                for p in root.rglob('*'):
                    if p.is_file() and p.relative_to(ROOT).as_posix() not in files:
                        p.unlink()
        modes = {m.name: m.mode for m in members}
        for name, data in files.items():
            path = ROOT / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(modes[name] & 0o777)
        (ROOT / '.sync-work').mkdir(exist_ok=True)
        (ROOT / '.sync-work/review-result.json').write_text(json.dumps(metadata['review']))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['pack', 'restore'])
    parser.add_argument('archive', type=Path)
    parser.add_argument('--base', required=True)
    args = parser.parse_args()
    (pack if args.operation == 'pack' else restore)(args.archive, args.base)
