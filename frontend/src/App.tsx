import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api/tauri";
import type { Folder, Note, TagCount } from "./types";
import { formatEdited, wordCount } from "./utils/noteText";
import NoteEditor from "./components/NoteEditor";
import "./styles.css";

export default function App() {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [notes, setNotes] = useState<Note[]>([]);
  const [tags, setTags] = useState<TagCount[]>([]);
  const [folder, setFolder] = useState("__all__");
  const [query, setQuery] = useState("");
  const [tag, setTag] = useState<string | null>(null);
  const [pinnedOnly, setPinnedOnly] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [current, setCurrent] = useState<Note | null>(null);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const refresh = useCallback(async () => {
    const [f, n, t] = await Promise.all([
      api.listFolders(),
      api.listNotes({ folder_id: folder, query, tag, pinned_only: pinnedOnly }),
      api.listTags(),
    ]);
    setFolders(f); setNotes(n); setTags(t);
  }, [folder, query, tag, pinnedOnly]);

  useEffect(() => { refresh(); }, [refresh]);

  const openNote = async (id: string | null) => {
    flush();
    setSelected(id);
    if (!id) { setText(""); setCurrent(null); return; }
    const n = await api.getNote(id);
    setCurrent(n);
    setText(n && !n.locked ? (n.body || "") : "");
  };

  const flush = () => {
    if (saveTimer.current) { clearTimeout(saveTimer.current); saveTimer.current = null; }
  };

  const onChange = (t: string) => {
    setText(t);
    if (!selected) return;
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(async () => {
      const n = await api.updateNote(selected, t);
      setCurrent(n);
      refresh();
    }, 350);
  };

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "n") { e.preventDefault(); newNote(); }
      if ((e.ctrlKey || e.metaKey) && e.key === "f") { e.preventDefault(); document.getElementById("notty-search")?.focus(); }
      if (e.key === "Escape") openNote(null);
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [folder, selected, text]);

  const newNote = async () => {
    flush();
    const n = await api.createNote(folder);
    await refresh();
    openNote(n.id);
  };

  const deleteCurrent = async () => {
    if (!selected) return;
    await api.deleteNote(selected);
    setSelected(null); setText(""); setCurrent(null);
    refresh();
  };

  return (
    <div className="notty-root">
      <header className="notty-header">
        <div className="notty-wordmark">Notty</div>
        <div className="notty-header-actions">
          <button className="pill suggested" onClick={newNote} title="Create new note (Ctrl+N)">+ New Note</button>
          <button className="pill" disabled={!selected} onClick={deleteCurrent} title="Delete note">🗑</button>
        </div>
      </header>
      <div className="notty-panes">
        <aside className="notty-sidebar">
          <div className="notty-section">FOLDERS</div>
          <button className={folder === "__all__" ? "row selected" : "row"} onClick={() => setFolder("__all__")}>All Notes</button>
          {folders.map((f) => (
            <button key={f.id} className={folder === f.id ? "row selected" : "row"} onClick={() => setFolder(f.id)}>{f.name}</button>
          ))}
          <button
            className="row new"
            onClick={async () => {
              const name = prompt("Folder name:");
              if (name?.trim()) { await api.createFolder(name.trim()); refresh(); }
            }}
          >+ New folder</button>
          <div className="notty-section">TAGS</div>
          <div className="tag-list">
            {tags.map((t) => (
              <button key={t.tag} className={tag === t.tag ? "tag-pill selected" : "tag-pill"} onClick={() => setTag(tag === t.tag ? null : t.tag)}>
                #{t.tag} <span>{t.count}</span>
              </button>
            ))}
          </div>
        </aside>
        <section className="notty-list">
          <div className="notty-search">
            <input id="notty-search" placeholder="Search…" value={query} onChange={(e) => setQuery(e.target.value)} />
            <label><input type="checkbox" checked={pinnedOnly} onChange={(e) => setPinnedOnly(e.target.checked)} /> Pinned</label>
          </div>
          <div className="notty-section">{notes.length} NOTES</div>
          {notes.map((n) => (
            <button key={n.id} className={selected === n.id ? "note-row selected" : "note-row"} onClick={() => openNote(n.id)}>
              <div className="note-title">{n.locked ? "🔒 Locked" : n.title || "Untitled"}{n.pinned ? " 📌" : ""}</div>
              <div className="note-preview">{n.locked ? "" : n.preview}</div>
            </button>
          ))}
          {notes.length === 0 && (
            <div className="notty-empty">
              <div className="title">No notes</div>
              <button className="notty-empty-cta" onClick={() => { setQuery(""); setTag(null); }}>Clear filters</button>
            </div>
          )}
        </section>
        <main className="notty-main">
          <NoteEditor
            noteId={selected}
            initialText={text}
            locked={!!current?.locked}
            onUnlock={async () => { if (selected) { await api.toggleLock(selected); const n = await api.getNote(selected); setCurrent(n); setText(n?.body ?? ""); refresh(); } }}
            onChange={onChange}
          />
          <footer className="notty-footer">
            <span>{current ? formatEdited(current.updated_at) : ""}</span>
            <span>{text ? `${wordCount(text)} words` : "Empty note"}</span>
            {current && (
              <>
                <button onClick={async () => { const v = await api.togglePin(current.id); setCurrent({ ...current, pinned: v }); refresh(); }}>
                  {current.pinned ? "Unpin" : "Pin"}
                </button>
                <button onClick={async () => { const v = await api.toggleLock(current.id); const n = await api.getNote(current.id); setCurrent(n ? { ...n, locked: v } : n); if (v) setText(""); refresh(); }}>
                  {current.locked ? "Unlock" : "Lock"}
                </button>
              </>
            )}
          </footer>
        </main>
      </div>
    </div>
  );
}
