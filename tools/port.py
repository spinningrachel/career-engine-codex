#!/usr/bin/env python3
"""Reproducible mechanical port; semantic adaptations are reviewed overrides."""
import argparse
import hashlib
import json
import shlex
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
INCLUDE = ('agents', 'skills', 'references', 'scripts', 'assets')
BOOT = '\n> **Codex host:** Before using this document, read `${CAREER_ENGINE_ROOT}/CODEX-RUNTIME.md`. Resolve the root from this skill’s installed path. That contract replaces Claude-specific APIs, installation, personal-data discovery, and role spawning; all career doctrine, gates, and required reads below still apply.\n'

def translate(text):
    text = text.replace('${CLAUDE_PLUGIN_ROOT}', '${CAREER_ENGINE_ROOT}').replace('$CLAUDE_PLUGIN_ROOT', '$CAREER_ENGINE_ROOT')
    # Gate 2 must run from a relocated installation, regardless of shell cwd.
    return text.replace('python3 skills/gatekeeper-checks/scripts/pregate-lint.py',
                        'python3 "${CAREER_ENGINE_ROOT}/skills/gatekeeper-checks/scripts/pregate-lint.py"')

def add_bootstrap(text):
    if text.startswith('---\n') and '\n---' in text[4:]:
        end = text.index('\n---', 4) + 4
        return text[:end] + '\n' + BOOT + text[end:]
    return BOOT + text

def adapt_usage(target):
    """Guarded edits retain new upstream doctrine; changed anchors require review."""
    def replace(path, old, new):
        p = target / path
        text = p.read_text()
        if text.count(old) != 1:
            raise RuntimeError('Usage adaptation anchor changed; review required: ' + path)
        p.write_text(text.replace(old, new))
    post = 'skills/career-engine-orchestrator/orchestrator-post-run.md'
    replace(post, 'Actual token counts are appended by a Stop hook configured during setup — the hook writes to this same file when the session ends.',
            'Apply references/run-metrics-host.md for host-specific accounting and report delivery. No Claude Stop hook runs on Codex or ChatGPT.')
    replace(post, '"token_counts": "pending — written by Stop hook at session end"',
            '"token_counts": {"status": "unavailable", "reason": "Host exposes no verified run-scoped token measurement"},\n  "cost": {"status": "unavailable", "reason": "Verified usage and applicable pricing unavailable"}')
    replace(post, 'Set each agent count from the actual invocations this run. Leave `token_counts` as the literal string `"pending — written by Stop hook at session end"` — the hook replaces this value when the session closes.',
            'Set `agents_invoked` from actual logical role passes this run, retaining the legacy keys. Also record `execution` with separate `sequential_role_passes` and `spawned_agent_invocations` counts and evidence references, per references/run-metrics-host.md. Record verified usage only when available; otherwise retain explicit unavailable objects with concrete host-specific reasons.')
    replace(post, '## Final Chat Delivery',
            '## Final Chat Delivery\n\nApply references/run-metrics-host.md: verify the metrics file on clean and interrupted runs and link the verified artifact, or explicitly report failure with the prescribed fallback.')
    setup = target / 'skills/career-engine-setup/SKILL.md'
    text = setup.read_text()
    start = text.index('**Token usage tracking (optional but recommended):**')
    end = text.index('Confirm: "Phase 6 complete.', start)
    setup.write_text(text[:start] + '**Run usage reporting:**\n\nRead references/run-metrics-host.md. The structural run report is required after applicable pipelines, including interrupted runs. Codex and ChatGPT do not run Claude’s Stop hook. Explain unavailable token counts and cost explicitly; never configure a Claude hook as a fallback on these hosts.\n\n' + text[end:])

def adapt_cv_word_count(text):
    # Preserve Gate 2's language-neutral token definition and comment exclusion.
    # Fail closed if upstream changes these implementation sites on a later sync.
    replacements = {
        '    total, skipping = 0, False\n    for line in lines:':
        '    total, skipping = 0, False\n'
        '    lines = re.sub(r"<!--.*?-->", "", "\\n".join(lines), flags=re.DOTALL).splitlines()\n'
        '    for line in lines:',
        'if re.search(r"[A-Za-z0-9]", tok)':
        'if any(char.isalnum() for char in tok)',
    }
    for original, replacement in replacements.items():
        if text.count(original) != 1:
            raise RuntimeError('Upstream CV word-count implementation changed; review required')
        text = text.replace(original, replacement)
    return text

