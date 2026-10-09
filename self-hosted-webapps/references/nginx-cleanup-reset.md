# Nginx Cleanup & Reset to Defaults

When cleaning up a server that has accumulated stale nginx site configs
(e.g., after deleting projects, migrating services, or re-architecting).

## Stale Files in ~/

Sometimes loose nginx config files (.conf) are left in the home
directory after projects are deleted. These aren't linked by `/etc/nginx`
but clutter the filesystem:

```bash
find ~ -maxdepth 2 -name "*nginx*" 2>/dev/null | grep -v node_modules
find ~ -maxdepth 2 -name "*myshop*" 2>/dev/null | grep -v node_modules
```

Delete with `rm -v` and confirm with a re-scan.

## Remove a Stale Site Config

### 1. Remove symlink from sites-enabled

```bash
sudo rm /etc/nginx/sites-enabled/stale-site.conf
```

If the target file in `sites-available/` is also stale:

```bash
sudo rm /etc/nginx/sites-available/stale-site.conf
```

### 2. Test and reload

```bash
sudo nginx -t              # must pass
sudo systemctl reload nginx
```

### 3. Check for orphaned references

After removing site configs, check the global nginx.conf for stale
`include` directives:

```bash
grep -r "myshop\|example.com\|example-app\|webui" /etc/nginx/ 2>/dev/null
```

## Reset Global nginx.conf to Clean Defaults

When the `nginx.conf` has accumulated commented-out blocks, old
includes, or experimental directives.

### 1. Backup the current config

```bash
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak.$(date +%Y%m%d_%H%M%S)
```

### 2. Write stock Ubuntu nginx.conf

Minimal, clean config (Ubuntu-style):

```nginx
user www-data;
worker_processes auto;
pid /run/nginx.pid;
error_log /var/log/nginx/error.log;

events {
	worker_connections 768;
}

http {
	sendfile on;
	tcp_nopush on;
	types_hash_max_size 2048;

	include /etc/nginx/mime.types;
	default_type application/octet-stream;

	ssl_protocols TLSv1.2 TLSv1.3;
	ssl_prefer_server_ciphers on;

	access_log /var/log/nginx/access.log;

	gzip on;

	include /etc/nginx/conf.d/*.conf;
	include /etc/nginx/sites-enabled/*;
}
```

### 3. Validate and reload

```bash
sudo nginx -t
sudo systemctl reload nginx       # zero-downtime
sudo systemctl status nginx       # confirm running
```

## Dangling Symlink Gotcha

A symlink in `sites-enabled/` pointing to a deleted file will cause
`nginx -t` to fail:

```
[emerg] open() "/etc/nginx/sites-enabled/ghost.conf" failed (2: No such file or directory)
```

Fix:

```bash
sudo rm /etc/nginx/sites-enabled/ghost.conf
sudo nginx -t && sudo systemctl reload nginx
```

## Pitfalls

- **Don't use `systemctl restart nginx` for config changes** — use
  `reload` (zero-downtime). Restart is only for binary/package updates.
- **Always `sudo nginx -t` before reloading** — a broken config makes
  the reload fail silently, leaving the old config running.
- **Check for broken includes** in nginx.conf after removing site
  configs that were referenced by `include` directives.
- **Backup before reset** — a small typo in nginx.conf can take the
  whole server offline. Always backup first.
