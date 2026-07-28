---
name: dev-flow
description: "Router that drives my standard per-ticket development flow end to end: load the ticket's context, stress-test the plan with /grill-with-docs, switch into /grug:grug for the build, then — once dev is done — run /pre-pr-gates, author the PR with /formlabs-pr-write, and babysit the open PR through CodeRabbit's automated review (wait ~15 min for it, then work its findings until clean). Use when the user hands over a ticket to work on: 'start on TICKET-123', 'kick off the dev flow for <ticket>', 'let's work this ticket', 'run my dev flow', 'begin <ticket>'. Also handles the back half on its own: when the user says 'dev is done', 'wrap up <ticket>', or 'ready for PR', run the gates, PR-write, and review-babysitting steps. Do NOT use for: a one-off question about a ticket, running a single one of these skills directly, or a change that isn't tied to a ticket."
---

# Dev Flow

A router that runs my standard sequence for taking a ticket from assignment to an open PR and through its automated review. It does not re-implement any step — it orchestrates existing skills in order, then babysits the PR once it's open.

The flow, and why the order is fixed:

1. **Load ticket** → shared understanding of what's being asked.
2. **Plan — `/grill-with-docs`** → the plan is stress-tested against the domain model and docs *before* any code exists, when changing direction is cheap.
3. **Build — `/grug:grug`** → implement under grug's anti-complexity judgment. This is where the real work is; it is human-driven and iterative.
4. **Done check** → when the build is done and verified, the flow auto-advances; otherwise it keeps iterating (or waits, if the user says to hold).
5. **Gates — `/pre-pr-gates`** → quality gates on the finished change.
6. **PR — `/formlabs-pr-write`** → author the PR body against the real change and the ticket.
7. **Babysit review** → wait for CodeRabbit to review the PR (~15 min), then work through its findings until the PR is clean.

## Two entry points

This skill can run start to finish in one pass. It has two entry points so the back half can also be triggered on its own:

- **Full run** (user hands over a ticket): run steps 1–3, and when the build reaches a genuinely done-and-verified state (see step 4) **continue automatically** into steps 5–6. No manual "go" required.
- **Wrap only** (user says "dev is done" / "wrap up <ticket>" / "ready for PR"): jump straight to steps 5–6 for a build that already exists.

Pick the entry from what the user said. A bare ticket handoff → full run. A "done / ready" signal on existing work → wrap only. If genuinely ambiguous, ask which.

## Step 1 — Load the ticket

Get the ticket into context before planning.

- If given a ticket ID and a ticket system is reachable, fetch it (Formlabs uses Jira — use the Atlassian MCP `getJiraIssue`; load the Atlassian tools via ToolSearch if deferred). Pull the summary, description, and acceptance criteria.
- If no ID, no reachable system, or the fetch fails, ask the user to paste the ticket details rather than guessing.

Restate the ticket in one or two sentences and confirm you have the right scope before moving on.

**Verify the ticket's definite references.** When a ticket says "supply the value at *the* call site" or "extend *the* existing handler", that definite article is a claim about the base you're actually on — not a fact. Grep for each referent before planning around it. In stacked or parallel story work an absent caller usually means the seam belongs to a sibling story that isn't in your base; building the "obvious" wiring there either collides with that story or creates dead code nobody calls. Surface the gap and confirm scope instead of inventing the call site.

## Step 2 — Plan: `/grill-with-docs`

Invoke `grill-with-docs` (Skill tool). It interviews you one question at a time and updates domain docs inline as decisions crystallise — it is inherently interactive, so hand control to it and let it run to a shared, agreed plan. Do not rush past it into code. The output of this step is a plan you and the user both endorse.

**When the design is already locked, or the session can't sustain an interview.** A one-question-at-a-time grill assumes open design questions and a human present to answer them. If every design decision was closed upstream by a prior planning effort, or this is a background run with the user away, the full interview blocks instead of helping. Substitute two things: (1) a **code-grounding pass** — read the real conventions the change must follow (models, migrations, adjacent modules, existing tests) so the plan is anchored in the codebase rather than the ticket's prose; and (2) surface **only the residual forks** the locked design doesn't dictate — via `AskUserQuestion`, or as a stated assumption you proceed on. Keep the full grill for genuinely open designs in interactive sessions.

## Step 3 — Build: `/grug:grug`

