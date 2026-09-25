#!/usr/bin/env python3
"""Load one or more related PRs into the shared Tilt env for hands-on review.

  tilt-review.py prepare URL [URL ...]   # fetch each PR into {repo}-worktrees/pr-N; no env change
  tilt-review.py apply   [--timeout SEC] # switch Tilt to the PR worktrees; needs an exclusive lease
  tilt-review.py restore [--remove-worktrees] [--timeout SEC]
                                         # switch back to the pre-review worktrees; needs an exclusive lease

`prepare` saves the current worktree selection once per review (in
review.json next to the tilt-env leases), so `restore` returns to it even after
several prepare rounds. `restore` deletes review.json and, if present, the
review wizard and its results file. Leases and health come from the sibling
tilt-env skill.

Exit codes: 0 ok, 1 env not healthy / git failure, 2 usage error or no lease.
"""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    'tilt_env', Path(__file__).resolve().parents[2] / 'tilt-env/scripts/tilt-env.py')
te = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(te)

STACK = te.ENV_DIR.parent
REVIEW = te.STATE_DIR / 'review.json'
WIZARD = te.STATE_DIR / 'review-wizard.sh'          # optional, written by the agent
RESULTS = te.STATE_DIR / 'review-results.env'       # the wizard's captured outcomes
CONFIG = te.ENV_DIR / 'tilt_config.json'

# GitHub repo name -> Tilt worktree keys it feeds (see switch-worktree.py REPO_MAP).
REPOS = {
    'form-now': ['form-now'],
    'form-now-ecommerce-backend': ['backend'],
    'formcloud-manufacturing': ['fcm'],
}
ALL_KEYS = ['form-now', 'backend', 'fcm', 'paas']

# (repo, path regex, hint). repo None = any repo.
HINTS = [
    ('formcloud-manufacturing', r'^(?!preform_service/).*/migrations/\d\w*\.py$',
     'Django migration -> tilt-env trigger fcm-migrations'),
    ('formcloud-manufacturing', r'^preform_service/migrations/versions/',
     'PaaS alembic migration -> tilt-env trigger paas-migrations'),
    ('form-now-ecommerce-backend', r'^src/(modules/[^/]+/)?migrations/',
     'Medusa migration -> tilt-env trigger medusa-migrations'),
    ('form-now-ecommerce-backend', r'^src/scripts/(seed|sample-part)',
     'Medusa seed script changed -> consider medusa-seed / medusa-sample-part-* triggers'),
    ('formcloud-manufacturing', r'/management/commands/[^/]*seed',
     'FCM seed command changed -> run it in fcm-api if the PR needs its data'),
    (None, r'(^|/)(package\.json|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|pyproject\.toml|poetry\.lock|uv\.lock|requirements[^/]*\.txt)$',
     'dependencies changed -> full image rebuild, first sync is slow'),
    (None, r'^(deployment|helm-chart|helm)/|(^|/)[^/]*\.env[^/]*$|(^|/)settings[^/]*\.py$',
     'deploy config / env / settings changed -> check form-now-dev-env values/ covers new keys'),
]


def run(*cmd, cwd=None):
    out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit('ERROR: %s\n%s' % (' '.join(cmd), out.stderr.strip()))
    return out.stdout.strip()


def load_review():
    return json.loads(REVIEW.read_text()) if REVIEW.exists() else None


def fetch_worktree(repo, number, base):
    """Check PR head out, detached, at {repo}-worktrees/pr-N. Returns the head sha.

    Also refreshes origin/<base>: a stacked PR's base is another PR's branch, and
    a review diff must be taken against it, not against main.
    """
    main = STACK / repo
    wt = STACK / ('%s-worktrees' % repo) / ('pr-%d' % number)
    run('git', '-C', str(main), 'fetch', '--quiet', 'origin', base)
    run('git', '-C', str(main), 'fetch', '--quiet', 'origin', 'pull/%d/head' % number)
    sha = run('git', '-C', str(main), 'rev-parse', 'FETCH_HEAD')  # FETCH_HEAD is per-worktree
    if wt.exists():
        if run('git', '-C', str(wt), 'status', '--porcelain', '--untracked-files=no'):
            sys.exit('ERROR: %s has local changes - commit, stash or remove it first' % wt)
        run('git', '-C', str(wt), 'checkout', '--quiet', '--detach', sha)
    else:
        wt.parent.mkdir(exist_ok=True)
        run('git', '-C', str(main), 'worktree', 'add', '--quiet', '--detach', str(wt), sha)
    return sha


