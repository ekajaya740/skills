# Code Quality Patterns for Retrospectives

Common patterns to look for when analyzing a Laravel/PHP codebase. Each pattern includes the signal, the severity, and the recommended fix.

## Architecture & Organization

### Monolithic Controller
- **Signal:** Controller method >100 lines or file >300 lines
- **Severity:** High
- **What to check:** Does the method handle validation, business logic, image uploads, AND nested relation creation?
- **Fix:** Extract to Service classes or Action classes. Controllers should only orchestrate.

### Mixed Concerns in One Method
- **Signal:** A single method queries 5+ models, makes HTTP calls, builds SEO data, and returns a view
- **Severity:** Medium
- **What to check:** `NewHomeController@index` pattern — homepage data aggregation
- **Fix:** Use View Composers, Service classes, or lazy-loaded view data

### Inline Validation vs Form Requests
- **Signal:** `$request->validate([...])` in controller methods instead of dedicated Form Request classes
- **Severity:** Medium
- **What to check:** Are there any Form Requests already in the project? If some exist but others don't, it's inconsistent.
- **Fix:** Extract validation rules into Form Request classes for reusability and testability

## Code Quality

### Debug Artifacts in Production
- **Signal:** `error_log()`, `dd()`, `var_dump()`, `print_r()`, `Log::info()` used for debugging
- **Severity:** High
- **What to check:** Search for these functions across the codebase
- **Fix:** Remove before committing. Use proper logging with context for production.

### Commented-Out Code
- **Signal:** Commented routes, commented method bodies, commented email addresses
- **Severity:** Medium
- **What to check:** Routes files, job files, controller files
- **Fix:** Remove dead code. Git history preserves it if needed later.

### Slug Generation Bug
- **Signal:** `pluck()` returns a Collection, but code treats it as a single model
- **Severity:** High (runtime error)
- **What to check:** `ProductController` JP slug assignment — `$productSlug->slug` on a Collection
- **Fix:** Use `value()` instead of `pluck()` for single values, or access `->first()->slug`

## Performance

### N+1 Queries
- **Signal:** Loading a collection then iterating to access relationships without eager loading
- **Severity:** Medium
- **What to check:** Loops that access `$item->relation` inside a `->map()` or `foreach`
- **Fix:** Use `->with('relation')` on the query builder

### External API Calls in Request Path
- **Signal:** HTTP calls to external services during page load
- **Severity:** Medium
- **What to check:** `Http::get()` or `Http::post()` in controller methods
- **Fix:** Cache aggressively, use queue jobs for non-critical data, or lazy-load via AJAX

### No Eager Loading on Homepage
- **Signal:** Homepage controller loads 8+ models in one request
- **Severity:** Medium
- **What to check:** Count the number of `Model::where()` / `Model::all()` calls in a single action
- **Fix:** Consolidate queries, use caching, or defer non-critical sections

## Testing

### Zero Test Coverage
- **Signal:** Test directory contains only Laravel scaffold tests
- **Severity:** High
- **What to check:** `tests/` directory — are there any custom test files?
- **Fix:** Start with integration tests for critical business flows (booking, email, CRUD)

## Commit Hygiene

### Mixed-Type Commits
- **Signal:** `mix:` prefix or `feat` + `fix` in the same commit message
- **Severity:** Low
- **What to check:** `git log --format="%h %s"` for patterns
- **Fix:** One concern per commit. If it's both a feature and a fix, split into two commits.

### Overly Broad Commits
- **Signal:** Single commit touching 15+ files across controllers, models, views, migrations, and config
- **Severity:** Low
- **What to check:** `git show --stat <hash>` for file count
- **Fix:** Commit related changes together, unrelated changes separately

### `hotfix:` Overuse
- **Signal:** `hotfix:` prefix used for routine fixes, CSS tweaks, and minor changes
- **Severity:** Low
- **What to check:** Count of `hotfix:` vs `fix:` commits
- **Fix:** Reserve `hotfix:` for production-critical patches. Use `fix:` for normal fixes.
