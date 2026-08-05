# my-skills

A personal [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces).
It hosts my own skills so I can version them in git, sync them into any
workspace, and share them with others.

## Layout

```
my-skills/
├── .claude-plugin/marketplace.json   # marketplace manifest — lists the plugins below
└── workflow/                         # the "workflow" plugin (bundles my skills)
    ├── .claude-plugin/plugin.json
    └── skills/
        ├── retrospective/SKILL.md     # a skill can be a single file…
        └── build-artifact/            # …or bundle its own resources
            ├── SKILL.md
            ├── scripts/               # executables the skill runs
            ├── assets/                # files used in the output
            └── references/            # docs loaded on demand
```

- **Marketplace:** `my-skills`
- **Plugin:** `workflow` — workflow-improvement skills.

## Install

From the local clone:

```
/plugin marketplace add /Users/daniel.racz/repos/my-skills
/plugin install workflow@my-skills
```

Or, once pushed to a remote, from anywhere:

```
/plugin marketplace add dracz-fl/my-skills         # GitHub owner/repo
/plugin install workflow@my-skills
```

Skills are then invoked namespaced by plugin, e.g. `/workflow:retrospective`.

## Update / sync after changing a skill

```
/plugin marketplace update my-skills
```

(or `/reload-plugins` inside a session after a local edit).

## Add a new skill

1. Create `workflow/skills/<skill-name>/SKILL.md` (use the `skill-creator`
   skill, or copy an existing one as a template).
2. Commit and push.
3. `/plugin marketplace update my-skills` to pull it in.

To group skills into a separate plugin instead, add a sibling directory with its
own `.claude-plugin/plugin.json` and list it in `marketplace.json`.

## Skills

| Skill | Plugin | What it does |
|-------|--------|--------------|
| `build-artifact` | `workflow` | Builds a shareable HTML artifact page from a short TOML spec instead of hand-written CSS — a walkthrough/explainer of a change or system, or a questionnaire that collects answers and decisions back from a human. Bundles its own builder and theme, so the spec carries content only. |
| `dev-flow` | `workflow` | Router for the standard per-ticket dev flow: loads the ticket, plans with `/grill-with-docs`, builds under `/grug:grug`, then (once dev is done) runs `/pre-pr-gates`, authors the PR with `/formlabs-pr-write`, and babysits the PR through CodeRabbit's review until it's clean. |
| `pre-pr-gates` | `workflow` | Runs the mandatory pre-PR quality gates — an assumptions audit (Gate 0) then `/simplify`, `/decontextualize-doc-comments`, and `/thermo-nuclear-review` in sequence — before declaring work done or PR-ready. |
| `prove-it` | `workflow` | Produces a proof-of-work artifact for a completed task: turns requirements into real tests, runs them, captures the evidence, and renders an HTML proof mapping each requirement to how it was tested. |
| `retrospective` | `workflow` | Reviews the current conversation for friction (corrections, wrong guesses, repetition, recurring permission prompts), filters to the durable lessons, and turns them into a CLAUDE.md rule, a new skill, a hook, or a reference doc. |
