---
name: tilt-env
description: Tilt dev env control for the shared local form-now-dev-env cluster, with leases so parallel sessions on this machine don't collide. Use for every Tilt interaction — any `tilt` command (up, down, trigger, logs, get), checking whether the env is up or healthy, `kubectl`/`helm` against the local cluster, switching a Tilt worktree or editing `tilt_config.json`, running tests, curl or DB queries against the cluster, and answering a `tilt-env lease request` message from another session. Service facts (ports, env vars, secrets, Helm values) live in the repo's `form-now-dev-env` skill.
---

# tilt-env

One Tilt env runs on this machine (`~/code/w/form-now-stack/form-now-dev-env`, UI on
http://localhost:10350), and many sessions share it. A session that switches a
worktree, edits `tilt_config.json`, or runs `tilt down` changes the env under every
other session's test run. A **lease** makes each session declare its use first.

```bash
TE=~/repos/my-skills/workflow/skills/tilt-env/scripts/tilt-env.py   # --help lists every flag
```

## Kube context

The local cluster is the kube context `orbstack`. The global kubectl context on
this machine often points at a production GKE cluster, so the default is never
safe to trust.

- Pass `--context orbstack` to every `kubectl` and `helm` command. Leave the global
  context as it is — other terminals rely on it.
- `tilt get / logs` and `$TE trigger` talk to Tilt's own API server and need no context.
- `$TE up` starts Tilt with `--context orbstack` and first checks the cluster
  answers; if it doesn't, run `orb start` and retry. `$TE health` reports broken if
  the running Tilt is on any other context.

## Leases

| You are about to… | Lease |
|---|---|
| read: `tilt get`, `tilt logs`, the UI, `$TE health`, `kubectl get/logs/describe` | none |
| use the env as it is: tests, curl, DB queries, an e2e flow | `shared` |
| change the env: `tilt up` when down, `tilt down`, `tilt trigger` (rebuild, migration, seed), worktree switch, `tilt_config.json` edit, pod restart, namespace delete | `exclusive` |

- Shared leases coexist. Exclusive is granted only when no other session holds a
  lease; while it waits, new shared requests are refused, so it is not starved.
- A lease dies when its TTL passes (default 30 min) or its owner session exits
  (owner = `CLAUDE_CODE_SESSION_ID`, liveness = `CLAUDE_PID`).
- Shared → exclusive drops your shared lease first (two upgraders would otherwise
  deadlock). Exclusive → shared downgrades in place, with no gap.

### Pre-flight — every shared or exclusive action

1. Your **peer name** is the name `ListAgents` gives for this session ("This
   session is …"). Look it up once per session; pass it as `--peer` on every
   acquire so blocked sessions can message you.
2. `python3 $TE lease status` — see who holds what.
3. `python3 $TE lease acquire --mode <shared|exclusive> --purpose "<what and why>" --peer <name>`.
   Exit 1 means busy → follow **Asking a holder** below. Run the action only while
   you hold the lease; breaking a live holder's lease is the user's call.
4. Work longer than the TTL → `python3 $TE lease renew` between steps. Read its
   output: `waiting for you:` lines are sessions blocked on you (see
   **Answering a request**).
5. Done — or failed, or stopping early → `python3 $TE lease release`. The step is
   complete when `lease status` no longer lists you.

### Asking a holder

1. The busy output ends with `ask with SendMessage to: <peer>`. Send each named
   holder one message that starts with the leading phrase **tilt-env lease
   request** — the phrase fires this skill in the receiving session:
   `tilt-env lease request from <your peer>: need <mode> to <purpose>, for about <N> min. When can you release?`
2. Then re-run the acquire with `--wait 600`. While it waits, the holder also sees
   you on its `renew`, `status` and `health` output, even if the message sits unread.
3. No peer name on a holder (a human, or an older session) → tell the user who
   holds it and for what, and wait or stop.

A message is a request, not a transfer: the lease is released only by its holder
or its TTL. An idle holder may not read the message until its next turn.

### Answering a request

On a `tilt-env lease request` message or a `waiting for you:` line:

1. Reply with `SendMessage` to the requester's peer name: when you expect to
   release, and what you are doing.
2. Release early only at a safe point — between test runs, never inside one. If
   releasing would cut into work the user asked for, ask the user first.
3. Once released, message the requester: `tilt-env lease released by <your peer>`.

## Patterns

### Bring the env up

```bash
python3 $TE health && exit 0                    # already up and healthy
python3 $TE lease acquire --mode exclusive --purpose "bring up tilt" --peer <name> --wait 600
python3 $TE up --timeout 900                    # detached; log: ~/.local/state/tilt-env/tilt-up.log
python3 $TE lease release
```

A cold bring-up can take 10+ minutes. If `health` reports `broken`, read that
resource's log (`tilt logs <resource> | tail -100`) before retrying anything.

### Use the env as it is

```bash
python3 $TE lease acquire --mode shared --purpose "backend integration tests" --peer <name> --wait 600
python3 $TE health || { python3 $TE lease release; exit 1; }   # test only against a healthy env
# ... run tests ...
python3 $TE lease release
```

### Point a repo at your worktree, then test on it

```bash
python3 $TE lease acquire --mode exclusive --purpose "fcm -> FN-1234 worktree" --peer <name> --wait 600
T0=$(date -u +%Y-%m-%dT%H:%M:%S)
cd ~/code/w/form-now-stack/form-now-dev-env && WORKTREE=FN-1234 python3 scripts/switch-worktree.py --repo fcm
python3 $TE health --after "$T0" --wait 900     # settles only after the Tiltfile reload AND the rebuilds
python3 $TE lease acquire --mode shared --purpose "fcm tests on FN-1234" --peer <name>   # downgrade: others may test too
# ... run tests ...
python3 $TE lease release
```

`--repo` keys: `form-now`, `backend`, `fcm`, `paas`, `printernet-api`,
`printernet-auth`, `printernet-license`, `printernet-dashboard`. The worktree lives
at `{repo}-worktrees/{name}/` beside the main checkout. Leave the repo on your
worktree when you release, and tell the user which repos you left off `default`.

### Run a migration, seed, or rebuild

```bash
python3 $TE trigger fcm-migrations     # exclusive lease required; waits for the run, exit 1 + log hint on failure
```

Resource names carry emoji labels (`🔧 fcm-migrations`); `trigger` accepts the
name without the label. Use it in place of raw `tilt trigger`, which needs the
exact name and returns before the run ends.

### Edit tilt_config.json

Same shape as the worktree pattern: exclusive lease, capture `T0`, edit with
`python3` (the repo's CLAUDE.md rules out `jq`), then `health --after "$T0" --wait 900`.

### Tear down or reset

`tilt down` and namespace deletes destroy cluster state for every session,
including local DB data. Get the user's explicit OK, then take an exclusive lease.

## When the lock looks wrong

- A holder the user says is gone still shows → its process is alive (e.g. an idle
  session). Ask the user to end it, or wait out its TTL.
- State: `~/.local/state/tilt-env/leases.json` (`TILT_ENV_STATE` overrides); the
  user decides whether to delete it. Other checkout → `TILT_ENV_DIR`; other
  cluster → `TILT_ENV_CONTEXT`.
