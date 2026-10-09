# Python Venv Path Fixes

When moving a Python project (rename directory, migrate server, or change absolute path), the virtualenv contains hardcoded absolute paths in:

- All files in `venv/bin/` (shebang lines pointing to old `venv/bin/python`)
- `venv/bin/activate` (`VIRTUAL_ENV=/old/path/...`)
- `venv/bin/activate.csh`
- `venv/bin/activate.fish`
- `venv/pyvenv.cfg` (`command = /old/path/...`)

## Fix: Delete and Recreate

The cleanest approach when the directory path changes:

```bash
# 1. Stop any running server using the venv
pgrep -f "uvicorn.*main:app" | xargs kill -TERM

# 2. Delete the old venv
rm -rf /old/path/api/venv

# 3. Rename/move the directory
mv /old/path /new/path

# 4. Recreate venv in new location
cd /new/path/api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Start the server
cd /new/path/api && uvicorn main:app --host 127.0.0.1 --port 8000
```

## Alternative: Fix Shebangs In-Place

If deleting is not an option (takes too long to reinstall, or has compiled packages):

```bash
cd /new/path/api/venv/bin
sed -i "s|/old/path|/new/path|g" *
sed -i "s|/old/path|/new/path|g" ../pyvenv.cfg
```

Then fix `activate` scripts:
```bash
sed -i "s|VIRTUAL_ENV=/old/path|VIRTUAL_ENV=/new/path|g" activate activate.csh activate.fish
```

## Warning Signs

- `ModuleNotFoundError` after moving a project that was working
- Server starts but uses wrong/old environment
- `which python` inside venv shows a non-existent path

## Prevention

Use `python3 -m venv venv --system-site-packages` only if you truly need system packages. Otherwise, the standard recreation approach is reliable and fast enough for most cases.