def prepare(args):
    prs = []
    for url in args.urls:
        m = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
        if not m:
            sys.exit('ERROR: not a GitHub PR URL: %s' % url)
        repo, number = m.group(2), int(m.group(3))
        info = json.loads(run('gh', 'pr', 'view', url, '--json', 'title,state,headRefOid,baseRefName,files'))
        files = [f['path'] for f in info['files']]
        keys = list(REPOS.get(repo, []))
        if repo == 'formcloud-manufacturing' and any(f.startswith('preform_service/') for f in files):
            keys.append('paas')
        hints = sorted({h for r, rx, h in HINTS
                        if r in (None, repo) and any(re.search(rx, f) for f in files)})
        prs.append({'url': url, 'repo': repo, 'number': number, 'title': info['title'],
                    'state': info['state'], 'sha': info['headRefOid'], 'keys': keys,
                    'worktree': 'pr-%d' % number, 'base': info['baseRefName'],
                    'path': str(STACK / ('%s-worktrees' % repo) / ('pr-%d' % number)),
                    'files': len(files), 'hints': hints})

    claimed = {}
    for pr in prs:
        for k in pr['keys']:
            if k in claimed:
                sys.exit('ERROR: %s and %s both need the %s slot - review them one at a time'
                         % (claimed[k], pr['url'], k))
            claimed[k] = pr['url']

    review = load_review()
    if review is None:
        cfg = json.loads(CONFIG.read_text())
        review = {'started': te.utc_now(), 'prs': [],
                  'snapshot': {k: cfg.get('%s-worktree' % k, 'default') for k in ALL_KEYS}}
    for pr in prs:
        if pr['repo'] in REPOS or pr['repo'] == 'form-now-dev-env':
            got = fetch_worktree(pr['repo'], pr['number'], pr['base'])
            if got != pr['sha']:
                print('WARNING: %s fetched %s but GitHub says head is %s' % (pr['url'], got, pr['sha']))
        review['prs'] = [p for p in review['prs'] if p['url'] != pr['url']] + [pr]
    te.STATE_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW.write_text(json.dumps(review, indent=2))

    for pr in prs:
        print('#%d %s [%s] %s' % (pr['number'], pr['repo'], pr['state'], pr['title']))
        if pr['repo'] in REPOS or pr['repo'] == 'form-now-dev-env':
            print('  path %s (base origin/%s)' % (pr['path'], pr['base']))
        if pr['repo'] == 'form-now-dev-env':
            print('  env repo itself: checked out at form-now-dev-env-worktrees/%s; Tilt runs from the'
                  ' main checkout, so testing it means restarting Tilt there - ask the user' % pr['worktree'])
        elif not pr['keys']:
            print('  not a Tilt worktree repo - nothing to load; review it by reading only')
        else:
            print('  worktree %s -> Tilt slots: %s' % (pr['worktree'], ', '.join(pr['keys'])))
        for h in pr['hints']:
            print('  hint: ' + h)
    print('saved %s (pre-review selection: %s)' % (REVIEW, review['snapshot']))
    return 0


def switch(selection, timeout):
    """Point each Tilt slot at its worktree, then wait for the reload and rebuilds."""
    if not te.holds_exclusive():
        print('switching worktrees changes the env for everyone - acquire an exclusive lease first')
        return 2
    t0 = te.utc_now()
    for key, wt in selection.items():
        out = subprocess.run(['python3', 'scripts/switch-worktree.py', '--repo', key],
                             cwd=te.ENV_DIR, env={**os.environ, 'WORKTREE': wt},
                             capture_output=True, text=True)
        print((out.stdout + out.stderr).strip())
        if out.returncode != 0:
            return 1
    time.sleep(te.POLL)  # let Tilt notice tilt_config.json before health reads it
    return te.health(argparse.Namespace(wait=timeout, after=t0, resource=None))


def apply(args):
    review = load_review()
    if not review:
        print('no review prepared - run prepare first')
        return 2
    return switch({k: p['worktree'] for p in review['prs'] for k in p['keys']}, args.timeout)


def restore(args):
    review = load_review()
    if not review:
        print('no review in progress')
        return 2
    used = {k for p in review['prs'] for k in p['keys']}
    back = {k: w for k, w in review['snapshot'].items() if k in used}
    rc = switch(back, args.timeout)
    if rc == 2:
        return rc
    if args.remove_worktrees:
        for p in review['prs']:
            wt = STACK / ('%s-worktrees' % p['repo']) / p['worktree']
            if wt.exists():
                out = subprocess.run(['git', '-C', str(STACK / p['repo']), 'worktree', 'remove', str(wt)],
                                     capture_output=True, text=True)
                print('removed %s' % wt if out.returncode == 0 else 'kept %s: %s' % (wt, out.stderr.strip()))
    for f in (REVIEW, WIZARD, RESULTS):
        f.unlink(missing_ok=True)
    print('review closed; Tilt slots restored: %s' % back)
    return rc


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    pr = sub.add_parser('prepare')
    pr.add_argument('urls', nargs='+')
    pr.set_defaults(fn=prepare)
    a = sub.add_parser('apply')
    a.add_argument('--timeout', type=int, default=1200)
    a.set_defaults(fn=apply)
    r = sub.add_parser('restore')
    r.add_argument('--remove-worktrees', action='store_true')
    r.add_argument('--timeout', type=int, default=1200)
    r.set_defaults(fn=restore)
    args = p.parse_args()
    sys.exit(args.fn(args))


if __name__ == '__main__':
    main()
