---
name: pre-pr-gates
description: Run the mandatory pre-PR quality gates before declaring work done or ready for a pull request. Audits load-bearing assumptions (Gate 0), then invokes /simplify, /decontextualize-doc-comments, and /thermo-nuclear-review in sequence on the current changes. Use this whenever you are about to tell the user the work is done, complete, finished, or ready for a PR — and whenever the user says "ready for PR?", "are we done?", "run the pre-PR checks", "run the gates", or asks to wrap up a change for review. Do NOT skip it because the change looks small.
---

# Pre-PR Gates

Before any claim that work is done or PR-ready, the change must pass an assumptions audit (Gate 0) and then three quality gates, in order. The order matters: audit the foundation first (a wrong assumption makes polishing the code moot), then simplify (it changes code), then clean up doc comments (on the now-final code), then the strict review last (so it judges the final state, not an intermediate one).

The user invoking this skill — directly or by asking "are we done / ready for PR" — counts as an explicit request for each gate below, including the strict review.

## Gate 0 — Assumptions audit (run first)

Before the code-quality gates, surface what this change *rests on*. This is the gate that catches the expensive failure: a whole design built on an external behavior that was never confirmed, then torn out.

List every load-bearing assumption the change depends on — especially anything an external party supplies (a header/field/response another service sends, an auth shape, a transport requirement, a token's scope, an ID format, whether a DB/table has data). For each, mark it:

- **Confirmed** — name the evidence (the real request you sent and what came back, the file:line, the command you ran).
- **Inferred** — you have not actually checked it for this change.

Then apply the rule: **any assumption that is both load-bearing and only inferred is a stop.** Confirm it with the cheapest real probe before declaring the work done — or, if it can't be confirmed now, say so explicitly and flag the risk to the user rather than shipping silently on top of it. Gate 0 produces findings, not edits; record the audit as a short table in the final summary.

## Subagents vs inline

Before running the gates, decide how to run them based on the size and shape of the change:

- **Default: run each gate in its own subagent** (Agent tool, `general-purpose`), instructing the subagent to invoke the gate's skill on the current branch's changes and report back what it changed or found. This is preferred for two reasons: each gate gets fresh eyes on the diff instead of inheriting your assumptions from writing the code, and the gates (especially thermo-nuclear-review) produce a lot of intermediate output that would bloat the main conversation.
- **Exception: run inline via the Skill tool** when the change is small and surgical — a handful of files, a tight diff, no structural changes. There the subagent overhead buys nothing and inline is faster.

Either way the gates stay sequential: each gate depends on the previous gate's edits being settled.

## The gates

Run each one (via subagent or the Skill tool, per the decision above), sequentially:

1. **`simplify`** — refines the changed code for reuse, simplification, efficiency, and clarity. Apply its fixes.
2. **`decontextualize-doc-comments:decontextualize-doc-comments`** — rewrites doc comments to describe steady-state behavior instead of PR-context narrative. Apply its rewrites.
3. **`thermo-nuclear-review:thermo-nuclear-review`** — strict maintainability review of the branch's changes. This runs last so it sees the post-cleanup code.

## Handling findings

- Gates 1 and 2 produce edits — apply them, and make sure the code still builds/tests pass after each gate before moving on.
- Gate 3 produces findings, not edits. Fix the high-confidence, in-scope findings. For findings that are out of scope or debatable, list them for the user instead of silently expanding the change.
- Only after Gate 0 and all three quality gates have run may you say the work is ready for a PR. Report a short summary: the Gate 0 assumptions table, what each quality gate changed or found, and anything left open.

If a gate's changes are substantial (e.g. simplify restructures something), it's fine to re-run verification (tests) but do not loop back and re-run earlier gates unless something clearly invalidated them.
