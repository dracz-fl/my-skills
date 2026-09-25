---
name: shared-worktrees
description: Git worktrees shared between herdr and Claude Code under one root (`~/code/worktrees/<repo>/<name>`). Use when creating, entering, opening or removing a worktree; when installing this layout on a machine or for a teammate; and when cleaning up stale worktrees.
---

# shared-worktrees

One worktree layout for every tool on the machine:

```
~/code/worktrees/<repo>/<name>     branch: <name>
```

`<repo>` is the basename of the main clone, `<name>` is the worktree name. herdr and Claude Code both create here, so a worktree either tool makes is visible to the other and to one `git worktree list`.

## How it works

| Piece | Where | What it does |
|---|---|---|
| herdr | `~/.config/herdr/config.toml` → `[worktrees] directory` | herdr natively builds `<directory>/<repo>/<name>`, branch `<name>`. |
| `WorktreeCreate` hook | `~/.claude/hooks/worktree-create.sh` | Replaces Claude Code's default `.claude/worktrees/<name>` placement for `claude -w`, `EnterWorktree` and subagent `isolation: worktree`. Resolves the main clone (also from inside a worktree), reuses the folder if it exists, checks out an existing branch or creates `<name>`, then copies `.worktreeinclude` files (Claude Code skips `.worktreeinclude` once a hook owns creation). When the herdr server runs, opens the worktree as an unfocused herdr workspace. Prints the path. |
| herdr sidebar | `herdr worktree open --cwd <main clone> --path <dir> --no-focus` | herdr lists a worktree only under an open workspace of its main clone. `worktree open` opens that parent workspace too, so worktrees of repos with no workspace (the service repos of a stack) become visible. |
| Subagent worktrees | `<root>/.agents/<repo>/agent-*` | The create hook sends `agent-*` names here and writes an owner file (`<root>/.agents/.owners/<repo>/<name>`) holding the parent session id. They show in the sidebar like any other worktree. |
| `WorktreeRemove` hook | `~/.claude/hooks/worktree-remove.sh` | `git worktree remove` (refuses when the worktree has modified or untracked files; non-zero exit keeps it), closes its herdr workspace, then `git branch -d` (deletes merged branches only). |
| `SessionEnd` sweep | `~/.claude/hooks/worktree-sweep.sh` | Claude Code does not clean up worktrees a hook made. The sweep removes the ending session's clean subagent worktrees and closes their herdr workspaces, plus any clean one whose owner file is older than a day (a session that died). Dirty ones stay; branches go only when merged. |
| `env.WORKTREE_ROOT` | `~/.claude/settings.json` | The root the create hook uses. Must equal herdr's `directory`. |

Claude Code has no setting for the worktree folder; the `WorktreeCreate` hook is the only lever.

## Install

1. Run `scripts/install.sh [root]` from this skill's directory (default root `~/code/worktrees`; needs `jq`). It copies the three hooks, writes them and `env.WORKTREE_ROOT` into `~/.claude/settings.json` (the sweep is appended to any existing `SessionEnd` hooks), and adds `[worktrees]` to the herdr config. It backs both files up as `*.bak-<timestamp>` and is safe to re-run. When herdr already has a `[worktrees]` section, it prints the value to set by hand.
2. Restart herdr and open a new Claude Code session; running sessions keep the old hooks.
3. Verify in a scratch repo: `claude -w hooktest -p "pwd"` → a worktree at `<root>/<repo>/hooktest`; then remove it with `echo '{"worktree_path":"<that path>"}' | ~/.claude/hooks/worktree-remove.sh`. Install is done when the path lands under the root and removal deletes it and the branch.

## Use

| Goal | Human | Agent |
|---|---|---|
| New worktree | `herdr worktree create --branch <name>` | `claude -w <name>`, `EnterWorktree`, or a subagent with `isolation: worktree` |
| Open an existing one | `herdr worktree open --path <root>/<repo>/<name>` | `claude -w <name>` (reuses the folder) or `EnterWorktree` with the path |
| Remove | `herdr worktree remove` or `git worktree remove <path>` | `ExitWorktree` with remove, or `git worktree remove <path>` |
| See all | `git -C <main clone> worktree list` | same |

Agent rules:

- Make every worktree through one of the paths above, so it lands under the root. A worktree made with a hand-typed `git worktree add` elsewhere is invisible to this layout.
- For a worktree of a different repo than the session's own (for example a service repo from a stack-root session), run `git -C <main clone> worktree add -b <name> <root>/<repo>/<name> origin/main`, then `herdr worktree open --cwd <main clone> --path <root>/<repo>/<name> --label <name> --no-focus` so it shows in the sidebar. The hooks do not run for plain git commands.
- Name the worktree after the ticket or task (`fn-1753-traveler`); the name is also the branch.
- Before removing, commit or move out anything the worktree holds that git ignores (a new `.env`, local data): ignored files go with the worktree. `.worktreeinclude` copies are safe to lose — the originals stay in the main clone.
- When removal refuses because of uncommitted work, report the file list to the user and let them choose; keep `--force` for their explicit word.
- Removing a worktree keeps its branch and commits, and stashes live in the main clone, so only uncommitted files are at risk.

## Cleaning up stale worktrees

Read [`references/cleanup.md`](references/cleanup.md) before removing more than one worktree or moving worktrees into the root.
