# Career Engine for Codex

Codex-native packaging and runtime adapters for [Career Engine for Claude](https://github.com/spinningrachel/career-engine-claude). Career doctrine, reference templates, Python DOCX tools, and review gates are imported from the upstream commit recorded in `upstream-lock.json`. Codex-specific adapters and synchronization controls live outside generated `plugin/`.

**No real user career data belongs in either repository or plugin.** First-time users install and configure their own external **career-data** skill separately. These repositories contain code, instructions, blank templates, and fictional test fixtures only. Generated documents and update prompts go to an external output folder. Installation does not import a user's Claude configuration or career data.

## Install in Codex

Use a current Codex CLI with `codex plugin` support. The native format and local installation were checked with Codex CLI `0.159.0-alpha.3`.

```sh
codex plugin marketplace add spinningrachel/career-engine-codex --ref main
codex plugin add career-engine@cheyfitz-codex
```

For a local checkout:

```sh
codex plugin marketplace add /absolute/path/to/career-engine-codex
codex plugin add career-engine@cheyfitz-codex
```

Start a new session after installation. Invoke `$career-engine`, describe the operation, or use a specific skill such as `$career-engine-setup` or `$source-open-roles`. The setup workflow prepares a **separate**, user-owned career-data skill; it never fills the shared plugin's templates. Follow `plugin/CODEX-RUNTIME.md` for file discovery, connectors, role execution, and host-specific differences.

After an upstream update merges, refresh the marketplace and plugin, then start a new session:

```sh
codex plugin marketplace upgrade cheyfitz-codex
codex plugin add career-engine@cheyfitz-codex
```

Each generated plugin version includes both the upstream commit and a Codex-adapter hash, so updates do not reuse a stale installation cache.

Python 3.10+, pandoc, python-docx, and lxml are required for DOCX export. Notion workflows additionally need a connected Notion integration with the required database operations. The plugin does not auto-connect external accounts. Codex plugin hook support and hook enablement are required for the pre-write personal-data and mid-run question guards. Build/repository scans remain mandatory whether hooks are available or not.

## Develop and verify

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
bash tools/validate.sh
```

Install pandoc using the operating system's package manager if absent. Validation includes native port tests, upstream DOCX export fixtures, 45 personal-data guard cases, 11 question-gate cases, 512 mechanical checks, 26 relational checks, and personal-data scans over the full publishable repository and archive, including Office XML. Six Claude hook-format assertions are translated to native Codex equivalents; career-doctrine checks stay in place.

`python3 tools/build.py` produces `dist/career-engine-codex.zip`. This is a ZIP distribution of the plugin directory, not a Claude `.plugin` upload; Codex installs through its marketplace. Test harnesses are omitted from the product archive.

To update manually:

```sh
git clone https://github.com/spinningrachel/career-engine-claude.git /tmp/career-engine-upstream
python3 tools/port.py --source /tmp/career-engine-upstream
bash tools/validate.sh
```

Generated `plugin/` files are never edited directly. Change `tools/port.py` for mechanical translation, or add a semantic override under `codex/overrides/` with the same relative path as the target plugin file. Regenerate and review the diff. `upstream-lock.json` hashes every generated file so accidental edits or stale outputs fail validation.

## Automatic upstream updates

`.github/workflows/sync-upstream.yml` checks upstream main hourly and also accepts manual runs or a `career-engine-updated` repository dispatch. When upstream changes, it fetches the exact old/new commits, regenerates the port, validates, and runs the official `openai/codex-action` for semantic review and needed adaptations. It validates again, refuses modifications to automation controls, and opens or updates a single `sync/upstream` PR. An already-pending imported commit does not incur another Codex review. Failed tests or blocked reviews do not create an update PR.

**Activation requires the repository to exist on GitHub**, Actions enabled, workflow permission to create PRs, and a repository Actions secret named **CODEX_SYNC_API_KEY** containing an OpenAI API key. Enter it in GitHub's secure secret settings; never put its value in a file, environment draft, or chat. API usage is billed separately from a ChatGPT subscription. The GitHub Actions `GITHUB_TOKEN` handles branches and PRs; the agent's model invocation does not receive that write credential.

For an immediate push trigger, copy `tools/upstream-dispatch.yml` to `.github/workflows/codex-port-dispatch.yml` in **career-engine-claude**. Add a source-repository Actions secret **CODEX_PORT_DISPATCH_TOKEN** with access to the Codex repository's dispatch endpoint (fine-grained token with contents write on the target repository, or a suitable GitHub App token). The workflow does not forward source text or credentials to Codex; it emits a fixed event. The hourly schedule is a fallback when dispatch is not configured. GitHub schedules can be delayed.

This is automation by a new Codex run on each update; it does not wake this chat. A PR is the reviewable record. By default, after Codex review and all validation pass, the workflow requests a squash merge of the exact tested head. It refuses to merge if main changed during the run, and never bypasses GitHub branch protections. If repository rules block merging, the PR remains open. Set the repository Actions variable `CODEX_SYNC_AUTO_MERGE` to `false` to leave all updates for manual review.

## Verified scope and limitations

The initial port is verified for native plugin installation, role-skill packaging, native hook payload adaptation, fixture-based DOCX export, upstream doctrine QA, and packaging without personal data. There is no live-user career-data or Notion end-to-end validation in CI. Claude Desktop/Cowork installation and exact token-accounting/history-search APIs have no guaranteed Codex equivalent; see the runtime contract. Roles execute as distinct sequential passes by default, with delegation only where the host and invoked workflow allow it. Connected-tool names are discovered at runtime rather than copied from Claude.

MIT license; upstream authorship is retained.
