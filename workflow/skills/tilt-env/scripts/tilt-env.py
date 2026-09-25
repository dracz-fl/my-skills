#!/usr/bin/env python3
"""Control a shared local Tilt env: leases between sessions, bring-up, health.

Leases (one state file per machine, guarded by flock):
  shared     - "I use the env as it is now; do not change it under me."
               Any number may coexist.
  exclusive  - "I change the env" (tilt up/down, worktree switch, config edit).
               Granted only when no other session holds any lease. While an
               exclusive request waits, new shared leases are refused, so a
               stream of test runs cannot starve it.
A lease dies when its TTL passes or its owner process exits.
--peer records the session's messaging name, so a blocked session knows whom
to ask. While a request waits, the holder sees it on renew / status / health.

  tilt-env.py lease acquire --mode shared|exclusive --purpose TEXT [--peer NAME] [--ttl MIN] [--wait SEC]
  tilt-env.py lease renew [--ttl MIN]
  tilt-env.py lease release
  tilt-env.py lease status
  tilt-env.py up [--timeout SEC]
  tilt-env.py trigger NAME [--timeout SEC]   # needs your exclusive lease; waits for the run
  tilt-env.py health [--wait SEC] [--after ISO8601 [--resource NAME ...]]

`up` runs `tilt up --context $TILT_ENV_CONTEXT` (default orbstack) and never
touches the global kubectl context.

Exit codes: 0 ok, 1 busy / not healthy / timed out, 2 usage or setup error.
"""
import argparse
import fcntl
import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

STATE_DIR = Path(os.environ.get('TILT_ENV_STATE', Path.home() / '.local/state/tilt-env'))
LEASES = STATE_DIR / 'leases.json'
LOCK = STATE_DIR / 'leases.lock'
TILT_LOG = STATE_DIR / 'tilt-up.log'
ENV_DIR = Path(os.path.expanduser(
    os.environ.get('TILT_ENV_DIR', '~/code/w/form-now-stack/form-now-dev-env')))
# The global kubectl context may point at a remote cluster, so pass this one
# explicitly instead of trusting (or switching) the kubeconfig default.
CONTEXT = os.environ.get('TILT_ENV_CONTEXT', 'orbstack')
POLL = 5
WAITER_TTL = 60  # a waiting request must re-assert itself this often


def owner():
    return os.environ.get('TILT_ENV_OWNER') or os.environ.get('CLAUDE_CODE_SESSION_ID') \
        or 'pid-%d' % os.getppid()


def owner_pid():
    # Claude runs each Bash call in a short-lived shell, so the parent pid dies
    # right after this script. CLAUDE_PID is the long-lived session process.
    return int(os.environ.get('CLAUDE_PID') or os.getppid())


def pid_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        pass
    return True


