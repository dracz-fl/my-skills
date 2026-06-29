---
name: retrospective
description: >-
  Run a retrospective on the current conversation to find where the work hit
  friction — corrections the user had to make, wrong guesses, repeated manual
  steps, rediscovered facts, recurring permission prompts — and turn the durable
  lessons into concrete workflow improvements (a CLAUDE.md rule, a new/updated
  skill, a hook, or a reference doc). Use this whenever the user asks for a
  "retro", "post-mortem", "what could have gone better", "how do we avoid this
  next time", "capture this lesson", or wants to improve their own workflow /
  make the AI more accurate over time — and proactively offer it at the natural
  end of a long or bumpy session. The goal is a workflow that gets better with
  every session, not a one-off critique.
---

# Retrospective

## What this is for

The point of this skill is **compounding improvement**: every session leaves
behind lessons, and most of them evaporate. A retrospective catches the few that
are worth keeping and writes them somewhere the next session will actually read —
so the same mistake doesn't happen twice and a smooth workflow gets a little
smoother each time.

You are looking back over the conversation so far and asking: *what would have
made this go better, and how do I make that true for next time?*

## The trap to avoid first

The failure mode of a retrospective is **over-capturing**. If every small
annoyance becomes a rule, `CLAUDE.md` bloats into noise that's read every single
session, skills pile up unused, and the signal drowns. A good retrospective is
*selective* — it captures the handful of lessons that are durable and
generalizable, and lets the rest go.

So the hard part isn't finding friction. It's judging which friction is worth a
permanent fix. Lead with that judgment, not with a long list.

## Step 1 — Mine the conversation for friction

Read back over the conversation and look for these signals. They're where the
real lessons hide:

- **Corrections** — the user said "no", "actually", "don't", "stop", "that's
  wrong", or restated something you'd misunderstood. Each correction is a place
  the model's default differed from what the user wanted.
- **Wrong guesses** — you assumed a file path, function name, version, command,
  or convention and it turned out wrong, costing a round-trip.
- **Rediscovery** — you (or the user) had to hunt down a fact, command, or piece
  of domain knowledge that should have been written down somewhere.
- **Repetition** — *the strongest signal.* The same thing done more than once:
  a multi-step procedure repeated by hand (build → test → deploy, a data
  wrangling sequence), the same explanation given twice, the same kind of edit
  applied across many files, the same helper logic re-derived. If you did it
  three times this session, you'll do it thirty times across future ones —
  that's a skill or a script waiting to be extracted. Treat any "again" as a
  near-automatic candidate for capture.
- **Recurring permission prompts** — the same safe command prompted for approval
  again and again.
- **Re-litigation** — a decision got re-argued because the rationale wasn't
  recorded.
- **Wasted turns** — the model went down a path the user clearly didn't want,
  burned effort, and backed out.

Note each one briefly with what actually happened (quote the user where it's
sharp). This is evidence-gathering, not yet recommendations.

## Step 2 — Filter to what deserves to be captured

For each friction point, apply this bar. Drop anything that fails it:

- **Pattern, not one-off.** Did this recur, or is it likely to recur across
  sessions? A single freak accident usually isn't worth a permanent rule.
- **The fix would actually have prevented it.** Be honest — would a rule/skill
  have changed the outcome, or is it just hindsight noise?
- **Not already covered.** Check existing `CLAUDE.md`, skills, and the repo
  itself before proposing anything. Don't capture what the code, git history, or
  an existing skill already encodes — duplication is its own kind of noise.
- **Durable.** Will it still be true next week? Skip tactical, this-task-only
  details.
- **Earns its cost.** Every `CLAUDE.md` line is re-read every session. Only
  propose a line that pulls its weight.

If nothing clears the bar, say so plainly — "this session was clean, nothing
worth capturing" is a perfectly good retrospective outcome. Don't manufacture
findings.

## Step 3 — Classify each surviving lesson into a fix

Match the lesson to the right kind of fix. The kind matters: a behavioral
nudge and a thing-that-must-happen-every-time want completely different homes.

| If the lesson is… | The right fix is… | Why |
|---|---|---|
| A behavioral default you want changed ("prefer X", "always check Y before Z", "don't assume…") | **A `CLAUDE.md` rule** | It's model judgment, read into context every session. |
| A repeated multi-step *workflow* with a describable procedure | **A new or updated skill** (hand to `skill-creator`) | Procedures belong in a skill that loads on demand, not as prose rules. |
| Something that must happen *deterministically* every time and shouldn't depend on the model remembering (run formatter after edit, block a dangerous command, auto-allow a safe one) | **A hook or settings change** (hand to `update-config`) | The harness enforces it; the model can't forget it. Recurring permission prompts almost always belong here. |
| Missing factual or domain knowledge that had to be rediscovered | **A reference doc** (in the project, or a `reference`-type memory) | Knowledge, not behavior — store it where it can be looked up. |

If a lesson could be two things, prefer the cheapest durable one: a one-line rule
beats a skill; a skill beats nothing. Don't build a hook for something a sentence
would fix.

## Step 4 — Pick the target (ask each time)

For each fix, decide whether it's **global** (true regardless of project — belongs
in `~/.claude/CLAUDE.md` or `~/.claude/skills/`) or **project-specific** (belongs
in the project's `CLAUDE.md` / `.claude/`). Propose the one you think fits and
say why, but confirm with the user before writing — the global/project split is
easy to get wrong and annoying to undo.

## Step 5 — Apply

**Low-risk fixes: apply, then show.** A small, clearly-scoped *new* `CLAUDE.md`
rule or a short reference note is low-risk. Append it, then immediately show the
exact diff and a one-line undo. Two hard limits that keep this safe:

- **Append only.** Never silently edit or delete an existing rule — only add new
  ones. Rewriting existing instructions is a "big" change (see below).
- **Always surface it.** Even auto-applied changes get reported in the output
  with their location and how to revert. Nothing invisible.

Match the house style of the target `CLAUDE.md` — terse, imperative, with a bold
lead-in if the file uses them. Explain the *why* inside the rule when it isn't
obvious; a rule the future model understands is followed better than a bare MUST.

**Big fixes: propose and wait.** Creating a whole skill, adding a hook, editing
`settings.json`, or rewriting an existing rule changes behavior broadly or is
fiddly to reverse. Describe what you'd do and get a yes first. Then:

- **New/updated skills** → invoke the `skill-creator` skill and pass it the
  workflow you extracted (the steps, the corrections, the I/O you observed).
- **Hooks / permissions / settings** → invoke the `update-config` skill.

When a fix lands outside this session's reach (something only the user can set
up, or a decision they need to make), say so and leave it as a clear next step.

## Output format

Lead with the verdict, then the findings as a scannable list. Keep it tight.

```
## Retrospective

**Verdict:** <one line — e.g. "3 lessons worth keeping, 1 applied, 2 need your call">

### Applied (low-risk)
- <lesson> → <fix> in <file>
  Undo: <exact revert>

### Needs your call
1. <friction observed, with evidence>
   Root cause: <why it happened>
   Proposed fix: <CLAUDE.md rule | skill | hook | reference doc> — <global|project>
   [apply? y/n]

### Let go
- <friction that didn't clear the bar> — <why not worth capturing>
```

The "Let go" section matters: showing what you *deliberately didn't* capture is
how the user trusts that the things you did capture were worth it.
