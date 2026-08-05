# Artifact authoring cost & friction — transcript archaeology

Scope: 817 transcript files under `~/.claude/projects/**/*.jsonl` (main sessions + subagent
transcripts), 94 main-session files contain at least one `Artifact` tool call. Cross-referenced
against all 817 files because several artifacts were authored inside subagent transcripts that
never call `Artifact` themselves (the parent session publishes on their behalf).

## 1. Authoring cost

131 distinct artifact `.html` file paths were ever published via the `Artifact` tool.

| metric | median | mean | max |
|---|---|---|---|
| `Write` calls per artifact file | 1 | 1.0 | 3 |
| `Edit` calls per artifact file | 0 | 2.3 | 32 |
| `Artifact` publishes per file (iteration count) | 1 | 1.6 | 5 |
| First-write size (chars) | 24,226 | 25,660 | 70,543 |
| Total chars written per file (sum of all Writes) | 22,954 | 25,798 | 85,112 |

**Total characters ever written into artifact HTML across all sessions: 3,379,489** (a lower
bound — see caveat below). At ~4 chars/token that is roughly **845,000 tokens** of raw HTML/CSS/JS
generation, before counting the Edit diffs layered on top or the read-backs when Claude re-reads
its own artifact to fix something.

Worst cases:
- `fn1557-auto-resolve-walkthrough.html` — 2 writes, 5 edits, 1 publish, 85,112 chars
- `fn1463-architecture-hub.html` — 2 writes, 0 edits, **4 publishes**, 83,758 chars
- `order-state-machine.html` — 2 writes, 8 edits, 4 publishes, 75,445 chars
- `artifact-medusa-guide.html` — 1 write, **32 edits**, 1 publish, 31,387 chars (most-edited file in the corpus — almost all cost was iteration, not the first draft)
- `fcm-walkthrough.html` — 1 write, 30 edits, 4 publishes, 60,524 chars

Caveat: 16 of 131 published files (12%) show zero `Write` calls anywhere in any transcript for
that exact path. Spot-checking one (`fcm-walkthrough-src.html`) confirmed the pattern: the file
was authored inside a **subagent's own transcript** under a working-directory-relative or
differently-normalized path, so the exact string match missed it. The true total is higher than
3.38M chars.

Most artifacts are a single big `Write` (median 1) — Claude tends to generate the whole page in
one shot rather than build it incrementally. Where `Edit` counts run high (13–32), it is almost
always driven by user content-correction or scope-expansion requests, not typos.

## 2. Iteration causes

Found 54 "iteration boundaries" (a second Write/Edit/Artifact call on the same file following an
earlier one), 42 of which had genuine human-authored text in between (the rest were pure
system-injected noise: task-notifications, background command output, teammate relay messages —
these were filtered out with a noise-marker classifier before categorizing).

| category | approx. count | example |
|---|---|---|
| Missing / requested-more content (scope expansion) | ~14 | "okay, also include how it could be consolidated"; "also please include DFM check... give an example for ON HOLD and QUARANTINE" |
| Factual / content correction | ~9 | "please fact check the datasheet specs, I think you failed bigtime"; "why did we change the spec sheet?"; "I got pointed out the following: ... So we might not need this new logic" |
| Wanting interactivity / different presentation | ~6 | "please make it less table-like, more visual and graph like if possible with scenario calculator tab built in"; "add A/A as well as a mode, is there any other mode i should consider?" |
| Diagram/sequence requests | ~3 | "include a sequence diagram too please" |
| Rejecting invented content | ~2 | "please drop this meshy landing or email me this quote features, its something you came up with and i never approved... Clean up all text/artifacts related to the hallucinated ab test proposals" |
| Asset/image correction | ~2 | "i made a cutout from the one i want to keep, put it under ~/Documents/cut.png... Can we replace that asset with this cutout?" |
| Organization/UI nits (accordion state) | ~2 | "open, close others"; "open, close old ones that we replaced" |
| Distribution requests (repo/PR/Confluence) | ~5 | "checking in this html artifact would be also useful. PR For it"; "create a 'one artifact rules them all' version... Add it to this confluence page" |
| Wanting real verification, not just narrative | ~3 | "then run it with in the tilt env yourself, show me the outputs for each commands" |

Notably **absent**: explicit dark-mode-broken or overflow/clipping complaints. A targeted regex
sweep for `dark mode`, `overflow`, `cut off`, `too wide`, `unreadable`, `contrast` across all 94
sessions' user turns returned only 2 genuine hits, one of them unrelated ("pull the Order Images
overflow fix"). The one real hit was a **readability/density** complaint, not a color-scheme bug:

> "Take a look at this artifact> [link]. I got the following critique: it is very hard to read,
> too textual. I would like you to suggest ways to make easier to consume for low attention span
> people who are more visual and wont read even a 7 line paragraph"

