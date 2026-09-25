#!/usr/bin/env bash
# Claude Code WorktreeRemove hook: remove a worktree made by worktree-create.sh.
# Refuses when the worktree has uncommitted or untracked files (non-zero exit keeps it),
# and deletes the branch only when it is merged.
set -euo pipefail

dir=$(jq -r .worktree_path)
[ -d "$dir" ] || exit 0

common=$(git -C "$dir" rev-parse --path-format=absolute --git-common-dir)
main=$(dirname "$common")
branch=$(git -C "$dir" symbolic-ref --quiet --short HEAD || true)

# herdr workspace showing this worktree, if any; looked up before git forgets the path.
ws=""
if command -v herdr >/dev/null && herdr status server >/dev/null 2>&1; then
  ws=$(herdr worktree list --cwd "$main" 2>/dev/null |
    jq -r --arg d "$dir" '.result.worktrees[]? | select(.path == $d) | .open_workspace_id // empty')
fi

git -C "$main" worktree remove "$dir" >&2

[ -z "$ws" ] || herdr workspace close "$ws" >/dev/null 2>&1 || true

if [ -n "$branch" ]; then
  git -C "$main" branch -d "$branch" >&2 || echo "kept unmerged branch $branch" >&2
fi