**Reconcile the base before writing any code.** If you're picking up an existing branch or worktree, `git fetch` updates the remote-tracking ref but does *not* move your local head — it can lag `origin/<branch>` by a teammate's commits pushed since the worktree was made. Compare (`git rev-list --left-right --count origin/<branch>...HEAD`) and fast-forward or rebase onto the pushed tip *before* building. Otherwise the divergence surfaces at push time, with your commit already sitting on a stale base, and you're rebasing after the fact — clean only if the two changes happened to touch disjoint files.

Invoke `grug` (Skill tool). This puts the session into grug mode — grug voice *and* grug engineering judgment (say no to complexity, don't factor early, small refactors, integration tests, profile before optimizing) — for the rest of the build. Implement the agreed plan under that judgment.

Grug mode persists across the whole dev phase. Stay in it until the build is done; the user drops the persona when they want ("normal mode").

**Orchestrate, don't hand-code, when the work is big enough to split.** If the plan decomposes into parts that can proceed independently — separate modules/files, or a build + tests + docs split — the preferred move is to spawn a team of subagents (Agent tool) and have this main thread act as the orchestrator, not the implementer: break the plan into well-scoped units, dispatch one agent per unit (in parallel where they don't conflict; give agents that edit files concurrently their own worktree via `isolation: "worktree"`), then integrate and verify their results. Grug's judgment still governs — each agent gets the plan and the anti-complexity brief, and the orchestrator keeps the pieces simple and coherent. For a small, single-seam change, skip the team and implement inline; the overhead of a team buys nothing there.

## Step 4 — Done check → auto-advance

When the build reaches a done-and-verified state on its own, continue straight into the gates and PR-write; don't wait to be told. "Done and verified" means all of:

- the agreed plan from step 2 is fully implemented,
- the change builds and its tests pass (state what you ran), and
- grug has no outstanding complexity/quality objections about the change.

When all three hold, say the build is done and roll straight into step 5.

Do **not** auto-advance while any of them is unmet — a plan item still open, failing/unrun tests, or unresolved review concerns. In that case keep iterating in grug mode; the user can also interject at any point, and if they say to hold off, park here and wait for their "dev is done" signal.

## Step 5 — Gates: `/pre-pr-gates`

When the user signals dev is done, invoke `pre-pr-gates` (Skill tool). It runs the assumptions audit plus the quality gates and must pass before any "ready for PR" claim. Apply its edits / fix its findings as that skill directs.

## Step 6 — PR: `/formlabs-pr-write`

Only after the gates pass, invoke `formlabs-pr-write` (Skill tool) to author the PR body — grounded in the real diff and the ticket loaded in step 1, with real test evidence, gating `gh pr create` on explicit approval. Once the PR is open, note its number/URL and continue to step 7.

## Step 7 — Babysit the review

The PR is open, but it isn't done — CodeRabbit reviews Formlabs PRs automatically and usually starts within about **15 minutes** of the PR opening. Don't sign off before its review lands; stay on it until the PR is clean.

**Wait for the first pass.** Schedule a wake-up ~15 minutes out (`ScheduleWakeup`), then poll — don't sit and spin. On each wake, check whether CodeRabbit has reviewed yet:

```
gh pr view <num> --json reviews,comments
gh api repos/{owner}/{repo}/pulls/<num>/comments   # inline review comments
```

CodeRabbit posts as `coderabbitai[bot]` (a summary review plus inline comments, often with committable suggestions). If nothing from it yet, sleep another ~10–15 min and re-check; give up only after a couple of empty rounds and tell the user it never showed.

**Work the findings.** Once its review is in, triage every comment:

- **Valid & in scope** → fix it in the build (still under grug's judgment), commit, and push to the PR branch. A push triggers CodeRabbit to re-review.
- **Wrong / out of scope / debatable** → reply on the comment explaining why, rather than silently ignoring it. Surface anything genuinely contentious to the user instead of deciding unilaterally.
- Resolve threads you've addressed where appropriate.

**Loop until clean.** After pushing fixes, wait for CodeRabbit's re-review (same wake-and-poll pattern) and repeat until it has no outstanding actionable comments. Then report: the PR link, what CodeRabbit raised, what you changed vs. pushed back on, and anything left for the user to decide.

Keep the human in the loop — never resolve a substantive disagreement or force-merge on CodeRabbit's behalf; the goal is a review-clean PR ready for a human approver.

## Notes

- This router never substitutes for the skills it calls — always invoke them via the Skill tool so their own procedures and gates run in full.
- Keep the ticket reference (ID + one-line summary) available throughout so step 6 can tie the PR back to it.
- If the user only wants part of the flow, run just that part; the router is a convenience, not a cage.
