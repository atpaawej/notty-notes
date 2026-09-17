mod commands;
mod db;

use std::path::PathBuf;
use std::sync::Mutex;

fn data_dir() -> PathBuf {
    if let Ok(p) = std::env::var("NOTTY_DB") {
        return PathBuf::from(p);
    }
    let base = std::env::var("XDG_DATA_HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|_| dirs_next());
    base.join("notty").join("notes.db")
}

fn dirs_next() -> PathBuf {
    PathBuf::from(std::env::var("HOME").unwrap_or_else(|_| "/root".into()))
        .join(".local")
        .join("share")
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let path = data_dir();
    let path_str = path.to_string_lossy().into_owned();
    let conn = db::open(&path_str).expect("open notes.db");
    tauri::Builder::default()
        .manage(Mutex::new(conn))
        .invoke_handler(tauri::generate_handler![
            commands::list_folders,
            commands::create_folder,
            commands::rename_folder,
            commands::delete_folder,
            commands::list_notes,
            commands::create_note,
            commands::get_note,
            commands::update_note,
            commands::delete_note,
            commands::toggle_pin,
            commands::toggle_lock,
            commands::list_tags
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
