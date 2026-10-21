# Tag Audit / Cleanup

When the user asks to audit or clean up tags across the second brain, use this approach.

## Rule

Tags answer exactly two questions:
1. **Status?** - `status/active`, `status/seed`, `status/archived`, `status/evergreen`
2. **Category?** - `type/*` (18 types) + flexible categories (`confidential`, `fitness`,
   `wedding`, `daily`, `tasks`, `testing`)

Everything else gets stripped. Topics, tools, project names, muscles, body parts - all belong in
the body or in relations.

## Audit

The `Tags` property is a multi-select, so it can be queried and counted directly:

```bash
nb POST "/v1/data_sources/$NOTES_DS/query" '{"page_size":100}'
python3 - <<'PY'
import json, collections
d = json.load(open("/tmp/notes.json"))
c = collections.Counter()
for r in d["results"]:
    for t in r["properties"].get("Tags", {}).get("multi_select", []):
        c[t["name"]] += 1
for name, n in c.most_common():
    print(f"{n:5d}  {name}")
PY
```

## Cleanup

For each row whose tag set contains a value outside the keep list, PATCH the property:

```bash
nb PATCH /v1/pages/<page_id> '{"properties":{"Tags":{"multi_select":[
  {"name":"status/active"},{"name":"type/reference"}]}}}'
```

Space the calls ~350 ms apart. If the row's tags become empty, send an empty
`{"multi_select":[]}` rather than removing the property.

## Post-cleanup

1. Re-run the audit and confirm the tag vocabulary is down to the keep list.
2. Check for stray `project/*` tags - those become a `Project` relation instead:
   ```bash
   nb POST "/v1/data_sources/$NOTES_DS/query" '{"filter":{"property":"Tags","multi_select":{"contains":"project/"}}}'
   ```
   For each hit, look up the project by name (`nb POST /v1/search`) and set the `Project`
   relation, then strip the tag.
3. No reindex needed - there is no QMD, no index, no reindex step.
4. No git commit - the vault is not a git repo any more.

## Lessons learned (2026-06-28)

- Before cleanup: 176 unique tags, ~700+ instances; after: 28 unique tags, 356 instances
- Biggest offenders: project names (`project/mitsukoshi-isetan` x75), body parts/muscles, exercise
  attributes
- The `project/*` tags were replaced by relations to the project row
