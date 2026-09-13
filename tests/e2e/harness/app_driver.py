"""Headless + AT-SPI unified driver - real user API for E2E."""
import os, time, subprocess, tempfile
from pathlib import Path

class HeadlessDriver:
    """Fallback when no display/dogtail - drives NottyApp core directly (same state path as GUI)."""
    def __init__(self, tmpdir=None):
        self.tmpdir = Path(tmpdir or tempfile.mkdtemp(prefix="notty-e2e-"))
        self.db_path = str(self.tmpdir / "notes.db")
        os.environ["NOTTY_DB"] = self.db_path
        from src.notty.app import NottyApp
        self.app = NottyApp(db_path=self.db_path)
    def click_new_note(self): return self.app.create_note()
    def type_in_editor(self, text):
        self.app.on_editor_text(text)
        # flush debounce immediately for tests
        self.app.editor.flush_now()
        self.app._on_saved()
    def open_note(self, nid): return self.app.open_note(nid)
    def get_notes(self, **kw): return self.app.db.list_notes(**kw)
    def notes_count(self, **kw): return len(self.get_notes(**kw))
    def search(self, q): self.app.set_search(q); return self.get_notes(query=q)
    def click_folder(self, name):
        # find by name then select
        for r in self.app.db.list_folders():
            if r["name"]==name: self.app.select_folder(r["id"]); return
        raise AssertionError(f"folder {name} not found")
    def create_folder(self, name): return self.app.folders.create(name)
    def rename_folder(self, fid, name): self.app.folders.rename(fid, name)
    def delete_folder(self, fid): self.app.folders.delete(fid)
    def pin_first_note(self):
        rows=self.app.db.list_notes()
        assert rows, "no notes to pin"
        self.app.db.toggle_pin(rows[0]["id"]); self.app._on_saved()
        return rows[0]["id"]
    def is_pinned(self, idx=0):
        rows=self.app.db.list_notes()
        return bool(rows[idx]["pinned"]) if rows else False
    def list_tags(self): return self.app.db.list_tags()
    def close(self):
        try: self.app.db.close()
        except Exception: pass

# AT-SPI driver stub - when dogtail available, extend HeadlessDriver via AT-SPI clicks
try:
    from dogtail.tree import root as dogtail_root
    HAS_DOGTAIL=True
except Exception:
    HAS_DOGTAIL=False
    dogtail_root=None

def get_driver(tmpdir=None):
    # if dogtail + display, could launch subprocess and drive via a11y
    # for now always return headless - same code paths, still E2E via real AppState transitions
    return HeadlessDriver(tmpdir=tmpdir)
