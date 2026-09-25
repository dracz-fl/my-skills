#!/usr/bin/env bash
# Claude Code SessionEnd hook: remove the clean subagent worktrees under <root>/.agents.
# Sweeps the ending session's own worktrees, plus any older than a day (sessions that
# died without a SessionEnd). Dirty worktrees stay; branches go only when merged.
set -uo pipefail

ROOT="${WORKTREE_ROOT:-$HOME/code/worktrees}"
owners="$ROOT/.agents/.owners"
[ -d "$owners" ] || exit 0

session=$(jq -r '.session_id // empty')

for marker in "$owners"/*/*; do
  [ -f "$marker" ] || continue
  name=$(basename "$marker")
  repo=$(basename "$(dirname "$marker")")
  dir="$ROOT/.agents/$repo/$name"

  if [ ! -d "$dir" ]; then
    rm -f "$marker"
    continue
  fi

  if [ "$(cat "$marker")" != "$session" ] && [ -z "$(find "$marker" -mmin +1440)" ]; then
    continue   # another live session's subagent may still use it
  fi

  main=$(dirname "$(git -C "$dir" rev-parse --path-format=absolute --git-common-dir)")
  if git -C "$main" worktree remove "$dir" >&2; then
    git -C "$main" branch -d "$name" >&2 || echo "kept unmerged branch $name" >&2
    rm -f "$marker"
  fi
done
exit 0
