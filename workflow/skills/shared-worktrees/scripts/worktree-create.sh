#!/usr/bin/env bash
# Claude Code WorktreeCreate hook: put worktrees where herdr puts them,
# <root>/<repo>/<name>, so both tools see the same set.
# Subagent worktrees (agent-*) go to <root>/.agents/<repo>/<name> instead, with an
# owner file naming the session, so worktree-sweep.sh can remove them when it ends.
set -euo pipefail

ROOT="${WORKTREE_ROOT:-$HOME/code/worktrees}"   # must match [worktrees] directory in ~/.config/herdr/config.toml

input=$(cat)
name=$(jq -r .name <<<"$input")
cwd=$(jq -r .cwd <<<"$input")
session=$(jq -r .session_id <<<"$input")

# Main clone, even when cwd is already inside a worktree.
common=$(git -C "$cwd" rev-parse --path-format=absolute --git-common-dir)
main=$(dirname "$common")
repo=$(basename "$main")

case "$name" in
  agent-*) dir="$ROOT/.agents/$repo/$name" ;;
  *)       dir="$ROOT/$repo/$name" ;;
esac

if [ -d "$dir" ]; then
  echo "$dir"   # reuse existing worktree (made by herdr or an earlier session)
  exit 0
fi

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

case "$name" in
  agent-*) mkdir -p "$ROOT/.agents/.owners/$repo" && echo "$session" > "$ROOT/.agents/.owners/$repo/$name" ;;
esac

echo "$dir"
