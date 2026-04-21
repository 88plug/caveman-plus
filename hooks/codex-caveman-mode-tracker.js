#!/usr/bin/env node
// caveman — Codex UserPromptSubmit hook
//
// Tracks on/off and mode switches, then emits a very small per-turn reminder.

const fs = require('fs');
const path = require('path');
const os = require('os');
const { GENERAL_MODES, getDefaultMode, safeWriteFlag, readFlag, normalizeMode } = require('./caveman-config');

const codexDir = process.env.CODEX_HOME || path.join(os.homedir(), '.codex');
const flagPath = path.join(codexDir, '.caveman-active');
const generalModePath = path.join(codexDir, '.caveman-general-mode');
const explicitOffPath = path.join(codexDir, '.caveman-explicit-off');
const GENERAL_MODE_SET = new Set(GENERAL_MODES.map(normalizeMode));
const AUTO_RESET_MODES = new Set(['commit', 'review']);

function setMode(mode) {
  if (mode === 'off') {
    clearFile(flagPath);
    return;
  }
  safeWriteFlag(flagPath, mode);
}

function clearFile(targetPath) {
  try { fs.unlinkSync(targetPath); } catch (e) {}
}

function setExplicitOff() {
  safeWriteFlag(explicitOffPath, 'off');
}

function clearExplicitOff() {
  clearFile(explicitOffPath);
}

function isExplicitOff() {
  return readFlag(explicitOffPath) === 'off';
}

function setGeneralMode(mode) {
  const normalized = normalizeMode(mode);
  if (!GENERAL_MODE_SET.has(normalized)) return;
  safeWriteFlag(generalModePath, normalized);
}

function getGeneralMode() {
  const saved = normalizeMode(readFlag(generalModePath));
  if (GENERAL_MODE_SET.has(saved)) return saved;

  const fallback = normalizeMode(getDefaultMode());
  if (GENERAL_MODE_SET.has(fallback)) return fallback;

  return 'full';
}

function restoreGeneralMode() {
  const mode = getGeneralMode();
  clearExplicitOff();
  setMode(mode);
  return mode;
}

function isCommitTask(prompt) {
  return (
    /\b(commit message|conventional commit)\b/i.test(prompt) ||
    /\b(write|generate|draft|create)\b.*\bcommit\b/i.test(prompt) ||
    /\bcommit\b.*\bmessage\b/i.test(prompt) ||
    /^\/commit\b/i.test(prompt)
  );
}

function isReviewTask(prompt) {
  return (
    /\bcode review\b/i.test(prompt) ||
    /\breview (this )?(pr|diff|patch|code)\b/i.test(prompt) ||
    /\bpull request review\b/i.test(prompt) ||
    /^\/review\b/i.test(prompt)
  );
}

let input = '';
process.stdin.on('data', chunk => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input || '{}');
    const prompt = (data.prompt || '').trim().toLowerCase();

    if (
      /\b(stop|disable|deactivate|turn off)\b.*\bcaveman\b/i.test(prompt) ||
      /\bcaveman\b.*\b(stop|disable|deactivate|turn off)\b/i.test(prompt) ||
      /\bnormal mode\b/i.test(prompt)
    ) {
      setExplicitOff();
      setMode('off');
      return;
    }

    if (prompt.startsWith('/caveman-review')) {
      clearExplicitOff();
      setMode('review');
    } else if (prompt.startsWith('/caveman-commit')) {
      clearExplicitOff();
      setMode('commit');
    } else if (prompt.startsWith('/caveman')) {
      const parts = prompt.split(/\s+/);
      const arg = normalizeMode(parts[1] || '');
      if (arg === 'lite') setMode('lite');
      else if (arg === 'full') setMode('full');
      else if (arg === 'full-plus') setMode('full-plus');
      else if (arg === 'ultra') setMode('ultra');
      else if (arg === 'mello-lite') setMode('mello-lite');
      else if (arg === 'mello') setMode('mello');
      else if (arg === 'mello-ultra') setMode('mello-ultra');
      else if (arg === 'off') setMode('off');
      else setMode(getGeneralMode());

      if (arg === 'off') {
        setExplicitOff();
      } else {
        clearExplicitOff();
        const active = normalizeMode(readFlag(flagPath));
        if (GENERAL_MODE_SET.has(active)) setGeneralMode(active);
      }
    } else if (
      /\b(activate|enable|start|use|talk like)\b.*\bcaveman\b/i.test(prompt) ||
      /\bcaveman\b.*\b(mode|activate|enable|start)\b/i.test(prompt)
    ) {
      restoreGeneralMode();
    } else if (isCommitTask(prompt)) {
      clearExplicitOff();
      setMode('commit');
    } else if (isReviewTask(prompt)) {
      setMode('off');
      return;
    } else {
      const active = normalizeMode(readFlag(flagPath));
      if (!active) {
        if (!isExplicitOff()) restoreGeneralMode();
      } else if (AUTO_RESET_MODES.has(active)) {
        if (!isExplicitOff()) restoreGeneralMode();
      }
    }

    const activeMode = readFlag(flagPath);
    if (!activeMode) return;

    const reminders = {
      lite: 'CAVEMAN lite active. Concise, direct, low-filler prose.',
      full: 'CAVEMAN full active. Terse. Drop filler/articles. Fragments OK. Code/commits/security normal.',
      'full-plus': 'CAVEMAN full-plus active. English only. Newest ask only. One path. Explainers: plain mechanism prose. Bug-fix/debug: root cause + direct fix, no extra caveat unless needed. Summary/comment/note/PR/checklist: polished artifact matching requested format, plus one obvious benefit if useful. No workspace inspection unless asked to patch/run here. Code/commits/security normal.',
      ultra: 'CAVEMAN ultra active. Very terse. Abbrev when clear. Code/commits/security normal.',
      'mello-lite': 'CAVEMAN mello-lite active. Light same-language compression. Code/commits/security normal.',
      mello: 'CAVEMAN mello active. Strong same-language compression. Code/commits/security normal.',
      'mello-ultra': 'CAVEMAN mello-ultra active. Extreme same-language compression. Code/commits/security normal.',
      commit: 'CAVEMAN commit active. Conventional commit. Terse. Why over what.',
      review: 'CAVEMAN review active. One line per finding: location, problem, fix.'
    };

    const additionalContext = reminders[activeMode];
    if (!additionalContext) return;

    process.stdout.write(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'UserPromptSubmit',
        additionalContext
      }
    }));
  } catch (e) {
    // Silent fail
  }
});
