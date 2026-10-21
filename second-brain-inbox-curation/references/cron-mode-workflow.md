# Cron-Mode Workflow for Inbox Curation

When running as a scheduled cron job (no user present), tool availability is restricted.

## Key Constraint: code execution may be blocked

In cron mode, a Python subprocess tool (execute_code) can be denied by policy. You CANNOT:
- batch many page writes into one Python script
- loop over pages programmatically in a single call
- shell out to a file-moving helper

## What works
- direct API calls with `curl` (`nb` helper) - one request per call
- reading a page body into a file, then POSTing that file's contents
- `skill_view`, `skill_manage` - skill management
- reading files

## Pattern: sequential calls

Instead of batching in Python, break the work into sequential calls:

```
1. nb POST ... /query        -> list the untriaged rows
2. nb GET  /v1/pages/{id}     -> read one row
3. nb POST /v1/pages          -> create the destination row
4. nb PATCH /v1/pages/{id}    -> retire the inbox row
5. repeat for the next row
```

Slower, but it works within cron constraints.

## Rate limiting is not optional

The Notion API allows **3 requests/second**. In a cron run you will do dozens of writes:

- sleep ~350 ms between calls (`sleep 0.35`) or batch reads and space the writes
- on `429`, honour the `Retry-After` header and back off exponentially
- never fire a tight loop of PATCHes

## Keep the run idempotent

Cron jobs get re-run. Before writing, check the destination rows (search the Notes/Decisions data
source for the title and the Source URL). If a destination row already exists, update it instead of
creating a second one. Set the Inbox row's Status to `Processing` as you start so a re-run can see
what was in flight.

## No git workflow

The vault is not a git repo any more. There is nothing to commit and nothing to push for
curation runs. (The second-brain *skills* repo is still versioned, but vault content is not in it.)
