#!/usr/bin/env python3
"""Validate the native cache version against the imported source provenance."""
import json
from pathlib import Path
import re
import sys

def check(root):
    manifest = json.loads((root / '.codex-plugin/plugin.json').read_text())
    commit = re.search(r'^Commit: ([0-9a-f]{40})$', (root / 'UPSTREAM.md').read_text(), re.M)
    if not commit:
        raise ValueError('Missing upstream commit provenance')
    expected = r'1\.0\.0\+upstream\.' + commit[1][:12] + r'\.codex\.[0-9a-f]{12}'
    if manifest.get('name') != 'career-engine' or not re.fullmatch(expected, manifest.get('version', '')):
        raise ValueError('Native cache version does not match upstream provenance and adapter hash')
    print('Native cache version matches imported upstream provenance')

if __name__ == '__main__':
    check(Path(sys.argv[1]))
