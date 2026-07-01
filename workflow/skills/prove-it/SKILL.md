---
name: prove-it
description: "Produces a proof-of-work artifact for a completed task: turns the stated goal and its requirements into concrete tests, RUNS them for real, captures the evidence (command output, test pass/fail, screenshots), and renders a consistent HTML proof artifact mapping each requirement to how it was tested and its result. Use whenever the user asks you to 'prove it', 'show me proof you did the work', 'prove that X works', 'verify the work is done', wants a verification/validation report, or wants evidence a finished task actually works — even if they don't say the word 'proof'. Also engage at the end of a task when you're about to claim something is done and the user will want the receipts. Do NOT engage for: proving an abstract or analytical property (a complexity bound like O(n log n), a mathematical or security proof) rather than that running code meets its requirements; a private 'does this work / is it green' self-check with no shareable artifact (that's the verify skill); writing a PR body (that's formlabs-pr-write); reviewing someone else's code or PR; or authoring a unit-test suite as the deliverable — this skill RUNS tests to produce evidence, it doesn't write the test suite."
---

# Prove It

Someone did a piece of work against a goal. This skill produces the **evidence** that it actually works — not an assertion that it does. It turns the goal's requirements into real tests, runs them, captures what came back, and renders a consistent proof artifact so a reader instantly sees what was proven and what wasn't.

## The one rule above all: no positive claim without evidence you captured

The entire value of this skill is the evidence. A proof that renders green boxes without running a real test is worse than useless — it launders a guess into something that looks verified. So the load-bearing step is always **run the real thing and capture its output.** The artifact is the presentation layer on top of that; it never substitutes for it.

Concretely, every ✓ in the proof must trace to something you actually observed this session — a command you ran and its exit code/output, a screenshot you captured, a file you read, or a result the user explicitly reported. If you didn't run it, it is not a pass. It is `not run`, and the artifact says so.

This mirrors the test-evidence ledger in the `formlabs-pr-write` skill. Hold to the same discipline.

## Provenance ledger — tag every result before it reaches the artifact

Keep an internal ledger (not shown to the user) as you gather evidence. Every requirement's result gets exactly one provenance tag:

| Tag | Means | Allowed in the proof as… |
|---|---|---|
| `ran-command` | You ran it this session and saw the result | a ✓ (or ✗ if it failed) — cite the command/output |
| `user-reported` | The user said they observed it — quote them | a ✓, labeled as user-reported in Scope |
| `not-run` | Nobody ran it this session | **never a ✓.** Shows as ✗ / "not run" and moves to Scope → user-must-verify |

`not-run` as a positive claim is the single failure mode this skill exists to prevent. A requirement you couldn't test is not a gap to paper over — it's the most important thing to surface honestly.

## Workflow

### 1. Pin the goal and its requirements

You need a concrete goal and a checklist of requirements to prove against. Get them, in this order of preference:

- **From the artifacts the user handed you** — a ticket, PR description, spec, or acceptance criteria. Read these first; they carry the real contract.
- **From the conversation** — what the user asked the work to do, including corrections they made along the way.
- **If neither is explicit,** state the requirements you're going to prove against and confirm them with the user before building. A proof against the wrong requirements is wasted work. Don't silently invent them.

Turn the goal into a numbered requirement checklist. Each item must be something you can point a test at. "It works" is not a requirement; "returns 200 with the build SHA" is.

### 2. Derive one concrete test per requirement

For each requirement, name the specific, executable thing that would prove it — the actual command, test file, or user action, not a description. Map requirement → test explicitly; this mapping becomes the core table of the artifact.

**Use the project's own test tooling. Do not hand-roll a harness.** This is the biggest time-sink to avoid. Before writing any throwaway script:

