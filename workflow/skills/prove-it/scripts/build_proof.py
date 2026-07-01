#!/usr/bin/env python3
"""Render a prove-it proof artifact from a JSON manifest.

The whole point of this script is *consistent style*: it owns the HTML/CSS
template so every proof looks identical, and the caller only supplies data.
Feed it a manifest describing what was proven and it emits a self-contained,
Artifact-ready HTML file (screenshots base64-embedded, no external assets).

    python build_proof.py --manifest proof.json --output proof.html

The output is meant to be handed to the Artifact tool as-is. It contains a
<title> and a <style> block but no <!doctype>/<html>/<head>/<body> wrappers,
because the Artifact tool supplies those at publish time.

See references/manifest-schema.md for the full manifest shape. A short version:

{
  "eyebrow": "FN-1400 · Live verification",           # context/ticket line
  "title": "The X event fires with the right payload", # may contain <code>
  "what_this_proves": "One sentence describing ...",   # lede
  "verdict": {
    "status": "PASS",              # PASS | PARTIAL | FAIL  (drives the color)
    "meta": "Playwright · 1 test · 3.0s · chromium",   # tools/counts, mono
    "summary": "5/6 requirements verified. ..."        # one-line human read
  },
  "method": ["Ran the app with <b>analytics on</b> ...", "..."],  # HTML ok
  "evidence": [
    {"type": "image", "path": "shots/01.png", "id": "01 · success.png",
     "caption": "...", "alt": "...", "intro": "optional para above image"},
    {"type": "output", "title": "Test output", "intro": "optional para",
     "text": "raw captured stdout — shown verbatim, escaped"}
  ],
  "requirements": [
    {"requirement": "...", "test": "...", "result": "...", "ok": true}
  ],
  "scope": {
    "proven": ["..."],              # what this artifact actually establishes
    "inferred": ["..."],            # believed true; say what would confirm it
    "user_must_verify": ["..."]     # only the user can check (real infra/hw)
  },
  "footer": ["repo @ branch", "test: e2e/x.spec.ts", "date: 2026-07-01"]
}

Narrative fields (title, method, intro, caption, requirement cells, scope
items) are treated as trusted HTML fragments so you can drop in <code>/<b>.
The `text` of an output panel and image `alt` are escaped — that content is
captured data, shown verbatim, never interpreted.
"""

import argparse
import base64
import html
import json
import mimetypes
import pathlib
import sys

# --- verdict styling -------------------------------------------------------
# Each verdict state gets its own wash/border/ink so the banner reads at a
# glance. Green = proven, amber = partial, red = something failed.
VERDICT_STYLES = {
    "PASS": {"wash": "#e3f3ea", "border": "#bfe3d0", "rule": "var(--pass)",
             "ink": "var(--pass)", "mark": "✓"},
    "PARTIAL": {"wash": "#fdf3e0", "border": "#f0dcae", "rule": "var(--warn)",
                "ink": "var(--warn)", "mark": "◑"},
    "FAIL": {"wash": "#fbe7e7", "border": "#eec6c6", "rule": "var(--fail)",
             "ink": "var(--fail)", "mark": "✗"},
}