@contextmanager
def locked_state():
    """Yield the lease table with dead entries dropped; write it back on exit."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOCK, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = json.loads(LEASES.read_text()) if LEASES.exists() else {}
        now = time.time()
        for table in ('leases', 'waiting'):
            state[table] = {o: e for o, e in state.get(table, {}).items()
                            if e['expires'] > now and pid_alive(e['pid'])}
        yield state
        tmp = LEASES.with_suffix('.tmp')
        tmp.write_text(json.dumps(state, indent=2))
        tmp.replace(LEASES)


def describe(o, e, waiting=False):
    who = e.get('peer') or 'session %s (no peer name)' % o[:8]
    left = '' if waiting else ', %dm left' % int((e['expires'] - time.time()) / 60)
    return '%s%-9s %s (pid %d%s) - %s' % (
        'wants ' if waiting else '', e['mode'], who, e['pid'], left, e['purpose'])


def print_waiters(state):
    """Tell a lease holder which other sessions wait on the env right now."""
    if owner() not in state['leases']:
        return
    for o, e in state['waiting'].items():
        if o != owner():
            print('waiting for you: ' + describe(o, e, waiting=True))


def blockers(state, me, mode):
    others = {o: e for o, e in state['leases'].items() if o != me}
    if mode == 'exclusive':
        return others
    blocking = {o: e for o, e in others.items() if e['mode'] == 'exclusive'}
    blocking.update({o: e for o, e in state['waiting'].items()
                     if o != me and e['mode'] == 'exclusive'})
    return blocking


def lease_acquire(args):
    me, deadline = owner(), time.time() + args.wait
    while True:
        with locked_state() as state:
            if args.mode == 'exclusive' and state['leases'].get(me, {}).get('mode') == 'shared':
                # Two shared holders that both upgrade would wait on each other forever.
                del state['leases'][me]
            blocking = blockers(state, me, args.mode)
            if not blocking:
                state['waiting'].pop(me, None)
                state['leases'][me] = {
                    'mode': args.mode, 'purpose': args.purpose, 'peer': args.peer,
                    'pid': owner_pid(), 'since': time.time(),
                    'expires': time.time() + args.ttl * 60}
                print('acquired %s lease for %s (%dm)' % (args.mode, me, args.ttl))
                return 0
            timed_out = time.time() >= deadline
            if not timed_out:
                state['waiting'][me] = {'mode': args.mode, 'purpose': args.purpose,
                                        'peer': args.peer, 'pid': owner_pid(),
                                        'expires': time.time() + WAITER_TTL}
            else:
                state['waiting'].pop(me, None)
        if timed_out:
            print('busy - %s lease refused. Held by:' % args.mode)
            for o, e in blocking.items():
                print('  ' + describe(o, e, waiting=o not in state['leases']))
            peers = sorted({e['peer'] for e in blocking.values() if e.get('peer')})
            if peers:
                print('ask with SendMessage to: ' + ', '.join(peers))
            return 1
        time.sleep(POLL)


def lease_renew(args):
    with locked_state() as state:
        lease = state['leases'].get(owner())
        if not lease:
            print('no live lease for %s - acquire again' % owner())
            return 1
        lease['expires'] = time.time() + args.ttl * 60
        print('renewed %s lease (%dm)' % (lease['mode'], args.ttl))
        print_waiters(state)
        return 0


def lease_release(args):
    with locked_state() as state:
        state['waiting'].pop(owner(), None)
        gone = state['leases'].pop(owner(), None)
    print('released' if gone else 'nothing to release')
    return 0


def lease_status(args):
    with locked_state() as state:
        rows = [describe(o, e) for o, e in state['leases'].items()]
        rows += [describe(o, e, waiting=True) for o, e in state['waiting'].items()]
    print('you: %s' % owner())
    print('\n'.join(rows) if rows else 'no leases')
    return 0


def tilt_resources():
    """Return the uiresource list, or None when no Tilt server answers."""
    out = subprocess.run(['tilt', 'get', 'uiresources', '-o', 'json'],
                         capture_output=True, text=True)
    return json.loads(out.stdout)['items'] if out.returncode == 0 else None


def resolve(items, name):
    """Match a resource by its full name or by the name after its emoji label."""
    names = [r['metadata']['name'] for r in items]
    if name in names:
        return name
    hits = [n for n in names if n.split(' ', 1)[-1] == name]
    return hits[0] if len(hits) == 1 else None


def utc_now():
    return time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())


def classify(items, after, resources):
    """Return (broken, pending) resource names. Manual resources never run are idle.

    With `after`, each of `resources` also counts as pending until it has a build
    that finished after that UTC time.
    """
    broken, pending = [], []
    for r in items:
        name, s = r['metadata']['name'], r['status']
        if (s.get('disableStatus') or {}).get('state') == 'Disabled':
            continue
        if 'error' in (s.get('runtimeStatus'), s.get('updateStatus')):
            broken.append(name)
        elif s.get('updateStatus') in ('pending', 'in_progress') \
                or s.get('runtimeStatus') == 'pending':
            pending.append(name)
    by_name = {r['metadata']['name']: r for r in items}
    for name in resources if after else []:
        full = resolve(items, name)
        if not full:
            broken.append('%s (no such resource)' % name)
            continue
        last = (by_name[full]['status'].get('buildHistory') or [{}])[0].get('finishTime', '')
        if last[:19] < after[:19]:  # ISO timestamps in UTC compare as strings
            pending.append('%s (no run since %s)' % (name, after))
    return broken, pending


def tilt_context():
    out = subprocess.run(['tilt', 'get', 'cluster', 'default', '-o', 'json'],
                         capture_output=True, text=True)
    if out.returncode != 0:
        return None
    return json.loads(out.stdout)['status'].get('connection', {}).get('kubernetes', {}).get('context')


def health(args):
    deadline = time.time() + args.wait
    while True:
        items = tilt_resources()
        if items is None:
            print('tilt is not running (no API server answered)')
            return 1
        broken, pending = classify(items, args.after, args.resource or ['(Tiltfile)'])
        ctx = tilt_context()
        if ctx != CONTEXT:
            broken.append('tilt runs on context %r, expected %r' % (ctx, CONTEXT))
        if not pending or time.time() >= deadline:
            break
        time.sleep(POLL)
    for label, names in (('broken', broken), ('pending', pending)):
        if names:
            print('%s: %s' % (label, ', '.join(sorted(names))))
    with locked_state() as state:
        print_waiters(state)
    if not broken and not pending:
        print('healthy: %d resources ok' % len(items))
        return 0
    return 1


def holds_exclusive():
    with locked_state() as state:
        lease = state['leases'].get(owner())
    return bool(lease) and lease['mode'] == 'exclusive'


def trigger(args):
    items = tilt_resources()
    if items is None:
        print('tilt is not running')
        return 1
    name = resolve(items, args.name)
    if not name:
        print('no resource %r - see `tilt get uiresources`' % args.name)
        return 2
    if not holds_exclusive():
        print('triggering %s changes the env for everyone - acquire an exclusive lease first' % name)
        return 2
    t0 = utc_now()
    subprocess.run(['tilt', 'trigger', name], check=True)
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        time.sleep(POLL)
        r = next(r for r in tilt_resources() or [] if r['metadata']['name'] == name)
        last = (r['status'].get('buildHistory') or [{}])[0]
        if last.get('finishTime', '')[:19] >= t0 and r['status'].get('updateStatus') != 'in_progress':
            if last.get('error'):
                print('%s failed: %s\nlog: tilt logs "%s" | tail -100' % (name, last['error'], name))
                return 1
            print('%s finished ok' % name)
            return 0
    print('%s did not finish in %ds - tilt logs "%s"' % (name, args.timeout, name))
    return 1


def up(args):
    if tilt_resources() is not None:
        print('tilt already running')
        return health(argparse.Namespace(wait=0, after=None, resource=None))
    if not holds_exclusive():
        print('starting tilt changes the env for everyone - acquire an exclusive lease first')
        return 2
    if not (ENV_DIR / 'Tiltfile').exists():
        print('no Tiltfile in %s - set TILT_ENV_DIR' % ENV_DIR)
        return 2
    ready = subprocess.run(['kubectl', '--context', CONTEXT, 'get', '--raw', '/readyz',
                            '--request-timeout=5s'], capture_output=True, text=True)
    if ready.returncode != 0:
        print('kube context %r is not reachable - start OrbStack (`orb start`) and retry:\n%s'
              % (CONTEXT, ready.stderr.strip()))
        return 2
    with open(TILT_LOG, 'w') as log:
        subprocess.Popen(['tilt', 'up', '--context', CONTEXT], cwd=ENV_DIR, stdout=log, stderr=log,
                         stdin=subprocess.DEVNULL, start_new_session=True)
    print('started tilt up --context %s in %s (log: %s, UI: http://localhost:10350)' % (CONTEXT, ENV_DIR, TILT_LOG))
    deadline = time.time() + 60
    while tilt_resources() is None:
        if time.time() >= deadline:
            print('tilt API did not come up in 60s - read %s' % TILT_LOG)
            return 1
        time.sleep(2)
    return health(argparse.Namespace(wait=args.timeout, after=None, resource=None))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    lease = sub.add_parser('lease').add_subparsers(dest='lease_cmd', required=True)
    a = lease.add_parser('acquire')
    a.add_argument('--mode', choices=['shared', 'exclusive'], required=True)
    a.add_argument('--purpose', required=True)
    a.add_argument('--peer', default=os.environ.get('TILT_ENV_PEER'),
                   help='your session name from ListAgents, for SendMessage')
    a.add_argument('--ttl', type=int, default=30, help='minutes (default 30)')
    a.add_argument('--wait', type=int, default=0, help='seconds to wait for the lease (default 0)')
    a.set_defaults(fn=lease_acquire)
    r = lease.add_parser('renew')
    r.add_argument('--ttl', type=int, default=30)
    r.set_defaults(fn=lease_renew)
    lease.add_parser('release').set_defaults(fn=lease_release)
    lease.add_parser('status').set_defaults(fn=lease_status)
    u = sub.add_parser('up')
    u.add_argument('--timeout', type=int, default=900, help='seconds to wait for healthy')
    u.set_defaults(fn=up)
    t = sub.add_parser('trigger')
    t.add_argument('name', help='resource name, with or without its emoji label')
    t.add_argument('--timeout', type=int, default=600)
    t.set_defaults(fn=trigger)
    h = sub.add_parser('health')
    h.add_argument('--wait', type=int, default=0, help='seconds to wait for pending to settle')
    h.add_argument('--after', help='also wait for a run of --resource that finished after this UTC time')
    h.add_argument('--resource', action='append',
                   help='resource to wait on with --after (repeatable; default: (Tiltfile))')
    h.set_defaults(fn=health)
    args = p.parse_args()
    sys.exit(args.fn(args))


if __name__ == '__main__':
    main()
