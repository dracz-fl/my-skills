#!/usr/bin/env python3
"""Build a self-contained artifact page from a TOML spec.

    python3 build.py spec.toml -o out.html

The spec carries content only. Theme, components, and per-genre behaviour come
from this kit, so a page costs roughly as many lines as it has ideas.
"""

import argparse
import html
import re
import sys
import tomllib
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# ── inline markup ────────────────────────────────────────────────────────────

_INLINE = [
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
    (re.compile(r"\*\*([^*]+)\*\*"), r"<strong>\1</strong>"),
    # Runs after bold, so any asterisk still standing is emphasis.
    (re.compile(r"\*([^*\n]+)\*"), r"<em>\1</em>"),
    (re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)"), r'<a href="\2">\1</a>'),
]


def inline(text):
    """Escape, then apply the small markdown subset the specs are written in."""
    out = html.escape(str(text), quote=False)
    for pattern, repl in _INLINE:
        out = pattern.sub(repl, out)
    return out


def paras(text):
    """Blank-line-separated prose to <p> blocks."""
    chunks = [c.strip() for c in re.split(r"\n\s*\n", str(text).strip()) if c.strip()]
    return "\n".join(f"<p>{inline(c)}</p>" for c in chunks)


def marked(item):
    """Split a leading '*' marker off a choice. '*Foo' -> (True, 'Foo')."""
    s = str(item)
    if s.startswith("*"):
        return True, s[1:].strip()
    return False, s.strip()


def asset(name):
    path = ASSETS / name
    if not path.exists():
        sys.exit(f"missing kit asset {path} — is the skill bundle complete?")
    return path.read_text()


# ── questionnaire genre ──────────────────────────────────────────────────────

QUESTIONNAIRE_CSS = """
/* respondent field */
.who { margin-top: 20px; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.who label { font-family: var(--mono); font-size: 12px; letter-spacing: .1em;
  text-transform: uppercase; color: var(--faint); }
.who input { font: inherit; font-size: 15px; padding: 8px 12px; border-radius: 8px;
  border: 1px solid var(--line-strong); background: var(--surface); color: var(--ink);
  min-width: 220px; flex: 1 1 220px; }

.q { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius);
  padding: 20px 20px 18px; margin-bottom: 16px; box-shadow: var(--shadow); }
.q-label { display: flex; gap: 10px; align-items: baseline; }
.q-idx { font-family: var(--mono); font-size: 13px; color: var(--faint); flex: none; }
.q-label h3 { font-size: 16.5px; font-weight: 620; margin: 0; line-height: 1.4;
  letter-spacing: -.005em; }
.q-ref { flex: none; align-self: flex-start; }

.opts { margin-top: 14px; display: flex; flex-direction: column; gap: 8px; }
.opt { display: flex; gap: 11px; align-items: flex-start; padding: 11px 13px;
  border: 1px solid var(--line-strong); border-radius: 8px; cursor: pointer;
  transition: border-color .12s, background .12s; background: var(--surface); }
.opt:hover { border-color: var(--accent); }
.opt input { margin: 3px 0 0; accent-color: var(--accent); width: 16px; height: 16px; flex: none; }
.opt .opt-text { font-size: 14.5px; }
.opt.is-current { background: var(--warn-soft); border-color: var(--warn-line); }
.opt:has(input:checked) { border-color: var(--accent); box-shadow: inset 0 0 0 1px var(--accent); }

.checks { margin-top: 14px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
@media (max-width: 560px) { .checks { grid-template-columns: 1fr; } }
.chk { display: flex; gap: 10px; align-items: center; padding: 10px 12px;
  border: 1px solid var(--line-strong); border-radius: 8px; cursor: pointer; font-size: 14px; }
.chk:hover { border-color: var(--accent); }
.chk input { accent-color: var(--accent); width: 16px; height: 16px; }
.chk:has(input:checked) { border-color: var(--accent); background: var(--accent-soft); }

.comment-row { margin-top: 13px; }
.comment-row label { font-family: var(--mono); font-size: 11px; letter-spacing: .08em;
  text-transform: uppercase; color: var(--faint); display: block; margin-bottom: 6px; }
textarea.comment { width: 100%; font: inherit; font-size: 14.5px; padding: 10px 12px;
  resize: vertical; min-height: 44px; border: 1px solid var(--line-strong);
  border-radius: 8px; background: var(--surface-2); color: var(--ink); }
textarea.comment:focus, .who input:focus { outline: 2px solid var(--accent); outline-offset: 1px; }
textarea.comment::placeholder { color: var(--faint); }

.footer-bar { position: fixed; left: 0; right: 0; bottom: 0; z-index: 20;
  background: color-mix(in srgb, var(--surface) 88%, transparent);
  backdrop-filter: blur(10px); border-top: 1px solid var(--line-strong); }
.footer-inner { max-width: 820px; margin: 0 auto; padding: 12px 20px; display: flex;
  align-items: center; gap: 14px; flex-wrap: wrap; }
.footer-inner .hint { font-size: 13px; color: var(--muted); flex: 1 1 200px; }
.footer-inner .saved { font-size: 12px; color: var(--faint); font-family: var(--mono); }
button.copy { font: inherit; font-weight: 600; font-size: 15px; cursor: pointer;
  background: var(--accent); color: #fff; border: none; border-radius: 9px; padding: 11px 20px;
  display: inline-flex; align-items: center; gap: 8px; transition: transform .1s, background .15s; }
button.copy:hover { background: var(--accent-ink); }
button.copy:active { transform: translateY(1px); }
button.copy.done { background: var(--ok); }

.preview { margin-top: 40px; }
.preview summary { font-family: var(--mono); font-size: 11.5px; letter-spacing: .08em;
  text-transform: uppercase; color: var(--faint); cursor: pointer; }
.preview textarea { width: 100%; margin-top: 12px; min-height: 220px; font-family: var(--mono);
  font-size: 12.5px; padding: 14px; border: 1px solid var(--line); border-radius: 10px;
  background: var(--surface-2); color: var(--ink); resize: vertical; }
"""

