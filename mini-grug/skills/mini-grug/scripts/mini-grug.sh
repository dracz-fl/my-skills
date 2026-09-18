#!/usr/bin/env bash
# mini-grug.sh — install, run, and feed the mini grug desktop mascot for Claude Code.
# macOS only. Needs: bash, python3, swiftc (Xcode Command Line Tools: `xcode-select --install`).
#
# Data lives in $MINI_GRUG_DIR (default ~/.mini-grug):
#   bin/MiniGrug       compiled window app (rebuilt when MiniGrug.swift changes)
#   state/<sid>.json   one file per Claude Code session, written by `hook`
#   app.pid            pid of the running window
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR="${MINI_GRUG_DIR:-$HOME/.mini-grug}"
# install copies this script and the Swift source into $DIR and points the hooks there, so a plugin
# update (which changes the cache path of this skill) does not break hooks that are already installed.
SRC="$DIR/MiniGrug.swift"; [ -f "$SRC" ] || SRC="$HERE/MiniGrug.swift"
BIN="$DIR/bin/MiniGrug"
STATE="$DIR/state"
PIDFILE="$DIR/app.pid"
SETTINGS="${MINI_GRUG_SETTINGS:-$HOME/.claude/settings.json}"
MARK="/mini-grug.sh"   # every hook command we own contains this path tail; uninstall removes only those

usage() {
  cat <<'USAGE'
usage: mini-grug.sh <command>

  install [--yes]  copy scripts to ~/.mini-grug, build the window app, add Claude Code hooks to
                   ~/.claude/settings.json (asks first; --yes skips the question), start the app
  uninstall     remove our hooks from settings.json, stop the app, keep ~/.mini-grug
  start         launch the floating grug (no-op if running)
  stop          quit the floating grug
  restart       stop, then start
  status        running or not, hooks installed or not, current session states
  preview FILE  render every sprite frame into FILE (png) — check the art
  demo          walk the grug through working → waiting → done with fake sessions (needs `start`)
  hook EVENT    called by Claude Code hooks; reads hook JSON on stdin and writes state/<session>.json
                EVENT is one of: start, prompt, waiting, stop, end

env: MINI_GRUG_DIR (default ~/.mini-grug), MINI_GRUG_SETTINGS (default ~/.claude/settings.json)
USAGE
}

die() { echo "mini-grug: $*" >&2; exit 1; }
need_mac() { [ "$(uname)" = Darwin ] || die "macOS only (needs AppKit)"; }

build() {
  need_mac
  command -v swiftc >/dev/null || die "swiftc not found. Install Xcode Command Line Tools: xcode-select --install"
  mkdir -p "$DIR/bin" "$STATE"
  local stamp="$DIR/bin/.src-sha"
  local want; want=$(shasum -a 256 "$SRC" | cut -c1-16)
  if [ -x "$BIN" ] && [ -f "$stamp" ] && [ "$(cat "$stamp")" = "$want" ]; then return 0; fi
  echo "building MiniGrug (one-time, ~10 s)…" >&2
  swiftc -O -framework Cocoa "$SRC" -o "$BIN"
  echo "$want" > "$stamp"
}

