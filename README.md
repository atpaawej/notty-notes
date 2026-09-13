# Notty — Native notes for Ubuntu

macOS Notes UX, GTK4 + Libadwaita, Python, SQLite FTS5. Lightweight, local-first, VSA extensible.

## Stack
Python + GTK4 + Libadwaita + GtkSourceView + SQLite FTS5 + Meson + Flatpak

## Quick start (Ubuntu 24.04+)
```bash
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-gtksource-5 meson
python3 -m notty            # dev run (needs display)
python3 -m notty --headless # verify without display
```

## Project layout (Vertical Slice Architecture)
Each feature in `src/notty/features/<slice>/` has its own store+view+repo. Add a slice = add a folder, no core changes. See `docs/VSA.md`.

## E2E tests (real user via dogtail/AT-SPI)
```bash
python3 -m pytest tests/e2e -v   # headless logic fallback when no Xvfb
xvfb-run -a python3 -m pytest tests/e2e -v  # full AT-SPI when dogtail installed
```

## Performance
- WAL + synchronous=NORMAL + FTS5 prefix match => <50ms on 10k notes
- Debounced 350ms save, prepared stmts, single writer lock
- Gio.ListStore recycled factories, no in-memory filtering