QUESTIONNAIRE_JS = """
(function () {
  var KEY = "artifact-kit:" + document.title;

  function buildSummary() {
    var lines = ["# " + document.title + " — Answers"];
    var who = document.getElementById("respondent");
    if (who) lines.push("From: " + (who.value.trim() || "(name not given)"));
    lines.push("");

    document.querySelectorAll("section.part").forEach(function (sec) {
      lines.push("## " + sec.querySelector(".part-head h2").textContent.trim());
      sec.querySelectorAll(".q").forEach(function (q) {
        lines.push("");
        // Number and ticket ref stay in the heading: the paste-back is often read
        // cold, in a different session, after passing through a third party. A
        // ticket-keyed heading is what made past paste-backs greppable.
        var head = "Q" + q.querySelector(".q-idx").textContent.trim();
        if (q.dataset.ref) head += " · " + q.dataset.ref;
        lines.push("### " + head + " · " +
                   (q.dataset.label || q.querySelector("h3").textContent.trim()));

        var radios = q.querySelectorAll('input[type="radio"]');
        if (radios.length) {
          var picked = q.querySelector('input[type="radio"]:checked');
          var val = picked ? picked.value : "(none selected)";
          var changed = picked && picked.dataset.current !== "1";
          lines.push("Answer: " + val + (changed ? "   [CHANGED]" : ""));
        }

        var boxes = q.querySelectorAll('input[type="checkbox"]');
        if (boxes.length) {
          var on = [];
          boxes.forEach(function (b) { if (b.checked) on.push(b.value); });
          lines.push("Selected: " + (on.length ? on.join(", ") : "(none checked)"));
        }

        var c = q.querySelector("textarea.comment");
        if (c && c.value.trim()) lines.push("Note: " + c.value.trim());
      });
      lines.push("");
    });
    return lines.join("\\n").replace(/\\n{3,}/g, "\\n\\n").trim() + "\\n";
  }

  // Answers survive a refresh; a half-filled questionnaire is easy to lose.
  function fields() {
    return Array.prototype.slice.call(
      document.querySelectorAll("input[type=radio], input[type=checkbox], textarea.comment, #respondent"));
  }
  function save() {
    var state = {};
    fields().forEach(function (el, i) {
      state[i] = el.type === "radio" || el.type === "checkbox" ? el.checked : el.value;
    });
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
    var s = document.getElementById("savedNote");
    if (s) s.textContent = "saved";
  }
  function restore() {
    var raw;
    try { raw = localStorage.getItem(KEY); } catch (e) { return; }
    if (!raw) return;
    var state;
    try { state = JSON.parse(raw); } catch (e) { return; }
    fields().forEach(function (el, i) {
      if (!(i in state)) return;
      if (el.type === "radio" || el.type === "checkbox") el.checked = !!state[i];
      else el.value = state[i];
    });
  }

  var previewBox = document.getElementById("previewBox");
  function refresh() {
    if (previewBox) previewBox.value = buildSummary();
  }

  restore();
  refresh();
  document.addEventListener("input", function () { save(); refresh(); });
  document.addEventListener("change", function () { save(); refresh(); });

  var btn = document.getElementById("copyBtn");
  var lbl = document.getElementById("copyLabel");
  if (btn) btn.addEventListener("click", function () {
    var text = buildSummary();
    if (previewBox) previewBox.value = text;
    function ok() {
      btn.classList.add("done");
      lbl.textContent = btn.dataset.doneLabel || "Copied ✓";
      setTimeout(function () { btn.classList.remove("done"); lbl.textContent = "Copy answers"; }, 3200);
    }
    function fallback() {
      if (!previewBox) return;
      previewBox.closest("details").open = true;
      previewBox.focus(); previewBox.select(); document.execCommand("copy"); ok();
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(ok, fallback);
    } else { fallback(); }
  });
})();
"""


