//! SQLite layer — verbatim port of `src/notty/shared/db.py`.
//! Same path, pragmas, schema, triggers, business rules. Single-writer via Mutex in lib.rs.

use regex::Regex;
use rusqlite::{params, Connection, Result, Row};
use serde::Serialize;
use std::path::Path;
use std::sync::OnceLock;

pub const SCHEMA: &str = r#"
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=-16000;
PRAGMA temp_store=MEMORY;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS folders (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    folder_id TEXT REFERENCES folders(id) ON DELETE SET NULL,
    title TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    preview TEXT NOT NULL DEFAULT '',
    pinned INTEGER NOT NULL DEFAULT 0,
    locked INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notes_folder ON notes(folder_id);
CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_notes_pinned ON notes(pinned DESC, updated_at DESC);

CREATE TABLE IF NOT EXISTS tags (
    note_id TEXT REFERENCES notes(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    PRIMARY KEY(note_id, tag)
);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);

CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    title, body, tags,
    content='notes', content_rowid='rowid',
    tokenize='unicode61'
);

-- Triggers keep FTS in sync + denormalize tags string
CREATE TRIGGER IF NOT EXISTS trg_notes_ai AFTER INSERT ON notes BEGIN
  INSERT INTO notes_fts(rowid, title, body, tags) VALUES (new.rowid, new.title, new.body, '');
END;
CREATE TRIGGER IF NOT EXISTS trg_notes_ad AFTER DELETE ON notes BEGIN
  INSERT INTO notes_fts(notes_fts, rowid, title, body, tags) VALUES('delete', old.rowid, old.title, old.body, '');
END;
CREATE TRIGGER IF NOT EXISTS trg_notes_au AFTER UPDATE ON notes BEGIN
  INSERT INTO notes_fts(notes_fts, rowid, title, body, tags) VALUES('delete', old.rowid, old.title, old.body, '');
  INSERT INTO notes_fts(rowid, title, body, tags) VALUES (new.rowid, new.title, new.body, (SELECT group_concat(tag,' ') FROM tags WHERE note_id=new.id));
END;
CREATE TRIGGER IF NOT EXISTS trg_tags_ai AFTER INSERT ON tags BEGIN
  INSERT INTO notes_fts(notes_fts, rowid, title, body, tags) VALUES('delete', (SELECT rowid FROM notes WHERE id=new.note_id), '', '', '');
  INSERT INTO notes_fts(rowid, title, body, tags) VALUES ((SELECT rowid FROM notes WHERE id=new.note_id), (SELECT title FROM notes WHERE id=new.note_id), (SELECT body FROM notes WHERE id=new.note_id), (SELECT group_concat(tag,' ') FROM tags WHERE note_id=new.note_id));
END;
CREATE TRIGGER IF NOT EXISTS trg_tags_ad AFTER DELETE ON tags BEGIN
  INSERT INTO notes_fts(notes_fts, rowid, title, body, tags) VALUES('delete', (SELECT rowid FROM notes WHERE id=old.note_id), '', '', '');
  INSERT INTO notes_fts(rowid, title, body, tags) VALUES ((SELECT rowid FROM notes WHERE id=old.note_id), (SELECT title FROM notes WHERE id=old.note_id), (SELECT body FROM notes WHERE id=old.note_id), (SELECT group_concat(tag,' ') FROM tags WHERE note_id=old.note_id));
END;
"#;

fn tag_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new(r"#(\w+)").unwrap())
}

#[derive(Debug, Clone, Serialize)]
pub struct Folder {
    pub id: String,
    pub name: String,
    pub created_at: i64,
}

#[derive(Debug, Clone, Serialize)]
pub struct Note {
    pub id: String,
    pub folder_id: Option<String>,
    pub title: String,
    pub body: String,
    pub preview: String,
    pub pinned: bool,
    pub locked: bool,
    pub created_at: i64,
    pub updated_at: i64,
}

