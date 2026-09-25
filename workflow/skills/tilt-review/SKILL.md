---
name: tilt-review
description: Load one or more related PRs into the local Tilt env, seed what they need, and guide me through testing them by hand — optionally with a thermo-nuclear review first and a test wizard.
disable-model-invocation: true
argument-hint: [--thermo] [--wizard] <PR URL> [<PR URL> ...]
---

# tilt-review

The user hands you one or more related PR links (form-now, form-now-ecommerce-backend,
formcloud-manufacturing). You turn them into a **test brief**, load them into the
shared Tilt env, prepare the data they need, then guide the user while they test
by hand. The env is shared, so every change runs under a tilt-env lease.

| Flag | Adds |
|---|---|
| `--thermo` | a thermo-nuclear review of each PR, run in the background while Tilt loads; its **findings** reach the user before testing starts (step 3, step 6) |
| `--wizard` | an interactive bash wizard that walks the user through the test steps and captures a pass/fail **result** per step (step 6, step 8) |

```bash
TR=~/repos/my-skills/workflow/skills/tilt-review/scripts/tilt-review.py   # --help for flags
TE=~/repos/my-skills/workflow/skills/tilt-env/scripts/tilt-env.py
DEV=~/code/w/form-now-stack/form-now-dev-env
```

## 1. Load the tilt-env rules

Read `~/repos/my-skills/workflow/skills/tilt-env/SKILL.md` — leases, peer names,
the `orbstack` context, messaging. Look up your peer name with `ListAgents`.
Done when you know your peer name and the lease table.

## 2. Fetch the PRs

`python3 $TR prepare <url> [<url> ...]` — checks each PR head out, detached, at
`{repo}-worktrees/pr-<N>` and prints its path, its base branch (often another PR's
branch, for a stacked PR), the Tilt slots it feeds, and **hints** from
its changed files (migrations, seeds, dependencies, deploy config). It changes no
env state, so it needs no lease. It refuses two PRs for one slot; ask the user which
to load.

Done when every URL printed a line: a slot list, "env repo itself", or "not a
Tilt worktree repo". For the env repo itself (form-now-dev-env), Tilt runs from
the main checkout — ask the user how they want to test it before going on.

## 3. Write the test brief

For each PR, read `gh pr view <url> --json title,body`. Read `gh pr diff <url>` too
when the body does not say how to exercise the change, when `prepare` printed a
hint, or when the change reads a feature flag or setting.

- Search the diff for feature flags (`unleash`, `isEnabled`, flag-name strings).
  Each flag the PR reads must exist in `$DEV/values/unleash-flags.yaml`; note any
  that are missing.
- A PR body that links a sibling PR not in the user's list → ask the user whether
  to add it, and re-run `prepare` with it.

The brief holds, per PR:

| Field | Content |
|---|---|
| Change | what a user or client of the service sees differently |
| Reach | where to exercise it: page URL, API call, admin screen, event |
| Data | records, flag states, settings the scenario needs to exist |
| Watch | what could break: related flows, the other PRs' seams |

Done when every PR has all four fields filled, or marked `unknown` with the question
for the user. Show the brief to the user and resolve the `unknown` items before step 4.
Neither flag given → end the brief with one line: `--thermo` and `--wizard` are
available; the user may add either now.

**`--thermo`:** once the brief is confirmed, launch one background `Agent`
(general-purpose) per PR that loads into Tilt, all in one message, with this prompt:

> Invoke the skill `thermo-nuclear-review:thermo-nuclear-review` and follow it on the
> worktree `<path>`. Its diff base is `origin/<base>`, not main:
> `git -C <path> diff origin/<base>...HEAD`. Read-only — no edits, commits, or PR
> comments. Return only the findings report.

Continue with step 4 while they run.

## 4. Load the PRs into Tilt

1. `python3 $TE lease acquire --mode exclusive --purpose "review PR <#s>" --peer <name> --wait 600`.
   Busy → tilt-env's **Asking a holder**.