STYLE = """<style>
  :root {
    --ground:#eef1f4; --paper:#ffffff; --ink:#14202e; --muted:#4b5a6b; --faint:#7a8794;
    --line:#dde2e8; --line-strong:#c7cfd8;
    --pass:#1f8f5f; --warn:#b7791f; --fail:#c0392b;
    --accent:#2f6f8f; --panel:#0f1520;
    --mono:ui-monospace,"SF Mono","JetBrains Mono",Menlo,Consolas,monospace;
    --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);line-height:1.6;-webkit-font-smoothing:antialiased}
  .page{max-width:920px;margin:0 auto;padding:clamp(24px,5vw,64px) clamp(18px,5vw,40px) 88px}
  .eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:0 0 12px}
  h1{font-size:clamp(27px,4.6vw,42px);line-height:1.06;letter-spacing:-.02em;font-weight:800;margin:0 0 14px;text-wrap:balance}
  .lede{font-size:clamp(16px,2vw,19px);color:var(--muted);max-width:64ch;margin:0}
  h2{font-size:clamp(19px,2.6vw,24px);letter-spacing:-.01em;font-weight:750;margin:0 0 6px}
  .kicker{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--faint);margin:0 0 10px}
  p{margin:0 0 14px;max-width:68ch} code{font-family:var(--mono);font-size:.86em;background:#eceff3;border:1px solid var(--line);border-radius:4px;padding:1px 5px}
  section{margin-top:clamp(40px,6vw,64px)}
  .verdict{margin-top:28px;border-radius:12px;padding:20px 24px;display:flex;flex-wrap:wrap;gap:6px 20px;align-items:baseline}
  .verdict .tag{font-family:var(--mono);font-weight:700;font-size:15px;letter-spacing:.04em}
  .verdict .meta{font-family:var(--mono);font-size:13px;color:var(--muted)}
  .verdict .say{flex-basis:100%;margin-top:8px;color:var(--ink);font-size:15.5px}
  ol.method{margin:18px 0 0;padding:0;list-style:none;counter-reset:s;display:flex;flex-direction:column;gap:12px}
  ol.method li{position:relative;padding-left:38px;color:var(--muted);font-size:15px}
  ol.method li::before{counter-increment:s;content:counter(s);position:absolute;left:0;top:-1px;width:26px;height:26px;border-radius:50%;background:var(--paper);border:1.5px solid var(--line-strong);font-family:var(--mono);font-size:12px;font-weight:600;color:var(--ink);display:grid;place-items:center}
  ol.method b{color:var(--ink);font-weight:650}
  figure{margin:22px 0 0;background:var(--paper);border:1px solid var(--line);border-radius:12px;overflow:hidden}
  figure img{display:block;width:100%;height:auto;border-bottom:1px solid var(--line)}
  figcaption{padding:12px 16px;font-size:13.5px;color:var(--muted)}
  figcaption b{color:var(--ink);font-weight:650}
  pre.output{margin:22px 0 0;background:var(--panel);color:#d7e0ea;border-radius:12px;padding:18px 20px;overflow-x:auto;font-family:var(--mono);font-size:12.5px;line-height:1.55;white-space:pre}
  pre.output .cap{display:block;color:#7f8ea0;font-size:11px;letter-spacing:.08em;text-transform:uppercase;margin-bottom:10px}
  .tablewrap{margin-top:20px;overflow-x:auto;border:1px solid var(--line);border-radius:12px}
  table{border-collapse:collapse;width:100%;min-width:560px;background:var(--paper)}
  th,td{text-align:left;padding:11px 15px;border-bottom:1px solid var(--line);vertical-align:top;font-size:14px}
  thead th{font-family:var(--mono);font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--faint);font-weight:600;background:var(--ground)}
  tbody tr:last-child td{border-bottom:none} td.m{font-family:var(--mono);font-size:12.5px}
  .tick{color:var(--pass);font-weight:700} .cross{color:var(--fail);font-weight:700}
  .scope{margin-top:22px;background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:20px 24px}
  .scope h3{margin:0 0 10px;font-size:15px;font-family:var(--mono);letter-spacing:.02em}
  .scope h3.proven{color:var(--pass)} .scope h3.inferred{color:var(--warn)} .scope h3.user{color:var(--accent)}
  .scope ul{margin:0;padding-left:18px} .scope li{margin:6px 0;color:var(--muted);font-size:14.5px}
  .scope li b{color:var(--ink);font-weight:650} .scope .block + .block{margin-top:16px}
  footer{margin-top:56px;padding-top:20px;border-top:1px solid var(--line);font-family:var(--mono);font-size:11.5px;color:var(--faint);display:flex;flex-wrap:wrap;gap:6px 18px}
</style>"""


