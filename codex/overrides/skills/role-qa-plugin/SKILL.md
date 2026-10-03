---
name: role-qa-plugin
description: Audit Career Engine compatibility with Codex, including native installation, roles, tools, paths, hooks, external career-data, connectors, exports, and sync behavior; also verify upstream semantic parity.
---

Resolve CAREER_ENGINE_ROOT from this skill's installed location, then read `${CAREER_ENGINE_ROOT}/CODEX-RUNTIME.md` and `${CAREER_ENGINE_ROOT}/CODEX-QA.md`.

Execute the Codex compatibility checklist as the primary QA procedure. Use `${CAREER_ENGINE_ROOT}/agents/qa-plugin.md` as the complete supplemental upstream career-doctrine catalog, interpreting its host-specific checks through CODEX-QA.md. Report findings without modifying the plugin. Keep Codex compatibility and upstream semantic parity separate, and distinguish PASS, FAIL, BLOCKED, and NOT RUN.