#[derive(Debug, Clone, Serialize)]
pub struct TagCount {
    pub tag: String,
    pub count: i64,
}

fn row_to_note(row: &Row) -> Result<Note> {
    Ok(Note {
        id: row.get("id")?,
        folder_id: row.get("folder_id")?,
        title: row.get("title")?,
        body: row.get("body")?,
        preview: row.get("preview")?,
        pinned: row.get::<_, i64>("pinned")? != 0,
        locked: row.get::<_, i64>("locked")? != 0,
        created_at: row.get("created_at")?,
        updated_at: row.get("updated_at")?,
    })
}

/// First line, trimmed, max 80 chars, fallback "Untitled". Mirrors `extract_title_body`.
pub fn extract_title(text: &str) -> String {
    let first = text.trim().split('\n').next().unwrap_or("").trim();
    let mut title = first.to_string();
    if title.chars().count() > 80 {
        title = title.chars().take(80).collect();
    }
    if title.is_empty() {
        "Untitled".into()
    } else {
        title
    }
}

/// `(body[:120] with \n→space or title[:120]) or "Untitled"`. Mirrors `Db.create_note`.
pub fn make_preview(title: &str, body: &str) -> String {
    let p = if body.is_empty() {
        title.chars().take(120).collect::<String>()
    } else {
        body.replace('\n', " ").chars().take(120).collect::<String>()
    };
    if p.is_empty() {
        "Untitled".into()
    } else {
        p
    }
}

pub fn open(path: &str) -> Result<Connection> {
    if path != ":memory:" {
        if let Some(parent) = Path::new(path).parent() {
            std::fs::create_dir_all(parent).ok();
        }
    }
    let conn = Connection::open(path)?;
    conn.execute_batch(SCHEMA)?;
    conn.execute(
        "INSERT OR IGNORE INTO folders(id,name,created_at) VALUES('__all__','All Notes',0)",
        [],
    )?;
    Ok(conn)
}

pub fn list_folders(conn: &Connection) -> Result<Vec<Folder>> {
    let mut stmt =
        conn.prepare("SELECT id,name,created_at FROM folders WHERE id!='__all__' ORDER BY created_at")?;
    let rows = stmt.query_map([], |row| {
        Ok(Folder {
            id: row.get(0)?,
            name: row.get(1)?,
            created_at: row.get(2)?,
        })
    })?;
    rows.collect()
}

pub fn create_folder(conn: &Connection, fid: &str, name: &str, ts: i64) -> Result<()> {
    conn.execute(
        "INSERT INTO folders(id,name,created_at) VALUES(?,?,?)",
        params![fid, name, ts],
    )?;
    Ok(())
}

pub fn rename_folder(conn: &Connection, fid: &str, name: &str) -> Result<()> {
    conn.execute("UPDATE folders SET name=? WHERE id=?", params![name, fid])?;
    Ok(())
}

pub fn delete_folder(conn: &Connection, fid: &str) -> Result<()> {
    conn.execute("UPDATE notes SET folder_id=NULL WHERE folder_id=?", params![fid])?;
    conn.execute("DELETE FROM folders WHERE id=?", params![fid])?;
    Ok(())
}

fn sync_tags(conn: &Connection, nid: &str, body: &str) -> Result<()> {
    let tags: std::collections::HashSet<String> =
        tag_re().captures_iter(body).map(|c| c[1].to_lowercase()).collect();
    conn.execute("DELETE FROM tags WHERE note_id=?", params![nid])?;
    for t in tags {
        conn.execute("INSERT OR IGNORE INTO tags(note_id,tag) VALUES(?,?)", params![nid, t])?;
    }
    Ok(())
}

pub fn create_note(
    conn: &Connection,
    nid: &str,
    folder_id: Option<&str>,
    title: &str,
    body: &str,
    ts: i64,
) -> Result<Note> {
    let preview = make_preview(title, body);
    conn.execute(
        "INSERT INTO notes(id,folder_id,title,body,preview,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
        params![nid, folder_id, title, body, preview, ts, ts],
    )?;
    sync_tags(conn, nid, body)?;
    get_note(conn, nid)?.ok_or(rusqlite::Error::QueryReturnedNoRows)
}

