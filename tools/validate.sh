#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/check-codex-compatibility.py
python3 tools/check-chatgpt-compatibility.py
python3 -m unittest discover -s tests -v
python3 plugin/skills/career-engine-export/scripts/test_assemble_brief_cv.py
bash plugin/scripts/test-personal-data-guard.sh
bash plugin/scripts/test-ask-question-gate.sh
python3 plugin/scripts/qa-parity.py plugin
bash plugin/scripts/qa-mechanical.sh plugin
python3 tools/scan-repo.py
