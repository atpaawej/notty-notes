"""Debounced save + title extraction - minimal, no extra deps."""
import time
def extract_title_body(text: str):
    lines=(text or "").strip().splitlines()
    title=lines[0].strip() if lines else "Untitled"
    if len(title)>80: title=title[:80]
    return title or "Untitled", text or ""

class EditorController:
    def __init__(self, repo, on_saved=None):
        self.repo=repo; self.on_saved=on_saved; self._timer=None; self._pending=None
    def request_save(self, nid, folder_id, text, ts=None):
        ts=ts or int(time.time())
        title, body=extract_title_body(text)
        self._pending=(nid,folder_id,title,body,ts)
        # use GLib timeout if available else immediate
        try:
            from gi.repository import GLib
            if self._timer: GLib.source_remove(self._timer)
            self._timer=GLib.timeout_add(350, self._flush)
        except Exception:
            self._flush()
    def _flush(self):
        if not self._pending: return False
        nid,folder_id,title,body,ts=self._pending; self._pending=None; self._timer=None
        try:
            row=self.repo.load(nid)
            if row: self.repo.save(nid,title,body,ts)
            else: self.repo.create(nid,folder_id,title,body,ts)
            if self.on_saved: self.on_saved(nid)
        except Exception: pass
        return False
    def flush_now(self):
        if self._timer:
            try: from gi.repository import GLib; GLib.source_remove(self._timer)
            except Exception: pass
            self._timer=None
        self._flush()