running() { [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; }

cmd_start() {
  build
  if running; then echo "mini grug already running (pid $(cat "$PIDFILE"))"; return 0; fi
  mkdir -p "$STATE"
  MINI_GRUG_DIR="$DIR" nohup "$BIN" >>"$DIR/app.log" 2>&1 &
  echo $! > "$PIDFILE"
  echo "mini grug awake (pid $!). bottom-right of your main screen. drag to move, right-click to quit."
}

cmd_stop() {
  if running; then
    # Remove the pidfile only after the kill succeeded; otherwise status/start would forget a live process.
    kill "$(cat "$PIDFILE")" || die "could not stop pid $(cat "$PIDFILE"); pidfile kept"
    echo "mini grug asleep"
  fi
  rm -f "$PIDFILE"
}

# ---- hooks in settings.json ----------------------------------------------------------------

hooks_json() {
  # Hook shape confirmed against the Claude Code hooks reference: matcher on Notification is notification_type.
  # async: the hook never blocks Claude; it only writes a small file.
  local sh="$DIR/mini-grug.sh"
  python3 - "$sh" <<'PY'
import json, shlex, sys
sh = shlex.quote(sys.argv[1])  # $HOME may contain spaces; the hook runner splits this string as a shell command
def h(ev): return {"type": "command", "command": f"{sh} hook {ev}", "async": True, "timeout": 5}
print(json.dumps({
  "SessionStart":     [{"hooks": [h("start")]}],
  "UserPromptSubmit": [{"hooks": [h("prompt")]}],
  "Notification":     [{"matcher": "permission_prompt|idle_prompt|elicitation_dialog|agent_needs_input", "hooks": [h("waiting")]}],
  "Stop":             [{"hooks": [h("stop")]}],
  "SessionEnd":       [{"hooks": [h("end")]}],
}))
PY
}

hooks_installed() { [ -f "$SETTINGS" ] && grep -q "$MARK" "$SETTINGS"; }

cmd_install() {
  local yes=0; [ "${1:-}" = "--yes" ] && yes=1
  need_mac
  mkdir -p "$DIR"
  # copy ourselves into $DIR so the hooks point at a stable path (see SRC comment above)
  if [ "$HERE" != "$DIR" ]; then
    cp "$HERE/MiniGrug.swift" "$DIR/MiniGrug.swift"
    cp "$HERE/mini-grug.sh" "$DIR/mini-grug.sh"; chmod +x "$DIR/mini-grug.sh"
    SRC="$DIR/MiniGrug.swift"
  fi
  build
  if hooks_installed; then
    echo "hooks already in $SETTINGS"
  else
    echo "mini grug wants to add these hooks to $SETTINGS:"
    hooks_json | python3 -m json.tool
    echo
    if [ $yes -eq 1 ]; then echo "(--yes given)"; else
      read -r -p "add them? [y/N] " yn
      [[ "$yn" =~ ^[Yy]$ ]] || die "not installed. nothing changed."
    fi
    mkdir -p "$(dirname "$SETTINGS")"
    [ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"
    # Keep the first pre-install snapshot; a reinstall must not overwrite it.
    [ -f "$SETTINGS.bak.mini-grug" ] || cp "$SETTINGS" "$SETTINGS.bak.mini-grug"
    MG_HOOKS="$(hooks_json)" python3 - "$SETTINGS" "$MARK" <<'PY'
import json, os, sys
path, mark = sys.argv[1], sys.argv[2]
add = json.loads(os.environ["MG_HOOKS"])
with open(path) as f: s = json.load(f)
hooks = s.setdefault("hooks", {})
for ev, groups in add.items():
    lst = hooks.setdefault(ev, [])
    lst[:] = [g for g in lst if not any(mark in (x.get("command") or "") for x in g.get("hooks", []))]
    lst.extend(groups)
with open(path, "w") as f: json.dump(s, f, indent=2); f.write("\n")
PY
    echo "hooks added (backup at $SETTINGS.bak.mini-grug). new Claude Code sessions pick them up."
  fi
  # Reinstall after an art or code change: a running app keeps the old binary, so restart it.
  if running; then cmd_stop; fi
  cmd_start
  echo
  echo "start on login: add \"$DIR/mini-grug.sh start\" to your shell profile, or run it when you need it."
}

cmd_uninstall() {
  cmd_stop
  if hooks_installed; then
    python3 - "$SETTINGS" "$MARK" <<'PY'
import json, sys
path, mark = sys.argv[1], sys.argv[2]
with open(path) as f: s = json.load(f)
hooks = s.get("hooks", {})
for ev in list(hooks):
    hooks[ev] = [g for g in hooks[ev] if not any(mark in (x.get("command") or "") for x in g.get("hooks", []))]
    if not hooks[ev]: del hooks[ev]
if not hooks: s.pop("hooks", None)
with open(path, "w") as f: json.dump(s, f, indent=2); f.write("\n")
PY
    echo "hooks removed from $SETTINGS"
  fi
  echo "kept $DIR (delete it yourself if you want the binary gone)"
}

# ---- hook target ---------------------------------------------------------------------------

cmd_hook() {
  local ev="${1:-}"; [ -n "$ev" ] || die "hook needs EVENT"
  mkdir -p "$STATE"
  # Field names are read defensively: session_id, cwd, message are documented; notification_type may vary.
  # stdin is read here because the heredoc below takes python's stdin.
  local input=""; [ -t 0 ] || input="$(cat || true)"
  MG_IN="$input" python3 - "$ev" "$STATE" "${TERM_PROGRAM:-}" <<'PY'
import json, os, sys, time
ev, state_dir, term = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    d = json.loads(os.environ.get("MG_IN") or "{}")
    if not isinstance(d, dict): d = {}
except Exception:
    d = {}
sid = str(d.get("session_id") or os.environ.get("CLAUDE_SESSION_ID") or "unknown")
sid = "".join(ch for ch in sid if ch.isalnum() or ch in "-_")[:64] or "unknown"
path = os.path.join(state_dir, sid + ".json")
if ev == "end":
    try: os.remove(path)
    except FileNotFoundError: pass
    sys.exit(0)
state = {"start": "working", "prompt": "working", "waiting": "waiting", "stop": "done"}.get(ev, "working")
msg = ""
if ev == "waiting":
    kind = str(d.get("notification_type") or d.get("type") or "")
    msg = {"permission_prompt": "grug need permission", "idle_prompt": "grug wait for chief",
           "elicitation_dialog": "grug have question", "agent_needs_input": "grug need input"}.get(kind, "")
    if not msg:
        msg = str(d.get("message") or "grug need chief")[:120]
elif ev == "stop":
    msg = "grug done"
out = {"state": state, "message": msg, "cwd": str(d.get("cwd") or os.getcwd()), "term": term, "updated": time.time()}
tmp = path + ".tmp"
with open(tmp, "w") as f: json.dump(out, f)
os.replace(tmp, path)
PY
}

# ---- status / demo -------------------------------------------------------------------------

cmd_status() {
  if running; then echo "app:    running (pid $(cat "$PIDFILE"))"; else echo "app:    not running"; fi
  if hooks_installed; then echo "hooks:  installed in $SETTINGS"; else echo "hooks:  not installed"; fi
  echo "state:  $STATE"
  if ls "$STATE"/*.json >/dev/null 2>&1; then
    python3 - "$STATE" <<'PY'
import json, os, sys, time
d = sys.argv[1]
for f in sorted(os.listdir(d)):
    if not f.endswith(".json"): continue
    try: s = json.load(open(os.path.join(d, f)))
    except Exception: continue
    age = int(time.time() - s.get("updated", 0))
    print(f"  {f[:-5][:12]:<12} {s.get('state','?'):<8} {age:>5}s ago  {os.path.basename(s.get('cwd',''))}  {s.get('message','')}")
PY
  else
    echo "  (no sessions)"
  fi
}

cmd_demo() {
  running || die "start the app first: mini-grug.sh start"
  local sid="demo-$$"
  fake() { printf '{"session_id":"%s","cwd":"%s","notification_type":"%s","message":"%s"}' "$sid" "$PWD" "${2:-}" "${3:-}" | cmd_hook "$1"; }
  echo "working…";  fake prompt;                         sleep 3
  echo "waiting…";  fake waiting permission_prompt;      sleep 4
  echo "done…";     fake stop;                            sleep 3
  echo "gone.";     fake end
}

cmd="${1:-}"; [ -n "$cmd" ] || { usage; exit 1; }
shift || true
case "$cmd" in
  install) cmd_install "$@" ;;
  uninstall) cmd_uninstall ;;
  start) cmd_start ;;
  stop) cmd_stop ;;
  restart) cmd_stop; cmd_start ;;
  status) cmd_status ;;
  preview) build; [ -n "${1:-}" ] || die "preview needs FILE"; MINI_GRUG_DIR="$DIR" "$BIN" --preview "$1" ;;
  demo) cmd_demo ;;
  hook) cmd_hook "$@" ;;
  -h|--help|help) usage ;;
  *) usage; die "unknown command '$cmd'" ;;
esac
