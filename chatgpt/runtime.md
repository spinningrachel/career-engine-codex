# ChatGPT runtime and knowledge index

GPT-INSTRUCTIONS.txt and PROJECT-INSTRUCTIONS.txt are the controlling host instructions. The knowledge preserves the upstream career doctrine, including files whose legacy prose names Claude or Codex. Those host APIs are historical source descriptions; use the explicit ChatGPT mappings below. Do not drop career rules, reviewer passes, required reads, or revision limits.

The knowledge uses **=== SOURCE: relative/path ===** sections. Resolve an internal reference by its section label rather than a filesystem path. Retrieve the whole required section; if retrieval is incomplete, ask for that source file and mark the check unrun. Installation-time placeholder replacement is forbidden. Personal identity, facts, voice, preferences, templates, and output paths come from the user's separate external career-data skill.

| Upstream host assumption | ChatGPT equivalent |
|---|---|
| Skill/plugin registration and slash commands | Instructions plus uploaded Knowledge/Project files; natural-language workflow routing |
| Agent/Task/subagent type | Separate sequential role passes; no claim of spawned agents |
| Read/Glob/Grep | Knowledge retrieval or private attached files; file inspection in Data Analysis if available |
| Write/Edit and Bash/pandoc | Python in Data Analysis; bundled controlled-Markdown exporter; downloadable outputs |
| ~/.claude or ~/.codex career-data lookup | Privately supplied external career-data files/marker; no computer filesystem access |
| Notion MCP tool identifier | Explicitly configured Custom GPT Action, or a Project tool that actually supplies the needed operation |
| Desktop Commander/iCloud | Private sandbox artifacts for download; user saves externally |
| PreToolUse/Stop hooks | Instruction-level behavior only; no claim of a preventive runtime hook |
| Session-history/token APIs | Available conversation context only; unavailable history or exact usage stays unverified |
| Public career-data installation | Never: setup creates a separate private user bundle, preserving the shared kit |

Private career-data files use the canonical upstream layout and health checks. All expected_files in its marker must be present, including any extra user-owned files. Distinguish access denial from absence. Preserve the explicit update workflow and user review; never overwrite user data as part of refreshing this public kit.

The portable runtime ships chatgpt_export.py.txt and the unchanged upstream assemble_brief_cv.py.txt. Attach them to the private chat and materialize .py files only in its Data Analysis sandbox. The exporter's constrained parser accepts headers, paragraphs, bold/emphasis, the upstream custom-style spans/divs, and bullets; unsupported tables/code/raw HTML/images/links cause an error instead of content loss. Brief assembly preserves the upstream table template and validation. Personal template customization, multilingual fonts/layout review, and final user review remain required. Check actual runtime dependencies rather than assuming they are installed.

The optional Notion Actions schema uses the data-source API and Notion-Version 2025-09-03. Resolve a database's actual data source rather than treating its database ID as a data-source ID. A Project's tool availability is inspected independently; it has no Actions import step. Never declare a Notion write successful before its response.

## ChatGPT compatibility QA

Check both installation routes on every package update: pasteable instructions within their budget, three readable Knowledge files, complete upstream source coverage with stable labels, valid runtime/template files, current manifest/hash match, and a reproducible archive. Check all required reads and gates against the underlying upstream changes. Verify the standalone Python exports without pandoc; reject unsupported Markdown and missing templates/dependencies. Review optional Actions schema shape, authentication guidance, and operation names. Keep actual ChatGPT import/response, live connectors, host feature enablement, and offline fixtures as distinct outcomes. Report PASS/FAIL/BLOCKED/NOT RUN; never mark an untested live host as passed.