def die(msg):
    print(f"build_proof: {msg}", file=sys.stderr)
    sys.exit(1)


def require(manifest, key):
    if key not in manifest or manifest[key] in (None, "", [], {}):
        die(f"manifest is missing required field: {key!r}")
    return manifest[key]


def data_uri(path: pathlib.Path) -> str:
    if not path.exists():
        die(f"evidence image not found: {path}")
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"


def render_verdict(v: dict) -> str:
    status = str(require(v, "status")).upper()
    if status not in VERDICT_STYLES:
        die(f"verdict.status must be PASS, PARTIAL, or FAIL (got {status!r})")
    st = VERDICT_STYLES[status]
    meta = html.escape(v.get("meta", ""))
    summary = v.get("summary", "")  # trusted HTML fragment
    style = (f"background:{st['wash']};border:1px solid {st['border']};"
             f"border-left:4px solid {st['rule']}")
    parts = [f'  <div class="verdict" style="{style}">']
    parts.append(f'    <span class="tag" style="color:{st["ink"]}">'
                 f'{st["mark"]} {status}</span>')
    if meta:
        parts.append(f'    <span class="meta">{meta}</span>')
    if summary:
        parts.append(f'    <span class="say">{summary}</span>')
    parts.append("  </div>")
    return "\n".join(parts)


def render_method(steps) -> str:
    if not steps:
        return ""
    lis = "\n".join(f"      <li>{s}</li>" for s in steps)  # trusted HTML
    return (
        '  <section>\n'
        '    <p class="kicker">How it was verified</p>\n'
        '    <h2>Method — real execution, mocked only where noted</h2>\n'
        f'    <ol class="method">\n{lis}\n    </ol>\n'
        '  </section>'
    )


def render_evidence(items, base: pathlib.Path) -> str:
    if not items:
        return ""
    blocks = []
    for it in items:
        kind = it.get("type", "image")
        intro = it.get("intro", "")  # trusted HTML fragment
        if intro:
            intro = f'    <p>{intro}</p>\n'
        if kind == "image":
            path = pathlib.Path(it["path"])
            if not path.is_absolute():
                path = base / path
            uri = data_uri(path)
            alt = html.escape(it.get("alt", ""))
            cap = it.get("caption", "")  # trusted HTML fragment
            ident = html.escape(str(it.get("id", "")))
            capline = f"<b>{ident}</b> — {cap}" if ident else cap
            blocks.append(
                f'{intro}    <figure>\n'
                f'      <img src="{uri}" alt="{alt}">\n'
                f'      <figcaption>{capline}</figcaption>\n'
                f'    </figure>'
            )
        elif kind == "output":
            title = html.escape(it.get("title", "captured output"))
            text = html.escape(it.get("text", ""))  # verbatim data, escaped
            blocks.append(
                f'{intro}    <pre class="output"><span class="cap">'
                f'{title}</span>{text}</pre>'
            )
        else:
            die(f"evidence item type must be 'image' or 'output' (got {kind!r})")
    body = "\n\n".join(blocks)
    return (
        '  <section>\n'
        '    <p class="kicker">Evidence</p>\n'
        '    <h2>Captured from the real run</h2>\n'
        f'{body}\n'
        '  </section>'
    )


def render_requirements(rows) -> str:
    if not rows:
        return ""
    trs = []
    for r in rows:
        ok = r.get("ok")
        mark = ('<span class="tick">✓</span>' if ok
                else '<span class="cross">✗</span>')
        trs.append(
            "          <tr>"
            f"<td>{r.get('requirement','')}</td>"
            f"<td>{r.get('test','')}</td>"
            f"<td class=\"m\">{r.get('result','')}</td>"
            f"<td>{mark}</td></tr>"
        )
    body = "\n".join(trs)
    return (
        '  <section>\n'
        '    <p class="kicker">Requirement by requirement</p>\n'
        '    <h2>Each requirement → how it was tested → result</h2>\n'
        '    <div class="tablewrap">\n'
        '      <table>\n'
        '        <thead><tr><th>Requirement</th><th>How it was tested</th>'
        '<th>Captured result</th><th>OK</th></tr></thead>\n'
        f'        <tbody>\n{body}\n        </tbody>\n'
        '      </table>\n'
        '    </div>\n'
        '  </section>'
    )