def adapt_intake_corrections(target):
    """Resolve legacy consumer wording against the explicit October 22 rules."""
    edits = {
        'skills/career-engine-intake/SKILL.md': (
            '**Confirmation pass — run immediately after this role\'s writes, before moving to the next role (this closes the past silent-drop; see the per-role sequencing rule above).**',
            ' **Schema eligibility applies to confirmation too:** exclude coach fields skipped under the no-matching-text-property rule from confirmation, retry, and unwritten-field reporting. Still require their coach output and the outreach-map details; all eligible mandatory properties retain the comparison, retry, and reporting gates below.'),
        'skills/database/SKILL.md': (
            '**Pipeline reads:**',
            '**Closure precedence:** the October 22 ATS rule governs every pipeline, including older fetch-ladder, prioritizer, and Edit summaries. A confirmed official ATS 404/410 or board-root redirect remains closed even if a mirror serves a copy; a mirror cannot reopen the official posting. A rendering failure without those verified responses remains a fetch problem and must be retried. In `Closed this run`, record the actual evidence observed (ATS response/redirect alone suffices under rule (c)); never claim an index check occurred if it did not. Include roles with no matching Closed option in this dedicated block as `NOT WRITTEN`, with prior Status, URL, and evidence, even when an older summary also lists them as skipped.\n\n'),
    }
    for relative, (anchor, addition) in edits.items():
        path = target / relative
        text = path.read_text()
        if text.count(anchor) != 1:
            raise RuntimeError('Intake correction anchor changed; review required: ' + relative)
        replacement = addition + anchor if relative == 'skills/database/SKILL.md' else anchor + addition
        text = text.replace(anchor, replacement, 1)
        path.write_text(text)

