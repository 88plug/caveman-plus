#!/bin/bash
# caveman — global installer for Codex
# Installs compact always-on Caveman hooks + global skills.
set -euo pipefail

if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: node required."
  exit 1
fi

CODEX_DIR="${CODEX_HOME:-$HOME/.codex}"
HOOKS_DIR="$CODEX_DIR/hooks"
CONFIG_PATH="$CODEX_DIR/config.toml"
HOOKS_PATH="$CODEX_DIR/hooks.json"
SKILLS_DIR="$HOME/.agents/skills"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

mkdir -p "$HOOKS_DIR" "$SKILLS_DIR"
mkdir -p "$SKILLS_DIR/caveman" "$SKILLS_DIR/caveman-commit"

cp "$SCRIPT_DIR/package.json" "$HOOKS_DIR/package.json"
cp "$SCRIPT_DIR/caveman-config.js" "$HOOKS_DIR/caveman-config.js"
cp "$SCRIPT_DIR/codex-caveman-activate.js" "$HOOKS_DIR/codex-caveman-activate.js"
cp "$SCRIPT_DIR/codex-caveman-mode-tracker.js" "$HOOKS_DIR/codex-caveman-mode-tracker.js"

cp "$ROOT_DIR/skills/caveman/SKILL.md" "$SKILLS_DIR/caveman/SKILL.md"
cp "$ROOT_DIR/skills/caveman-commit/SKILL.md" "$SKILLS_DIR/caveman-commit/SKILL.md"
rm -rf "$SKILLS_DIR/caveman-review"

touch "$CONFIG_PATH"
touch "$HOOKS_PATH"

CAVEMAN_CODEX_CONFIG="$CONFIG_PATH" node <<'NODE'
const fs = require('fs');

const configPath = process.env.CAVEMAN_CODEX_CONFIG;
let text = fs.readFileSync(configPath, 'utf8');

if (!text.trim()) {
  text = '[features]\ncodex_hooks = true\n';
} else if (/\[features\][\s\S]*?^\s*codex_hooks\s*=.*$/m.test(text)) {
  text = text.replace(/(^\s*codex_hooks\s*=.*$)/m, 'codex_hooks = true');
} else if (/\[features\]/m.test(text)) {
  text = text.replace(/\[features\]\n/, '[features]\ncodex_hooks = true\n');
} else {
  if (!text.endsWith('\n')) text += '\n';
  text += '\n[features]\ncodex_hooks = true\n';
}

fs.writeFileSync(configPath, text);
NODE

CAVEMAN_CODEX_HOOKS="$HOOKS_PATH" CAVEMAN_CODEX_DIR="$CODEX_DIR" node <<'NODE'
const fs = require('fs');
const path = require('path');

const hooksPath = process.env.CAVEMAN_CODEX_HOOKS;
const codexDir = process.env.CAVEMAN_CODEX_DIR;
const hooksDir = path.join(codexDir, 'hooks');

let config = {};
const raw = fs.readFileSync(hooksPath, 'utf8').trim();
if (raw) config = JSON.parse(raw);
if (!config.hooks) config.hooks = {};

const startCmd = `node "${path.join(hooksDir, 'codex-caveman-activate.js')}"`;
const promptCmd = `node "${path.join(hooksDir, 'codex-caveman-mode-tracker.js')}"`;

function ensureEvent(name) {
  if (!Array.isArray(config.hooks[name])) config.hooks[name] = [];
}

function hasCommand(event, needle) {
  return config.hooks[event].some(entry =>
    Array.isArray(entry.hooks) &&
    entry.hooks.some(hook => typeof hook.command === 'string' && hook.command.includes(needle))
  );
}

ensureEvent('SessionStart');
if (!hasCommand('SessionStart', 'codex-caveman-activate.js')) {
  config.hooks.SessionStart.push({
    matcher: 'startup|resume',
    hooks: [{
      type: 'command',
      command: startCmd,
      timeout: 5,
      statusMessage: 'Loading caveman mode'
    }]
  });
}

ensureEvent('UserPromptSubmit');
if (!hasCommand('UserPromptSubmit', 'codex-caveman-mode-tracker.js')) {
  config.hooks.UserPromptSubmit.push({
    hooks: [{
      type: 'command',
      command: promptCmd,
      timeout: 5
    }]
  });
}

fs.writeFileSync(hooksPath, JSON.stringify(config, null, 2) + '\n');
NODE

echo "Installed Codex-global Caveman."
echo "  Config: $CONFIG_PATH"
echo "  Hooks:  $HOOKS_PATH"
echo "  Skills: $SKILLS_DIR/{caveman,caveman-commit}"
echo "Restart Codex. Default mode: env/config driven (fallback full)."
