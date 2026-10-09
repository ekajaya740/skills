#!/usr/bin/env python3
"""Generic board migration. Job spec via argv JSON file.

    python3 migrate_generic.py jobs.json --dry
    python3 migrate_generic.py jobs.json --apply
"""
import sqlite3, sys, time, os, json

NOW = int(time.time())
DRY = "--apply" not in sys.argv
spec_path = sys.argv[1]
JOBS = json.load(open(spec_path))

CHILD_TABLES = ["task_comments", "task_events", "task_runs", "task_attachments"]


def cols(conn, table):
    return [r[1] for r in conn.execute(f"pragma table_info({table})")]


def fetch(conn, table, where, params=()):
    cs = cols(conn, table)
    q = f"select {','.join(cs)} from {table}" + (f" where {where}" if where else "")
    return cs, list(conn.execute(q, params))


def migrate(src_path, tgt_path, ids, label):
    if not os.path.exists(src_path):
        print(f"  !! source missing: {src_path}"); return 0
    src = sqlite3.connect(f"file:{src_path}?mode=ro", uri=True)
    tgt = sqlite3.connect(tgt_path)
    existing = {r[0] for r in tgt.execute("select id from tasks")}
    tgt_cs = cols(tgt, "tasks")
    print(f"\n=== {label} -> {os.path.basename(os.path.dirname(tgt_path))} ({len(ids)} tasks)")
    moved, skipped = [], []

    for tid in ids:
        if tid in existing:
            skipped.append(tid); print(f"  [skip] {tid}: already on target"); continue
        tcs, trows = fetch(src, "tasks", "id=?", (tid,))
        if not trows:
            print(f"  !! {tid}: not found in source"); continue
        row = trows[0]
        title = row[tcs.index("title")][:58]
        keep = [c for c in tcs if c in tgt_cs]
        dropped = [c for c in tcs if c not in tgt_cs]
        vals = [row[tcs.index(c)] for c in keep]

        kids = {}
        for tbl in CHILD_TABLES:
            try:
                kids[tbl] = fetch(src, tbl, "task_id=?", (tid,))
            except sqlite3.OperationalError:
                kids[tbl] = ([], [])
        links = list(src.execute(
            "select parent_id, child_id from task_links where parent_id=? or child_id=?", (tid, tid)))

        if DRY:
            print(f"  [dry] {tid}: {title}")
            print("        " + ", ".join(f"{k.replace('task_','')}={len(v[1])}" for k, v in kids.items())
                  + f", links={len(links)}")
            if dropped:
                print(f"        dropped cols: {dropped}")
            continue

        ph = ",".join("?" * len(keep))
        tgt.execute(f"insert into tasks ({','.join(keep)}) values ({ph})", vals)
        for tbl, (cc, crows) in kids.items():
            if not crows: continue
            tcc = cols(tgt, tbl)
            k = [c for c in cc if c in tcc]
            if not k: continue
            ph2 = ",".join("?" * len(k))
            for r in crows:
                tgt.execute(f"insert or ignore into {tbl} ({','.join(k)}) values ({ph2})",
                            [r[cc.index(c)] for c in k])
        for p, c in links:
            tgt.execute("insert or ignore into task_links (parent_id, child_id) values (?,?)", (p, c))
        tgt.execute("insert into task_comments (task_id, author, body, created_at) values (?,?,?,?)",
                    (tid, "orchestrator",
                     f"Migrated 2026-10-05 from board `{label}` -> "
                     f"`{os.path.basename(os.path.dirname(tgt_path))}` as part of the per-project board "
                     f"consolidation (kanban-operations standard). Task id and full history preserved; "
                     f"the origin board is archived read-only.", NOW))
        moved.append(tid)

    if not DRY:
        tgt.commit()
    print(f"  moved={len(moved)} skipped={len(skipped)}")
    return len(moved)


total = 0
for j in JOBS:
    total += migrate(j["src"], j["tgt"], j["ids"], j["label"])
print(f"\n{'DRY RUN — nothing written' if DRY else 'APPLIED'} (tasks moved: {total})")
