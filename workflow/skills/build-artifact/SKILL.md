---
name: build-artifact
description: "Builds a shareable HTML artifact page from a short TOML spec instead of hand-writing hundreds of lines of CSS — a walkthrough/explainer of a change, PR, or how a system works, or a questionnaire that collects answers and decisions back from a human. Use whenever the user wants something written up as a page to share, asks you to 'explain this in an artifact', 'write this up', 'make me a page/walkthrough/explainer/one-pager', wants to hand a colleague context on a change, or needs to ask someone a set of questions and get structured answers back — even if they don't say the word 'artifact'. Also engage when you're about to hand over a long wall of chat prose that would land better as a page. Do NOT engage for: proof-of-work or verification evidence for completed work (that's prove-it, which owns that genre and has its own builder); documentation that belongs in the repo as markdown; a PR body (that's formlabs-pr-write); or an interactive diagram/architecture map, which this kit has no genre for and needs hand-authoring."
---

# Build Artifact

An artifact page is worth building when prose in a chat window would get skimmed and lost. The trap is that hand-writing one costs 300 lines of CSS before the first idea lands — so the page ends up beautiful and half-finished, and the missing content gets asked for a second time.

This skill separates those costs. The bundled builder owns everything presentational; you write a spec that is almost entirely prose. What you save goes into being complete and being right, which is where the real rework was.

## What the record says about the cost

Measured across 144 previously hand-built artifacts and the 94 sessions that produced them:

- Median page was **488 lines, of which 176 were `<style>`** — roughly one line of CSS per line of real content. About **3.4M characters** of artifact HTML got generated in total.
- **Iteration dominated, not the first draft.** One page took 32 edits. The causes were **missing content** ("also include…", the single largest category) and **factual corrections** — never theming.
- **Nobody ever complained about dark mode or overflow.** Those bugs shipped unnoticed. The builder fixes them for free; that is a side benefit, not the point.

So the expensive mistake is an incomplete or wrong page, not an ugly one. Budget accordingly: the presentation is handled, spend your attention on content.

Full data in `references/artifact-anatomy.md` and `references/authoring-cost-and-friction.md` — read them only if you're extending the kit, not to build a page.

## Pick the shape first

Two genres, and the choice is about direction of information flow:

| Genre | Use when | Reader does |
|---|---|---|
| `walkthrough` | Explaining a change, a PR, a system, a decision you already made | Reads and understands |
| `questionnaire` | You need answers, confirmations, or vetoes from a human | Fills in and sends back |

If you want both — explain something *and* ask about it — build two pages and link them. A page that mixes teaching and asking gets read but not answered.

If the content is really an interactive diagram or architecture map, this kit has no genre for it; say so and hand-author instead of forcing it into a walkthrough.

## Workflow

### 1. Lead with the claim, not the topic

The title is the single most-read line. Make it the finding: *"The hold now ends on a date the customer was actually told"*, not *"FN-1557 changes"*. If you can't state a claim, you probably don't understand the change well enough to write the page yet — go read more first.

### 2. Do a completeness pass before writing anything

This is the step that saves the most time, because "you forgot X" was the most common reason pages got rebuilt. Before opening a spec file, list what this reader will ask for the moment they finish reading. Aim to answer it in v1.

Reliable omissions worth checking every time:

- The thing you deliberately did *not* do, and why.
- The migration, backfill, or manual step that hasn't run yet.
- What happens in the null/empty/legacy case.
- Who has to do something next, and by when.
- The number or example that makes it concrete rather than abstract.

The `walkthrough` genre has a `[gap]` field for exactly this, and it renders last. Nearly every good walkthrough in the corpus ended by naming what it did not establish. Omit it only when there is genuinely nothing outstanding — which is rare enough to be worth doubting.

### 3. Write the spec

TOML, in your scratchpad. Start from a working example rather than a blank file:

```bash
SKILL=<this skill directory>
cp $SKILL/assets/examples/walkthrough.toml my-page.toml   # or questionnaire.toml
```

`references/spec-schema.md` has the full field reference: every block type, the questionnaire's `ref`/`choose`/`check`/`note` fields, and a recipe for a decision that can be vetoed. Read it while writing — it's short.

Prose fields take `**bold**`, `*italic*`, `` `code` ``, and links. Everything else is escaped, so write `<`, `&`, and quotes literally without thinking about it.

### 4. Build

```bash
python3 $SKILL/scripts/build.py my-page.toml -o my-page.html
```

It inlines the theme, then refuses to write a page that would break the publish constraints — external hosts, network calls, document-skeleton tags, modal dialogs, an unresolvable `var()`, a missing theme block, or anything over 16MB. A failure here is a real problem, not a lint nit; fix the spec.

**Iterate on the spec and rebuild. Never hand-edit the generated HTML** — the next build silently discards those edits, and you lose the one guarantee the kit provides.

### 5. Look at it before you publish it

Do not publish a page you have not seen rendered. The browser tools refuse `file://`, so serve it:

```bash
cd $(dirname my-page.html) && python3 -m http.server 8971 &
# then navigate to http://127.0.0.1:8971/my-page.html
```

Read the page as the recipient would. You're checking that it *communicates*, which no build check can tell you: does the title carry the finding, is any section a wall of text, does the gap section say something real.

If the browser extension goes unresponsive — it does, especially after many screenshots — don't spend the session fighting it. Verify programmatically instead and say what you checked:

