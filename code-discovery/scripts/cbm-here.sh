#!/usr/bin/env bash
# cbm-here — decide whether THIS directory's code index can be trusted, and fix it.
#
# One index per directory: the graph is keyed by root path, so every worktree is
# its own project and no index answers for another branch. An agent may start in
# one worktree and work in another, so this resolves from the CURRENT directory,
# never from where the session began.
#
# Usage:
#   cbm-here.sh            # one line: state= project= ...
#   cbm-here.sh --json     # same facts as JSON
#   cbm-here.sh --ensure   # reindex if stale, then report — one call, current
#   cbm-here.sh --project  # print only the project name (empty if absent)
#
#   fresh    index is current — query it
#   stale    the tree differs from what the index parsed — reindex, or grep until it lands
#   absent   this directory was never indexed — grep; index only if you will edit here
#   unknown  the index exists but its schema is unreadable — treat as absent
#   missing  no git worktree at CWD
#
# Exit codes: 0 fresh/absent (nothing to fix), 1 stale (reindex, or use --ensure),
#             2 not a worktree or unreadable index.
#
# ── How staleness is decided ─────────────────────────────────────────────────
# Not by git heuristics. The index stores, for every file it parsed, the path,
# size, mtime and sha256 (`file_hashes`). Comparing that table to the filesystem
# is the exact test, and it catches what `git log --since` cannot: a switch to an
# OLDER ref, an uncommitted edit, a file the indexer skipped, and a brand-new
# file that was never parsed.
#
# The parsed-extension set is read back out of that same table rather than
# hardcoded, so it cannot drift from what the indexer actually walks.
set -uo pipefail

JSON=0
ENSURE=0
PROJECT_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --json) JSON=1 ;;
    --ensure) ENSURE=1 ;;
    --project) PROJECT_ONLY=1 ;;
    -h|--help) sed -n '2,27p' "$0"; exit 0 ;;
    *) echo "unknown flag: $arg" >&2; exit 2 ;;
  esac
done

CBM_BIN="${CBM_BIN:-$(command -v codebase-memory-mcp || echo "$HOME/.local/bin/codebase-memory-mcp")}"
CACHE_DIR="${CBM_CACHE_DIR:-$HOME/.cache/codebase-memory-mcp}"

HERE=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "state=missing reason=not-a-worktree"; exit 2; }
BRANCH=$(git -C "$HERE" rev-parse --abbrev-ref HEAD 2>/dev/null)

# The project name is the absolute root with "/" -> "-" and no leading dash — a
# pure function of the path, so it is derived, never looked up.
NAME="${HERE#/}"
NAME="${NAME//\//-}"
DB="$CACHE_DIR/$NAME.db"

if [ ! -f "$DB" ]; then
  [ "$PROJECT_ONLY" = 1 ] && { echo ""; exit 0; }
  if [ "$JSON" = 1 ]; then
    python3 -c 'import json,sys; print(json.dumps({"state":"absent","project":None,"worktree":sys.argv[1],"branch":sys.argv[2]}))' "$HERE" "$BRANCH"
  else
    echo "state=absent project=none worktree=$HERE branch=$BRANCH"
  fi
  exit 0
fi

# ── The oracle ──────────────────────────────────────────────────────────────
# `changed`   — the index's own sha256 disagrees with the file. Stat first;
#               hash only the rows whose size or mtime moved, because a
#               checkout restores identical bytes with a new mtime.
# `missing`   — indexed, now gone.
# `unindexed` — a file the index parses (same extension set, read out of
#               `file_hashes` so it cannot drift) that git tracks or does not
#               ignore, which is newer than the index.
ORACLE=$(python3 - "$DB" "$HERE" <<'PY'
import calendar, hashlib, os, sqlite3, subprocess, sys, time

db, root = sys.argv[1], os.path.realpath(sys.argv[2])
try:
    # Busy timeout: the project DB is rollback-journal, not WAL, so a read can
    # collide with a reindex writer. Wait rather than report a false verdict.
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True, timeout=5.0)
    idx, = con.execute("select indexed_at from projects limit 1").fetchone()
    mode = "?"
    if con.execute("select count(*) from sqlite_master where type='table' and name='index_coverage_meta'").fetchone()[0]:
        r = con.execute("select index_mode from index_coverage_meta limit 1").fetchone()
        mode = r[0] if r and r[0] else "?"
    rows = con.execute("select rel_path, size, mtime_ns, sha256 from file_hashes where size > 0").fetchall()
    nodes, = con.execute("select count(*) from nodes").fetchone()
    idx_epoch = calendar.timegm(time.strptime(idx, "%Y-%m-%dT%H:%M:%SZ"))
    # Fail closed. `file_hashes` is an internal schema: if a tool upgrade renames
    # it, an empty result set must not read as "nothing changed" and hand back a
    # confident `fresh` on a stale graph. An index with nodes but no hash rows is
    # unreadable, not clean.
    if nodes > 0 and not rows:
        raise ValueError("file_hashes empty for a non-empty graph")
except Exception:
    print("unknown|?|0|0|0|0|")
    raise SystemExit(0)

