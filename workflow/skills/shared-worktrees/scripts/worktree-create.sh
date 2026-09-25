#!/usr/bin/env bash
# Claude Code WorktreeCreate hook: put worktrees where herdr puts them,
# <root>/<repo>/<name>, so both tools see the same set.
set -euo pipefail

ROOT="${WORKTREE_ROOT:-$HOME/code/worktrees}"   # must match [worktrees] directory in ~/.config/herdr/config.toml

input=$(cat)
name=$(jq -r .name <<<"$input")
cwd=$(jq -r .cwd <<<"$input")

# Main clone, even when cwd is already inside a worktree.
common=$(git -C "$cwd" rev-parse --path-format=absolute --git-common-dir)
main=$(dirname "$common")
repo=$(basename "$main")
dir="$ROOT/$repo/$name"

if [ ! -d "$dir" ]; then   # else reuse (made by herdr or an earlier session)
  if git -C "$main" show-ref --verify --quiet "refs/heads/$name"; then
    git -C "$main" worktree add "$dir" "$name" >&2
  else
    git -C "$main" worktree add -b "$name" "$dir" >&2
  fi

  # The hook replaces Claude Code's own creation, so honour .worktreeinclude here.
  if [ -f "$main/.worktreeinclude" ]; then
    git -C "$main" ls-files -z --others --ignored --exclude-from=.worktreeinclude |
      (cd "$main" && xargs -0 -I{} rsync -R "{}" "$dir/") >&2 || true
  fi
fi

# Show it in herdr's sidebar; subagent worktrees (agent-*) are short-lived, so skip them.
if [[ $name != agent-* ]] && command -v herdr >/dev/null && herdr status server >/dev/null 2>&1; then
  herdr worktree open --cwd "$main" --path "$dir" --label "$name" --no-focus >/dev/null 2>&1 || true
fi

echo "$dir"
