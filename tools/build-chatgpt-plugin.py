#!/usr/bin/env python3
"""Build the portable ChatGPT Plugins artifact from the validated doctrine kit."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'

def members():
    with zipfile.ZipFile(ROOT / 'career-engine-chatgpt.zip') as kit:
        provenance = json.loads(kit.read('manifest.json'))
        source_index = provenance['source_index']
        data = {}
        for name in ('01-workflows-and-roles.txt', '02-reference-templates.txt'):
            data['skills/career-engine/references/' + name] = kit.read('knowledge/' + name)
        for name in kit.namelist():
            if name.startswith(('runtime/', 'templates/')):
                data['skills/career-engine/' + name] = kit.read(name)
        index = {path: dict(info, knowledge_file=info['knowledge_file'].replace('knowledge/', 'references/'))
                 for path, info in source_index.items()}
        data['skills/career-engine/references/source-index.json'] = (json.dumps(index, indent=2)+'\n').encode()
        data['skills/career-engine/UPDATE-CONTRACT.md'] = kit.read('UPDATE-CONTRACT.md')
        data['LICENSE'] = kit.read('LICENSE')
    data['skills/career-engine/SKILL.md'] = (ROOT / 'chatgpt/plugin-skill.md').read_bytes()
    digest = hashlib.sha256(Path(__file__).read_bytes()+b''.join(n.encode()+b for n,b in sorted(data.items()))).hexdigest()
    version = '1.0.0+upstream.'+provenance['upstream_commit'][:12]+'.chat.'+digest[:12]
    stamp = ('\n\n## Loaded package version\n\n'
             'Package build: `'+version+'`\n\n'
             'Upstream commit: `'+provenance['upstream_commit']+'`\n\n'
             'These values identify the package loaded with this skill, not an account release ID. '
             'On “Career Engine version”, “was Career Engine updated?”, or “check for updates”, '
             'report these embedded values first. When authorized fetch is available, read '
             'https://raw.githubusercontent.com/spinningrachel/career-engine-codex/main/chatgpt-plugin-version.json '
             'and report its package_version and upstream_commit separately as Latest published. '
             'Equal package_version means this loaded build matches the published package; '
             'a different value means a different published build is available (do not order SemVer build metadata). '
             'If fetching fails, state Latest published: unknown; never assume this chat upgraded. '
             'Never use the remote version as the loaded version. A newly published ZIP does not update this chat. '
             'If this stamp is absent in an older installation, report Loaded build: unknown. '
             'Applying an account update and opening a fresh chat may be necessary to load new instructions.\n')
    data['skills/career-engine/SKILL.md'] += stamp.encode()
    data['skills/career-engine-version/SKILL.md'] = (
        '---\nname: career-engine-version\ndescription: Report the loaded Career Engine package version and check for a published update.\n---\n'
        + stamp).encode()
    manifest = {'$schema': SCHEMA, 'name': 'career-engine',
                'version': version,
                'description': 'Career coaching, tailored CVs and cover letters, reviews, and document export.',
                'author': {'name': 'Rachel Cheyfitz'}, 'license': 'MIT',
                'repository': 'https://github.com/spinningrachel/career-engine-codex',
                'extensions': {'com.openai': {'interface': {
                    'displayName': 'Career Engine', 'shortDescription': 'Career coaching and documents',
                    'longDescription': 'Career workflows with preserved review gates and private external career-data.',
                    'developerName': 'Rachel Cheyfitz', 'category': 'Productivity',
                    'capabilities': [], 'defaultPrompt': 'Use Career Engine to help with my career workflow.'}}}}
    data['plugin.json'] = (json.dumps(manifest, indent=2)+'\n').encode()
    metadata = {'format': 'chatgpt-plugin', 'upstream_commit': provenance['upstream_commit'],
                'codex_plugin_version': provenance['codex_plugin_version'],
                'sha256': {n: hashlib.sha256(b).hexdigest() for n,b in sorted(data.items())}}
    data['provenance.json'] = (json.dumps(metadata, indent=2)+'\n').encode()
    return data

def published_version(data, archive_bytes):
    manifest = json.loads(data['plugin.json'])
    provenance = json.loads(data['provenance.json'])
    return {'package_version': manifest['version'],
            'upstream_commit': provenance['upstream_commit'],
            'archive': 'career-engine-chatgpt-plugin.zip',
            'archive_sha256': hashlib.sha256(archive_bytes).hexdigest()}

def build(output):
    output.parent.mkdir(parents=True, exist_ok=True)
    data = members()
    with zipfile.ZipFile(output, 'w') as archive:
        for name, content in sorted(data.items()):
            info = zipfile.ZipInfo('career-engine/'+name, (2026,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    (output.parent/'chatgpt-plugin-version.json').write_text(
        json.dumps(published_version(data, output.read_bytes()), indent=2)+'\n')
    print('Built ChatGPT Plugins artifact:', output)

if __name__ == '__main__':
    build(ROOT / 'career-engine-chatgpt-plugin.zip')