pub fn update_note(
    conn: &Connection,
    nid: &str,
    title: &str,
    body: &str,
    ts: i64,
    folder_id: Option<Option<&str>>,
) -> Result<Option<Note>> {
    let preview = make_preview(title, body);
    match folder_id {
        Some(fid) => conn.execute(
            "UPDATE notes SET title=?,body=?,preview=?,updated_at=?,folder_id=? WHERE id=?",
            params![title, body, preview, ts, fid, nid],
        )?,
        None => conn.execute(
            "UPDATE notes SET title=?,body=?,preview=?,updated_at=? WHERE id=?",
            params![title, body, preview, ts, nid],
        )?,
    };
    sync_tags(conn, nid, body)?;
    Ok(get_note(conn, nid)?)
}

pub fn toggle_pin(conn: &Connection, nid: &str) -> Result<bool> {
    let cur: Option<i64> =
        conn.query_row("SELECT pinned FROM notes WHERE id=?", params![nid], |r| r.get(0)).ok();
    match cur {
        None => Ok(false),
        Some(v) => {
            let nv = if v != 0 { 0 } else { 1 };
            conn.execute("UPDATE notes SET pinned=? WHERE id=?", params![nv, nid])?;
            Ok(nv != 0)
        }
    }
}

pub fn toggle_lock(conn: &Connection, nid: &str) -> Result<bool> {
    let cur: Option<i64> =
        conn.query_row("SELECT locked FROM notes WHERE id=?", params![nid], |r| r.get(0)).ok();
    let nv = match cur {
        Some(v) if v != 0 => 0,
        _ => 1,
    };
    conn.execute("UPDATE notes SET locked=? WHERE id=?", params![nv, nid])?;
    Ok(nv != 0)
}

pub fn delete_note(conn: &Connection, nid: &str) -> Result<()> {
    conn.execute("DELETE FROM notes WHERE id=?", params![nid])?;
    Ok(())
}

pub fn get_note(conn: &Connection, nid: &str) -> Result<Option<Note>> {
    let mut stmt = conn.prepare("SELECT * FROM notes WHERE id=?")?;
    let mut rows = stmt.query_map(params![nid], row_to_note)?;
    Ok(rows.next().transpose()?)
}

/// FTS prefix query builder. Mirrors `Db.list_notes`: `"word"*` per token, `[]` on malformed.
pub fn build_fts_query(query: &str) -> String {
    query.split_whitespace().filter(|w| !w.is_empty()).map(|w| format!("\"{}\"*", w.replace('"', ""))).collect::<Vec<_>>().join(" ")
}

pub struct NoteFilter<'a> {
    pub folder_id: Option<&'a str>,
    pub query: &'a str,
    pub tag: Option<&'a str>,
    pub pinned_only: bool,
    pub limit: i64,
}

