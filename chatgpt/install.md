# Install Career Engine in ChatGPT

This ZIP is a **ChatGPT installation kit**, not a one-click plugin importer. Extract it first. It supports both a reusable Custom GPT and a ChatGPT Project. Neither route installs Codex or Claude command hooks. Feature availability depends on the ChatGPT account/workspace; the same knowledge and instructions support text workflows without external accounts.

## Option A: Custom GPT

1. Open ChatGPT's [GPT editor](https://chatgpt.com/gpts/editor). Creating/editing GPTs requires an eligible account and any workspace permission. If the editor is unavailable, use the Project route below.
2. In **Configure**, name it **Career Engine**. Paste **GPT-INSTRUCTIONS.txt** into **Instructions**.
3. Upload the three **knowledge/*.txt** files into **Knowledge**. Do not upload the whole ZIP as Knowledge. These are public rules and blank templates only; never add personal career-data to a reusable/shared GPT's Knowledge.
4. Enable **Data Analysis / Code Interpreter** for generated files and DOCX export, and **Web Search** for research, where available. Start with **Only me** visibility. The kit does not contain credentials or create connected accounts.
5. Save and open the GPT. Say: **"Run first-time Career Engine setup. Help me configure my separate career-data skill and return its files as private downloads."** Supply existing career-data privately in the conversation if you already have it.
6. For exports, attach the needed runtime/*.txt and templates/*.docx files to that private conversation if they are not accessible to Data Analysis from Knowledge. The assistant checks its dependencies and runs the bundled Python exporter; it must report if file execution is unavailable.

Optional Notion integration: in the GPT's **Actions**, import **actions/notion-openapi.json**. Configure API-key authentication with **Bearer** authorization using your own Notion integration credential in the editor's secure authentication field. Share the required database with that integration. Do not paste a credential into Instructions, Knowledge, this repository, or chat. Verify the actual database/data-source read, query, page/property update, and block operations before using tracker pipelines. Creating a publicly shared GPT with Actions may require additional privacy-policy/workspace settings; this kit's default is personal use. Projects do not import this Actions schema.

## Option B: ChatGPT Project

1. In ChatGPT, create a **new Project** named **Career Engine**, and keep it private unless you deliberately want its participants to access its contents.
2. Open **Project instructions/settings** and paste **PROJECT-INSTRUCTIONS.txt** as the instructions.
3. Add the three **knowledge/*.txt** files to the Project's files. Do not add the whole ZIP and expect it to register a plugin. Observe the account's current file limits; runtime/template files can be attached only to the conversation that needs an export.
4. Start a chat **inside that Project**. Say: **"Run first-time Career Engine setup using the Project instructions and knowledge. Keep my separately configured career-data and outputs private."**
5. Provide your external career-data files privately in that chat or as deliberately selected private Project files, separate from the kit's public knowledge. The assistant does not search your computer or install a native .skill. It can return a private career-data bundle for you to save outside the package.
6. For DOCX exports use Data Analysis if offered in the Project chat and attach the needed runtime/*.txt and template .docx files. For research use available web tools. Use connected Notion capabilities only if the Project actually exposes the required operations; a read-only app cannot perform tracker writeback. The Custom GPT Actions schema cannot be imported into a Project.

## What works and what needs a host capability

Career setup/interviews, coaching, analysis of a supplied JD, CV/letter drafting, reviewer/gatekeeper passes, and content planning use the uploaded doctrine and privately supplied career-data. Python DOCX export requires Data Analysis plus python-docx/lxml; the bundled exporter handles the controlled CV syntax without pandoc. Live web research requires web tools. Notion tracker pipelines require verified connector/Action operations. Full file-based queues require a file runtime; a text-only conversation must not pretend to execute one. Claude/Codex hooks, background agents, local/iCloud writes, and token/history APIs are not installed by this kit.

## Updating an existing installation

Download the latest career-engine-chatgpt.zip and extract it. In the Custom GPT editor replace GPT Instructions and the three public Knowledge files; in a Project replace Project instructions and those same public files. Replace runtime/template files used for export. Keep the user's separate career-data and prior outputs untouched. Start a new chat with the updated public materials and verify the source commit in manifest.json. Do not accumulate old and new copies of the public knowledge. If using Notion Actions, review any schema changes and retest the required operations with your own connection.

## Documentation sources and validation

Supported configuration concepts: OpenAI's [Creating a GPT](https://help.openai.com/en/articles/8554397-creating-a-gpt), [Knowledge in GPTs](https://help.openai.com/en/articles/8843948-knowledge-in-gpts), [Projects in ChatGPT](https://help.openai.com/en/articles/10169521-using-projects-in-chatgpt), and [official Notion GPT Actions example](https://github.com/openai/openai-cookbook/blob/main/examples/chatgpt/gpt_actions_library/gpt_action_notion.ipynb). UI labels, account eligibility, and file limits can change; use the live editor's equivalent fields. This package's structure, instruction budget, source coverage, data scans, and Python exports are validated offline. A live import/response and authenticated Notion write require testing in the user's ChatGPT account and are not claimed by those offline checks.