2. `python3 $TE health` — Tilt down → `python3 $TE up`.
3. `python3 $TR apply` — switches each slot to its `pr-<N>` worktree and waits for
   the Tiltfile reload and rebuilds (up to 20 min; dependency hints make it slow).

Done when `apply` exits 0. On `broken`, read `tilt logs "<resource>" | tail -100`,
report the failure to the user, and stop — a PR that does not build is itself the
first review finding.

## 5. Prepare the data

Work through every hint and every **Data** field of the brief, in this order:

1. Migrations: `python3 $TE trigger <fcm-migrations|medusa-migrations|paas-migrations>`.
2. Flags: add each missing flag under `flags:` in `$DEV/values/unleash-flags.yaml`
   (schema at the top of the file), then `python3 $TE trigger unleash-seed`. Turn a
   flag on for the test in the Unleash UI (http://localhost:4242, `admin` /
   `unleash4all`).
3. Seeds: `python3 $TE trigger <medusa-seed|medusa-sample-part-update-prices|medusa-sample-part-seed-fcm-files|fcm-seed-consolidation-shelves>`
   as the brief needs. Shipping and fulfillment scenarios → the repo's
   `dev-shipping-harness` skill (`$DEV/.claude/skills/`).
4. Anything else: create it through the service's own API or admin (the repo's
   `form-now-dev-env` skill has credentials and admin access).

Done when every Data item is marked either done, with the command that did it, or
as a manual step for the user.

## 6. Hand over to the user

1. Downgrade, so other sessions can still run tests:
   `python3 $TE lease acquire --mode shared --purpose "user testing PR <#s>" --peer <name> --ttl 120`.
2. **`--thermo`:** wait for every review agent. Show the findings per PR, `high`
   first, before the test steps; add each `high` finding that has a runtime effect to
   that PR's **Watch** field and to the test steps.
3. Write the guide, per PR:
   - the numbered steps to test it, with concrete URLs and credentials (a
     resource's links: `tilt get uiresource "<name>" -o json`, `status.endpointLinks`);
   - what "working" looks like for each step;
   - where to look when it doesn't: `tilt logs "<resource>"`, Jaeger
     http://localhost:16686, the Tilt UI http://localhost:10350;
   - the manual Data steps from step 5.
4. **`--wizard`:** build the wizard from the guide as `references/wizard.md` says.
   Done when `bash -n` passes and every guide step is one of its stages.
5. Send the guide. End with: which worktrees are loaded, that you hold a shared
   lease for 2 h, and that they say **done** when finished. With `--wizard`, add the
   run command — `bash ~/.local/state/tilt-env/review-wizard.sh`, in a separate
   terminal, because it reads keyboard input, which a `!` command cannot.

## 7. While the user tests

- Every time you act: `python3 $TE lease renew --ttl 120`, and answer any
  `waiting for you:` line (tilt-env's **Answering a request**).
- A PR got new commits → `python3 $TR prepare <its url>` updates the worktree in
  place and Tilt syncs it; with a dependency hint, `python3 $TE health --wait 900`.
- The user reports a bug → read the logs, find the cause in the PR's worktree, and
  report it as a review finding with file and line.

## 8. Finish

On **done**:

1. `python3 $TE lease acquire --mode exclusive --purpose "close review PR <#s>" --peer <name> --wait 600`.
   **`--wizard`:** read `~/.local/state/tilt-env/review-results.env` now — `restore`
   deletes it. Every `fail` and every note is a finding.
2. Migrations from step 5 stay in the local DBs after the switch back. Tell the user
   which ran, and roll them back now if they ask — while the PR code, which holds the
   migration files, is still loaded.
3. Flags you added to `unleash-flags.yaml`: ask whether to keep them. To remove,
   delete only your entries — the file may carry the user's own uncommitted edits.
4. Ask whether to delete the PR worktrees, then
   `python3 $TR restore [--remove-worktrees]` — switches the slots back to their
   pre-review worktrees and waits for healthy.
5. `python3 $TE lease release`.
6. Report, per PR: the findings from testing, the wizard results (`--wizard`), the
   thermo findings still open (`--thermo`), and anything left changed in the env.

Done when `lease status` no longer lists you and the report is sent.
