#!/usr/bin/env python3
"""Nightly kanban hygiene sweep. Silent when healthy; prints a report when not.

Checks every live board for:
  * WIP breach        - > WIP_LIMIT tasks 'running' for one assignee
  * stale running     - 'running' with a heartbeat older than STALE_MIN
  * unassignable      - 'ready' rows with assignee NULL (unroutable)
  * fragile blocks    - 'blocked', untyped (block_kind NULL), consecutive_failures >= failure_limit
                        (held only by the failure gate -> a failure_limit raise un-parks them)
  * duplicates        - identical titles sitting in ready/todo
  * counts            - per-status tally per board (informational)

Exit code is always 0; this is a reporter, not a gate. Findings go to stdout only.
"""
import sqlite3, json, time, glob, os, sys

HOME = os.environ.get("HERMES_HOME") or "/home/user/.hermes"
WIP_LIMIT = 3
STALE_MIN = 120          # heartbeat older than this while 'running'
now = int(time.time())
problems = []
report = []


def board_dbs():
    yield "default", os.path.join(HOME, "kanban.db")
    root = os.path.join(HOME, "kanban", "boards")
    for d in sorted(glob.glob(os.path.join(root, "*/kanban.db"))):
        yield os.path.basename(os.path.dirname(d)), d


def failure_limit():
    try:
        import yaml
        cfg = yaml.safe_load(open(os.path.join(HOME, "config.yaml")))
        return int((cfg.get("kanban") or {}).get("failure_limit", 2))
    except Exception:
        return 2


FL = failure_limit()

for slug, path in board_dbs():
    if not os.path.exists(path):
        continue
    # honour board.json archived flag
    bj = os.path.join(os.path.dirname(path), "board.json")
    if os.path.exists(bj):
        try:
            if json.load(open(bj)).get("archived"):
                continue
        except Exception:
            pass
    try:
        c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        tasks = list(c.execute(
            "select id,status,assignee,block_kind,block_recurrences,"
            "consecutive_failures,last_heartbeat_at,title from tasks"))
    except Exception as e:
        problems.append(f"[{slug}] unreadable: {e}")
        continue

    by_status = {}
    for t in tasks:
        by_status[t[1]] = by_status.get(t[1], 0) + 1
    report.append(f"  {slug:18s} " + " ".join(f"{k}={v}" for k, v in sorted(by_status.items())))

    wip = {}
    for tid, status, asg, bk, br, cf, hb, title in tasks:
        if status == "running":
            wip[asg] = wip.get(asg, 0) + 1
            if hb and now - int(hb) > STALE_MIN * 60:
                problems.append(
                    f"[{slug}] STALE running {tid} ({asg}) — heartbeat "
                    f"{(now-int(hb))//60}m old; reclaim it: hermes kanban --board {slug} reclaim {tid}")
        elif status == "ready" and not asg:
            problems.append(f"[{slug}] UNROUTABLE ready {tid} — assignee NULL: {str(title)[:50]!r}")
        elif status == "blocked":
            if not bk and (cf or 0) >= FL:
                problems.append(
                    f"[{slug}] FRAGILE block {tid} — untyped, failures={cf}>={FL}; "
                    f"only the failure gate holds it (a failure_limit raise un-parks it). "
                    f"Type it: hermes kanban --board {slug} block {tid} --kind needs_input \"reason\"")
            if not bk and not (cf or 0):
                problems.append(f"[{slug}] block {tid} has no kind and no failure evidence — untriaged")

    for asg, n in wip.items():
        if n > WIP_LIMIT:
            problems.append(f"[{slug}] WIP breach — {n} running for assignee {asg!r} (limit {WIP_LIMIT})")

    seen = {}
    for tid, status, asg, bk, br, cf, hb, title in tasks:
        if status in ("ready", "todo"):
            key = (str(title).strip().lower(), asg)
            seen.setdefault(key, []).append(tid)
    for (title, asg), ids in seen.items():
        if len(ids) > 1:
            problems.append(f"[{slug}] DUPLICATE x{len(ids)} {ids} assignee={asg!r}: {title[:50]!r}")

# Always keep a full audit trail on disk; stay SILENT on stdout when healthy so
# the nightly cron only speaks up when something is actually wrong.
try:
    logdir = os.path.join(HOME, "logs")
    os.makedirs(logdir, exist_ok=True)
    with open(os.path.join(logdir, "kanban-hygiene.log"), "a") as fh:
        fh.write("\n" + "=" * 60 + "\n")
        fh.write("kanban hygiene sweep — " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n")
        for r in report:
            fh.write(r + "\n")
        if problems:
            fh.write(f"{len(problems)} issue(s):\n")
            for p in problems:
                fh.write("  - " + p + "\n")
        else:
            fh.write("healthy: no issues\n")
except Exception:
    pass

if problems:
    print(f"kanban hygiene sweep — {time.strftime('%Y-%m-%d %H:%M')}")
    print("boards:")
    for r in report:
        print(r)
    print(f"\n{len(problems)} kanban hygiene issue(s):")
    for p in problems:
        print("  -", p)
sys.exit(0)

