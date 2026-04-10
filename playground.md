# playground.py — Wiki Playground Generator

`genwiki/playground.py` generates configuration files and scripts for managing the
[CompGen Semantic MediaWiki Spielwiesen](https://wiki-playground.genealogy.net/) —
a set of 44 individual MediaWiki instances (one per Greek god), each running in its
own Docker container and served by Caddy.

## Overview

The `Playground` class manages a list of 44 Greek gods, each corresponding to a wiki
instance. Wikis are assigned sequential port pairs starting at `base_port` (default 9100),
stepping by 2 (`mw_port`, `sql_port`).

```
Aglaea   → ports 9100/9101
Amicitia → ports 9102/9103
...
Zeus     → ports 9186/9187
```

## CLI Usage

```bash
python -m genwiki.playground [OPTIONS]
```

| Option | Output file | Description |
|--------|-------------|-------------|
| `--index` | `/tmp/index.html` | Generate overview HTML page (fetches Wikimedia Commons thumbnails) |
| `--caddy` | `/tmp/Caddyfile` | Generate Caddy reverse-proxy config |
| `--apache` | `/tmp/playground.conf` | Generate Apache VirtualHost config |
| `--setup` | `/tmp/setup_wikis.sh` | Generate wiki setup script (uses `profiwiki`) |
| `--patch` | `/tmp/patch_wikis.sh` | Generate patch script fixing `wgServer` to `https://` |
| `--list` | stdout | Print all god names, one per line |
| `--host HOST` | — | Override hostname (default: `wiki-playground.genealogy.net`) |

Running without any option prints help and exits with code 1.

## Generated Artifacts

### `--index` → `/tmp/index.html`

Generates a 5×9 HTML grid overview page. Each cell contains:
- A link to `/<GodName>` (the wiki's Caddy entry point)
- A 105×105px thumbnail image

**Important:** The `--index` flag fetches thumbnails live from Wikimedia Commons via
`get_thumbnail_url()`, which follows HTTP redirects from `Special:FilePath` URLs and
constructs thumbnail URLs. This is intended for generating a **new** index file into
`/tmp/` for review.

**The production `/var/www/html/index.html` uses local relative image paths
(`src="images/<Name>.jpg"`) served from `/var/www/html/images/` by Caddy. Do not
overwrite it with `--index` output.**

### `--caddy` → `/tmp/Caddyfile`

Caddy configuration for `wiki-playground.genealogy.net` that:
- Serves the overview page from `/var/www/html` at `handle /`
- Reverse-proxies each `/<GodName>` path to `localhost:<mw_port>`
- Serves `/images/*` statically from `/var/www/html` (fixes [#35](https://github.com/WolfgangFahl/genwiki2024/issues/35))

### `--apache` → `/tmp/playground.conf`

Apache `VirtualHost` config with `ProxyPass`/`ProxyPassReverse` entries for all 44 wikis.

### `--setup` → `/tmp/setup_wikis.sh`

Bash script that calls `profiwiki` to create and configure each wiki container with
the assigned port pair.

### `--patch` → `/tmp/patch_wikis.sh`

Bash script that patches `LocalSettings.php` inside each running Docker container to set:
- `$wgScriptPath` → `/<GodName>`
- `$wgArticlePath` → `/<GodName>/index.php?title=$1`
- `$wgServer` → `https://<host>` (fixes [#36](https://github.com/WolfgangFahl/genwiki2024/issues/36))

This ensures MediaWiki generates correct HTTPS URLs for CSS/JS assets when running
behind the Caddy TLS terminator.

## Architecture

```
internet
   │  HTTPS
   ▼
Caddy (wiki-playground.genealogy.net)
   ├── /            → /var/www/html/index.html  (overview page)
   ├── /images/*    → /var/www/html/images/     (local god images)
   ├── /Aglaea/*    → localhost:9100             (MediaWiki container)
   ├── /Amicitia/*  → localhost:9102
   └── ...          → ...
```

Each wiki container has its `LocalSettings.php` patched so that
`$wgServer = "https://wiki-playground.genealogy.net"`, preventing mixed-content errors.

## Source

`genwiki/playground.py` — [`Playground`](genwiki/playground.py) class, `main()` entry point.