changed = missing = 0
seen = set()
for rel, size, mtime_ns, sha in rows:
    seen.add(rel)
    p = os.path.join(root, rel)
    try:
        st = os.stat(p)
    except OSError:
        missing += 1
        continue
    if st.st_size != size:
        changed += 1
    elif st.st_mtime_ns != mtime_ns:
        try:
            if hashlib.sha256(open(p, "rb").read()).hexdigest() != sha:
                changed += 1
        except OSError:
            changed += 1

exts = {os.path.splitext(r)[1] for r in seen if os.path.splitext(r)[1]}
unindexed = 0
if exts and rows:
    # The high-water mark is the newest mtime the index actually recorded, not
    # `projects.indexed_at`: an incremental run refreshes `file_hashes` without
    # moving `indexed_at`, so the latter reads stale forever after one edit.
    high_water = max(r[2] for r in rows)
    # A file the indexer never intends to index is not a staleness signal. It
    # records those directories in `index_coverage`, and they are real: a repo
    # that excludes `docs` at the top level would otherwise report
    # "new-files-not-indexed" on every doc edit, on an index that is current.
    skipped_dirs = [d for (d,) in con.execute(
        "select rel_path from index_coverage where kind='not_indexed_dir'")]
    tracked = subprocess.run(
        ["git", "-C", root, "ls-files", "-z", "-co", "--exclude-standard"],
        capture_output=True, text=True,
    ).stdout
    for rel in tracked.split("\0"):
        if not rel or rel in seen or os.path.splitext(rel)[1] not in exts:
            continue
        if any(rel == d or rel.startswith(d + "/") for d in skipped_dirs):
            continue
        try:
            if os.stat(os.path.join(root, rel)).st_mtime_ns > high_water:
                unindexed += 1
        except OSError:
            pass

print("%s|%s|%d|%d|%d|%d|%s" % (idx, mode, changed, missing, unindexed, nodes, ",".join(sorted(exts))))
PY
)

[ -z "${ORACLE:-}" ] && { echo "state=missing reason=index-unreadable" >&2; exit 2; }
IFS='|' read -r IDX MODE CHANGED MISSING UNINDEXED NODES EXTS <<<"$ORACLE"

STATE=unknown
REASON=""
case "$IDX" in
  unknown) STATE=unknown; REASON="index-unreadable" ;;
  "")
    # Never let an unread index read as `fresh`.
    STATE=unknown; REASON="index-unreadable" ;;
  *)
    STATE=fresh
    if [ "${CHANGED:-0}" -gt 0 ]; then STATE=stale; REASON="tree-differs-from-index"
    elif [ "${MISSING:-0}" -gt 0 ]; then STATE=stale; REASON="indexed-files-deleted"
    elif [ "${UNINDEXED:-0}" -gt 0 ]; then STATE=stale; REASON="new-files-not-indexed"
    fi ;;
esac

# ── --ensure: remediate instead of report ───────────────────────────────────
# A reindex is incremental, so the useful default is "make it true", not "tell
# me it is not". Re-runs itself without --ensure, so a file the indexer declines
# to parse cannot loop.
if [ "$STATE" = stale ] && [ "$ENSURE" = 1 ]; then
  [ -x "$CBM_BIN" ] || { echo "codebase-memory-mcp not found (set CBM_BIN)" >&2; exit 2; }
  # Preserve the index's own mode: a root indexed `full` is the reference graph,
  # and reindexing it `moderate` would silently drop semantic edges.
  REINDEX_MODE="$MODE"
  case "$REINDEX_MODE" in full|moderate|fast) ;; *) REINDEX_MODE=moderate ;; esac
  "$CBM_BIN" cli index_repository --repo-path "$HERE" --mode "$REINDEX_MODE" >/dev/null 2>&1
  # `set -u` plus bash 3.2 (the macOS default) makes an empty `"${ARGS[@]}"` an
  # unbound-variable error, so the flags are joined as a plain string.
  REARGS=""
  [ "$JSON" = 1 ] && REARGS="$REARGS --json"
  [ "$PROJECT_ONLY" = 1 ] && REARGS="$REARGS --project"
  exec "$0" $REARGS
fi

[ "$PROJECT_ONLY" = 1 ] && { echo "$NAME"; exit 0; }

if [ "$JSON" = 1 ]; then
  python3 -c 'import json,sys
print(json.dumps({"state":sys.argv[1],"reason":sys.argv[2],"project":sys.argv[3],"mode":sys.argv[4],
"worktree":sys.argv[5],"branch":sys.argv[6],"changed":int(sys.argv[7]),"missing":int(sys.argv[8]),
"unindexed":int(sys.argv[9]),"nodes":int(sys.argv[10]),"indexed_at":sys.argv[11]}))' \
    "$STATE" "$REASON" "$NAME" "$MODE" "$HERE" "$BRANCH" \
    "${CHANGED:-0}" "${MISSING:-0}" "${UNINDEXED:-0}" "${NODES:-0}" "$IDX"
else
  echo "state=$STATE${REASON:+ reason=$REASON} project=$NAME mode=$MODE worktree=$HERE branch=$BRANCH changed=${CHANGED:-0} missing=${MISSING:-0} unindexed=${UNINDEXED:-0} nodes=${NODES:-0} indexed_at=$IDX"
fi

case "$STATE" in
  stale) exit 1 ;;
  unknown) exit 2 ;;
  *) exit 0 ;;
esac
