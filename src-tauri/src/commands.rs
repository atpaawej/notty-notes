//! Tauri commands — 1:1 with SPEC §2. Single-writer via Mutex<Connection>.

use crate::db;
use std::sync::{Mutex, MutexGuard};
use std::time::{SystemTime, UNIX_EPOCH};
use tauri::State;

pub type DbState = Mutex<rusqlite::Connection>;

fn lock<'a>(state: &'a State<'a, DbState>) -> Result<MutexGuard<'a, rusqlite::Connection>, String> {
    state.lock().map_err(|e| e.to_string())
}

fn now_ts() -> i64 {
    SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs() as i64).unwrap_or(0)
}

fn short_id() -> String {
    uuid::Uuid::new_v4().as_simple().to_string()[..8].to_string()
}

#[tauri::command]
pub fn list_folders(state: State<DbState>) -> Result<Vec<db::Folder>, String> {
    let conn = lock(&state)?;
    db::list_folders(&conn).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn create_folder(state: State<DbState>, name: String) -> Result<db::Folder, String> {
    let conn = lock(&state)?;
    let fid = short_id();
    let ts = now_ts();
    db::create_folder(&conn, &fid, name.trim(), ts).map_err(|e| e.to_string())?;
    Ok(db::Folder { id: fid, name: name.trim().to_string(), created_at: ts })
}

#[tauri::command]
pub fn rename_folder(state: State<DbState>, id: String, name: String) -> Result<(), String> {
    let conn = lock(&state)?;
    db::rename_folder(&conn, &id, name.trim()).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn delete_folder(state: State<DbState>, id: String) -> Result<(), String> {
    let conn = lock(&state)?;
    db::delete_folder(&conn, &id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn list_notes(
    state: State<DbState>,
    folder_id: Option<String>,
    query: Option<String>,
    tag: Option<String>,
    pinned_only: Option<bool>,
    limit: Option<i64>,
) -> Result<Vec<db::Note>, String> {
    let conn = lock(&state)?;
    db::list_notes(
        &conn,
        db::NoteFilter {
            folder_id: folder_id.as_deref(),
            query: query.as_deref().unwrap_or(""),
            tag: tag.as_deref(),
            pinned_only: pinned_only.unwrap_or(false),
            limit: limit.unwrap_or(1000),
        },
    )
    .map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_note(state: State<DbState>, id: String) -> Result<Option<db::Note>, String> {
    let conn = lock(&state)?;
    db::get_note(&conn, &id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn create_note(state: State<DbState>, folder_id: Option<String>) -> Result<db::Note, String> {
    let conn = lock(&state)?;
    let fid = if folder_id.as_deref() == Some("__all__") { None } else { folder_id.as_deref() };
    db::create_note(&conn, &short_id(), fid, "Untitled", "", now_ts()).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn update_note(
    state: State<DbState>,
    id: String,
    text: String,
    folder_id: Option<String>,
) -> Result<db::Note, String> {
    let conn = lock(&state)?;
    let title = db::extract_title(&text);
    let fid_opt = match folder_id {
        None => None, // leave folder unchanged
        Some(f) if f == "__all__" => Some(None),
        Some(f) => Some(Some(f)),
    };
    // flatten Option<Option<String>> to the db helper's Option<Option<&str>>
    let updated = match fid_opt {
        None => db::update_note(&conn, &id, &title, &text, now_ts(), None),
        Some(inner) => db::update_note(&conn, &id, &title, &text, now_ts(), Some(inner.as_deref())),
    }
    .map_err(|e| e.to_string())?;
    updated.ok_or_else(|| "note not found".to_string())
}

#[tauri::command]
pub fn delete_note(state: State<DbState>, id: String) -> Result<(), String> {
    let conn = lock(&state)?;
    db::delete_note(&conn, &id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn toggle_pin(state: State<DbState>, id: String) -> Result<bool, String> {
    let conn = lock(&state)?;
    db::toggle_pin(&conn, &id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn toggle_lock(state: State<DbState>, id: String) -> Result<bool, String> {
    let conn = lock(&state)?;
    db::toggle_lock(&conn, &id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn list_tags(state: State<DbState>) -> Result<Vec<db::TagCount>, String> {
    let conn = lock(&state)?;
    db::list_tags(&conn).map_err(|e| e.to_string())
}
