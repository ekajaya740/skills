# Target: Python CLI / service

For a command-line tool, a long-running service, a scraper, or a data job. `src` layout, `uv`
for everything, ruff + type checks in CI.

Use the same layout for an API service — the only difference is the entry point and whether there
is a `Dockerfile`.

## Tree

```
.
├── AGENTS.md
├── CLAUDE.md                 # @AGENTS.md
├── .gitignore
├── .env.example
├── pyproject.toml            # metadata, deps, tool config in one file
├── uv.lock
├── README.md
├── docs/
│   ├── architecture.md
│   └── testing.md
├── src/
│   └── <package>/
│       ├── __init__.py
│       ├── __main__.py       # `python -m <package>` works
│       ├── cli.py            # arg parsing only; calls into services
│       ├── config.py         # env loading, one place, validated at startup
│       ├── models.py         # dataclasses / pydantic types
│       └── services/         # the logic; no I/O at import time
├── tests/
│   ├── conftest.py
│   └── test_<mirrors src/>
└── .github/workflows/ci.yml
```

## `pyproject.toml` shape

```toml
[project]
name = "<package>"
requires-python = ">=3.12"
dependencies = ["…"]

[project.scripts]
<name> = "<package>.cli:main"

[tool.ruff]
line-length = 100
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.pyright]
include = ["src"]
typeCheckingMode = "standard"
```

One file, all tool config. Scattered `setup.cfg` + `tox.ini` + `.flake8` is three places to
disagree.

## Green commands

```bash
uv sync                       # install
uv run ruff check src tests   # lint
uv run ruff format --check .  # format
uv run pyright                # types
uv run pytest -q              # tests
```

Put these in `AGENTS.md` with **Green when: exits 0**.

## Seams that matter

1. **Config is validated once, at startup.** `config.py` reads env into a typed object; nothing
   else calls `os.getenv`. This is the single biggest source of "works locally, dies in CI".
2. **Services take their dependencies as arguments.** A service that constructs its own client
   cannot be tested without the network.
3. **`cli.py` and the HTTP handlers are thin.** Parsing and formatting only; logic is in
   `services/`.
4. **One `conftest.py` for fixtures**, not one per test file. Duplicated fixtures drift.

## Anti-patterns

- Logic in `__init__.py` — it runs on import and breaks every future import.
- A `utils.py`. Same as TypeScript: name the concept.
- `requirements.txt` alongside `pyproject.toml`. Pick one; `uv` writes the lock.
- `sys.exit()` inside a service. The entry point owns exit codes.
- Tests that hit the real network or a real database. Use a fixture with a local container or a
  fake, and say which in `docs/testing.md`.

## When it is a service, not a CLI

Add a `Dockerfile` and a health endpoint, and keep the same layout. The deployable check changes:
`docker build` becomes a green command, and the first `curl` of the health endpoint is the first
piece of evidence under skill `verify-change`.

## Related

- Stack choices → [`../DEFAULTS.md`](../DEFAULTS.md)
- Proving a change → skill `verify-change`