def render_scope(scope: dict) -> str:
    if not scope:
        return ""
    blocks = []
    spec = [
        ("proven", "proven", "Proven here"),
        ("inferred", "inferred", "Inferred (not directly exercised)"),
        ("user_must_verify", "user", "Left for the user to verify"),
    ]
    for key, cls, heading in spec:
        items = scope.get(key)
        if not items:
            continue
        lis = "\n".join(f"        <li>{i}</li>" for i in items)  # trusted HTML
        blocks.append(
            f'      <div class="block">\n'
            f'        <h3 class="{cls}">{heading}</h3>\n'
            f'        <ul>\n{lis}\n        </ul>\n'
            f'      </div>'
        )
    if not blocks:
        return ""
    body = "\n".join(blocks)
    return (
        '  <section>\n'
        '    <p class="kicker">Scope — honest read</p>\n'
        '    <h2>What this proves, and what it does not</h2>\n'
        f'    <div class="scope">\n{body}\n    </div>\n'
        '  </section>'
    )


def render_footer(items) -> str:
    if not items:
        return ""
    spans = "\n".join(f"    <span>{html.escape(str(i))}</span>" for i in items)
    return f'  <footer>\n{spans}\n  </footer>'


def build(manifest: dict, base: pathlib.Path) -> str:
    eyebrow = html.escape(require(manifest, "eyebrow"))
    title = require(manifest, "title")            # trusted HTML fragment
    lede = require(manifest, "what_this_proves")  # trusted HTML fragment
    title_text = html.escape(manifest.get("doc_title", _strip_tags(title)))

    parts = [
        f"<title>{title_text}</title>",
        STYLE,
        '',
        '<div class="page">',
        '  <header>',
        f'    <p class="eyebrow">{eyebrow}</p>',
        f'    <h1>{title}</h1>',
        f'    <p class="lede">{lede}</p>',
        '  </header>',
        '',
        render_verdict(require(manifest, "verdict")),
    ]
    for chunk in (
        render_method(manifest.get("method")),
        render_evidence(manifest.get("evidence"), base),
        render_requirements(manifest.get("requirements")),
        render_scope(manifest.get("scope")),
        render_footer(manifest.get("footer")),
    ):
        if chunk:
            parts += ['', chunk]
    parts.append('</div>')
    return "\n".join(parts) + "\n"


def _strip_tags(s: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", s)


def main():
    ap = argparse.ArgumentParser(description="Render a prove-it proof artifact.")
    ap.add_argument("--manifest", required=True, help="path to the JSON manifest")
    ap.add_argument("--output", required=True, help="path to write the HTML to")
    ap.add_argument("--base-dir", default=None,
                    help="base dir for relative evidence image paths "
                         "(default: the manifest's directory)")
    args = ap.parse_args()

    mpath = pathlib.Path(args.manifest)
    if not mpath.exists():
        die(f"manifest not found: {mpath}")
    try:
        manifest = json.loads(mpath.read_text())
    except json.JSONDecodeError as e:
        die(f"manifest is not valid JSON: {e}")

    base = pathlib.Path(args.base_dir) if args.base_dir else mpath.parent
    html_out = build(manifest, base)

    out = pathlib.Path(args.output)
    out.write_text(html_out)
    print(f"wrote {out} ({len(html_out)} bytes) — verdict: "
          f"{manifest['verdict']['status'].upper()}")


if __name__ == "__main__":
    main()
