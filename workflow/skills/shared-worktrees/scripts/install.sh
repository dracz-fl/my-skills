#!/usr/bin/env bash
# Install the shared worktree layout: Claude Code WorktreeCreate/WorktreeRemove hooks
# plus herdr's [worktrees] directory, both pointing at one root.
# Usage: install.sh [root]   (default root: ~/code/worktrees)
# Safe to re-run: backs up both config files and overwrites only the keys it owns.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
root="${1:-$HOME/code/worktrees}"
root="${root/#\~/$HOME}"
settings="$HOME/.claude/settings.json"
herdr_config="$HOME/.config/herdr/config.toml"
stamp=$(date +%Y%m%d-%H%M%S)

command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }

mkdir -p "$HOME/.claude/hooks" "$root"
install -m 755 "$here/worktree-create.sh" "$HOME/.claude/hooks/worktree-create.sh"
install -m 755 "$here/worktree-remove.sh" "$HOME/.claude/hooks/worktree-remove.sh"
install -m 755 "$here/worktree-sweep.sh" "$HOME/.claude/hooks/worktree-sweep.sh"

[ -f "$settings" ] || echo '{}' > "$settings"
cp "$settings" "$settings.bak-$stamp"
tmp=$(mktemp)
jq --arg root "$root" '
  .hooks.WorktreeCreate = [{"hooks":[{"type":"command","command":"~/.claude/hooks/worktree-create.sh"}]}]
  | .hooks.WorktreeRemove = [{"hooks":[{"type":"command","command":"~/.claude/hooks/worktree-remove.sh"}]}]
  | .env.WORKTREE_ROOT = $root
  | .hooks.SessionEnd = ((.hooks.SessionEnd // [])
      | map(select(any(.hooks[]?; .command == "~/.claude/hooks/worktree-sweep.sh") | not))
      + [{"hooks":[{"type":"command","command":"~/.claude/hooks/worktree-sweep.sh"}]}])
' "$settings" > "$tmp"
mv "$tmp" "$settings"
echo "claude: hooks + env.WORKTREE_ROOT written to $settings (backup .bak-$stamp)"

if [ -f "$herdr_config" ]; then
  cp "$herdr_config" "$herdr_config.bak-$stamp"
  if grep -q '^\[worktrees\]' "$herdr_config"; then
    echo "herdr: [worktrees] already present in $herdr_config; make sure it says: directory = \"$root\"" >&2
  else
    printf '\n[worktrees]\ndirectory = "%s"\n' "$root" >> "$herdr_config"
    echo "herdr: [worktrees] directory = \"$root\" added (backup .bak-$stamp); restart herdr"
  fi
else
  echo "herdr: no $herdr_config found; skipped"
fi

echo "root: $root"
