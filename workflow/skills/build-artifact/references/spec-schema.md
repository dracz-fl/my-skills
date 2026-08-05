# Spec schema

A spec is TOML. Prose fields accept a small markdown subset: `**bold**`,
`` `code` ``, `[text](https://url)`. Everything else is escaped, so you can
write `<`, `&` and quotes literally. Use TOML `"""` strings for anything
longer than a line.

## Page level

| Key | Required | Meaning |
|---|---|---|
| `title` | yes | Page title and `<title>`. Also keys the autosave store. |
| `genre` | no | Defaults to `questionnaire`. |
| `eyebrow` | no | Small uppercase kicker above the title. |
| `lede` | no | Opening paragraph under the title. |

## Genre: `questionnaire`

Extra page-level keys:

| Key | Meaning |
|---|---|
| `return_to` | Who receives the answers. Woven into the instructions and the button's confirmation. |
| `how` | Overrides the default instruction callout. The default already explains pre-filling, the `Current` badge, and the copy button — override only if your flow differs. |
| `hint` | Overrides the sticky footer text. |
| `respondent` | Set `false` to drop the "Your name" field. Defaults to on. |

### Sections

Each `[[section]]` is a numbered block.

| Key | Meaning |
|---|---|
| `heading` | Section title. Also the `##` heading in the copied output. |
| `blurb` | Optional paragraph under the heading. |
| `marker` | Character in the section badge. Defaults to `?`. |

### Questions

Each `[[section.question]]`:

| Key | Meaning |
|---|---|
| `ask` | The question, as the respondent reads it. Required. |
| `label` | Short handle used as the `###` heading in the copied output. Defaults to `ask`. Keep it short — this is what you will be reading in the paste-back. |
| `ref` | Ticket or decision id (e.g. `FN-1597`). Rendered as a badge and keyed into the copied heading. Set it whenever the question maps to a tracked item — a ticket-keyed paste-back is greppable weeks later. |
| `why` | Disclosure body: why the answer matters and what changes. Blank lines become paragraphs. |
| `choose` | Radio options. Prefix exactly one with `*` to mark it current — it renders pre-selected with a `Current` badge, and any *other* pick is flagged `[CHANGED]` in the output. |
| `check` | Checkbox options. Prefix any with `*` to start them checked. |
| `note` | Label for the free-text box. Omit for a box labelled `Notes`; set `false` to remove the box. |
| `note_placeholder` | Placeholder inside the box. Use it to show the *shape* of a useful answer. |

A question may combine `choose`, `check` and a note, or use only the note for
a pure free-text ask.

### Recipe: a decision that can be vetoed

When you are not asking an open question but confirming a call you already made,
give it an explicit reject path. A page that only offers "answer" gets silence
for disagreement; the highest-fidelity page in the corpus paired every decision
with a one-click veto.

```toml
[[section.question]]
ref = "FN-1597"
label = "D1 data shape"
ask = "We treat a finishing option as just another finish. Does that stand?"
why = "It reuses the existing finish table rather than adding a parallel one."
choose = [
  "*It stands",
  "VETO — this needs to change before it ships",
]
note = "If you're vetoing, what breaks?"
```

### Worked example

```toml
genre = "questionnaire"
title = "Ship-Estimate Ops Sanity Pass"
eyebrow = "Form Now · Ship-Estimate"
return_to = "Daniel"
lede = "What we had to decide on our own — **the spec covers everything else.**"

[[section]]
heading = "Where the spec left gaps"
blurb = "Six calls the spec doesn't spell out."

[[section.question]]
label = "Where does the Cure step belong?"
ask = "The Cure step isn't in the spec's tables — Finishing or Post-Processing?"
why = """
The SLA table lists Printing → Wash → Post-Processing → Finishing, with no Cure
row. We fold it into **Finishing** today.

This decides how much time is left when a part is *at* cure.
"""
choose = [
  "*Group it with Finishing",
  "Group it with Post-Processing",
  "It's really its own step (I'll note roughly how long)",
]
note = "Notes"
```

## Genre: `walkthrough`

The default shape for explaining a change, a PR, or how something works — half
the previous corpus was this genre.

Extra page-level keys:

| Key | Meaning |
|---|---|
| `chips` | Array of short meta labels (date, PR number, repo) rendered as pills. |
| `toc` | Set `false` to suppress the contents list. It appears automatically once there are more than two sections. |
| `gap` | A `[gap]` table with `heading` and `text`. Renders last, as a warning callout. |
| `footer` | Small print at the very bottom. |

Title it with a **claim, not a topic** — "The hold now ends on a date the
customer was told", not "FN-1557 changes". Every section is `[[section]]` with
`heading` and optional `body` prose, followed by ordered `[[section.block]]`
entries.

### Blocks

Each `[[section.block]]` has a `type`:

| `type` | Keys | Notes |
|---|---|---|
| `table` | `columns`, `rows` | `rows` is an array of arrays. Always scrolls inside its own box. |
| `code` | `text` | Rendered verbatim, no highlighting. |
| `diff` | `text` | Lines starting `+`, `-`, `@@` are coloured. Nothing else to do. |
| `steps` | `items` | Numbered vertical sequence with a connecting rule. |
| `callout` | `text`, `tone` | `tone` is `ok`, `warn`, `bad`, or omitted for accent. |
| `mermaid` | `text` | Emitted as `<pre class="mermaid">`; artifacts render it natively. |

Prefer a `table`, `steps` or `diff` block over another paragraph. A wall of
prose is the one failure mode this user has actually complained about.

### The `[gap]` section

Almost every walkthrough in the corpus ended by naming what it did *not*
establish, so the genre makes it a field. Use it for the unverified assumption,
the migration that hasn't run, the case you didn't test. Omit it only when
there is genuinely nothing outstanding — which is rare and worth doubting.

## Copied output format

The copy button produces markdown shaped for reading back:

```
# <title> — Answers
From: <respondent>

## <section heading>

### <question label>
Answer: <selected option>   [CHANGED]
Selected: <checked, items>
Note: <free text>
```

Absent lines mean absent input: no `Note:` line means the box was empty, and no
`[CHANGED]` means the respondent left your assumption standing. Treat an
unchanged answer as confirmation, not as a non-response.