So for this user, the design failure mode isn't "broke in dark mode" — it's "wall of prose,
should have been visual/scannable" and "missing content I now have to ask for a second time."

## 3. The answer-collection genre

Four clear specimens, one plain-markdown outlier:

### `fn-1424-quiz.html` — self-test quiz, graded client-side
- **Interaction model:** 12 multiple-choice questions, radio buttons, JS grades in-browser
  (compares selection to an answer key baked into the page), shows a scored results panel.
- **Persistence/export:** a `<textarea id="teachblock">` auto-fills with a plain-text summary
  (score + per-missed-question breakdown) and a "Copy" button copies it to the clipboard.
- **How the answer got back to Claude — it worked, cleanly:** the user copied the block and
  pasted it as the **argument to a slash command**, `/teach`:
  ```
  <command-name>/teach</command-name>
  <command-args>FN-1424 ship-estimate + FN-1425 registry — quiz result 9/12
  Missed topics: read-path-io, timing-semantics, on-hold-shape
  Q3 [read-path-io]
    I chose:  One per part
    Correct:  Zero
  ...
  Please teach me these topics from first principles using the actual code and spec, then re-quiz me.
  </command-args>
  ```
  This is the single tightest loop in the whole corpus: artifact → JS-generated structured text →
  clipboard → same-session slash command. No manual retyping, no ambiguity about format.

### `ship-estimate-ops-questionnaire.html` — multi-hop human relay (the interesting failure mode)
- **Interaction model:** ~15-20 questions across radio buttons, checkboxes, and free-text
  textareas, grouped into numbered "parts," with a "respondent" name field at the top.
- **Persistence/export:** identical pattern to the quiz — a live-updating preview `<textarea>`
  fed by a `buildSummary()` JS function, plus a copy button. But the button's success label
  reveals the *intended* recipient isn't Claude: `"Copied — send it to Daniel ✓"`.
- **How the answer actually got back — multi-hop, and it worked, but not automatically:**
  1. The user (Daniel) published the artifact and evidently sent the link to an ops colleague,
     Ben, out-of-band (Slack, most likely) — there is no trace of that hop in any transcript.
  2. Ben filled out the form and hit "Copy answers," producing the exact markdown format the
     `buildSummary()` JS emits.
  3. Ben sent that text back to Daniel through some external channel.
  4. **Weeks later, in a brand-new Claude Code session** (different session ID, after the
     referenced PR had already merged), Daniel pasted the block in verbatim:
     ```
     We merged this: https://github.com/Formlabs/formcloud-manufacturing/pull/1854
     I asked you beforehand to create a quiz for the OPS to clarify stuff, here are the results:
     # Ship-Estimate Ops Sanity Pass — Answers
     From: Ben
     ## Where the spec left gaps
     ### Can we detect strip-and-ship / supports-attached orders?
     Answer: There IS a reliable signal for strip-and-ship / supports-attached (explained below)
     Note: Even if the field is free text, isnt it going to be consistent across orders?...
     ```
  The artifact's own text format survived the whole relay intact and was directly usable — the
  design succeeded — but the *transport* between artifact and Claude was 100% manual, spanned
  people and days, and left zero trace in the tool-call record. If Ben had pasted his answers into
  Slack instead of copying the generated block, or paraphrased instead of pasting verbatim, this
  loop breaks silently and nobody would know until Daniel went looking for the answers.

### `fn1596-answers.html` / `fn1596-veto-review.html` — the request that specifies the answer, verbatim
This is the most important data point for what to build next, because the user **directly stated
the requirement**, unprompted:

> "Ask me questions that are waiting on me. Create a very simple artifact that shows me questions
> with enough context and i can select/type my answers the the result can be copy pasted back to
> you easily"

- **Interaction model:** ~8 questions, each with radio-button preset options plus a "type your
  own" free-text fallback (`type="radio"` + `type="text"`), one big textarea for a catch-all note.
  The follow-up `fn1596-veto-review.html` used the same pattern for a design-review pass, adding
  an explicit **VETO** option per decision so "no objection" and "reject this" are both one click.
- **Persistence/export:** copy-to-clipboard of a compact `KEY (label): value` text block —
  deliberately terse, matching Jira ticket IDs to answers.
- **How it got back to Claude — worked perfectly, same session, no relay:**
  ```
  FN-1596 answers — Daniel, 2026-08-04
  FN-1597 (D1 data shape): [typed] Treat it the same as already existing finishes
  FN-1598 (D2 MES statuses): one generic status pair
  FN-1599 (D3 size-tier basis): implement spec §1.2 percentile-of-max basis
  ...
  ```
  and for the veto pass:
  ```
  FN-1596 design feedback — Daniel, 2026-08-04
  FN-1613 (routing design): stands
  FN-1614 (config plan): stands
  FN-1617 (gating design): VETO — Btw, it's fine if we leak it. Its not a big secret if it
    significantly decreases complexity. Its totally acceptable to just gatekeep on the ui
  ```
  Because the user asked for exactly this pattern up front, there was no failed first attempt —
  it's the cleanest specimen in the corpus and effectively a design spec for the ideal artifact.