pub fn list_notes(conn: &Connection, f: NoteFilter) -> Result<Vec<Note>> {
    if !f.query.trim().is_empty() {
        let q = build_fts_query(f.query);
        let mut sql = String::from(
            "SELECT n.* FROM notes_fts f JOIN notes n ON n.rowid=f.rowid WHERE notes_fts MATCH ?",
        );
        let mut args: Vec<Box<dyn rusqlite::ToSql>> = vec![Box::new(q)];
        if let Some(tag) = f.tag {
            sql.push_str(" AND n.id IN (SELECT note_id FROM tags WHERE tag=?)");
            args.push(Box::new(tag.to_lowercase()));
        }
        if let Some(fid) = f.folder_id {
            if fid != "__all__" {
                sql.push_str(" AND n.folder_id=?");
                args.push(Box::new(fid.to_string()));
            }
        }
        if f.pinned_only {
            sql.push_str(" AND n.pinned=1");
        }
        sql.push_str(" ORDER BY n.pinned DESC, n.updated_at DESC LIMIT ?");
        args.push(Box::new(f.limit));
        let mut stmt = conn.prepare(&sql)?;
        let params_ref: Vec<&dyn rusqlite::ToSql> = args.iter().map(|b| b.as_ref()).collect();
        match stmt.query_map(params_ref.as_slice(), row_to_note) {
            Ok(rows) => rows.collect(),
            Err(_) => Ok(vec![]), // malformed FTS query → empty, don't crash
        }
    } else {
        let mut sql = String::from("SELECT * FROM notes WHERE 1=1");
        let mut args: Vec<Box<dyn rusqlite::ToSql>> = vec![];
        if let Some(tag) = f.tag {
            sql.push_str(" AND id IN (SELECT note_id FROM tags WHERE tag=?)");
            args.push(Box::new(tag.to_lowercase()));
        }
        if let Some(fid) = f.folder_id {
            if fid != "__all__" {
                sql.push_str(" AND folder_id=?");
                args.push(Box::new(fid.to_string()));
            }
        }
        if f.pinned_only {
            sql.push_str(" AND pinned=1");
        }
        sql.push_str(" ORDER BY pinned DESC, updated_at DESC LIMIT ?");
        args.push(Box::new(f.limit));
        let mut stmt = conn.prepare(&sql)?;
        let params_ref: Vec<&dyn rusqlite::ToSql> = args.iter().map(|b| b.as_ref()).collect();
        let rows = stmt.query_map(params_ref.as_slice(), row_to_note)?;
        rows.collect()
    }
}

pub fn list_tags(conn: &Connection) -> Result<Vec<TagCount>> {
    let mut stmt = conn.prepare("SELECT tag, count(*) c FROM tags GROUP BY tag ORDER BY c DESC")?;
    let rows = stmt.query_map([], |row| Ok(TagCount { tag: row.get(0)?, count: row.get(1)? }))?;
    rows.collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn mem() -> Connection {
        open(":memory:").unwrap()
    }

    #[test]
    fn crud_and_preview_title() {
        let c = mem();
        create_note(&c, "n1", None, "Untitled", "Hello #World", 100).unwrap();
        let n = get_note(&c, "n1").unwrap().unwrap();
        assert_eq!(n.preview, "Hello #World");
        assert_eq!(extract_title("My Title\nbody"), "My Title");
        assert_eq!(extract_title(""), "Untitled");
        let tags = list_tags(&c).unwrap();
        assert_eq!(tags.len(), 1);
        assert_eq!(tags[0].tag, "world");
    }

    #[test]
    fn fts_prefix_and_malformed_never_crashes() {
        let c = mem();
        create_note(&c, "n1", None, "Shopping", "buy milk eggs", 100).unwrap();
        let r = list_notes(&c, NoteFilter { folder_id: None, query: "mil", tag: None, pinned_only: false, limit: 100 }).unwrap();
        assert_eq!(r.len(), 1);
        let bad = list_notes(&c, NoteFilter { folder_id: None, query: "\"\"\"", tag: None, pinned_only: false, limit: 100 }).unwrap();
        assert!(bad.is_empty());
    }

    #[test]
    fn pin_sort_and_folder_delete_nulls() {
        let c = mem();
        create_folder(&c, "f1", "Work", 1).unwrap();
        create_note(&c, "a", Some("f1"), "A", "a", 10).unwrap();
        create_note(&c, "b", Some("f1"), "B", "b", 20).unwrap();
        toggle_pin(&c, "a").unwrap();
        let r = list_notes(&c, NoteFilter { folder_id: Some("f1"), query: "", tag: None, pinned_only: false, limit: 100 }).unwrap();
        assert_eq!(r[0].id, "a"); // pinned first despite older ts
        delete_folder(&c, "f1").unwrap();
        let n = get_note(&c, "a").unwrap().unwrap();
        assert_eq!(n.folder_id, None);
    }
}
