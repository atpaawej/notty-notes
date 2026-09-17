import type { Folder, ListNotesArgs, Note, TagCount } from "../types";
import { extractTitle, makePreview } from "../utils/noteText";

const hasTauri = () => typeof window !== "undefined" && "__TAURI__" in window;

async function invoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  const { invoke } = await import("@tauri-apps/api/core");
  return invoke<T>(cmd, args);
}

/* ---------- localStorage mock (browser dev without Rust) ---------- */

const LS_KEY = "notty.mock.v1";
interface MockDb {
  folders: Folder[];
  notes: Note[];
}
function loadMock(): MockDb {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (raw) return JSON.parse(raw) as MockDb;
  } catch { /* ignore */ }
  const seed: MockDb = {
    folders: [{ id: "f1", name: "Welcome", created_at: 1 }],
    notes: [
      {
        id: "n1", folder_id: "f1", title: "Welcome to Notty",
        body: "Welcome to Notty\n\nTry #tags, pin me, search me.",
        preview: "Welcome to Notty Try #tags, pin me, search me.",
        pinned: true, locked: false, created_at: 1, updated_at: 2,
      },
    ],
  };
  localStorage.setItem(LS_KEY, JSON.stringify(seed));
  return seed;
}
function saveMock(db: MockDb) {
  localStorage.setItem(LS_KEY, JSON.stringify(db));
}
const nowSec = () => Math.floor(Date.now() / 1000);
const shortId = () => Math.random().toString(16).slice(2, 10);

function mockListNotes(a: ListNotesArgs): Note[] {
  const db = loadMock();
  let rows = [...db.notes];
  if (a.tag) {
    const re = new RegExp(`#${a.tag}\\b`, "i");
    rows = rows.filter((n) => re.test(n.body));
  }
  if (a.folder_id && a.folder_id !== "__all__") rows = rows.filter((n) => n.folder_id === a.folder_id);
  if (a.query?.trim()) {
    const toks = a.query.toLowerCase().split(/\s+/);
    rows = rows.filter((n) => toks.every((t) => (n.title + " " + n.body).toLowerCase().includes(t)));
  }
  if (a.pinned_only) rows = rows.filter((n) => n.pinned);
  rows.sort((x, y) => Number(y.pinned) - Number(x.pinned) || y.updated_at - x.updated_at);
  return rows.slice(0, 1000);
}

/* ---------- public API (same surface as SPEC §2 commands) ---------- */

export const api = {
  listFolders: async (): Promise<Folder[]> => {
    if (hasTauri()) return invoke("list_folders");
    return loadMock().folders;
  },
  createFolder: async (name: string): Promise<Folder> => {
    if (hasTauri()) return invoke("create_folder", { name });
    const db = loadMock();
    const f = { id: shortId(), name: name.trim(), created_at: nowSec() };
    db.folders.push(f); saveMock(db); return f;
  },
  renameFolder: async (id: string, name: string): Promise<void> => {
    if (hasTauri()) return invoke("rename_folder", { id, name });
    const db = loadMock();
    db.folders.find((f) => f.id === id)!.name = name; saveMock(db);
  },
  deleteFolder: async (id: string): Promise<void> => {
    if (hasTauri()) return invoke("delete_folder", { id });
    const db = loadMock();
    db.notes.forEach((n) => { if (n.folder_id === id) n.folder_id = null; });
    db.folders = db.folders.filter((f) => f.id !== id); saveMock(db);
  },
  listNotes: async (a: ListNotesArgs): Promise<Note[]> => {
    if (hasTauri()) {
      return invoke("list_notes", {
        folderId: a.folder_id ?? "__all__",
        query: a.query ?? "",
        tag: a.tag ?? null,
        pinnedOnly: a.pinned_only ?? false,
      });
    }
    return mockListNotes(a);
  },
  getNote: async (id: string): Promise<Note | null> => {
    if (hasTauri()) return invoke("get_note", { id });
    return loadMock().notes.find((n) => n.id === id) ?? null;
  },
  createNote: async (folder_id?: string): Promise<Note> => {
    if (hasTauri()) return invoke("create_note", { folderId: folder_id ?? "__all__" });
    const db = loadMock();
    const fid = folder_id === "__all__" ? null : (folder_id ?? null);
    const n: Note = { id: shortId(), folder_id: fid, title: "Untitled", body: "", preview: "Untitled", pinned: false, locked: false, created_at: nowSec(), updated_at: nowSec() };
    db.notes.push(n); saveMock(db); return n;
  },
  updateNote: async (id: string, text: string): Promise<Note> => {
    if (hasTauri()) return invoke("update_note", { id, text });
    const db = loadMock();
    const n = db.notes.find((x) => x.id === id)!;
    n.title = extractTitle(text); n.body = text; n.preview = makePreview(n.title, text); n.updated_at = nowSec();
    saveMock(db); return n;
  },
  deleteNote: async (id: string): Promise<void> => {
    if (hasTauri()) return invoke("delete_note", { id });
    const db = loadMock();
    db.notes = db.notes.filter((n) => n.id !== id); saveMock(db);
  },
  togglePin: async (id: string): Promise<boolean> => {
    if (hasTauri()) return invoke("toggle_pin", { id });
    const db = loadMock();
    const n = db.notes.find((x) => x.id === id)!; n.pinned = !n.pinned; saveMock(db); return n.pinned;
  },
  toggleLock: async (id: string): Promise<boolean> => {
    if (hasTauri()) return invoke("toggle_lock", { id });
    const db = loadMock();
    const n = db.notes.find((x) => x.id === id)!; n.locked = !n.locked; saveMock(db); return n.locked;
  },
  listTags: async (): Promise<TagCount[]> => {
    if (hasTauri()) return invoke("list_tags");
    const counts = new Map<string, number>();
    for (const m of loadMock().notes.flatMap((n) => n.body.match(/#(\w+)/g) ?? [])) {
      const t = m.slice(1).toLowerCase();
      counts.set(t, (counts.get(t) ?? 0) + 1);
    }
    return [...counts.entries()].map(([tag, count]) => ({ tag, count })).sort((a, b) => b.count - a.count);
  },
};
