# Codex runtime contract

Read this before any Career Engine workflow. This contract governs host-specific instructions in imported doctrine; career-writing rules and pipeline gates stay authoritative in the imported files.

## Locate files and personal data

Resolve CAREER_ENGINE_ROOT from the active skill's installed path: walk upward to the ancestor containing .codex-plugin/plugin.json. For a role skill under skills/role-NAME, the root is two directories above SKILL.md. Do not assume the current working directory or a platform-injected shell variable. Pass the resolved absolute root and CAREER_DATA in every role handoff. When using shell tools, set those variables explicitly in that command.

Find career-data through the host skill catalog, an explicitly supplied CAREER_DATA directory, the connected workspace, ~/.agents/skills/career-data, or ~/.codex/skills/career-data. Confirm career-data-marker.json and the required files using the imported discovery and health checks. A denied path is an access blocker, not proof the skill is absent. Do not read another user's filesystem or search outside authorized directories. Never replace a configured user's missing personal data with shipped blank templates. Shipped templates are for the new-user setup workflow only.

Personal data stays external to this shared plugin. Export outputs and update prompts into the configured external output folder. Existing career-data is changed only through the explicit update workflow and user review. Codex does not require a Claude Desktop installation: an explicitly requested new career-data skill can be created in a user-selected external directory, with marker, SKILL.md, and the same references layout. Use the source interview and schema; leave unknown facts unresolved and request them instead of guessing.

## Tools and roles

Claude's Read/Glob/Grep mean Codex file reading and search; Bash means the available shell execution tool; Write/Edit mean Codex's file editing tools. Use rg for searches. WebSearch/WebFetch mean the host's available search/fetch tools or an authorized HTTP request. AskUserQuestion means the host's user-input tool. Do not call tool names that do not exist.

Claude Task/Agent and career-engine:NAME identify a logical role, not a Codex agent type. Load skills/role-NAME/SKILL.md (or agents/NAME.md if no role skill exists), apply its inputs, and execute its work sequentially by default. If the host exposes delegation and the invoked workflow authorizes it, hand the role instructions, absolute paths, and full required parameters to a Codex agent. File-based R-41 output protocols apply equally in sequential and delegated execution. Reviewer and gatekeeper roles perform distinct passes; never silently omit them or claim an independent agent ran when it did not. Unsupported Claude frontmatter such as tools, model, memory, and disallowedTools is not an access policy in Codex; enforce scope through role instructions and host permissions.

Treat legacy /career-engine:COMMAND invocations as routing examples. In Codex invoke $career-engine or the relevant installed skill by name, with the desired operation in the message. Automatic completion means finish the authorized queue and preserve genuine blockers; it does not permit inventing credentials or overriding host approval rules.

## Connectors and storage

Discover connected tools by capability. Imported mcp__claude_ai_Notion, mcp__notionApi, Desktop Commander, directory-access, LinkedIn, and scheduled-task names are examples from the upstream host; they are not callable Codex identifiers. Bind the installed Notion tools only after inspecting their schemas. Verify the required database read/query/update operations before a Notion pipeline; writes require user authorization from the workflow. If unsupported, report the concrete missing capability. Do not invent a connector ID or claim that CSV/Sheets has an implemented adapter: the shipped adapter is Notion.

Use the Codex filesystem directly for pandoc, Python, local files, and output directories. iCloud is an optional user-mounted location, not a cloud prerequisite. On path denial use the host's supported permission flow; a Claude Desktop directory-request API has no meaning here. No connectors are auto-installed or connected by this port.

Claude history-search tools and token-accounting hooks have no equivalent guarantee in Codex. Use available session history if provided; otherwise say that the requested history or usage metric is unavailable. Never fabricate token totals. The Codex port adapts question-gate transcript detection to Codex function-call and patch records. It cannot enforce a prompt Stop hook on hosts that do not support it: follow queue-completion rules directly. It retains native pre-write personal-data and mid-run question hooks, plus build-time scans.

## Hooks and prerequisites

The native plugin declares a PreToolUse hook that normalizes Codex shell/apply_patch payloads into the upstream detector. Hooks require a Codex host/version supporting plugin hooks and hook enablement. Plugin installation alone does not prove a hook ran. The artifact scanner is also mandatory. Shell detection is conservative and cannot identify every computed write; user review and package scanning remain required.

Python 3.10+ with python-docx and lxml, and pandoc on PATH, are required for export. Run the existing export fixture tests and actual DOCX generation to validate. Claude CLI commands, .plugin uploads, Cowork installation, and /skill-creator are replaced by the Codex installation and external career-data procedures in this contract.
