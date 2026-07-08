---
name: dev-flow
description: "Router that drives my standard per-ticket development flow end to end: load the ticket's context, stress-test the plan with /grill-with-docs, switch into /grug:grug for the build, then — once dev is done — run /pre-pr-gates and author the PR with /formlabs-pr-write. Use when the user hands over a ticket to work on: 'start on TICKET-123', 'kick off the dev flow for <ticket>', 'let's work this ticket', 'run my dev flow', 'begin <ticket>'. Also handles the back half on its own: when the user says 'dev is done', 'wrap up <ticket>', or 'ready for PR', run the gates and PR-write steps. Do NOT use for: a one-off question about a ticket, running a single one of these skills directly, or a change that isn't tied to a ticket."
---

# Dev Flow

A router that runs my standard sequence for taking a ticket from assignment to an open PR. It does not re-implement any step — it orchestrates four existing skills in order, with a mandatory human checkpoint in the middle where the actual coding happens.

The flow, and why the order is fixed:

1. **Load ticket** → shared understanding of what's being asked.
2. **Plan — `/grill-with-docs`** → the plan is stress-tested against the domain model and docs *before* any code exists, when changing direction is cheap.
3. **Build — `/grug:grug`** → implement under grug's anti-complexity judgment. This is where the real work is; it is human-driven and iterative.
4. **[Checkpoint]** → the flow pauses here. Gates and PR-write only run once dev is actually finished.
5. **Gates — `/pre-pr-gates`** → quality gates on the finished change.
6. **PR — `/formlabs-pr-write`** → author the PR body against the real change and the ticket.

## Two entry points

This skill spans a long, human-driven middle. Treat it as two segments:

- **Kickoff** (user hands over a ticket): run steps 1–3, then **stop at the checkpoint**. Do not run the gates or open a PR — dev isn't done yet.
- **Wrap** (user says "dev is done" / "wrap up <ticket>" / "ready for PR"): run steps 5–6. This half can be re-triggered independently later in the session, after the build has settled.

Pick the segment from what the user said. A bare ticket handoff → kickoff. A "done / ready" signal → wrap. If genuinely ambiguous, ask which.

## Step 1 — Load the ticket

Get the ticket into context before planning.

- If given a ticket ID and a ticket system is reachable, fetch it (Formlabs uses Jira — use the Atlassian MCP `getJiraIssue`; load the Atlassian tools via ToolSearch if deferred). Pull the summary, description, and acceptance criteria.
- If no ID, no reachable system, or the fetch fails, ask the user to paste the ticket details rather than guessing.

Restate the ticket in one or two sentences and confirm you have the right scope before moving on.

## Step 2 — Plan: `/grill-with-docs`

Invoke `grill-with-docs` (Skill tool). It interviews you one question at a time and updates domain docs inline as decisions crystallise — it is inherently interactive, so hand control to it and let it run to a shared, agreed plan. Do not rush past it into code. The output of this step is a plan you and the user both endorse.

## Step 3 — Build: `/grug:grug`

Invoke `grug` (Skill tool). This puts the session into grug mode — grug voice *and* grug engineering judgment (say no to complexity, don't factor early, small refactors, integration tests, profile before optimizing) — for the rest of the build. Implement the agreed plan under that judgment.

Grug mode persists across the whole dev phase. Stay in it until the build is done; the user drops the persona when they want ("normal mode").

## Step 4 — Checkpoint (stop here on kickoff)

Do **not** auto-advance to the gates. Coding is iterative and the user decides when it's finished. End the kickoff segment by telling the user dev is underway and that you'll run the gates and PR-write when they say dev is done.

## Step 5 — Gates: `/pre-pr-gates`

When the user signals dev is done, invoke `pre-pr-gates` (Skill tool). It runs the assumptions audit plus the quality gates and must pass before any "ready for PR" claim. Apply its edits / fix its findings as that skill directs.

## Step 6 — PR: `/formlabs-pr-write`

Only after the gates pass, invoke `formlabs-pr-write` (Skill tool) to author the PR body — grounded in the real diff and the ticket loaded in step 1, with real test evidence, gating `gh pr create` on explicit approval.

## Notes

- This router never substitutes for the skills it calls — always invoke them via the Skill tool so their own procedures and gates run in full.
- Keep the ticket reference (ID + one-line summary) available throughout so step 6 can tie the PR back to it.
- If the user only wants part of the flow, run just that part; the router is a convenience, not a cage.
