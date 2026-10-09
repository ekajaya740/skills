# Postgres Role Creation and Grant Recipes

Common Postgres auth setup for local MCP servers and web apps.

## Create Role with Password

```bash
sudo -u postgres psql -c "CREATE ROLE ubuntu WITH LOGIN PASSWORD 'yourpass';"
```

If the role already exists, alter it:
```bash
sudo -u postgres psql -c "ALTER ROLE ubuntu WITH LOGIN PASSWORD 'yourpass';"
```

## Create Database

```bash
sudo -u postgres psql -c "CREATE DATABASE myapp;"
```

## Full Grant Sequence

Run all four — creating DB alone is not enough:

```bash
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE myapp TO ubuntu;"
sudo -u postgres psql -d myapp -c "GRANT ALL ON SCHEMA public TO ubuntu;"
sudo -u postgres psql -d myapp -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ubuntu;"
```

## Connection URL Format

```
postgresql://ubuntu:yourpass@localhost/myapp
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `InvalidPasswordError` | Role has no password or wrong password | `ALTER ROLE ... PASSWORD` |
| `permission denied for schema public` | Missing schema grant | `GRANT ALL ON SCHEMA public` |
| `permission denied for relation habits` | Table created before default privileges | `GRANT ALL ON ALL TABLES IN SCHEMA public` |
