#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== smoke: plugin.json is valid JSON ==="
python3 -c "
import json
p = json.load(open('.claude-plugin/plugin.json'))
assert 'hooks' in p, 'plugin.json missing hooks'
assert 'mcpServers' not in p, 'caveman-shrink must not be auto-wired as mcpServers (middleware needs upstream)'
assert '_note' in p and 'caveman-shrink' in p['_note'], 'plugin.json missing _note documenting optional caveman-shrink middleware'
print('  ok: .claude-plugin/plugin.json')
"

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

echo "=== smoke: caveman-shrink middleware loads ==="
SHRINK_DIR=src/mcp-servers/caveman-shrink
node --check "$SHRINK_DIR/index.js" && echo "  ok: $SHRINK_DIR/index.js syntax"
node --check "$SHRINK_DIR/compress.js" && echo "  ok: $SHRINK_DIR/compress.js syntax"
node -e "
const path = require('path');
const c = require(path.resolve('$SHRINK_DIR/compress.js'));
if (typeof c.compress !== 'function') throw new Error('compress export missing');
if (typeof c.compressDescriptionsInPlace !== 'function') throw new Error('compressDescriptionsInPlace export missing');
const r = c.compress('The function just returns the value');
if (!r || typeof r.compressed !== 'string') throw new Error('compress() returned invalid shape');
if (r.after >= r.before) throw new Error('expected size reduction from sample prose');
console.log('  ok: compress.js loads and compresses');
"
# Middleware is not a standalone MCP server — missing upstream must exit 2.
set +e
node "$SHRINK_DIR/index.js" >/dev/null 2>&1
code=$?
set -e
if [ "$code" -ne 2 ]; then
  echo "  FAIL: index.js without upstream should exit 2, got $code" >&2
  exit 1
fi
echo "  ok: index.js refuses launch without upstream (exit 2)"

echo "=== smoke: all good ==="