def preserve_stop_policy(source, target):
    # Codex has no prompt Stop hook. Preserve its career policy as required
    # runtime guidance instead of dropping it with the Claude hook API.
    upstream_hooks = json.loads((source / 'hooks/hooks.json').read_text())
    stop_prompts = [translate(h['prompt'])
                    for group in upstream_hooks.get('hooks', {}).get('Stop', [])
                    for h in group['hooks'] if h.get('type') == 'prompt']
    if not stop_prompts:
        raise RuntimeError('Upstream Stop policy missing; review required')
    policy_path = 'references/upstream-stop-policy.md'
    (target / policy_path).write_text(
        '# Upstream queue-completion policy\n\n'
        'Read and apply this policy through CODEX-RUNTIME.md. The quoted upstream '
        'prompt is instruction-level guidance on Codex, not an installed Stop hook. '
        'Claude tool names and response JSON describe the upstream host; continue '
        'the authorized queue using available Codex tools and preserve genuine blockers.\n\n'
        + '\n\n'.join(stop_prompts) + '\n')
    # Keep relational assertions checking the actual preserved policy. Only
    # references to the replaced hook file move; all terms and siblings remain.
    parity_path = target / 'scripts/qa-parity.json'
    parity = json.loads(parity_path.read_text())
    for assertion in parity.get('defined_terms', []):
        if 'hooks/hooks.json' in assertion['files']:
            if assertion['term'].lower() not in '\n'.join(stop_prompts).lower():
                raise RuntimeError('Unmapped upstream hook assertion: ' + assertion['id'])
            assertion['files'] = [policy_path if f == 'hooks/hooks.json' else f
                                  for f in assertion['files']]
    parity_path.write_text(json.dumps(parity, indent=2) + '\n')

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
            if p.relative_to(target).as_posix() == 'skills/gatekeeper-checks/scripts/pregate-lint.py':
                text = adapt_cv_word_count(text)
            if p.name == 'SKILL.md' or (p.parent.name == 'agents' and p.suffix == '.md'):
                text = add_bootstrap(text)
            if p.relative_to(target).as_posix() == 'agents/qa-plugin.md':
                text = add_bootstrap(text.replace(BOOT, '\n> **Codex QA entrypoint:** Read `${CAREER_ENGINE_ROOT}/CODEX-QA.md` and run its Codex compatibility checklist first. The original checklist below remains the supplemental career-doctrine catalog; map its Claude host procedures through CODEX-QA.md. Report Codex compatibility separately from upstream semantic parity.\n',1))
            p.write_text(text)
    # Native plugin recognition by the retained guard.
    guard = target / 'scripts/block-personal-data-writes.sh'
    guard.write_text(guard.read_text().replace('".claude-plugin"', '".codex-plugin"'))
    # The source checkout is a marketplace, while installed bundles have a
    # native plugin manifest. Preserve both boundaries without treating an
    # unrelated marketplace as Career Engine. Keep the upstream plugin-name
    # check and nearest-manifest boundary intact.
    anchor = '        parent = os.path.dirname(cur)\n'
    guard_text = guard.read_text()
    if guard_text.count(anchor) != 1:
        raise RuntimeError('Upstream guard root traversal changed; review required')
    marketplace_check = '''        marketplace = os.path.join(cur, ".agents", "plugins", "marketplace.json")
        if os.path.isfile(marketplace):
            try:
                with open(marketplace, encoding="utf-8") as fh:
                    catalog = json.load(fh)
                if catalog.get("name") == "cheyfitz-codex" and any(
                    entry.get("name") == "career-engine"
                    and entry.get("source") == {"source": "local", "path": "./plugin"}
                    for entry in catalog.get("plugins", [])
                ):
                    return cur
            except Exception:
                pass
            return None
'''
    guard.write_text(guard_text.replace(anchor, marketplace_check + anchor, 1))
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
    (target / 'UPDATE-CONTRACT.md').write_text((ROOT / 'codex/update-contract.md').read_text())
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
    preserve_stop_policy(source, target)
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
    # New doctrine checks can cite the Stop prompt too. Preserve each check's
    # pattern and count, pointing literal policy checks at the retained text.
    policy = (target / 'references/upstream-stop-policy.md').read_text()
    for i, line in enumerate(lines):
        if line.startswith('expect_ge ') and '"hooks/hooks.json"' in line:
            args = shlex.split(line)
            if len(args) == 5 and args[3] in policy:
                lines[i] = line.replace('"hooks/hooks.json"', '"references/upstream-stop-policy.md"', 1)
    qa.write_text('\n'.join(lines)+'\n')
    # Claude duplicates versions in two manifests. Codex's marketplace format
    # has no version field: validate the actual native cache key and provenance.
    text = qa.read_text()
    start = text.find('V_PLUGIN=$(python3 ')
    if start >= 0:
        end_marker = 'expect_ge "73" "scripts/check-invariants.sh"'
        end = text.find(end_marker, start)
        block = text[start:end]
        if end < 0 or '.claude-plugin/plugin.json' not in block or '.claude-plugin/marketplace.json' not in block:
            raise RuntimeError('Upstream version assertion changed; native mapping review required')
        replacement = ('if python3 "$(dirname "$0")/check-native-version.py" "$TARGET"; then report "73" 1 "";\n'
                       'else report "73" 0 "native cache version/provenance invalid"; fi\n')
        qa.write_text(text[:start] + replacement + text[end:])
    shutil.copy2(ROOT / 'codex/native-version.py', target / 'scripts/check-native-version.py')
    # Resolve the reviewed upstream cleanup contradiction without allowing any
    # write to an archived, trashed, or status-changed page. Match the exact
    # conflicting clause so future upstream edits are not broadly rewritten.
    role_path = target / 'agents/role-prioritizer.md'
    role = role_path.read_text()
    conflicting = "**First, release unfinished claims (2026-10-21):** set `Agent Status = No Status` on every role claimed in Step 1 that did not get its Step 3 write (skipped, failed, archived mid-run). Never touch a role this run did not claim."
    resolved = "**First, release unfinished claims (2026-10-21):** for each role claimed in Step 1 that did not get its Step 3 write (skipped or failed), re-fetch the page immediately before cleanup. Set `Agent Status = No Status` only for this run's own unfinished claim when the page is live (not archived/trashed), its Status still matches the target from Step 0, and its Agent Status is still In Progress. If archived/trashed, Status-changed, inaccessible, or no longer this run's claim, make no write, never unarchive it, and report `claim not released — page archived/changed or ownership unverified` with the role in Step 4. Report cleanup failures too; never claim release succeeded without its result. The archival and liveness gates take precedence over cleanup. Never touch a role this run did not claim."
    if conflicting in role:
        role_path.write_text(role.replace(conflicting, resolved, 1))
        shared = target / 'skills/database/SKILL.md'
        shared_text = shared.read_text()
        release_rule = "Never clear a claim another session wrote."
        if shared_text.count(release_rule) != 1:
            raise RuntimeError('Upstream shared claim release rule changed; review required')
        shared.write_text(shared_text.replace(release_rule, release_rule + " **Cleanup safety:** wrap-up releases are still writes: re-fetch first, release only this run's own unfinished claim on a live page whose target Status is unchanged, and never write to or unarchive archived/trashed pages. When cleanup is unsafe, unavailable, or fails, leave the page untouched and name the unreleased claim and reason in the run report. Cleanup never overrides the adapter's liveness gate.", 1))
    overrides = ROOT / 'codex/overrides'
    if overrides.exists():
        for p in overrides.rglob('*'):
            if p.is_file():
                if p.name == '.gitkeep':
                    continue
                out = target / p.relative_to(overrides)
                out.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(p,out)
    adapt_usage(target)
    adapt_intake_corrections(target)
    hashes = {str(p.relative_to(target)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(target.rglob('*')) if p.is_file()}
    (ROOT / 'upstream-lock.json').write_text(json.dumps({'repository':'spinningrachel/career-engine-claude','commit':commit,'generated_sha256':hashes},indent=2)+'\n')
    print('Ported',commit,'to',target,':',len(hashes),'files')

if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',type=Path,required=True)
    generate(ap.parse_args().source)