def render_question(q, idx):
    label = q.get("label") or q.get("ask", "")
    ref = q.get("ref")
    ref_attr = f' data-ref="{html.escape(str(ref), quote=True)}"' if ref else ""
    parts = [f'<div class="q" data-label="{html.escape(str(label), quote=True)}"{ref_attr}>']
    parts.append(
        '<div class="q-label">'
        f'<span class="q-idx">{idx}</span>'
        f'<h3>{inline(q["ask"])}</h3>'
        + (f'<span class="badge accent q-ref">{inline(ref)}</span>' if ref else "")
        + "</div>"
    )

    if q.get("why"):
        parts.append(
            '<details class="disclose"><summary>Why we ask</summary>'
            f'<div class="disclose-body">{paras(q["why"])}</div></details>'
        )

    name = f"q{idx}"
    if q.get("choose"):
        parts.append('<div class="opts">')
        for opt in q["choose"]:
            is_current, text = marked(opt)
            value = f"{text} (current)" if is_current else text
            parts.append(
                f'<label class="opt{" is-current" if is_current else ""}">'
                f'<input type="radio" name="{name}" value="{html.escape(value, quote=True)}"'
                f'{" checked data-current=\"1\"" if is_current else ""}>'
                f'<span class="opt-text">{inline(text)}'
                f'{" <span class=\"badge current\">Current</span>" if is_current else ""}'
                "</span></label>"
            )
        parts.append("</div>")

    if q.get("check"):
        parts.append('<div class="checks">')
        for item in q["check"]:
            is_on, text = marked(item)
            parts.append(
                '<label class="chk">'
                f'<input type="checkbox" name="{name}c" value="{html.escape(text, quote=True)}"'
                f'{" checked" if is_on else ""}>{inline(text)}</label>'
            )
        parts.append("</div>")

    note = q.get("note")
    if note or note is None:
        note_label = note if isinstance(note, str) else "Notes"
        placeholder = html.escape(str(q.get("note_placeholder", "")), quote=True)
        parts.append(
            '<div class="comment-row">'
            f"<label>{inline(note_label)}</label>"
            f'<textarea class="comment" placeholder="{placeholder}"></textarea></div>'
        )

    parts.append("</div>")
    return "\n".join(parts)