- Look for a **project verification skill** first (e.g. a repo's `local-e2e-verification`, a `verify` or `run` skill). If one exists, it is the golden path for *how to run* — defer to it rather than re-describing bring-up. This skill owns the "what to prove and how to present it"; the project skill owns the "how to run it."
- Otherwise reach for the repo's own runner — its Playwright/jest/pytest/etc. with real mocking and screenshots — the way its existing tests do. Mock only at the edges (the network boundary), and say what you mocked.
- A bespoke browser-CLI or a scratch script with no `node_modules` is almost always the wrong first move. Prove the real client path runs, not a reimplementation of it.

### 3. Run them for real and capture evidence

Run each test. As you go, capture the evidence in a form you can embed:

- **Command/test output** → copy the real stdout, exit status, pass/fail counts. Verbatim.
- **Screenshots** → save PNGs (the project test tooling's screenshot capture is ideal). These get base64-embedded into the artifact.
- **File reads** → the `file:line` and the actual content, when the proof rests on what the code says.

Record a baseline where it matters (a bug fix: broken on `main`, gone on the branch). Tag each result in the ledger as you capture it.

### 4. Classify scope honestly

Sort every requirement into three buckets — this becomes the Scope section:

- **Proven here** — you ran it and captured the evidence (`ran-command`, or `user-reported` with a quote).
- **Inferred** — you believe it holds but didn't directly exercise it (e.g. a mocked boundary means the real backend path wasn't run). Say what *would* confirm it.
- **User must verify** — only checkable on real infra/hardware you don't have (prod TLS, a physical device, a real payment). `not-run` results land here.

A proof that overclaims is worse than none. The Scope section is where you stay honest.

### 5. Set the verdict

Check the rules in order — the first that matches wins:

- **FAIL** — a requirement's test came back failing. The work is broken; a failing test is FAIL even if the other requirements pass. Report it; don't soften it to PARTIAL.
- **PARTIAL** — nothing you ran failed, but at least one requirement is untested, inferred, or left to the user. State the count ("5/6 verified").
- **PASS** — every requirement is Proven here, nothing failed, no `not-run` positives.

The distinction that trips people up: a requirement whose test **failed** → FAIL (broken); a requirement that was **never tested** → PARTIAL (unknown). Don't conflate the two.

### 6. Render the manifest to HTML

Write a manifest JSON and run the bundled builder — it owns the template so every proof looks identical:

```bash
python3 scripts/build_proof.py --manifest proof.json --output proof.html
```

**Do not hand-write the HTML.** The consistency is the point, and the script guarantees it. Your job is to get the *evidence* into the manifest, written tight (see "Write it tight" below); the script makes it look right. See `references/manifest-schema.md` for the full manifest shape (a worked example is in `references/example-manifest.json`).

### 7. Publish it and hand back the link

**The deliverable is a published Artifact URL, not a file on disk.** The whole point is a link the user can paste into a PR body, a Slack message, or a ticket to show their peers the work was confirmed. A local `proof.html` no one can open is not done.

Pass `proof.html` to the **Artifact tool** (set `title`, `favicon`, a one-line `description`). It returns a `https://claude.ai/code/artifact/…` URL — that URL is what you report back, front and center. The HTML is already Artifact-ready: it carries a `<title>` and `<style>` but no `<!doctype>/<html>/<head>/<body>` wrappers (the tool supplies those), and it is fully self-contained — screenshots are embedded as `data:` URIs, so the CSP that blocks external assets is satisfied.

If you genuinely have no Artifact tool available (e.g. a headless run), say so plainly and hand back the `proof.html` path as a fallback — don't silently pretend a local file is the shareable proof.

## The artifact's fixed shape

Every proof has the same sections, in this order — a reader who has seen one knows how to read all of them:

1. **Header** — eyebrow (ticket/context) + title + one-sentence "what this proves".
2. **Verdict banner** — PASS / PARTIAL / FAIL, the tool/counts, and a one-line human summary.
3. **How it was verified** — the method as short numbered steps: what tools, what was real vs mocked.
4. **Evidence** — screenshots and/or captured command output in a mono panel. The raw receipts.
5. **Requirement-by-requirement table** — requirement → how it was tested → captured result → ✓/✗.
6. **Scope** — proven vs inferred vs left-for-the-user.
7. **Footer** — repo/branch, the commands/test files, the date (pass the date in; don't read a clock).

The builder renders exactly these from the manifest; you supply the content, not the layout.

## Write it tight

A proof is scanned, not read. The **evidence** (captured output) and the **requirement table** carry the substance; the prose around them is connective tissue and must stay minimal. Overwritten prose buries the one line that matters and makes the reader work — the opposite of a proof's job. Aim to cut every manifest string to roughly half of your first draft.

Concretely:

- **Lede (`what_this_proves`):** one sentence. What was proven, against what, how. Not a paragraph.
- **Verdict `summary`:** one line with the count. `"2/3 verified — parse_items truncates names."` Not three clauses.
- **Method steps:** a clause each, not a sentence with sub-clauses. `"Ran <code>python3 -m unittest</code>, captured stdout + exit code."` — not "Ran the project's own suite unmodified, stdlib only, no test files edited, and captured stdout and the exit code verbatim."
- **Requirement cells:** the test name and the result value. Let the code speak; skip narration.
- **Scope items:** the fact, then stop. A fix is `receipt.py:27 <code>[:-1]</code> truncates names; drop the slice.` — not a paragraph re-explaining the bug.

Plain words, no filler. Prefer "use" over "leverage", "reads" over "consumes". Cut "essentially", "fundamentally", "robust", "seamless", "it should be noted that". No hedges ("appears to", "seems to"). Active voice, short sentences, one idea each. The tone is a terse lab notebook, not an essay.

## Anti-patterns

- **Theatre** — rendering a proof with green ticks for tests you never ran. The cardinal sin; the whole skill exists to prevent it.
- **`not-run` shown as a pass.** A requirement you couldn't test is a Scope item, never a ✓.
- **Hand-rolling a test harness** when the project has Playwright/jest/pytest and a verification skill. Defer to the project's tooling.
- **Hand-writing the artifact HTML** instead of using the builder — you lose the consistency that is the point.
- **Stopping at a local `proof.html`** — the deliverable is the published Artifact URL, not a file on disk. Publish it and hand back the link.
- **Word-salad prose** — verbose ledes, method steps with sub-clauses, scope paragraphs. A proof is scanned; keep prose terse (see "Write it tight").
- **Overclaiming in Scope** — calling something proven when a mock stood in for the real path. Say what the mock replaced.
- **Reading the date from the clock** — pass it in from context so the artifact is reproducible.
- **Proving against invented requirements** — when the goal is unclear, confirm the checklist first.

## Out of scope

- **Writing the PR body** — that's `formlabs-pr-write`. This skill produces the evidence the PR's test plan rests on; it doesn't write the PR.
- **Reviewing someone else's code or PR** — that's a code-review tool.
- **Authoring the test suite** as the deliverable — this skill runs existing or quickly-derived tests to produce evidence; it isn't a TDD/test-writing skill.
- **Deciding whether the work is good** — it proves the work meets its stated requirements, not that the requirements were the right ones.
