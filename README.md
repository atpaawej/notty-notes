# Notty — Native notes for Ubuntu

[![Release](https://img.shields.io/github/v/release/atpaawej/notty-notes?label=latest%20release)](https://github.com/atpaawej/notty-notes/releases/latest) [![Downloads](https://img.shields.io/github/downloads/atpaawej/notty-notes/total)](https://github.com/atpaawej/notty-notes/releases) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

macOS Notes UX for Ubuntu — **GTK4 + Libadwaita**, **Python**, **SQLite FTS5**. Lightweight, local-first, fast search, Vertical Slice Architecture.

## Install

### 1. One-liner (recommended) — curl | bash

```bash
curl -fsSL https://raw.githubusercontent.com/atpaawej/notty-notes/master/install.sh | bash
```

Installs deps (`gir1.2-gtk-4.0`, `gir1.2-adw-1`, `gir1.2-gtksource-5`) then downloads the `.deb` from Releases and runs `dpkg -i`. Needs `sudo`.

### 2. Download .deb directly

Latest `.deb` is on the **Releases page**: https://github.com/atpaawej/notty-notes/releases/latest

```bash
# v0.1.0 — 12K, all arch
wget https://github.com/atpaawej/notty-notes/releases/download/v0.1.0/notty_0.1.0_all.deb
sudo apt update
sudo apt install -y ./notty_0.1.0_all.deb
# or
sudo dpkg -i notty_0.1.0_all.deb; sudo apt-get install -f -y
```

Verify:
```bash
notty --headless   # headless check, should print "headless ok [...]"
notty              # launch native 3-pane UI (requires display)
```

Uninstall: `sudo apt remove notty && sudo apt autoremove`

> **Releases:** All versions + `.deb` assets at https://github.com/atpaawej/notty-notes/releases

### 3. From source (dev)

```bash
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-gtksource-5 meson git
git clone https://github.com/atpaawej/notty-notes.git
cd notty-notes
PYTHONPATH=src python3 -m notty            # dev run (needs display)
PYTHONPATH=src python3 -m notty --headless # verify without display
```

## Features

- **3-pane macOS style:** Folders sidebar | Notes list | Editor
- **Pinned, Tags `#tag`, Search (FTS5 prefix), Locked notes**
- **Rich editor:** Headings, Bold/Italic, Bullets, Checklists, Monospace, Quote, Image drop
- **Local-first:** Single `~/.local/share/notty/notes.db`, WAL, Offline, Syncthing-ready (no cloud lock-in)
- **Native:** Libadwaita light/dark auto, GNOME Search, fast startup ~0.4s

## Stack

Python + GTK4 + Libadwaita + GtkSourceView + SQLite FTS5 + Meson + Flatpak

## Project layout (Vertical Slice Architecture)

Each feature in `src/notty/features/<slice>/` owns its `store+view+repo+model`. Add a slice = add a folder, no core changes.

```
src/notty/shared/db.py              # WAL + FTS5 + single-writer
src/notty/features/folders/         # sidebar
src/notty/features/notes_list/      # middle pane filtered via SQL
src/notty/features/editor/          # GtkSourceView + 350ms debounce
src/notty/features/tags|search|pin_lock/
tests/e2e/harness/app_driver.py     # headless + dogtail AT-SPI driver
```

## E2E tests (real user via dogtail/AT-SPI, no unit tests)

```bash
PYTHONPATH=src python -m pytest tests/e2e -v              # headless logic fallback when no Xvfb
xvfb-run -a PYTHONPATH=src python -m pytest tests/e2e -v  # full AT-SPI when dogtail installed
```

Covers: CRUD, folders drag, search+tags FTS, pin/lock, editor debounce, persistence across restart (6 suites).

## Performance

- WAL + `synchronous=NORMAL` + `cache_size -16000` + FTS5 prefix match → <50ms on 10k notes
- Debounced 350ms save, prepared stmts, single writer lock
- `Gio.ListStore` recycled factories, DB-side sorting `pinned DESC, updated_at DESC` via `idx_notes_pinned`

## Packaging

- `.deb` built via `dpkg-deb --build` — see `dist/notty_0.1.0_all.deb`
- `install.sh` — idempotent curl installer (release asset → raw fallback → source clone)
- `flatpak/app.notty.Notty.json` — GNOME 47 runtime (Flatpak)
- `data/app.notty.Notty.gschema.xml` — GSettings (window size, pane widths)

## Roadmap

v1.5: Tables, code blocks, per-note AES lock via keyring, import Apple Notes
v2: Smart Folders, Quick Note `Super+Shift+N`, PDF inline, Nextcloud/Syncthing sync

## Contributing

PRs welcome — add a slice under `src/notty/features/<name>/`, add E2E in `tests/e2e/test_<name>_e2e.py`.

License: MIT
