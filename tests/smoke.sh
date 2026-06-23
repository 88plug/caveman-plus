#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== smoke: plugin.json is valid JSON ==="
python3 -c "import json; json.load(open('.claude-plugin/plugin.json')); print('  ok: .claude-plugin/plugin.json')"

echo "=== smoke: hook node syntax ==="
for f in src/hooks/*.js; do
    [ -e "$f" ] || continue
    node --check "$f" && echo "  ok: $f"
done

echo "=== smoke: hook bash syntax ==="
for f in src/hooks/*.sh; do
    [ -e "$f" ] || continue
    bash -n "$f" && echo "  ok: $f"
done

echo "=== smoke: all good ==="
