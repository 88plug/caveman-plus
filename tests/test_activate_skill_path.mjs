#!/usr/bin/env node
// Regression: SessionStart must load skills/caveman/SKILL.md from src/hooks layout
// and default mode must be full-plus (88plug edition).
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const require = createRequire(import.meta.url);
const { getDefaultMode, VALID_MODES } = require(path.join(root, 'src/hooks/caveman-config.js'));

function assert(cond, msg) {
  if (!cond) {
    console.error('FAIL:', msg);
    process.exit(1);
  }
}

assert(VALID_MODES.includes('full-plus'), 'VALID_MODES must include full-plus');
assert(getDefaultMode() === 'full-plus', `default mode is ${getDefaultMode()}, want full-plus`);

const env = { ...process.env };
delete env.CAVEMAN_DEFAULT_MODE;
// Isolate from user config
env.XDG_CONFIG_HOME = path.join(root, 'tests', '.tmp-xdg-no-config');
env.CLAUDE_CONFIG_DIR = path.join(root, 'tests', '.tmp-claude-no-config');
env.CLAUDE_PLUGIN_ROOT = root;

const r = spawnSync(process.execPath, [path.join(root, 'src/hooks/caveman-activate.js')], {
  env,
  encoding: 'utf8',
  timeout: 5000,
});
assert(r.status === 0, `activate exit ${r.status}: ${r.stderr}`);
const out = r.stdout || '';
assert(out.includes('CAVEMAN MODE ACTIVE'), 'activate must emit active banner');
assert(out.includes('full-plus'), `activate must mention full-plus, got: ${out.slice(0, 200)}`);
// SKILL.md body markers (not fallback-only mini ruleset)
assert(out.includes('88plug edition'), 'must inject SKILL.md (88plug edition marker)');
assert(out.includes('Intensity') || out.includes('artifact-first'), 'must include intensity/rules body');
assert(out.length > 400, 'output too short for full SKILL inject');

console.log('ok: activate loads SKILL.md; default full-plus');
