# Anatomy of the Artifact Corpus (144 files)

Data sources: `existing.txt` (144 live paths), `measure.py` + `measurements.csv`
(per-file byte/line/style/script/content counts), `titles.csv` (title/h1/feature
scan), plus targeted greps quoted inline below. All 144 files were measured;
genre classification and defect-hunting are based on titles/headings/class-name
frequency across the full set plus close reading of ~15 representative files.

---

## 1. Measurements

Aggregate, all 144 files:

| Metric | Value |
|---|---|
| Total bytes | 11,374,071 (11.4 MB) |
| Total lines | 76,033 |
| `<style>` lines | 26,463 (34.8%) |
| `<script>` lines | 10,441 (13.7%) |
| Content lines (everything else) | 39,129 (51.5%) |
| Aggregate boilerplate (style+script) / content ratio | **0.94×** |

Per-file (more representative than aggregate, which three huge outliers skew):

| Metric | Median |
|---|---|
| Bytes | 28,520 |
| Total lines | 488 |
| Style lines | 176 |
| Script lines | 8 |
| Content lines | 212 |
| **Boilerplate/content ratio** | **0.86×** (mean 1.52×, pulled up by a long tail) |

Reading: the typical artifact is essentially **one line of CSS for every one
line of "real" content**, and script is a rounding error (median 8 lines —
most artifacts have no JS at all, or a single click handler). CSS is the
dominant boilerplate cost, not JS.

**Size distribution (bytes):**

| Bucket | Files |
|---|---|
| 0 – 10K | 14 |
| 10K – 25K | 45 |
| 25K – 50K | 58 |
| 50K – 100K | 20 |
| 100K – 200K | 1 |
| 200K+ | 6 (outliers — see below) |

**Line-count distribution:**

| Bucket | Files |
|---|---|
| 0 – 300 | 42 |
| 300 – 600 | 56 |
| 600 – 1,000 | 37 |
| 1,000 – 1,500 | 7 |
| 1,500 – 2,500 | 1 |
| 2,500+ | 1 |

**Per-file boilerplate/content ratio distribution:**

| Ratio | Files |
|---|---|
| 0 – 0.5× | 26 |
| 0.5 – 1.0× | 55 |
| 1.0 – 1.5× | 31 |
| 1.5 – 2.0× | 17 |
| 2.0 – 3.0× | 6 |
| 3.0×+ | 9 |

The 9 files above 3× boilerplate are almost all the **Architecture/Lineage**
genre (interactive lineage maps, SVG/JS-heavy diagram shells) plus one quiz.
The 26 files under 0.5× are dense prose walkthroughs, decision records, and a
handful of degenerate cases (styleless raw-content fragments used to assemble
a bigger page — `part-02-runB-scenarios.html`, `new-section-stack.html`).

**Outliers to know about, not to design around:**
- `artifact-1aeaba92-…5be8.html` (3.3 MB, 4,068 lines, 3,477 script lines) —
  a cached tool-results copy with an embedded large JS payload; skews every
  aggregate. Treat as noise, not signal.
- `proof/proof.html` (1.1 MB, only 236 lines) — almost certainly embeds a
  base64 image/screenshot inline.
- `fn1463-latest-run-slides.html` (826 KB, 577 lines) — a slide deck, likely
  with embedded screenshots.
- `fcm-bigquery-lineage.html` and `fcm-lineage.html` (~700 KB each) — the
  interactive BigQuery lineage explorer, which embeds a large graph-data JSON
  blob inline.

---

## 2. Genres

