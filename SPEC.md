# Notty Tauri+React Port — SPEC (Option B)

Source: `src/notty/` (Python + GTK4 + Libadwaita, ~1888 LOC, SQLite FTS5).
Target: Tauri v2 + React 18 + Vite + TypeScript, Ubuntu-first.
Constraint: **100% `notes.db` compatible** — same path, same schema, zero migration.

## 1. DB contract (must not change)

- Path: `$XDG_DATA_HOME/notty/notes.db` (fallback `~/.local/share/notty/notes.db`), `NOTTY_DB` env override for tests.
- Pragmas: `journal_mode=WAL`, `synchronous=NORMAL`, `cache_size=-16000`, `temp_store=MEMORY`, `foreign_keys=ON`.
- Tables: `folders(id TEXT PK, name UNIQUE, created_at INT)`, `notes(id PK, folder_id FK→SET NULL, title, body, preview, pinned INT, locked INT, created_at, updated_at)`, `tags(note_id FK CASCADE, tag, PK(note_id,tag))`, `notes_fts` virtual FTS5 `(title, body, tags, content='notes', content_rowid='rowid', tokenize='unicode61')` + 5 sync triggers (`trg_notes_ai/ad/au`, `trg_tags_ai/ad`).
- Special row: `folders('__all__','All Notes',0)` always present (not listed).
- Business rules (port verbatim from `shared/db.py`):
  - `preview = (body[:120].replace("\n"," ") or title[:120]) or "Untitled"`.
  - Tags derived from body via `#(\w+)` regex, lowercased, resynced on every create/update (`DELETE + INSERT OR IGNORE`).
  - `list_notes(folder_id, query, tag, pinned_only, limit=1000)`: FTS path when `query.strip()` non-empty — `q = ' '.join(f'"{w}"*' for w in query.split())`, `SELECT n.* FROM notes_fts f JOIN notes n ON n.rowid=f.rowid WHERE notes_fts MATCH ? [+tag/folder/pinned filters] ORDER BY n.pinned DESC, n.updated_at DESC LIMIT ?`, malformed FTS → return `[]` (never crash). Non-FTS path: `SELECT * FROM notes WHERE 1=1 [+filters] ORDER BY pinned DESC, updated_at DESC LIMIT ?`.
  - Title extraction (from `features/editor/controller.py`): first non-empty line, trimmed, max 80 chars, fallback `"Untitled"`.
  - Debounce: 350ms trailing-edge save (frontend), `flush_now` on note switch/close.
  - Sort everywhere: `pinned DESC, updated_at DESC`, index `idx_notes_pinned`.

## 2. Tauri commands (Rust backend, `rusqlite` + `bundled` FTS5)

State: `Mutex<Connection>` single-writer (mirrors `Db._lock: RLock`).

| Command | Args | Returns | Maps to |
|---|---|---|---|
| `list_folders` | – | `Vec<Folder{id,name,created_at}>` (excl `__all__`, `ORDER BY created_at`) | `Db.list_folders` |
| `create_folder` | `name: String` | `Folder` (id=`uuid hex[..8]`, ts=`now()`) | `FoldersStore.create` |
| `rename_folder` | `id, name` | `()` | `Db.rename_folder` |
| `delete_folder` | `id` | `()` (nulls child notes first) | `Db.delete_folder` |
| `list_notes` | `folder_id?: String, query?: String, tag?: String, pinned_only?: bool, limit?: i64` | `Vec<Note>` | `Db.list_notes` |
| `get_note` | `id` | `Note \| null` | `Db.get_note` |
| `create_note` | `folder_id?: String` | `Note` (title `"Untitled"`, empty body) | `NottyApp.create_note` |
| `update_note` | `id, text: String, folder_id?: String` | `Note` (extract title server-side, recompute preview+tags) | `EditorController.request_save` + flush |
| `delete_note` | `id` | `()` | `Db.delete_note` |
| `toggle_pin` | `id` | `pinned: bool` | `Db.toggle_pin` |
| `toggle_lock` | `id` | `locked: bool` | `Db.toggle_lock` |
| `list_tags` | – | `Vec<{tag,count}> ORDER BY count DESC` | `Db.list_tags` |

`Note{id, folder_id?, title, body, preview, pinned: bool, locked: bool, created_at, updated_at}` — ints `0/1` on the wire map to bool in TS.

## 3. Frontend (React + TS, `frontend/`)

- Layout: 3 panes mirroring `app.py build_ui()`: left sidebar 240px (folders + tag browser), middle 320px (search on top + notes list), right flex (TipTap editor + footer `Edited %b %d, %H:%M • N words • pin/lock`).
- Styling: port `data/style.css` to CSS variables; light/dark via `prefers-color-scheme` (no GSettings dependency; persist window/pane prefs to `localStorage`).
- Behavior parity: `Ctrl+N` new, `Ctrl+F` focus search, `Ctrl+Delete/Backspace` delete, `Esc` deselect; locked note shows locked placeholder (never render body); debounce 350ms; word count; header `New Note` + delete button (disabled when nothing selected); empty/filtered-empty states with CTA.
- Editor: TipTap (`@tiptap/react`, `starter-kit`, `placeholder`, `task-list`, `code-block-lowlight`) storing **plain text** (`editor.getText()`) as `body` for DB compat; title = first line. Tables + code blocks enabled (the reason for this port) but serialized back to text.
- API layer: `frontend/src/api/tauri.ts` wrapping `@tauri-apps/api/core` `invoke` with the 12 commands above; **dev fallback**: when `window.__TAURI__` is absent (browser/`vite dev`), use a `localStorage`-backed mock implementing the same interface so UI is testable without Rust.

## 4. Packaging & compat

- `src-tauri/tauri.conf.json`: app id `app.notty.Notty`, product `Notty`, data dir maps to existing `notes.db` (no import step — open in place).
- `.deb` via `tauri build --bundles deb`; Flatpak documented as freshly-written manifest (webview runtime differs from current `flatpak/app.notty.Notty.json` GNOME 47).
- Tests: frontend `vitest` for title/preview/tag-query builders; Rust `cargo test` for FTS prefix + tag sync; manual checklist: CRUD, folder move, FTS prefix, `#tag` filter, pin/lock, debounce, restart persistence against a real `notes.db` copied from the Python app.
- Out of scope: GSettings, GNOME Search provider, Syncthing conflict UI, AES per-note lock, Apple Notes import (roadmap, unchanged).

## 5. Acceptance

1. Point at existing `~/.local/share/notty/notes.db` — all notes/folders/tags appear, FTS search identical results to Python build.
2. 350ms debounce saves; switching notes flushes; restart persists.
3. Locked notes never leak body to renderer before unlock.
4. `npm run build` (frontend) + `cargo check` (backend) green; `.deb` installs and launches on Ubuntu 24.04.
