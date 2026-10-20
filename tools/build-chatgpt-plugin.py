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
    digest = hashlib.sha256(b''.join(n.encode()+b for n,b in sorted(data.items()))).hexdigest()
    manifest = {'$schema': SCHEMA, 'name': 'career-engine',
                'version': '1.0.0+upstream.'+provenance['upstream_commit'][:12]+'.chat.'+digest[:12],
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

def build(output):
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w') as archive:
        for name, content in sorted(members().items()):
            info = zipfile.ZipInfo('career-engine/'+name, (2026,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    print('Built ChatGPT Plugins artifact:', output)

if __name__ == '__main__':
    build(ROOT / 'career-engine-chatgpt-plugin.zip')
