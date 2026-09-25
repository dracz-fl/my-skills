# Cleaning up stale worktrees

Removing a worktree deletes only its working files. The branch, its commits and all stashes stay in the main clone. So the risk per worktree is its **uncommitted files**; whether the branch is still wanted is a separate decision.

## 1. Inventory

For every main clone on the machine (and every main clone that owns worktrees in `~/.herdr/worktrees`, `*/.claude/worktrees`, `*-worktrees/` or the shared root):

1. `git fetch --prune origin` — refreshes remote-tracking refs only, so "merged" is current.
2. `git worktree list --porcelain` — every linked worktree, including prunable ones.
3. Per worktree, record: path, branch, dirty count (`git status --porcelain`), commits not on any remote (`git log <branch> --not --remotes`), merged (tip is an ancestor of `origin/<default>`, upstream `[gone]`, or `gh pr list --head <branch> --state merged` returns a PR), open PR, last-touched date, running process (`ps -eo pid,command | grep -F <path>`).

The inventory is done when every linked worktree of every main clone has a class below. On many repos, hand this to a subagent that writes the table to a file and returns only the counts plus one line per worktree.

## 2. Classify

| Class | Condition | Action |
|---|---|---|
| A | clean, and merged or 0 commits ahead, no process | Remove in one batch after the user approves the list. |
| B | clean, unmerged commits or open PR | Remove the worktree if the user agrees; the branch stays. Ask separately about deleting the branch. |
| C | dirty | Show the file names. The user chooses: commit, move files out, or discard. One worktree at a time. |
| D | prunable (folder gone) | `git -C <main clone> worktree prune`. |
| E | a process runs in it (an agent, a herdr pane, a dev server) | Leave it until that work ends. |

## 3. Remove

- A and B: `git -C <main clone> worktree remove <path>`. Without `--force` git refuses dirty trees, which is the safety net if the inventory went stale.
- Delete a branch only with `git branch -d` (merged only), unless the user names the branch for `-D`.
- After removal, `herdr worktree list` and the herdr session may still name the old path; close that herdr workspace.

## 4. Move a worktree into the root

A worktree folder cannot be moved with `mv` safely; use git:

- Clean worktree: `git -C <main clone> worktree move <old path> <root>/<repo>/<name>`.
- Or remove it and recreate at the root: `git worktree remove <old>`, then `herdr worktree create --branch <name>` or `claude -w <name>`.

## 5. Remove a duplicate main clone

A main clone is safe to delete only when all of these hold:

- `git worktree list` shows no linked worktrees (they break when their main clone goes).
- `git status --porcelain` is empty and `git stash list` is empty.
- `git log --branches --not --remotes` is empty, or each listed branch is confirmed merged (squash-merged PRs show upstream `[gone]` and still list local commits).

Re-run the inventory after the cleanup; it is done when every remaining worktree sits under the root or belongs to class E.