144 files sorted into 11 buckets by reading titles, `<h1>`, and structure.
Three "genres" from the original candidate list didn't hold up as separate —
**hub/index** turned out to be a presentation variant of Architecture, not a
distinct genre — and one new bucket emerged (**Fragment/Build-artifact**:
partial HTML used as input to assemble a bigger page, not itself a finished
artifact) plus one one-off (**Reference/Registry**, a single vocabulary-table
page that's really a stub Reference genre).

| Genre | Count | Representative files |
|---|---|---|
| **Walkthrough/Explainer** | 72 | `fn1557-auto-resolve-walkthrough.html`, `fcm-walkthrough.html`, `pr524-explainer.html`, `order-query-walkthrough.html` |
| **Proof-of-Work / Verification** | 14 | `fn-1424-proof-of-work.html`, `fn-1409-smoke-test-evidence.html`, `behavior-proof.html`, `fn1463-e2e-session-summary.html` |
| **Architecture-Map / Lineage / State-Machine** | 13 | `fcm-lineage.html`, `order-state-machine.html`, `fcm-part-state-architecture.html`, `fn1463-architecture-hub.html` |
| **Decision-Record / Comparison** | 8 | `dash-4622-decision.html`, `bi-tool-comparison.html`, `metabase-spike-readout.html`, `fn1596-veto-review.html` |
| **Prototype / Mockup / Deck** | 8 | `order-status-mockup.html`, `variant-a-statusboard.html`, `slides-template.html`, `dfm-decision-page-prototype.html` |
| **Plan / Epic / Status** | 7 | `finishing-options-epic.html`, `dfm-wayfinder-plan.html`, `fn1463-rebuild-status.html`, `roadmap.html` |
| **Reference / Glossary / Lesson** | 6 | `bigquery-glossary.html`, `kubernetes-glossary.html`, `0001-reading-a-ship-estimate.html`, `ship-estimate-contract.html` |
| **Incident / RCA** | 5 | `rma_outage_rca.html`, `ppd-010-root-cause.html`, `abidingmammoth-incident.html`, `incident-2026-07-27-fcm-shipped-email.html` |
| **Quiz / Questionnaire** | 4 | `fn-1424-quiz.html`, `fn1596-answers.html`, `ship-estimate-ops-questionnaire.html` |
| **Fragment / Build-artifact** (not standalone) | 2 | `body-raw.html`, `new-section-stack.html` |
| **Reference / Registry** (n=1, folded into Reference above conceptually) | 1 | `registry-pr.html` |
| **Excluded** (not artifacts from this practice) | 4 | 3× Django `dfm_review_email.html` transactional-email templates checked into service repos; `kidsofa/index.html`, an unrelated personal sandbox page |

Notes on the merge/split calls:
- **Walkthrough/Explainer absorbs "PR reviewer's guide"** — files like
  `pr-1856-models.html`, `fcm-walkthrough-src.html`, `artifact-fcm-guide.html`
  read identically to narrative walkthroughs (same skeleton, same components);
  the only difference is subject matter (a PR diff instead of a shipped
  feature). Not worth a separate genre.
- **Incident/RCA is a distinct genre from Walkthrough**, not a subtype —
  it has an inverted skeleton (symptom → evidence → root cause → ruled-out
  list) rather than the walkthrough's forward narrative, and a much heavier
  evidence-table density.
- **Hub/index pages are Architecture-Map presentations**, not a separate
  genre — `fn1463-architecture-hub.html`, `hub-fn1463.html` are landing pages
  for a set of diagrams/links, structurally identical to a lineage-map file
  with a nav-heavy top section.
- **Quiz is not merely a walkthrough feature** — the 4 quiz-genre files exist
  standalone with a single job (post-hoc knowledge check), even though the
  *quiz component* itself (self-check questions embedded near the end) also
  appears bolted onto 12 other Walkthrough files.

---

## 3. Shared design DNA

### 3.1 CSS custom-property tokens

`:root { … }` blocks appear in 136 of 144 files (94%). Token **names** are
highly convergent — this is the strongest evidence of a de facto standard —
but token **values** are reinvented almost every time.

Top token names by number of `:root` block occurrences they appear in
(519 total `:root` blocks counted, including per-file media/attribute
overrides):

```
494  --ink            344  --accent-soft     183  --shadow         138  --ok
412  --accent         282  --bg              156  --surface-2      120  --card
350  --line           216  --ink-soft        156  --line-strong    115  --ground
                       214  --muted           154  --panel          111  --paper
                       192  --surface         153  --ink-faint      102  --warn-soft
                                                                     100  --mono
```

So the near-universal vocabulary is: `--ink` (text), `--accent` (brand/link),
`--line` (hairline borders), `--bg`/`--ground`/`--paper` (page background —
three synonyms competing), `--surface`/`--panel`/`--card` (raised-element
background — three more synonyms), `--muted`/`--ink-soft`/`--ink-faint`
(de-emphasized text — three levels, inconsistently named), `--ok`/`--good`,
`--warn`, `--bad`/`--danger`/`--fail` (status colors, again 2-3 synonyms per
concept), and `--mono`/`--sans` (font stacks).

**No two files share the same hex values for these tokens.** Sampling the
top 5 most common `--ink` values across the corpus: `#18202e`, `#dbe3ef`,
`#e7edf3`, `#e9edf3`, `#1c1b22` — each appears in only 12-16 of 136 files.
Same story for `--accent` (`#0762c8`, `#4a9bf0`, `#2f52d0`, `#7d9cff`,
`#45438f` — a different blue every time) and every other token. There is no
canonical palette; there is a canonical *naming scheme* that gets a fresh
palette invented per file.

**Canonical token block worth adopting as-is for a template kit** (from
`fn1557-auto-resolve-walkthrough.html`, chosen because it cleanly separates
light/dark without redundancy):

```css
:root {
  --ground: #F6F7F7;      --surface: #FFFFFF;     --sunk: #EDF0F0;
  --ink: #14181B;         --muted: #5F6769;       --faint: #8A9294;
  --rule: #DBE0E0;
  --accent: #0F5257;      --accent-soft: #E2EDED;
  --signal: #8A5800;      --signal-soft: #FBF0D9;   /* warn */
  --good: #1E6F45;        --good-soft: #E3F0E8;
  --bad: #8C2F1E;         --bad-soft: #F7E7E3;
  --display: system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
  --body: system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
  --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
}
```

Recommendation for the template kit: standardize on ONE name per concept
(`--bg` not `--ground`/`--paper`; `--surface` not `--panel`/`--card`;
`--text-muted` not `--muted`/`--ink-soft`/`--ink-faint` as three tiers —
pick two max) and ship one real palette, not a reinvented one per doc.

### 3.2 Dark/light theme handling

This is the most consistent thing in the entire corpus. Of 136 files with a
`:root` block, the combination of **(media query, `[data-theme="dark"]`,
`[data-theme="light"]`)** breaks down as:

| media query | `[data-theme=dark]` | `[data-theme=light]` | own JS toggle | Files |
|---|---|---|---|---|
| yes | yes | yes | no | **118** |
| no | no | no | no | 18 (no dark-mode support at all) |
| yes | yes | yes | yes | 6 (redundant — see defects) |
| yes | no | no | no | 2 |

**82% of files (118/144) use the identical canonical three-block pattern**:
a default `:root{}`, a `@media (prefers-color-scheme: dark)` override, and
explicit `:root[data-theme="dark"]` / `:root[data-theme="light"]` attribute
overrides — with **no JS toggle code**, because the hosting viewer stamps
`data-theme` on the root element itself. This is the correct, minimal
pattern and should be the template kit's default.

Canonical version (same file as above):

```css
:root { /* light values, see 3.1 */ }

@media (prefers-color-scheme: dark) {
  :root {
    --ground: #0E1213; --surface: #171D1E; --sunk: #121718;
    --ink: #E7ECEC; --muted: #A0A9AA; --faint: #6E7778; --rule: #2A3233;
    --accent: #57A8AD; --accent-soft: #16292B;
    --signal: #D8A62E; --signal-soft: #2A2113;
    --good: #59B383; --good-soft: #16281E;
    --bad: #D98570; --bad-soft: #2A1815;
  }
}
:root[data-theme="dark"] {  /* identical block to the media query, repeated */ }
:root[data-theme="light"] { /* identical block to the top-level :root, repeated */ }
```

Note the defect baked into even the canonical pattern: the dark values are
written out **twice** (once under the media query, once under the attribute
selector) and the light values are written out **twice** too (top-level
`:root` and `:root[data-theme="light"]`). Every file pays this 2× tax. A
template kit should define the values once as a map and generate both
selectors, or accept the duplication as a known, deliberate cost of
self-contained single-file HTML (no build step) — but it shouldn't be
copy-pasted by hand each time, which is what's happening now.

### 3.3 Recurring component markup

Class-name frequency across files (unique files using the class, not total
occurrences) — the top ~15 are a genuine shared vocabulary:

```
109 .eyebrow    70 .callout    65 .tag       50 .chip      33 .card
101 .wrap       69 .lede       63 .toc       48 .k         31 .verdict
                                45 .node     45 .sub       31 .note
                                                            30 .panel
```
(`.warn`/`.ok`/`.opt`/`.quiz`/`.lbl`/`.q` etc. are quiz/status-specific and
covered under Quiz in 4.)

**`.eyebrow`** (109/144 files — the single most universal class in the
corpus): a small uppercase mono-font label above the H1.
```css
.eyebrow {
  font-family: var(--mono); font-size: .69rem; text-transform: uppercase;
  letter-spacing: .13em; color: var(--muted); margin: 0 0 .7rem;
}
```
```html
<p class="eyebrow">FN-1557 · SHIPPED 2026-06-30</p>
<h1>The hold now ends on a date the customer was told</h1>
```

**`.wrap`** (101/144): the outer page container.
```css
.wrap { max-width: 60rem; margin: 0 auto; padding: 0 1.5rem 6rem; }
```

**`.callout`** (70/144): a bordered, tinted aside box, usually with a
`.warn` variant.
```css
.callout {
  background: var(--accent-soft); border: 1px solid var(--accent);
  padding: .95rem 1.15rem 1rem; margin: 1.4rem 0; border-radius: 3px;
}
.callout.warn { border-color: var(--signal); background: var(--signal-soft); }
.callout .lbl {
  font-family: var(--mono); font-size: .68rem; text-transform: uppercase;
  letter-spacing: .11em; display: block; margin-bottom: .35rem;
  color: var(--accent); font-weight: 600;
}
```
```html
<div class="callout warn">
  <span class="lbl">Gap</span>
  <p>The SQL pre-filter uses a 5-minute window; a burst past that boundary is missed.</p>
</div>
```

**`.verdict`** (31/144, but conceptually present in every Proof-of-Work file
under some name — `.verdict`/`.pass-fail`/status pill): a pass/fail banner.
```css
.verdict {
  display: flex; gap: .55rem; align-items: baseline; margin-top: .8rem;
  font-size: .92rem; padding: .6rem .75rem; border-radius: 3px;
  background: var(--surface); border: 1px solid var(--rule);
}
.verdict b {
  font-family: var(--mono); font-size: .68rem; text-transform: uppercase;
  letter-spacing: .09em; padding: .16rem .45rem; border-radius: 2px;
}
.verdict.ok { border-color: var(--good); }
.verdict.ok b { background: var(--good-soft); color: var(--good); }
.verdict.no { border-color: var(--bad); }
.verdict.no b { background: var(--bad-soft); color: var(--bad); }
```

**`.pill`/`.chip`/`.tag`/`.badge`** (50-65 files, three-to-four names for
the same idea — small rounded status label):
```css
.pill {
  font-family: var(--mono); font-size: .68rem; padding: .16rem .42rem;
  border-radius: 2px; white-space: nowrap; display: inline-block;
}
.pill.good { background: var(--good-soft); color: var(--good); }
.pill.bad  { background: var(--bad-soft);  color: var(--bad); }
```

**KPI/stat tile** (`.kpi`, seen in Plan/Epic and Decision-Record genres,
~10 files): a grid of number+label+sublabel cells.
```css
.kpis { display:grid; grid-template-columns:repeat(auto-fit, minmax(158px,1fr));
        gap:1px; background:var(--rule); border:1px solid var(--rule); margin:26px 0 0; }
.kpi  { background:var(--surface); padding:13px 14px; }
.kpi__n { font-family:var(--mono); font-size:1.55rem; font-variant-numeric:tabular-nums; }
.kpi__l { font-family:var(--mono); font-size:9.5px; letter-spacing:.1em;
          text-transform:uppercase; color:var(--ink-3); margin-top:6px; }
.kpi__s { font-size:12px; color:var(--ink-2); margin-top:3px; line-height:1.35; }
```
```html
<div class="kpi kpi--exists">
  <div class="kpi__n">≈60%</div>
  <div class="kpi__l">already-built infra</div>
  <div class="kpi__s">of the customer-facing requirements</div>
</div>
```

**Table** (89/144 files have at least one `<table>`) — canonical version
pairs the table with a `.tablewrap`/`.tscroll` overflow container:
```css
table { width: 100%; border-collapse: collapse; font-size: .88rem; margin: 1.2rem 0; }
.tscroll { overflow-x: auto; }
th, td { text-align: left; padding: .55rem .6rem; border-bottom: 1px solid var(--rule); }
th { font-family: var(--mono); font-size: .66rem; text-transform: uppercase;
     letter-spacing: .09em; color: var(--muted); border-bottom: 1px solid var(--ink); }
td.num { font-variant-numeric: tabular-nums; }
```
But — see defect list — this wrapper is present in only 65/89 (73%) of
files that have tables.

**Code block** (near-universal, no file count needed — every genre uses it):
```css
pre {
  font-family: var(--mono); font-size: .8rem; line-height: 1.55;
  background: var(--sunk); border: 1px solid var(--rule); border-radius: 3px;
  padding: .85rem 1rem; overflow-x: auto; margin: 1.1rem 0;
}
code { font-family: var(--mono); font-size: .875em; background: var(--sunk);
       padding: .1em .32em; border-radius: 2px; }
pre code { background: none; padding: 0; font-size: 1em; }
```

**TOC / nav** (`.toc`, 63/144): a numbered link list at the top of long
walkthroughs, using CSS counters:
```css
nav.toc ol { list-style: none; margin: 0; padding: 0; display: grid; gap: .1rem; counter-reset: t; }
nav.toc li { counter-increment: t; border-bottom: 1px solid var(--rule); }
nav.toc a::before {
  content: counter(t, decimal-leading-zero);
  font-family: var(--mono); font-size: .72rem; color: var(--faint);
}
```

**`<details>` collapsible** (14/144 — a real component, but far rarer than
the class-name grep first suggested): used in Plan/Epic and Prototype genres
for optional/secondary content, plain native markup with light CSS styling
of `summary`, no JS.

**Mermaid diagrams** (10/144 — also rarer than a naive "mentions the word
mermaid" search suggested; 10/10 of those really render a diagram): appears
almost exclusively in Architecture-Map genre and a couple of Plan/Epic files
that include a flow diagram. No custom mermaid theme config found beyond the
default — none of the 10 files re-theme mermaid to match the page's dark
mode, which is itself a defect (see 5).

**Timeline/step list**: present under several different implementations
per genre (see 5 — this is one of the least standardized components), most
commonly a vertical list with a numbered/dotted connector rendered in pure
CSS (`::before` pseudo-elements on list items), no shared class name — seen
as `.step`, `.seq`, `.flow .node`, `.states .state` depending on the file.

**"Diff block"**: no dedicated, reusable diff component was found anywhere
in the corpus — PR-focused walkthroughs (`pr-1856-models.html` etc.) either
paste code as plain `<pre>` blocks with manual `+`/`-` prefixes and ad hoc
inline-styled green/red spans, or skip diff rendering and describe the
change in prose. This is a real gap for the "Walkthrough of a PR" skeleton.

### 3.4 Recurring JS

Script is thin (median 8 lines/file) and mostly limited to four patterns:

**Copy-to-clipboard** (49/144 files — the single most common script):
```js
document.getElementById('copyBtn').addEventListener('click', function () {
  var text = /* build a plaintext summary of misses / findings */;
  out.querySelector('pre').textContent = text;
  if (navigator.clipboard) { navigator.clipboard.writeText(text).catch(function () {}); }
});
```
The overwhelmingly common *use* of clipboard-copy is not "copy this code
snippet" (the generic dev-tool pattern) but **"copy a structured summary of
what the reader got wrong/needs clarified"** — i.e., it's coupled to the quiz
pattern below, not a standalone utility.

**Self-check quiz** (16/144 files, but conceptually the dominant "interactive"
element of the whole corpus — every Quiz-genre file plus roughly a third of
Walkthrough files end with one): a `QUESTIONS` array driving generated
multiple-choice buttons, disables options after first click, reveals the
correct answer + a "why" explanation, and tracks misses for the copy button
above.
```js
QUESTIONS.forEach((item, qi) => {
  const card = document.createElement("div");
  card.className = "q";
  item.opts.forEach((text, oi) => {
    const btn = document.createElement("button");
    btn.addEventListener("click", () => {
      if (card.dataset.answered) return;
      card.dataset.answered = "1";
      buttons.forEach((b, bi) => { b.classList.add("disabled");
        if (bi === item.correct) b.classList.add("correct"); });
      if (oi !== item.correct) { btn.classList.add("wrong"); missed.set(qi, {picked:text}); }
      explain.textContent = item.why; explain.classList.add("show");
    });
  });
});
```
Two independent implementations of this exist in the corpus with different
variable names and slightly different DOM-building strategies (inline HTML
string vs. `createElement` calls) — see defects.

**Theme-toggle JS** (6/144 — and a defect, not a feature, per 3.2): a
`matchMedia('(prefers-color-scheme: dark)')` listener duplicating what the
CSS attribute-selector pattern already covers.

**Mermaid init**: only 1 of the 10 mermaid files calls `mermaid.initialize()`
explicitly; the rest rely on default init behavior of whatever mermaid build
they inlined/loaded.

**Not found anywhere in the corpus** (despite being asked about specifically):
a genuine tab-switching component (`role="tab"`/`data-tab=`/`.tab-btn`
appears in only 2/144 files — everything else that superficially matched
"tab" in a naive grep was `.tablewrap`/`<table>`), filter/search UI,
collapse-all-details control (only 1 file), and localStorage-based state
persistence beyond the (rare) theme toggle. These are gaps, not omissions
from measurement.

---

## 4. Per-genre skeletons

**Walkthrough/Explainer** (n=72, the default shape):
1. `.eyebrow` ticket/PR id + status chips
2. `<h1>` — a claim, not a topic ("The hold now ends on a date the customer
   was told", not "FN-1557 changes")
3. `.standfirst`/`.lede` — one-sentence expansion of the claim
4. `.meta` chip row (date, author, links)
5. `nav.toc` — numbered section list
6. Body sections, each: `<h2>`, prose, then one of {table, code block,
   diagram/strip visualization, callout}
7. A "gap/limitation" callout near the end (very common — "The gap I did not
   close", "What wasn't verified")
8. Optional: "Check your understanding" quiz block
9. Footer with generation metadata

**Proof-of-Work/Verification** (n=14):
1. `.eyebrow` + `<h1>` framed as a PASS/FAIL claim ("PASSED", "proven
   end-to-end")
2. Summary/verdict banner immediately under H1
3. "What each stage proved" — ordered list mapping requirement → test → result
4. Evidence table (command output, screenshots, log excerpts) — often the
   single largest section
5. Gate checklist (explicit pass/fail per named check)
6. Configuration/environment appendix

**Incident/RCA** (n=5, inverted relative to Walkthrough):
1. `<h1>` states the symptom, not the cause ("RMA records stopped reaching
   the warehouse")
2. Summary
3. A visual "cliff"/anomaly chart or timeline
4. "How X is created" — normal-path explainer (context before blame)
5. Evidence section, heavy on tables
6. "Root cause · ranked" — ordered hypothesis list
7. "Ruled out (with evidence)" — explicitly listing rejected hypotheses
8. "What to check next" / reporting impact

**Architecture-Map/Lineage** (n=13):
1. Title + short framing line
2. Legend (color/shape key)
3. Interactive canvas/SVG diagram (the bulk of the file's script+style)
4. "Selection" detail panel that updates on click (reads-from/used-by counts)
5. Minimal prose — this genre is diagram-first, text-second

**Decision-Record/Comparison** (n=8):
1. `<h1>` frames it as a forced choice, not a report
2. "What's verified, and what isn't" — grounds the decision in known facts
3. "The constraint" — the real limiter
4. "The option space" — options named neutrally (A/B/C), not pre-ranked
5. Side-by-side comparison table
6. "Consequences by surface" — impact broken out per affected system
7. Recommendation, stated last, with "if you pick X the work is…" scoping

**Plan/Epic/Status** (n=7):
1. Title + KPI tile row ("60% already-built", "3 open questions")
2. `<details>`-collapsed sections per requirement/workstream (the one genre
   that leans on native `<details>` as primary structure, not an aside)
3. Numbered requirement deltas
4. Cross-system flow description (pricing, lead time, MES, etc.)
5. Open/dormant items called out separately at the end

**Prototype/Mockup/Deck** (n=8): least standardized — genuinely a grab-bag
of UI mockups (order-status page clone), A/B design variants (three parallel
files, same content three visual treatments), and literal slide decks
(full-viewport sections, one per "slide", no shared chrome with the rest of
the corpus).

**Quiz/Questionnaire** (n=4): title framed as a direct question to the
reader ("Do you know what actually shipped?"), then straight into the
QUESTIONS-array quiz component from 3.4 with no other prose scaffolding.

**Reference/Glossary/Lesson** (n=6): term-definition list or numbered lesson
sequence; notably the two *outside* `~/.claude/teach/` (i.e. `~/teach/…`)
have **no dark-mode CSS at all**, unlike every other genre.

---

## 5. Divergences and defects

Ranked by how often they recur and how much rework they'd save:

1. **Same token names, different palette, every single file (136/136).**
   Nobody is starting from a shared palette; the naming convention is
   memorized but the values are reinvented per session. This is the single
   highest-leverage fix for a template kit — ship one real palette.

2. **Three-way synonym competition for the same concept.** Page background:
   `--bg` vs `--ground` vs `--paper` (three names, no file uses more than
   one, but different files pick different ones). Raised surface:
   `--surface` vs `--panel` vs `--card`. Muted text: `--muted` vs
   `--ink-soft` vs `--ink-faint` (sometimes all three in one file, at three
   different opacities, sometimes just one doing all three jobs). Status
   colors: `--ok`/`--good`, `--bad`/`--danger`/`--fail`. A kit should pick
   one name per concept and enforce it.

3. **Tables that don't scroll — 24 of 89 files with a `<table>` (27%) have
   at least one table not wrapped in an `overflow-x:auto` container.** On a
   narrow viewport these tables cause horizontal page overflow. This is a
   pure omission — the fix (`.tscroll { overflow-x: auto }`) is already the
   majority pattern in the other 73%, it's just not applied consistently.

4. **Dark mode is present-but-duplicated, or simply absent.** The canonical
   118-file pattern (3.2) hand-copies the same color values twice (media
   query block + attribute-selector block). Separately, 18/144 files (12.5%)
   have no dark-mode handling at all — concentrated in the Proof-of-Work
   genre (4/14) and files outside the `.claude/teach/` lesson tree.

5. **Redundant JS theme toggles (6 files).** These files re-implement
   `matchMedia` + manual class toggling on top of the CSS attribute-selector
   pattern that the hosting viewer already drives via `data-theme`. Dead
   weight, and a maintenance trap if the two disagree.

6. **The quiz component has at least two independently-written
   implementations** with different DOM-construction strategies
   (`document.createElement` chains vs. innerHTML string building) and
   different variable names (`misses` vs `missed`, `opt.dataset.i` vs
   closure index) doing the identical job. A single quiz partial would
   eliminate this.

7. **No diff-block component exists.** Every PR-walkthrough file that shows
   a code change does it differently — plain `<pre>` with manually-typed
   `+`/`-` markers and ad hoc `<span style="color:...">` runs, or skips
   showing the diff and describes it in prose instead. This is a genuine
   gap worth designing a component for, not just standardizing an existing
   one.

8. **Timeline/step-list has 3+ different implementations** across genres
   (`.step`, `.seq`, `.flow .node`) with no shared CSS, despite functionally
   identical output (a vertical connected sequence). Worth consolidating
   into one canonical component.

9. **False-positive "tabs" everywhere.** A naive grep for "tab" hits
   `.tablewrap`/`<table>` in 25 files but a real tab-switcher UI component
   exists in only 2 files corpus-wide. Worth calling out explicitly so a
   template kit doesn't over-invest in a tab component nobody's actually
   using — the interaction pattern for "compare N things" in this corpus is
   almost always a side-by-side table or three parallel prototype files, not
   client-side tabs.

10. **Mermaid diagrams aren't re-themed for dark mode (10/10 files).** Every
    file that uses mermaid renders it with default colors regardless of the
    surrounding page's `data-theme`, producing a jarring light-diagram
    on-dark-page mismatch. A kit should ship a mermaid theme call keyed to
    `data-theme`.

11. **Three near-duplicate copies of the same walkthrough exist as separate
    files** in at least two cases (`order-query-walkthrough.html` appears
    verbatim-ish in `7d761608/`, `a828df0d/`, and as a cached
    `tool-results/artifact-*.html`; similarly for the FCM Order Query
    reviewer's guide). Not a markup defect, but a process one: the same
    artifact is being regenerated/re-pasted across sessions instead of
    updated in place, multiplying the boilerplate cost counted in §1 by however
    many times a walkthrough gets redone.

12. **A handful of size outliers embed large data blobs inline** (base64
    screenshots in `proof/proof.html`, a full lineage-graph JSON in
    `fcm-lineage.html`/`fcm-bigquery-lineage.html`). These aren't wrong, but
    they should be excluded from any "typical artifact size" budget the
    template kit assumes, and are candidates for an external-data-file
    convention if the kit wants to keep base artifacts small.
