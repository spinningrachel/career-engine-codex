# Run metrics on Codex and ChatGPT

This host adaptation governs usage reporting in setup, Step 9c, and final delivery. Preserve upstream applicability, run order, revision limits, and interrupted-run requirements. Always produce `run-metrics-YYYY-MM-DD.json` in the external run output folder after applicable pipelines, including interrupted runs as prescribed by Step 9c. Never store private run reports in this public plugin or shared Knowledge.

## Evidence and structure

Maintain a private run ledger incrementally, so interruption does not erase completed work. Record logical role, draft/revision pass, execution mode, outcome, and artifact/tool-result references as each pass runs. Do not reconstruct invocation counts from the planned pipeline or conversation memory. Read this run's completed entries in `state.json` for `roles_processed`, `halted-roles.json` for flagged roles, and each role's `cv-type.txt` for `cv_type`. Preserve every Step 9c field and its omission rules, including interrupted metadata, roles not started, per-company track/language, and flagged deliverables. Count clean completions only; flags are not clean completions.

`agents_invoked` retains its legacy per-role keys and counts actual logical role passes, including revisions and flagged work. Add `execution`: `sequential_role_passes` and `spawned_agent_invocations` are separate per-role count maps, plus `evidence` references to the private ledger/tool results. Every logical pass belongs to one mode. Sequential reviewer passes are distinct passes, never independent agents. Count actual delegated invocations (including resumed revision calls) only when tool results establish they happened; do not confuse invocation count with unique agent instances. ChatGPT normally records all passes as sequential and zero spawned invocations. If evidence is missing, mark affected counts unavailable with a reason; never substitute planned counts or invented zeroes. Zero spawned calls is valid when the ledger establishes wholly sequential execution.

## Host accounting

Codex: use only host-exposed, verified token measurements attributable to this run. Session-wide totals cannot silently stand for a shorter run or include unrelated work. ChatGPT: exact usage is normally not exposed; conversation length is not a measurement. Neither host runs the upstream Claude Stop hook or promises later population. The upstream Claude transcript hook is historical code, not installed accounting for these distributions.

Default JSON accounting (replace the reasons with the actual limitation):

```json
{
  "token_counts": {"status": "unavailable", "reason": "Codex or ChatGPT exposes no verified run-scoped token measurement"},
  "cost": {"status": "unavailable", "reason": "Verified usage and applicable pricing unavailable"}
}
```

If verified measurements exist, record `status: verified`, measured values, units, source, run scope, coverage, and evidence references. Preserve provider token categories; never guess missing categories, sum overlapping parent/child usage, or treat missing values as zero. Partial measurements must identify missing coverage and must not claim a complete total. Cost requires verified billable usage and applicable model/pricing evidence; label a calculation as an estimate with its rate/source/date, currency and coverage. Otherwise cost remains unavailable with its own reason, even if tokens are measured. Never invent totals, prices, or a pending Stop-hook placeholder.

## Delivery and failure

Before final delivery, read back this run's exact report path, verify nonzero bytes, parse JSON, check required structural fields against the ledger/state and accounting status/reasons, and ensure the linked artifact is the file just verified. Codex: provide a Markdown link to its absolute external output path. ChatGPT: create and read back the file in Data Analysis, then provide a sandbox download link to that exact file. A filename in prose or an unexecuted write is not a usable file link.

If writing, read-back, validation, or linking fails, retry once using the actual host capability. Never claim the report exists or provide a fabricated link. Clean-run persistent failure remains non-blocking under Step 9c: explicitly name the failed report and concrete error in final delivery. Interrupted-run failure follows the upstream hard gate: retry, then provide the full report content inline with `run-metrics-YYYY-MM-DD.json write failed — content follows`, explaining any download failure. Do not claim successful interrupted delivery without the verified file or this explicit fallback. With no ChatGPT file execution, state that file creation/download is unavailable and use that failure path. These reporting rules do not skip any career gate or change other output applicability.
