#!/usr/bin/env python3
"""Repair PK collisions from the board migration.

task_events/task_comments/task_runs/task_attachments use an autoincrement `id`
that is unique only *within* a board. Migrating rows while preserving those ids
collided across source boards and `insert or ignore` silently dropped rows.

Fix: for every migrated task, delete the (incomplete) copied child rows on the
target and re-insert them with fresh ids from the source boards, preserving
chronological order. task_runs ids are remapped and task_events.run_id rewritten
to keep the run linkage intact.

    python3 repair_events.py --dry
    python3 repair_events.py --apply
"""
import sqlite3, sys, os

DRY = "--apply" not in sys.argv
HOME = "/home/user/.hermes"
B = f"{HOME}/kanban/boards"
DF = f"{HOME}/kanban.db"
WO = f"{B}/_archived/finance-app-coding-1791186972/kanban.db"
WF = f"{B}/_archived/finance-app-finance-1791186974/kanban.db"

# board -> list of (source_db, task_ids)
JOBS = {
    f"{B}/finance-app/kanban.db": [
        (WO, None),   # None = every task id in that source
        (WF, None),
        (DF, ["t_f4140ed4", "t_422f6621", "t_b38d32dc"]),
    ],
    f"{B}/storykami/kanban.db": [
        (DF, ["t_5ff600cf"]),
    ],
}

CHILD = ["task_runs", "task_events", "task_comments", "task_attachments"]


def cols(c, t):
    return [r[1] for r in c.execute(f"pragma table_info({t})")]


def source_tids(path, explicit):
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    if explicit is not None:
        return set(explicit)
    return {r[0] for r in c.execute("select id from tasks")}


def rows_for(path, table, tid, cs):
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    return list(c.execute(f"select {','.join(cs)} from {table} where task_id=?", (tid,)))


for tgt_path, sources in JOBS.items():
    if not os.path.exists(tgt_path):
        print(f"!! missing target {tgt_path}"); continue
    src_tids = [(sp, source_tids(sp, ex)) for sp, ex in sources]
    tgt = sqlite3.connect(tgt_path)
    present = {r[0] for r in tgt.execute("select id from tasks")}
    all_ids = set()
    for _, tids in src_tids:
        all_ids |= tids
    all_ids &= present
    print(f"\n=== {tgt_path}  ({len(all_ids)} migrated tasks)")
    if not all_ids:
        print("   nothing to repair"); continue
    if DRY:
        before = {t: len(list(tgt.execute(f"select 1 from {t} where task_id in "
                      f"({','.join('?'*len(all_ids))})", tuple(all_ids)))) for t in CHILD}
        wanted = {}
        for t in CHILD:
            tcs = cols(tgt, t)
            src_rows = []
            for sp, tids in src_tids:
                for tid in tids & all_ids:
                    try:
                        src_rows += rows_for(sp, t, tid, tcs)
                    except sqlite3.OperationalError:
                        pass
            wanted[t] = len(src_rows)
        for t in CHILD:
            print(f"   {t:18s} on-target={before[t]:5d}  in-sources={wanted[t]:5d}  "
                  f"{'LOST=' + str(wanted[t]-before[t]) if wanted[t] != before[t] else 'ok'}")
        continue

    ph = ",".join("?" * len(all_ids))
    args = tuple(all_ids)

    # --- task_runs: delete + reinsert, remap ids ---
    run_map = {}
    tgt.execute("delete from task_runs where task_id in (%s)" % ph, args)
    rcs = cols(tgt, "task_runs")
    ins_cs = [c for c in rcs if c != "id"]
    for sp, tids in src_tids:
        for tid in sorted(tids & all_ids):
            try:
                rs = rows_for(sp, "task_runs", tid, rcs)
            except sqlite3.OperationalError:
                continue
            for r in sorted(rs, key=lambda x: x[rcs.index("id")]):
                vals = [r[rcs.index(c)] for c in ins_cs]
                cur = tgt.execute(
                    f"insert into task_runs ({','.join(ins_cs)}) values ({','.join('?'*len(ins_cs))})",
                    vals)
                run_map[(tid, r[rcs.index('id')])] = cur.lastrowid

    # --- task_events: delete + reinsert, rewrite run_id ---
    tgt.execute("delete from task_events where task_id in (%s)" % ph, args)
    ecs = cols(tgt, "task_events")
    ein = [c for c in ecs if c != "id"]
    for sp, tids in src_tids:
        for tid in sorted(tids & all_ids):
            try:
                es = rows_for(sp, "task_events", tid, ecs)
            except sqlite3.OperationalError:
                continue
            for e in sorted(es, key=lambda x: x[ecs.index("id")]):
                vals = [e[ecs.index(c)] for c in ein]
                if "run_id" in ein:
                    ri = ein.index("run_id")
                    if vals[ri] is not None:
                        vals[ri] = run_map.get((tid, vals[ri]))
                tgt.execute(
                    f"insert into task_events ({','.join(ein)}) values ({','.join('?'*len(ein))})", vals)

    # --- comments + attachments: delete + reinsert ---
    for t in ["task_comments", "task_attachments"]:
        tgt.execute(f"delete from {t} where task_id in (%s)" % ph, args)
        ccs = cols(tgt, t)
        cin = [c for c in ccs if c != "id"]
        for sp, tids in src_tids:
            for tid in sorted(tids & all_ids):
                try:
                    rs = rows_for(sp, t, tid, ccs)
                except sqlite3.OperationalError:
                    continue
                for r in sorted(rs, key=lambda x: x[ccs.index("id")]):
                    vals = [r[ccs.index(c)] for c in cin]
                    tgt.execute(
                        f"insert into {t} ({','.join(cin)}) values ({','.join('?'*len(cin))})", vals)

    tgt.commit()
    print(f"   repaired. runs_remapped={len(run_map)}")
    # re-add provenance comment (was deleted above)
    for tid in sorted(all_ids):
        tgt.execute("insert into task_comments (task_id, author, body, created_at) values (?,?,?,?)",
                    (tid, "orchestrator",
                     "Migrated 2026-10-05 from a superseded board to this per-project board "
                     "(kanban-operations standard). Task id and full history preserved; "
                     "origin board archived read-only."))
    tgt.commit()

print("\n" + ("DRY RUN — nothing written" if DRY else "APPLIED"))
