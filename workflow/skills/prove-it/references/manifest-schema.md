# Proof manifest schema

`build_proof.py` reads a JSON manifest and renders the fixed proof template. You supply the content; the script owns the layout. This file documents every field. A complete, runnable example is in `example-manifest.json`.

## Trusted-HTML vs escaped fields

Two kinds of fields, and the difference matters:

- **Narrative fields** (`title`, `what_this_proves`, `verdict.summary`, `method[]`, evidence `intro`/`caption`, requirement `requirement`/`test`/`result`, `scope.*[]`) are treated as **trusted HTML fragments**. Drop in `<code>…</code>`, `<b>…</b>` freely — that's how you get inline code styling. Because they're not escaped, don't paste untrusted/raw data here.
- **Verbatim data** (an output panel's `text`, and every image's `alt`) is **HTML-escaped** for you. Put raw captured stdout in an output panel's `text` exactly as it came out — `<`, `&`, quotes are all handled.

## Fields

### Top level

| Field | Required | Type | Notes |
|---|---|---|---|
| `eyebrow` | yes | string | Context/ticket line above the title, e.g. `"FN-1400 · Live verification"`. Escaped. |
| `title` | yes | HTML | The headline. Trusted HTML (use `<code>`). |
| `what_this_proves` | yes | HTML | One-sentence lede under the title. Trusted HTML. |
| `doc_title` | no | string | The `<title>`/browser-tab text. Defaults to `title` with tags stripped. |
| `verdict` | yes | object | See below. |
| `method` | no | HTML[] | Numbered "how it was verified" steps. Each is a trusted HTML string. |
| `evidence` | no | object[] | Screenshots and/or output panels. See below. |
| `requirements` | no | object[] | The requirement-by-requirement rows. See below. |
| `scope` | no | object | Proven / inferred / user-must-verify. See below. |
| `footer` | no | string[] | Footer spans: repo/branch, test files, date. Escaped. |

Only `eyebrow`, `title`, `what_this_proves`, and `verdict` are structurally required — but a proof with no `evidence`, `requirements`, or `scope` is almost certainly theatre. Fill them.

### `verdict`

| Field | Required | Notes |
|---|---|---|
| `status` | yes | `"PASS"`, `"PARTIAL"`, or `"FAIL"` (case-insensitive). Drives the banner color: green / amber / red. |
| `meta` | no | Tools and counts, mono, e.g. `"Playwright · 1 test · 3.0s · chromium"`. Escaped. |
| `summary` | no | One-line human read, e.g. `"5/6 requirements verified."`. Trusted HTML. |

### `evidence[]` — two kinds

**Image:**
```json
{
  "type": "image",
  "path": "shots/01-success.png",   // relative to --base-dir (default: manifest dir), or absolute
  "id": "01 · success-page.png",     // bold label in the caption; escaped
  "caption": "Live capture by Playwright.",  // trusted HTML
  "alt": "Order confirmation page showing Total $120",  // escaped
  "intro": "Optional paragraph shown above the figure."  // trusted HTML, optional
}
```

**Output panel** (dark mono block for captured command/test output):
```json
{
  "type": "output",
  "title": "curl -i localhost:3000/health",  // uppercase label atop the panel; escaped
  "intro": "Raw captured output — verbatim:",  // trusted HTML, optional
  "text": "HTTP/1.1 200 OK\n\n{\"status\":\"ok\"}"  // VERBATIM, escaped for you
}
```

### `requirements[]`

```json
{
  "requirement": "Returns HTTP 200",     // trusted HTML
  "test": "curl -i /health",             // trusted HTML — how it was tested
  "result": "200 OK",                    // trusted HTML, rendered mono
  "ok": true                             // true → green ✓, false → red ✗
}
```

Set `ok: false` for anything that failed or wasn't run — never fake a ✓.

### `scope`

```json
{
  "proven": ["What you ran and captured. Trusted HTML."],
  "inferred": ["Believed true but not directly exercised — say what would confirm it."],
  "user_must_verify": ["Only checkable on real infra/hardware you don't have."]
}
```

Any of the three arrays may be omitted or empty; empty sections are dropped. `not-run` requirements belong in `user_must_verify`.

## Running

```bash
python3 scripts/build_proof.py --manifest proof.json --output proof.html
# optional: --base-dir DIR   (where relative image paths resolve; default = manifest's dir)
```

The script fails loudly (non-zero exit, message on stderr) if a required field is missing, an evidence image doesn't exist, or `verdict.status` is invalid — so a broken manifest never silently produces a half-empty proof. Then hand `proof.html` to the Artifact tool.