def render_questionnaire(spec):
    body = ['<div class="wrap pad-bottom-bar">', '<header class="masthead">']
    if spec.get("eyebrow"):
        body.append(f'<p class="eyebrow">{inline(spec["eyebrow"])}</p>')
    body.append(f'<h1>{inline(spec["title"])}</h1>')
    if spec.get("lede"):
        body.append(f'<p class="lede">{inline(spec["lede"])}</p>')

    return_to = spec.get("return_to")
    how = spec.get("how") or (
        "Each answer is **pre-filled with what we assume today** (badged **Current**). "
        "Change only what's wrong — leaving an answer as-is tells us \"that's right.\" "
        "Every question has a free-text box. When you're done, hit **Copy answers** "
        f"at the bottom and send the copied text back{f' to {return_to}' if return_to else ''}."
    )
    body.append(f'<div class="callout">{paras(how)}</div>')

    if spec.get("respondent", True):
        body.append(
            '<div class="who"><label for="respondent">Your name</label>'
            '<input id="respondent" type="text" '
            'placeholder="so we know who to follow up with" autocomplete="off"></div>'
        )
    body.append("</header>")

    idx = 0
    for sec in spec.get("section", []):
        body.append('<section class="part">')
        marker = inline(sec.get("marker", "?"))
        body.append(
            '<div class="part-head">'
            f'<span class="part-num">{marker}</span>'
            f'<h2>{inline(sec["heading"])}</h2></div>'
        )
        if sec.get("blurb"):
            body.append(f'<p class="part-sub">{inline(sec["blurb"])}</p>')
        for q in sec.get("question", []):
            idx += 1
            body.append(render_question(q, idx))
        body.append("</section>")

    body.append(
        '<details class="preview"><summary>Preview the text that gets copied</summary>'
        '<textarea id="previewBox" readonly></textarea></details>'
    )
    body.append("</div>")

    hint = spec.get(
        "hint",
        "Change anything that's off, then copy and send the text back"
        + (f" to {return_to}." if return_to else ".")
        + " Unchanged = \"that's right.\"",
    )
    done = f"Copied — send it to {return_to} ✓" if return_to else "Copied ✓"
    body.append(
        '<div class="footer-bar"><div class="footer-inner">'
        f'<span class="hint">{inline(hint)}</span>'
        '<span class="saved" id="savedNote"></span>'
        f'<button class="copy" id="copyBtn" type="button" '
        f'data-done-label="{html.escape(done, quote=True)}">'
        '<span id="copyLabel">Copy answers</span></button>'
        "</div></div>"
    )
    return "\n".join(body), QUESTIONNAIRE_CSS, QUESTIONNAIRE_JS


# ── walkthrough genre ────────────────────────────────────────────────────────

WALKTHROUGH_CSS = """
nav.toc { margin-top: 30px; background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--radius); padding: 16px 20px; }
nav.toc h2 { font-family: var(--mono); font-size: 11.5px; letter-spacing: .1em;
  text-transform: uppercase; color: var(--faint); margin: 0 0 10px; font-weight: 600; }
nav.toc ol { margin: 0; padding-left: 22px; }
nav.toc li { margin: 5px 0; font-size: 14.5px; }
nav.toc a { text-decoration: none; }
nav.toc a:hover { text-decoration: underline; }

section.part p { max-width: 68ch; }
section.part > h2 { font-size: 21px; letter-spacing: -.01em; margin: 0 0 12px; font-weight: 660; }

/* Diff — the corpus had no shared component for this, so every PR page
   hand-rolled inline colour spans. */
.diff { background: var(--code-bg); border: 1px solid var(--line); border-radius: 8px;
  padding: 12px 0; margin: 16px 0; overflow-x: auto; font-family: var(--mono);
  font-size: 13px; line-height: 1.55; }
.diff div { padding: 0 16px; white-space: pre; }
.diff .add { background: var(--ok-soft); color: var(--ink); }
.diff .del { background: var(--bad-soft); color: var(--ink); }
.diff .hunk { color: var(--faint); }

/* Canonical vertical step sequence, replacing .step / .seq / .flow .node. */
ol.steps { list-style: none; margin: 18px 0; padding: 0; }
ol.steps li { position: relative; padding: 0 0 18px 34px; }
ol.steps li::before {
  content: counter(step); counter-increment: step;
  position: absolute; left: 0; top: 0;
  font-family: var(--mono); font-size: 12px; font-weight: 600;
  color: var(--accent); background: var(--accent-soft);
  border: 1px solid var(--accent); border-radius: 50%;
  width: 22px; height: 22px; display: flex; align-items: center; justify-content: center;
}
ol.steps { counter-reset: step; }
ol.steps li:not(:last-child)::after {
  content: ""; position: absolute; left: 11px; top: 24px; bottom: 2px;
  width: 1px; background: var(--line-strong);
}
ol.steps li p { margin: 0; }
"""


