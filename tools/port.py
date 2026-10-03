#!/usr/bin/env python3
"""Reproducible mechanical port; semantic adaptations are reviewed overrides."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INCLUDE = ('agents', 'skills', 'references', 'scripts', 'assets')
BOOT = '\n> **Codex host:** Before using this document, read `${CAREER_ENGINE_ROOT}/CODEX-RUNTIME.md`. Resolve the root from this skill’s installed path. That contract replaces Claude-specific APIs, installation, personal-data discovery, and role spawning; all career doctrine, gates, and required reads below still apply.\n'

def translate(text):
    return text.replace('${CLAUDE_PLUGIN_ROOT}', '${CAREER_ENGINE_ROOT}').replace('$CLAUDE_PLUGIN_ROOT', '$CAREER_ENGINE_ROOT')

def add_bootstrap(text):
    if text.startswith('---\n') and '\n---' in text[4:]:
        end = text.index('\n---', 4) + 4
        return text[:end] + '\n' + BOOT + text[end:]
    return BOOT + text

def generate(source):
    source = source.resolve()
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    target = ROOT / 'plugin'
    if target.exists():
        shutil.rmtree(target)
    target.mkdir()
    for item in INCLUDE:
        shutil.copytree(source / item, target / item, ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for p in target.rglob('*'):
        if p.is_file() and p.suffix in ('.md','.sh','.py','.json'):
            text = translate(p.read_text())
            if p.name == 'SKILL.md' or (p.parent.name == 'agents' and p.suffix == '.md'):
                text = add_bootstrap(text)
            if p.relative_to(target).as_posix() == 'agents/qa-plugin.md':
                text = add_bootstrap(text.replace(BOOT, '\n> **Codex QA entrypoint:** Read `${CAREER_ENGINE_ROOT}/CODEX-QA.md` and run its Codex compatibility checklist first. The original checklist below remains the supplemental career-doctrine catalog; map its Claude host procedures through CODEX-QA.md. Report Codex compatibility separately from upstream semantic parity.\n',1))
            p.write_text(text)
    # Native plugin recognition by the retained guard.
    guard = target / 'scripts/block-personal-data-writes.sh'
    guard.write_text(guard.read_text().replace('".claude-plugin"', '".codex-plugin"'))
    guard.write_text(guard.read_text().replace('if os.path.isfile(os.path.join(cur, ".codex-plugin", "plugin.json")):', 'if os.path.isfile(os.path.join(cur, ".codex-plugin", "plugin.json")) or os.path.isfile(os.path.join(cur, ".agents", "plugins", "marketplace.json")):'))
    # QA test fixtures exercise the same native plugin-recognition path.
    tests = target / 'scripts/test-personal-data-guard.sh'
    tests.write_text(tests.read_text().replace('.claude-plugin', '.codex-plugin'))
    for agent in sorted((source / 'agents').glob('*.md')):
        name = 'role-' + agent.stem
        path = target / 'skills' / name / 'SKILL.md'
        path.parent.mkdir(parents=True)
        path.write_text('---\nname: '+name+'\ndescription: Execute the '+agent.stem+' role in the Career Engine pipeline on Codex.\n---\n'+BOOT+'\nRead `${CAREER_ENGINE_ROOT}/agents/'+agent.name+'` and execute that role with the supplied inputs and file-based output protocol. Its frontmatter describes the upstream host; use the Codex runtime contract for tool access and role execution.\n')
    (target / 'CODEX-RUNTIME.md').write_text((ROOT / 'codex/runtime.md').read_text())
    (target / 'CODEX-QA.md').write_text((ROOT / 'codex/qa-plugin.md').read_text())
    (target / 'UPSTREAM.md').write_text('Source: https://github.com/spinningrachel/career-engine-claude\nCommit: '+commit+'\nMIT; original authorship preserved in LICENSE.\n')
    shutil.copy2(source / 'LICENSE', target / 'LICENSE')
    shutil.copy2(source / 'LICENSE', ROOT / 'LICENSE')
    (target / 'README.md').write_text(translate((source / 'README.md').read_text()))
    (target / 'CLAUDE.md').write_text(translate((source / 'CLAUDE.md').read_text()))
    (target / 'CONNECTORS.md').write_text(translate((source / 'CONNECTORS.md').read_text()))
    (target / '.codex-plugin').mkdir()
    adapter_files=[Path(__file__),*(ROOT/'codex').rglob('*')]
    adapter_hash=hashlib.sha256(b''.join(p.relative_to(ROOT).as_posix().encode()+p.read_bytes() for p in sorted(adapter_files) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')).hexdigest()[:12]
    version='1.0.0+upstream.'+commit[:12]+'.codex.'+adapter_hash
    manifest = {'name':'career-engine','version':version,'description':'Career management, tailored CVs, cover letters, and DOCX export for Codex.','skills':'./skills','hooks':'./hooks/hooks.json','interface':{'displayName':'Career Engine','shortDescription':'Career workflows and document exports for Codex','developerName':'Rachel Cheyfitz','category':'Productivity','defaultPrompt':'Use $career-engine to help with my career workflow.'}}
    (target / '.codex-plugin/plugin.json').write_text(json.dumps(manifest,indent=2)+'\n')
    hook = {'hooks':{'PreToolUse':[{'matcher':'.*','hooks':[{'type':'command','command':'python3 "${PLUGIN_ROOT}/scripts/codex-personal-data-hook.py"','timeout':10}]}]}}
    (target / 'hooks').mkdir(exist_ok=True)
    (target / 'hooks/hooks.json').write_text(json.dumps(hook,indent=2)+'\n')
    hook['hooks']['PreToolUse'].append({'matcher':'request_user_input|request_user_input_async|AskUserQuestion','hooks':[{'type':'command','command':'python3 "${PLUGIN_ROOT}/scripts/codex-question-gate.py"','timeout':10}]})
    (target / 'hooks/hooks.json').write_text(json.dumps(hook,indent=2)+'\n')
    shutil.copy2(ROOT / 'codex/personal-data-hook.py', target / 'scripts/codex-personal-data-hook.py')
    shutil.copy2(ROOT / 'codex/question-gate.py', target / 'scripts/codex-question-gate.py')
    # Keep all career-doctrine assertions. Replace six Claude hook API assertions
    # with their native equivalents; an upstream assertion change stops generation.
    qa=target/'scripts/qa-mechanical.sh'
    lines=qa.read_text().splitlines()
    adaptations=[
        ('"log-token-usage.sh"', 'expect_ge "21t" "hooks/hooks.json" "codex-personal-data-hook.py" 1'),
        ("'\"type\": \"prompt\"'", 'expect_ge "21t" "hooks/hooks.json" "codex-question-gate.py" 1'),
        ('"last_assistant_message"', 'expect_ge "21t" "scripts/codex-question-gate.py" "transcript_path" 1'),
        ("'ok", 'expect_ge "21t" "scripts/codex-question-gate.py" "permissionDecision" 1'),
        ('AskUserQuestion', 'expect_ge "21t" "hooks/hooks.json" "request_user_input" 1'),
        ('gate-ask-user-question.sh', 'expect_ge "21t" "scripts/codex-question-gate.py" "gate-ask-user-question.sh" 1'),
    ]
    for needle,replacement in adaptations:
        found=[i for i,line in enumerate(lines) if line.startswith('expect_ge "21t" "hooks/hooks.json"') and needle in line]
        if len(found)!=1:
            raise RuntimeError('Upstream host-hook assertion changed; review required: '+needle)
        lines[found[0]]=replacement
    qa.write_text('\n'.join(lines)+'\n')
    overrides = ROOT / 'codex/overrides'
    if overrides.exists():
        for p in overrides.rglob('*'):
            if p.is_file():
                if p.name == '.gitkeep':
                    continue
                out = target / p.relative_to(overrides)
                out.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(p,out)
    hashes = {str(p.relative_to(target)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(target.rglob('*')) if p.is_file()}
    (ROOT / 'upstream-lock.json').write_text(json.dumps({'repository':'spinningrachel/career-engine-claude','commit':commit,'generated_sha256':hashes},indent=2)+'\n')
    print('Ported',commit,'to',target,':',len(hashes),'files')

if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',type=Path,required=True)
    generate(ap.parse_args().source)
