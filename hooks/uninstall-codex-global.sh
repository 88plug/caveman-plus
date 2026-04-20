#!/bin/bash
# caveman — global uninstaller for Codex
set -euo pipefail

if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: node required."
  exit 1
fi

CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
HOOKS_DIR="$CODEX_DIR/hooks"
HOOKS_PATH="$CODEX_DIR/hooks.json"
FLAG_PATH="$CODEX_DIR/.caveman-active"
SKILLS_DIR="$HOME/.agents/skills"

rm -f \
  "$HOOKS_DIR/package.json" \
  "$HOOKS_DIR/caveman-config.js" \
  "$HOOKS_DIR/codex-caveman-activate.js" \
  "$HOOKS_DIR/codex-caveman-mode-tracker.js" \
  "$FLAG_PATH"

CAVEMAN_CODEX_HOOKS="$HOOKS_PATH" node <<'NODE'
const fs = require('fs');

const hooksPath = process.env.CAVEMAN_CODEX_HOOKS;
if (!fs.existsSync(hooksPath)) process.exit(0);

const raw = fs.readFileSync(hooksPath, 'utf8').trim();
if (!raw) process.exit(0);
const config = JSON.parse(raw);

for (const event of ['SessionStart', 'UserPromptSubmit']) {
  if (!Array.isArray(config.hooks?.[event])) continue;
  config.hooks[event] = config.hooks[event].filter(entry =>
    !(Array.isArray(entry.hooks) && entry.hooks.some(hook =>
      typeof hook.command === 'string' &&
      (hook.command.includes('codex-caveman-activate.js') || hook.command.includes('codex-caveman-mode-tracker.js'))
    ))
  );
  if (config.hooks[event].length === 0) delete config.hooks[event];
}

if (config.hooks && Object.keys(config.hooks).length === 0) delete config.hooks;
fs.writeFileSync(hooksPath, JSON.stringify(config, null, 2) + '\n');
NODE

rm -rf \
  "$SKILLS_DIR/caveman" \
  "$SKILLS_DIR/caveman-commit" \
  "$SKILLS_DIR/caveman-review"

echo "Removed Codex-global Caveman hooks and skills."
