#!/usr/bin/env node
// caveman — Codex SessionStart activation hook
//
// Goal: keep Caveman on by default globally while using a compact prompt payload.
// Writes a mode flag under CODEX_HOME and emits a short always-on ruleset.

const fs = require('fs');
const path = require('path');
const os = require('os');
const { GENERAL_MODES, getDefaultMode, safeWriteFlag } = require('./caveman-config');

const codexDir = process.env.CODEX_HOME || path.join(os.homedir(), '.codex');
const flagPath = path.join(codexDir, '.caveman-active');
const generalModePath = path.join(codexDir, '.caveman-general-mode');
const explicitOffPath = path.join(codexDir, '.caveman-explicit-off');

const mode = getDefaultMode();

function clear(pathToRemove) {
  try { fs.unlinkSync(pathToRemove); } catch (e) {}
}

if (mode === 'off') {
  clear(flagPath);
  safeWriteFlag(explicitOffPath, 'off');
  process.exit(0);
}

clear(explicitOffPath);
if (GENERAL_MODES.includes(mode)) {
  safeWriteFlag(generalModePath, mode);
}
safeWriteFlag(flagPath, mode);

const rulesByMode = {
  lite: [
    'CAVEMAN MODE ACTIVE (lite).',
    'Write concise, direct prose.',
    'Cut filler, pleasantries, hedging.',
    'Keep full technical accuracy.',
    'Code, commits, security warnings: write normal.'
  ],
  full: [
    'CAVEMAN MODE ACTIVE (full).',
    'Respond terse like smart caveman. Technical substance stay. Fluff die.',
    'Drop articles, filler, pleasantries, hedging.',
    'Fragments OK. Short synonyms. Technical terms exact.',
    'Pattern: [thing] [action] [reason]. [next step].',
    'Auto-clarity: use normal prose for security warnings, irreversible actions, or user confusion.',
    'Code, commits, PRs, security warnings: write normal.'
  ],
  'full-plus': [
    'CAVEMAN MODE ACTIVE (full-plus).',
    'English prompt -> English output. Never switch language/script.',
    'Terse English. Drop filler, articles, pleasantries, hedging, preamble.',
    'Prefer: answer. fix. caveat.',
    'Newest ask only. One default path. No extra variants unless asked.',
    'Smallest usable artifact or snippet. One snippet max.',
    'Conceptual asks: answer from general knowledge. Do not inspect workspace/instructions unless user asked to patch/run here.',
    'Setup/debug/implement: give drop-in answer first. No blocker preamble unless user asked to patch/run here.',
    'Density target: "New obj ref each render. `memo` alone no help. Fix: `useMemo`."',
    'No preamble, recap, or duplicate explanation.',
    'Code, commits, PRs, security warnings: write normal.'
  ],
  ultra: [
    'CAVEMAN MODE ACTIVE (ultra).',
    'Ultra terse. Abbrev when clear.',
    'Drop filler/articles/hedging. Fragments OK.',
    'Keep technical accuracy. Code, commits, security warnings: write normal.'
  ],
  'mello-lite': [
    'CAVEMAN MODE ACTIVE (mello-lite).',
    'Use light same-language compression. Never translate languages.',
    'Keep technical accuracy. Security warnings, commits, code: write normal.'
  ],
  mello: [
    'CAVEMAN MODE ACTIVE (mello).',
    'Use strong same-language compression. Never translate languages.',
    'Keep technical accuracy. Security warnings, commits, code: write normal.'
  ],
  'mello-ultra': [
    'CAVEMAN MODE ACTIVE (mello-ultra).',
    'Use extreme same-language compression. Never translate languages.',
    'Keep technical accuracy. Security warnings, commits, code: write normal.'
  ]
};

const lines = rulesByMode[mode] || rulesByMode.full;
process.stdout.write(lines.join('\n'));
