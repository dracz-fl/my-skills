#!/usr/bin/env bash
# Claude Code WorktreeRemove hook: remove a worktree made by worktree-create.sh.
# Refuses when the worktree has uncommitted or untracked files (non-zero exit keeps it),
# and deletes the branch only when it is merged.
set -euo pipefail

ROOT="${WORKTREE_ROOT:-$HOME/code/worktrees}"

dir=$(jq -r .worktree_path)
[ -d "$dir" ] || exit 0

common=$(git -C "$dir" rev-parse --path-format=absolute --git-common-dir)
main=$(dirname "$common")
branch=$(git -C "$dir" symbolic-ref --quiet --short HEAD || true)
workspace=$(herdr worktree list --cwd "$main" 2>/dev/null |
  jq -r --arg d "$dir" '.result.worktrees[]? | select(.path == $d) | .open_workspace_id // empty' || true)

git -C "$main" worktree remove "$dir" >&2

[ -n "$workspace" ] && herdr workspace close "$workspace" >/dev/null 2>&1 || true

if [ -n "$branch" ]; then
  git -C "$main" branch -d "$branch" >&2 || echo "kept unmerged branch $branch" >&2
fi

case "$dir" in
  "$ROOT/.agents/"*) rm -f "$ROOT/.agents/.owners/$(basename "$(dirname "$dir")")/$(basename "$dir")" ;;
esac
