# Usage reporting adaptation QA

Review scope: cumulative reporting change against upstream commit `9de575055e375b5a1282a5bfa69c6cf17df3bd36`. No upstream version bump, CI/sync-policy edit, personal career-data, writing-doctrine change, or pipeline-gate change.

## Results

- PASS — Codex offline compatibility and isolated native installation: `python3 tools/check-codex-compatibility.py --install`, codex-cli 0.159.0-alpha.3. This establishes installation, not model adherence or live hook execution.
- PASS — ChatGPT offline compatibility: both Custom GPT and Project instructions, 92 indexed source sections, templates/runtime, manifest/hash validation, reproducible archive.
- PASS — `bash tools/validate.sh`: 16 repository tests; detailed/brief synthetic export fixtures; personal-data guard 45/45; question gate 11/11; mechanical 512/512; parity 26/26; repository and Office XML personal-data scan.
- PASS — upstream semantic parity for affected behavior: Step 9c applicability/order, structural fields, clean-completion count, flagged-role read-back, CV type, omission rules, clean non-blocking failure and interrupted hard-gate/full-inline fallback retained. Accounting and verified links are explicit host adaptations.
- PASS — regeneration regression uses synthetic upstream files, regenerates twice, repairs simulated generated-cache damage, preserves an added upstream gate, and rejects a changed delivery anchor. No real career-data used. Accounting example parses as JSON with explicit unavailable status/reasons for both tokens and cost.
- NOT RUN — live ChatGPT import/model response, Data Analysis sandbox downloads, account feature availability, authenticated Notion, live Codex career pipeline, host-hook enablement, actual host token measurement ingestion, changed-upstream model-backed automation. Instruction-level checks do not establish those behaviors.

## Diff-scoped consumer sweep and trace

Setup now routes directly to `references/run-metrics-host.md`; it cannot offer a Claude accounting-hook fallback. The generator imports upstream doctrine, overlays the new reference, then applies guarded accounting replacements. A changed upstream anchor fails generation rather than silently masking new doctrine. The ChatGPT builder includes the reference as a fully indexed source section; both controlling instruction variants and host runtime route to it.

Synthetic clean reporting trace: a private ledger records one sequential writer pass and one sequential reviewer pass. Step 9c reads completed state entries and any current flagged records; it never uses the queue size as completed count. Legacy role keys count actual passes. Execution records two sequential passes and zero spawned invocations, with ledger evidence. No verified host usage is available, so token_counts and cost each carry unavailable status and the concrete host reason. The host writes the report, reads it back, parses JSON, compares structural fields with state/ledger, and links the exact verified artifact. A persistent failure after one retry is named in the final delivery and stays non-blocking on a clean run.

Synthetic interrupted reporting trace: one role completed, a second mid-chain, a third not started. The report counts only the clean completed entry, preserves interrupted/reason/not-started fields and any persisted flags, and includes observed role passes even for unfinished work. It does not advance a mid-chain role's status. Steps 8–9c retain their upstream applicability. If a report write/read-back/download fails, retry once; persistent interruption failure requires full report content inline with the explicit failure note. No fabricated path or successful-delivery claim is permitted.

Delegated reporting trace: a real Codex tool result establishes a writer spawn and a resumed revision call. Those are two delegated invocations, not two unique independent agents; the sequential reviewer remains a sequential pass. Missing evidence makes affected counts unavailable, never planned totals. ChatGPT uses sequential execution by default. Verified usage, if exposed, must identify source, scope, coverage and categories; incomplete or overlapping usage cannot become a complete total. Cost additionally requires applicable pricing evidence.

Contradiction review: the legacy `agents_invoked` name is preserved for compatibility but explicitly defined as logical passes; execution mode is recorded separately. The upstream interrupted failure text is interpreted together with its existing final-delivery inline fallback. Imported Claude historical hook prose/code does not install a Stop hook: native hooks remain unchanged, and both controlling host contracts route accounting to the adaptation. Unrelated setup permissions and writing gates are outside this diff.

Installation documentation retains Codex marketplace and both ChatGPT routes. No installation interface changed; no new import operation is asserted. Private run ledgers/reports and external career-data remain separate from public packages.