```javascript
JSON.stringify({
  overflow: document.body.scrollWidth - document.documentElement.clientWidth,  // must be 0
  bareTables: document.querySelectorAll('table:not(.table-scroll table)').length,  // must be 0
})
```

Kill the server when you're done.

### 6. Publish, and hand back the link

The deliverable is a **published Artifact URL**, not a file on disk — a link that can go into a PR body, a Slack message, or a ticket. Pass the built `.html` to the **Artifact tool** with a `title`, a one-line `description`, and a `favicon`. The output is already Artifact-ready: it carries a `<title>` and `<style>` but no document skeleton, and it's fully self-contained.

Report that URL front and centre. If you have no Artifact tool available, say so plainly and hand back the file path — don't imply a local file is shareable.

**Before building a page that sounds familiar, check whether it already exists.** The same walkthrough was independently rebuilt in 3+ near-identical copies across sessions. Updating the existing artifact (pass its `url` to the Artifact tool) keeps the link people already have.

## Already handled — don't re-solve these

Time gets wasted re-deriving things the kit already owns. It handles:

- **Light and dark theme**, honouring both `prefers-color-scheme` and the viewer's `data-theme` toggle — the two signals that must agree.
- **One canonical token per concept.** `assets/theme.css` documents the set in its header, with the corpus frequency each name was chosen by. Use those names; never add a synonym.
- **Responsive layout with no horizontal page scroll.** Tables and code scroll inside their own box.
- **`<meta charset>`**, so em dashes survive local preview.

If you find yourself writing CSS while building a page, stop — either the kit has the component already, or you're adding one that belongs in `assets/theme.css` for every future page, not inline in this one.

## Content rules the builder cannot enforce

These came up repeatedly across sessions and are the actual quality bar. The kit handles none of them for you.

- **Never present your own suggestion as something agreed.** The sharpest rejection on record was about proposals a page presented as settled that had never been approved, and it cost a cleanup pass across several artifacts. If it's your idea, label it.
- **Flag assumptions; cite sources for claims.** The standing instruction is to flag assumptions explicitly and otherwise cite where a claim comes from. An unsourced confident sentence in a page reads as established fact — that's how a guess quietly becomes a decision.
- **Show real output, not narration.** A block quoting what a command actually printed beats a sentence claiming it works.
- **Visual over prose.** The one design complaint ever raised was "very hard to read, too textual," on behalf of readers who "wont read even a 7 line paragraph." Reach for a table, a step list, or a diff before another paragraph.

## Answer collection: the return path is the hard part

For `questionnaire`, getting the answers *back* is the part that fails, not the asking. The generated page already handles the mechanics — pre-filled current assumptions badged `Current`, a `[CHANGED]` marker so you can tell a real decision from an accepted default, one-button copy of a structured block, and autosave so a refresh doesn't lose a half-filled form.

What's on you:

- **Pre-fill every question with your current assumption.** This is the highest-leverage property: the human only has to touch what's wrong, so silence becomes a usable answer instead of a blocked task.
- **Set `ref`** to the ticket or decision id. A ticket-keyed paste-back stays greppable weeks later.
- **Assume the round trip is not same-session.** These pages get forwarded to a colleague and the answers come back through Slack days later, pasted into an unrelated session. Write every question so it makes sense to someone with no memory of the conversation.
- **Give decisions a reject path**, not just an answer field. A page that only offers "answer" gets silence for disagreement.
- **Ask only what you cannot determine yourself**, and put the stakes in `why`. A question whose consequences are invisible gets a shrug.

## Anti-patterns

- **Hand-writing the HTML**, or hand-editing the built page. You lose the guarantee and the next build erases it.
- **Publishing unseen.** Build checks catch broken pages, not unclear ones.
- **A beautiful page missing the thing the reader needed.** The failure mode the cost data actually points at.
- **No gap section**, on a change that plainly has loose ends.
- **Mixing teaching and asking** in one page.
- **A fourth near-identical copy** of a page that already exists — update it instead.
- **Fighting a wedged browser extension** for many turns instead of verifying programmatically and moving on.
- **Reading the date from the clock** — pass it in from context so the page is reproducible.

## Out of scope

- **Proof-of-work / verification evidence** — that's `prove-it`. It owns that genre, has its own builder and manifest schema, and enforces an evidence ledger this skill knows nothing about.
- **Repo documentation** — if it belongs in the codebase as markdown, write markdown.
- **The PR body** — that's `formlabs-pr-write`.
- **Interactive diagrams and architecture maps** — no genre exists; hand-author.
- **Deciding whether the underlying work is any good** — this presents the work, it doesn't review it.

## Extending the kit

`GENRES` in `scripts/build.py` maps a genre name to a function returning `(body_html, css, js)`. Add one when a second page of that shape is actually needed, not in advance. Shared components belong in `assets/theme.css`; only genre-specific rules go in the genre's own CSS string. Never introduce a token synonym — `--panel`, `--ground`, `--paper` competing with `--surface` and `--bg` is the exact divergence this kit exists to end.

By measured frequency, the highest-value unbuilt piece is a **self-check quiz block** for walkthroughs: it appeared in about a third of them, was independently reimplemented twice, and its graded output copies out as a list of missed topics that feeds straight into a teaching prompt. Do not build a tab switcher — a real one existed in 2 of 144 pages.
