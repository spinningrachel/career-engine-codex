# Career Engine for Codex and ChatGPT

Career Engine's career doctrine, reference templates, roles, and review gates come from [Career Engine for Claude](https://github.com/spinningrachel/career-engine-claude), pinned in `upstream-lock.json`. This parallel repository adapts that source for Codex and for **both ChatGPT Custom GPTs and Projects**. All three installation paths are maintained on every update.

**Personal career data never belongs in either public repository or package.** First-time users install and configure their own external **career-data** skill separately. Packages contain instructions, code, blank templates, and fictional test fixtures. Updating an installation replaces shared materials and preserves the user's private career-data and outputs.

| Host | Installation | Package |
|---|---|---|
| Codex | Register the GitHub marketplace and install the native plugin | [career-engine-codex.zip](https://github.com/spinningrachel/career-engine-codex/raw/refs/heads/main/career-engine-codex.zip) — native plugin distribution |
| ChatGPT Custom GPT | Extract the kit; paste GPT instructions and upload its three Knowledge files | [career-engine-chatgpt.zip](https://github.com/spinningrachel/career-engine-codex/raw/refs/heads/main/career-engine-chatgpt.zip) |
| ChatGPT Project | Extract the same kit; paste Project instructions and add its three knowledge files | Same ChatGPT ZIP |

The ChatGPT ZIP is an installation kit. ChatGPT does not import it as a Codex plugin; follow the configuration steps below. Both ZIPs are committed at the repository root with the matching source.

## Install in Codex — new users

Install [Node.js](https://nodejs.org/) if needed, then install and sign in to the current [Codex CLI](https://developers.openai.com/codex/cli):

```sh
npm install -g @openai/codex@latest
codex login
codex plugin marketplace add spinningrachel/career-engine-codex --ref main
codex plugin add career-engine@cheyfitz-codex
codex
```

Use a Codex version with `codex plugin` support; native installation was exercised with CLI `0.159.0-alpha.3`. In the new session, say: **“Use $career-engine-setup to configure my separate career-data skill.”** Supply your existing external skill if already configured. You can then invoke `$career-engine`, describe an operation, or use a specific skill such as `$source-open-roles`.

For a local repository checkout, substitute `codex plugin marketplace add /absolute/path/to/career-engine-codex` for the GitHub registration command, then install the same plugin. Read [plugin/CODEX-RUNTIME.md](plugin/CODEX-RUNTIME.md) for paths, tools, roles, and prerequisites. DOCX export requires Python 3.10+, pandoc, python-docx, and lxml. Tracker workflows require connected Notion operations. Hook protection requires a supporting Codex host and enabled hooks; installation alone does not prove hooks ran.

After an update merges, refresh the marketplace/plugin and start a new session:

```sh
codex plugin marketplace upgrade cheyfitz-codex
codex plugin add career-engine@cheyfitz-codex
codex
```

Native versions include the upstream commit and adapter hash to avoid stale installation caches. Keep career-data and outputs outside this shared plugin.

## Install in ChatGPT — Custom GPT

1. Download [career-engine-chatgpt.zip](https://github.com/spinningrachel/career-engine-codex/raw/refs/heads/main/career-engine-chatgpt.zip) and extract it.
2. Open the [GPT editor](https://chatgpt.com/gpts/editor). Creating/editing requires an eligible account and workspace permissions. In **Configure**, name the GPT **Career Engine** and paste **GPT-INSTRUCTIONS.txt** into **Instructions**.
3. Upload the three **knowledge/*.txt** files as **Knowledge**. These public files preserve the career workflows, roles, reference templates, and host mappings. Keep personal career-data out of reusable GPT Knowledge.
4. Enable **Data Analysis / Code Interpreter** for files and DOCX export, and **Web Search** for research, where offered. Save with **Only me** visibility.
5. Open the GPT and say: **“Run first-time Career Engine setup. Help me configure my separate career-data skill and return its files as private downloads.”** Provide existing career-data privately in the conversation if already configured.
6. For DOCX export, attach the needed **runtime/*.txt** and **templates/*.docx** files to the private conversation if Data Analysis cannot access them from Knowledge. The assistant materializes the Python helpers and checks dependencies before exporting.

Optional Notion tracker support: import **actions/notion-openapi.json** into the GPT's **Actions** and configure secure **API Key / Bearer** authentication with your own Notion integration. Share the relevant database with that integration and verify its read/query/write operations. Never put credentials in chat, Knowledge, or this repository. Full instructions are in [chatgpt/install.md](chatgpt/install.md), also shipped as **START-HERE.md** inside the ZIP.

## Install in ChatGPT — Project

1. Extract the same [ChatGPT ZIP](https://github.com/spinningrachel/career-engine-codex/raw/refs/heads/main/career-engine-chatgpt.zip).
2. Create a private **Career Engine** Project. In its **Project instructions/settings**, paste **PROJECT-INSTRUCTIONS.txt**.
3. Add the three **knowledge/*.txt** files to the Project's files. The ZIP itself does not register a plugin.
4. Start a chat **inside the Project** and say: **“Run first-time Career Engine setup using the Project instructions and knowledge. Keep my separately configured career-data and outputs private.”**
5. Supply external career-data privately in that chat or as deliberately selected private Project files, separately from public kit files. Save generated career-data downloads in your own external folder.
6. For DOCX export, use Data Analysis where available and attach the needed runtime helpers/templates to the chat. Use only web tools and connected apps actually available in the Project. Projects do not import Custom GPT Actions; tracker writeback requires an available tool with the necessary operations.

Both ChatGPT routes support text setup, coaching, supplied-JD analysis, CV/letter drafting, and prescribed review passes. DOCX export requires Data Analysis plus python-docx/lxml; the kit's controlled-Markdown exporter works without pandoc. Web research and live tracker operations require their respective capabilities. ChatGPT does not gain Claude/Codex hooks, background agents, local/iCloud filesystem access, or exact history/token APIs from this package. Missing required capabilities remain explicit workflow blockers.

To update either ChatGPT installation, download and extract the latest kit. Replace its public Instructions and three knowledge files in the GPT editor or Project settings; replace runtime/template files used for export. Remove old public copies, preserve separate private career-data and outputs, and start a new chat. Review and retest any changed optional Actions schema. `manifest.json` records the upstream commit, source coverage, and file hashes.

## Develop, package, and verify

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
bash tools/validate.sh
```

Install pandoc through the operating system's package manager. QA covers native compatibility, ChatGPT source coverage and instruction budgets, reproducible archives, portable and upstream DOCX exports, 45 personal-data guard cases, 11 question-gate cases, 512 mechanical checks, 26 relational checks, and repository/archive scans including Office XML. Six Claude hook-format assertions are translated to Codex equivalents; the career-doctrine checks remain intact. Run `python3 tools/check-codex-compatibility.py --install` for actual CLI installation in an isolated test configuration.

Every update follows [codex/update-contract.md](codex/update-contract.md), included as **UPDATE-CONTRACT.md in both packages** and read by the QA role and automated Codex review. Review Codex and ChatGPT compatibility separately from upstream semantic parity. Maintain this README and the packaged installation guide for all three paths. Rebuild **both** root ZIPs with `python3 tools/build.py`; validation rejects stale archives rather than silently replacing them.

To import an upstream version manually:

```sh
git clone https://github.com/spinningrachel/career-engine-claude.git /tmp/career-engine-upstream
python3 tools/port.py --source /tmp/career-engine-upstream
python3 tools/build.py
bash tools/validate.sh
```

Never hand-edit generated `plugin/`. Use `tools/port.py` for mechanical translations or `codex/overrides/` for semantic adaptations, then regenerate. ChatGPT adapters and its installation guide live in `chatgpt/`; `tools/build-chatgpt.py` packages all applicable generated doctrine with stable source labels. `upstream-lock.json` hashes generated native files; the ChatGPT manifest indexes every included source section. Commit both ZIPs, matching source, and any affected installation documentation.

## Automatic upstream updates

`.github/workflows/sync-upstream.yml` checks upstream main hourly and also accepts manual runs or a `career-engine-updated` repository dispatch. When upstream changes, it fetches the exact old/new commits, regenerates the port, validates, and runs the official `openai/codex-action` for semantic review and needed adaptations. It validates again, refuses modifications to automation controls, and opens or updates a single `sync/upstream` PR. An already-pending imported commit does not incur another Codex review. Failed tests or blocked reviews do not create an update PR.

**Activation requires the repository to exist on GitHub**, Actions enabled, workflow permission to create PRs, and a repository Actions secret named **CODEX_SYNC_API_KEY** containing an OpenAI API key. Enter it in GitHub's secure secret settings; never put its value in a file, environment draft, or chat. API usage is billed separately from a ChatGPT subscription. The GitHub Actions `GITHUB_TOKEN` handles branches and PRs; the agent's model invocation does not receive that write credential.

For an immediate push trigger, copy `tools/upstream-dispatch.yml` to `.github/workflows/codex-port-dispatch.yml` in **career-engine-claude**. Add a source-repository Actions secret **CODEX_PORT_DISPATCH_TOKEN** with access to the Codex repository's dispatch endpoint (fine-grained token with contents write on the target repository, or a suitable GitHub App token). The workflow does not forward source text or credentials to Codex; it emits a fixed event. The hourly schedule is a fallback when dispatch is not configured. GitHub schedules can be delayed.

This is automation by a new Codex run on each update; it does not wake this chat. A PR is the reviewable record. By default, after Codex review and all validation pass, the workflow requests a squash merge of the exact tested head. It refuses to merge if main changed during the run, and never bypasses GitHub branch protections. If repository rules block merging, the PR remains open. Set the repository Actions variable `CODEX_SYNC_AUTO_MERGE` to `false` to leave all updates for manual review.

## Verified scope and limitations

Offline validation covers actual native CLI installation, package/source integrity, hook payload adapters, fixture-based DOCX exports including the portable ChatGPT runtime, upstream doctrine QA, and personal-data scanning. It does **not** establish a live ChatGPT import/response, host hook enablement, authenticated Notion writes, or a personal career pipeline. These require the relevant account and separately authorized data/tools; unrun checks stay NOT RUN. Roles execute as distinct sequential passes unless the host and invoked workflow authorize delegation.

MIT license; upstream authorship is retained.