def render_block(b):
    kind = b.get("type", "callout")

    if kind == "table":
        head = "".join(f"<th>{inline(c)}</th>" for c in b.get("columns", []))
        rows = "".join(
            "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>"
            for row in b.get("rows", [])
        )
        return (
            '<div class="table-scroll"><table>'
            + (f"<thead><tr>{head}</tr></thead>" if head else "")
            + f"<tbody>{rows}</tbody></table></div>"
        )

    if kind == "code":
        return f"<pre><code>{html.escape(b['text'].strip(), quote=False)}</code></pre>"

    if kind == "diff":
        lines = []
        for raw in b["text"].strip("\n").split("\n"):
            cls = ""
            if raw.startswith("+"):
                cls = " class=\"add\""
            elif raw.startswith("-"):
                cls = " class=\"del\""
            elif raw.startswith("@@"):
                cls = " class=\"hunk\""
            lines.append(f"<div{cls}>{html.escape(raw, quote=False) or '&nbsp;'}</div>")
        return '<div class="diff">' + "".join(lines) + "</div>"

    if kind == "steps":
        items = "".join(f"<li><p>{inline(i)}</p></li>" for i in b.get("items", []))
        return f'<ol class="steps">{items}</ol>'

    if kind == "mermaid":
        # Artifacts render mermaid natively; no library to load.
        return f'<pre class="mermaid">{html.escape(b["text"].strip(), quote=False)}</pre>'

    if kind == "callout":
        tone = b.get("tone", "")
        cls = f"callout {tone}".strip()
        return f'<div class="{cls}">{paras(b["text"])}</div>'

    sys.exit(f"unknown block type {kind!r}")


def render_walkthrough(spec):
    sections = spec.get("section", [])
    body = ['<div class="wrap">', '<header class="masthead">']
    if spec.get("eyebrow"):
        body.append(f'<p class="eyebrow">{inline(spec["eyebrow"])}</p>')
    body.append(f'<h1>{inline(spec["title"])}</h1>')
    if spec.get("lede"):
        body.append(f'<p class="lede">{inline(spec["lede"])}</p>')
    if spec.get("chips"):
        chips = "".join(f'<span class="chip">{inline(c)}</span>' for c in spec["chips"])
        body.append(f'<div class="chips">{chips}</div>')
    body.append("</header>")

    if spec.get("toc", True) and len(sections) > 2:
        items = "".join(
            f'<li><a href="#s{i}">{inline(s["heading"])}</a></li>'
            for i, s in enumerate(sections, 1)
        )
        body.append(f'<nav class="toc"><h2>Contents</h2><ol>{items}</ol></nav>')

    for i, sec in enumerate(sections, 1):
        body.append(f'<section class="part" id="s{i}">')
        body.append(f'<h2>{inline(sec["heading"])}</h2>')
        if sec.get("body"):
            body.append(paras(sec["body"]))
        for b in sec.get("block", []):
            body.append(render_block(b))
        body.append("</section>")

    # Nearly every walkthrough in the corpus ended by naming what it did not
    # establish; the genre makes that a first-class field rather than a habit.
    gap = spec.get("gap")
    if gap:
        body.append('<section class="part">')
        body.append(f'<h2>{inline(gap.get("heading", "What this does not cover"))}</h2>')
        body.append(f'<div class="callout warn">{paras(gap["text"])}</div>')
        body.append("</section>")

    if spec.get("footer"):
        body.append(f'<footer class="foot">{paras(spec["footer"])}</footer>')
    body.append("</div>")
    return "\n".join(body), WALKTHROUGH_CSS, ""