### `finishing-options-asks.md` — the non-artifact control case
A plain markdown file (no `Artifact` tool call, no JS, no interactivity) from the same FN-1596
project, structured as a prioritized list: `🔴/🟠/🟡` urgency flags, per-item **Ask** +
**My recommendation** fields, grouped "FOR THE PM" / presumably "FOR DESIGN" sections. This
predates the interactive HTML artifacts in the same session lineage — it reads like the first,
static attempt at "collect open questions," superseded once the user asked for something
"copy-pasted back easily." It has no return mechanism at all: whoever reads it would have to
answer in prose, by hand, in whatever medium they're using — there's no format to preserve
structure on the way back. It's useful as the "before" picture.

### What the ideal answer-collection artifact would do differently
1. **State the copy format as ticket-ID-keyed key:value pairs**, not prose — `fn1596-answers.html`
   already nails this, and it's what made the paste-back trivially parseable by Claude days later.
2. **Never assume the round trip is same-session.** The ops-questionnaire case proves people
   forward these artifacts to third parties and the answers come back through Slack/email into an
   unrelated future session. Any built-in "submit" step (email link, `mailto:`, a hosted endpoint)
   would remove the silent-failure risk of "did the answer text survive the human relay."
3. **A VETO/one-click-reject option matters as much as an answer field** — the veto-review
   variant shows decisions aren't just "what's the answer," they're also "should this decision
   even stand," and the artifact should surface both.
4. **Keep it terse.** The user explicitly said "very simple artifact" and got the highest-fidelity
   round trip of the whole corpus; the more elaborate multi-part questionnaire (ops one) worked
   too, but only because the copy-button format was disciplined — the elaborate CSS/visual layer
   contributed nothing to whether the answer got back correctly.

## 4. What the user praised / rejected — standing preferences

Direct feedback found in the transcripts (quotes are the user's own words):

- **Wants visual/scannable over prose-heavy**, explicitly after a colleague's critique:
  > "it is very hard to read, too textual. I would like you to suggest ways to make easier to
  > consume for low attention span people who are more visual and wont read even a 7 line
  > paragraph"

- **Wants sourcing/citations, not confident-sounding assertions**, mid-build of a research
  artifact:
  > "Fixable by connecting the data source properly. - why do you claim this, explain"
  > "please flag all 'ASSUMPTIONS', otherwise cite sources for claims"

- **Hard line against invented/unapproved content appearing in artifacts** — this is the sharpest
  rejection in the corpus:
  > "please drop this meshy landing or email me this quote features, its something you came up
  > with and i never approved. First target is the new landing page, period. Clean up all
  > text/artifacts related to the hallucinated ab test proposals"

- **Prefers less-tabular, more-visual, with built-in interactivity** for data/decision pages:
  > "please make it less table-like, more visual and graph like if possible with scenario
  > calculator tab built in"

- **Wants a single canonical artifact rather than a scattered set**, when consolidating a
  decision record for sharing outside Claude Code:
  > "create a 'one artifact rules them all' version that I can share with the team, contains every
  > decision. Add it to this confluence page: [...] For interactive stuff, its fine to render
  > separate claude artifacts and link them there."

- **Treats useful artifacts as worth checking into the repo**, not just ephemeral:
  > "update the artifact for it, and also please create a detailed markdown descripition of our
  > data architecture for later context when we need to work with it. Should go into the repo on
  > a feature branch, i think checking in this html artifact would be also useful. PR For it"

- **The explicit design brief for answer-collection artifacts** (already quoted above, repeated
  here because it's the single most load-bearing sentence in the corpus for this investigation):
  > "Create a very simple artifact that shows me questions with enough context and i can
  > select/type my answers the the result can be copy pasted back to you easily"

- **Wants real execution over narrated confidence**, a recurring theme outside artifacts too but
  visible in artifact-adjacent turns:
  > "then run it with in the tilt env yourself, show me the outputs for each commands"

No standing instruction anywhere (CLAUDE.md, skill files) currently codifies artifact
conventions — the `artifact-design` / `artifact-diagramming` skills exist at the harness level,
but this user's own project CLAUDE.md files have no artifact-specific rules. The `/teach` and
FN-1596 sessions suggest the lessons are currently living only in the user's memory / habit of
re-asking each time, which is exactly the cost this investigation is meant to justify cutting.
