#!/usr/bin/env bash
# test.sh — end-to-end check of mini-grug.sh against a throwaway data dir and settings file.
# Does not touch ~/.mini-grug or ~/.claude/settings.json. Does not open a window (hooks and JSON only).
# Usage: bash scripts/test.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MG="$HERE/mini-grug.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
# The data dir has a space on purpose: hook commands must stay valid when $HOME contains one.
export MINI_GRUG_DIR="$TMP/grug home" MINI_GRUG_SETTINGS="$TMP/settings.json"
mkdir -p "$MINI_GRUG_DIR"
fail=0
check() { if eval "$2"; then echo "ok   $1"; else echo "FAIL $1"; fail=1; fi; }

# a settings file that already has content we must not destroy
cat > "$MINI_GRUG_SETTINGS" <<'JSON'
{"permissions":{"allow":["Bash(ls:*)"]},"hooks":{"Stop":[{"hooks":[{"type":"command","command":"echo keepme"}]}]}}
JSON

# install (answer yes to the prompt); builds the binary too, so this needs swiftc
echo y | "$MG" install >/dev/null 2>"$TMP/install.err" || { cat "$TMP/install.err"; exit 1; }
"$MG" stop >/dev/null   # install starts the window; we do not want it during the test
check "binary built"            '[ -x "$MINI_GRUG_DIR/bin/MiniGrug" ]'
check "settings still parse"    'python3 -m json.tool "$MINI_GRUG_SETTINGS" >/dev/null'
check "5 hook events added"     '[ "$(python3 -c "import json;print(len(json.load(open(\"$MINI_GRUG_SETTINGS\"))[\"hooks\"]))")" = 5 ]'
check "other Stop hook kept"    'grep -q keepme "$MINI_GRUG_SETTINGS"'
check "permissions kept"        'grep -q "Bash(ls:\*)" "$MINI_GRUG_SETTINGS"'
check "hooks are async"         'grep -q "\"async\": true" "$MINI_GRUG_SETTINGS"'
check "backup written"          '[ -f "$MINI_GRUG_SETTINGS.bak.mini-grug" ]'
check "scripts copied to dir"   '[ -x "$MINI_GRUG_DIR/mini-grug.sh" ] && [ -f "$MINI_GRUG_DIR/MiniGrug.swift" ]'
check "hooks point at dir copy" 'grep -q "$MINI_GRUG_DIR/mini-grug.sh. hook" "$MINI_GRUG_SETTINGS"'
"$MG" uninstall >/dev/null; "$MG" install --yes >/dev/null 2>&1; "$MG" stop >/dev/null
check "install --yes works"     'grep -q "mini-grug.sh.* hook" "$MINI_GRUG_SETTINGS"'

# install twice is idempotent
echo y | "$MG" install >/dev/null 2>&1; "$MG" stop >/dev/null
check "install idempotent"      '[ "$(grep -c "mini-grug.sh.* hook" "$MINI_GRUG_SETTINGS")" = 5 ]'

# hook writes state files
S="$MINI_GRUG_DIR/state"
printf '{"session_id":"abc-123","cwd":"/tmp/proj","notification_type":"permission_prompt","message":"x"}' | "$MG" hook waiting
check "waiting state"           'grep -q "\"state\": \"waiting\"" "$S/abc-123.json"'
check "waiting message mapped"  'grep -q "grug need permission" "$S/abc-123.json"'
printf '{"session_id":"abc-123","cwd":"/tmp/proj"}' | "$MG" hook stop
check "done state"              'grep -q "\"state\": \"done\"" "$S/abc-123.json"'
printf '{"session_id":"abc-123","cwd":"/tmp/proj"}' | "$MG" hook prompt
check "working state"           'grep -q "\"state\": \"working\"" "$S/abc-123.json"'
printf '{"session_id":"../evil","cwd":"/tmp"}' | "$MG" hook prompt
check "session id sanitised"    '[ ! -e "$MINI_GRUG_DIR/evil.json" ] && [ -f "$S/evil.json" ]'
echo "not json" | "$MG" hook prompt
check "bad stdin tolerated"     '[ -f "$S/unknown.json" ]'
"$MG" status | grep -q "abc-123" && echo "ok   status lists session" || { echo "FAIL status"; fail=1; }
printf '{"session_id":"abc-123"}' | "$MG" hook end
check "end removes file"        '[ ! -e "$S/abc-123.json" ]'

# preview renders
"$MG" preview "$TMP/preview.png" >/dev/null
check "preview png"             '[ -s "$TMP/preview.png" ]'

# uninstall removes only ours
"$MG" uninstall >/dev/null
check "our hooks removed"       '! grep -q "mini-grug.sh hook" "$MINI_GRUG_SETTINGS"'
check "other Stop hook kept"    'grep -q keepme "$MINI_GRUG_SETTINGS"'
check "settings still parse"    'python3 -m json.tool "$MINI_GRUG_SETTINGS" >/dev/null'

[ $fail -eq 0 ] && echo "all green" || { echo "some checks failed"; exit 1; }