GENRES = {
    "questionnaire": render_questionnaire,
    "walkthrough": render_walkthrough,
}


# ── assembly ─────────────────────────────────────────────────────────────────

def build(spec):
    genre = spec.get("genre", "questionnaire")
    if genre not in GENRES:
        sys.exit(f"unknown genre {genre!r}; known: {', '.join(sorted(GENRES))}")
    body, genre_css, genre_js = GENRES[genre](spec)
    out = [
        # Not a document skeleton — just guarantees the em dashes survive when the
        # page is previewed over a server that doesn't send a charset.
        '<meta charset="utf-8">',
        f"<title>{inline(spec['title'])}</title>",
        "<style>",
        asset("theme.css"),
        genre_css,
        "</style>",
        body,
    ]
    if genre_js.strip():
        out += ["<script>", genre_js, "</script>"]
    return "\n".join(out) + "\n"


CHECKS = [
    (re.compile(r'<(?:script|link)[^>]+(?:src|href)\s*=\s*["\']https?://', re.I),
     "external script/stylesheet — the artifact CSP blocks every other host"),
    (re.compile(r'<img[^>]+src\s*=\s*["\']https?://', re.I),
     "remote image — inline it as a data: URI instead"),
    (re.compile(r"\b(?:fetch|XMLHttpRequest|WebSocket)\s*\(", re.I),
     "network call — blocked by the artifact CSP"),
    (re.compile(r"<!doctype|<html|<head\b|<body\b", re.I),
     "document skeleton tag — the publisher wraps the file, so these must be absent"),
    (re.compile(r"\balert\s*\(|\bconfirm\s*\(|\bprompt\s*\(", re.I),
     "modal dialog — blocks the page and the automation harness"),
]


THEME_BLOCKS = [
    ("light default", re.compile(r":root\s*\{(.*?)\}", re.S)),
    ("prefers-color-scheme: dark", re.compile(r"prefers-color-scheme:\s*dark.*?:root\s*\{(.*?)\}", re.S)),
    ('data-theme="light"', re.compile(r':root\[data-theme="light"\]\s*\{(.*?)\}', re.S)),
    ('data-theme="dark"', re.compile(r':root\[data-theme="dark"\]\s*\{(.*?)\}', re.S)),
]


def check_tokens(css):
    """Every var() must resolve under all four theme states.

    A token defined only in the light block renders as nothing in dark mode —
    the most common defect in the hand-built corpus, and invisible until someone
    views the page with the other theme.
    """
    used = set(re.findall(r"var\((--[a-z0-9-]+)", css))
    problems = []
    for name, pattern in THEME_BLOCKS:
        m = pattern.search(css)
        if not m:
            problems.append(f"theme block missing: {name}")
            continue
        defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", m.group(1)))
        # The dark blocks legitimately re-declare only what changes; anything
        # they omit falls through to the light default, which is fine. What is
        # never fine is a var() no block defines at all.
        if name == "light default":
            for token in sorted(used - defined):
                problems.append(f"var({token}) is used but never defined")
    return problems


def check(path, text):
    problems = [why for pattern, why in CHECKS if pattern.search(text)]
    css = "\n".join(re.findall(r"<style>(.*?)</style>", text, re.S))
    problems += check_tokens(css)
    size = len(text.encode())
    if size > 16 * 1024 * 1024:
        problems.append(f"page is {size / 1e6:.1f}MB — the limit is 16MB")
    for why in problems:
        print(f"{path}: {why}", file=sys.stderr)
    return not problems


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("spec", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    args = ap.parse_args()

    spec = tomllib.loads(args.spec.read_text())
    if "title" not in spec:
        sys.exit("spec needs a title")

    page = build(spec)
    if not check(args.spec, page):
        sys.exit(1)

    args.out.write_text(page)
    lines = page.count("\n")
    spec_lines = args.spec.read_text().count("\n")
    print(f"{args.out}  {lines} lines from a {spec_lines}-line spec")


if __name__ == "__main__":
    main()
