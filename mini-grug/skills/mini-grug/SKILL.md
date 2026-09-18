---
name: mini-grug
description: "Opt-in macOS desktop mascot for Claude Code: a small floating pixel grug that waves when any session waits for the user (permission prompt, question, idle), idles while sessions work, and celebrates when a turn ends. Driven by Claude Code hooks that write one state file per session; click the grug to bring the terminal forward. Use this skill whenever the user asks to install, start, stop, check, demo, or remove mini grug, or says things like 'floating grug', 'desktop grug', 'grug mascot', 'nudge me when you need input', 'is mini grug running', 'turn mini grug off'. Do NOT use for: the grug persona itself (/grug, 'grug mode'), caveman mode, the grug cave or its dashboard, generic macOS notification settings, or questions about other tools' mascots (Codex, Copilot)."
---

# mini-grug

A Claude Code session that waits for the user is silent. The user works in another window and does not see it. Mini grug is a small always-on-top pixel character on macOS. It shows the state of all Claude Code sessions at one glance:

| state | grug | when |
|---|---|---|
| waiting | waves the club, speech bubble names the project | a session needs permission, asks a question, or waits idle |
| working | idle breathing | a session is running |
| done | happy face, bubble "grug done" for 45 s | a turn ended |
| asleep | eyes closed, zzz | no active session |

Timing follows Claude Code's own notification gates: the permission wave starts about six seconds after the prompt appears and only if you have not typed since, and the idle wave about 60 seconds after a turn ends. A session in auto or bypass permission mode never asks, so it never triggers the permission wave; you still get the done face and the idle wave.

A red badge shows the count when more than one session waits. Click the grug to acknowledge the current waits (bubble and badge clear until a session asks again) and bring the terminal app forward. Drag it to move it. Right-click for a menu.

Everything is in `scripts/`. The agent runs the CLI for the user. It never edits `settings.json` by hand.

## How it works

1. `mini-grug.sh install` copies the scripts to `~/.mini-grug/`, compiles `MiniGrug.swift` with `swiftc`, and adds five hooks to `~/.claude/settings.json`: `SessionStart`, `UserPromptSubmit`, `Notification` (matcher `permission_prompt|idle_prompt|elicitation_dialog|agent_needs_input`), `Stop`, `SessionEnd`. All hooks are `async` command hooks, so they never block Claude.
2. Each hook runs `~/.mini-grug/mini-grug.sh hook <start|prompt|waiting|stop|end>`. The hook reads the JSON on stdin and writes `~/.mini-grug/state/<session_id>.json`. `end` deletes the file.
3. The window polls the state directory twice per second and shows the most urgent state: waiting, then working, then done.

Hooks live in the user's own settings file. New sessions pick them up. Sessions that are already open do not.

## Requirements

- macOS. The window is AppKit.
- Xcode Command Line Tools for `swiftc`. If missing: `xcode-select --install`. Say this before install if `swiftc --version` fails.
- `python3` (ships with the Command Line Tools).

## Commands

Run from this skill's directory. After install, `~/.mini-grug/mini-grug.sh` is the same script and is the copy the hooks call.

| user wants | run |
|---|---|
| install, set up, turn on | `scripts/mini-grug.sh install --yes` (after the confirmation step below) |
| start the window | `scripts/mini-grug.sh start` |
| stop, hide, turn off | `scripts/mini-grug.sh stop` |
| is it running, what sessions | `scripts/mini-grug.sh status` |
| show me, demo, test it | `scripts/mini-grug.sh demo` (needs a running window; cycles working, waiting, done) |
| see the sprite frames | `scripts/mini-grug.sh preview out.png` |
| remove, uninstall | `scripts/mini-grug.sh uninstall` (removes only our hooks, stops the app, keeps `~/.mini-grug`) |
| run the checks | `bash scripts/test.sh` (uses a temp dir and temp settings file) |

Env overrides: `MINI_GRUG_DIR` (data dir, default `~/.mini-grug`), `MINI_GRUG_SETTINGS` (settings file, default `~/.claude/settings.json`).

## Install flow

Installing changes the user's Claude Code settings. Do it in two steps so the user sees what changes before it happens.

1. Tell the user in two or three sentences what install does: builds a small window app, adds five hooks to `~/.claude/settings.json` that write a state file per session, and writes a backup at `settings.json.bak.mini-grug`. Mention that the hooks are async and only write a small JSON file.
2. Wait for a yes from the user in chat. Then run `scripts/mini-grug.sh install --yes`. Without `--yes` the script asks on its own terminal, which the agent cannot answer.
3. After install, offer the demo once so the user sees the states. Tell the user that only new Claude Code sessions fire the hooks.

Without a user yes, do not run install. The script itself refuses without `--yes` or a typed `y`.

## Troubleshooting

- **Click does nothing.** Check `~/.mini-grug/app.log`; each click logs which terminal it tried to activate. When hooks run without `TERM_PROGRAM`, the click activates whichever known terminal app is running.
- **Grug never wakes up.** Run `status`. If the state list is empty, the hooks are not firing: the session was started before install, or `~/.claude/settings.json` was edited by another tool. Re-run `install`, it is idempotent.
- **Grug shows the wrong terminal on click.** Click uses `TERM_PROGRAM` from the hook environment. Sessions started from an IDE or `tmux` map to Terminal.
- **Build fails.** Check `swiftc --version`. The Swift file uses only Cocoa and has no dependencies.
- **Art edits break the build.** Every frame is 18 by 22 characters. The app exits with the frame and row number when a row has the wrong length.

## Grug persona

In a `/grug` session, grug may offer mini grug once when the user misses a prompt or asks to be told when input is needed. One offer, no nagging. The persona does not install anything on its own.
