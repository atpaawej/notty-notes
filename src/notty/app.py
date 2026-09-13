"""AppShell - composes VSA slices, single state propagation path, Adw.Leaflet 3-pane."""
import os, uuid, time
from pathlib import Path

from .shared.db import Db
from .shared.settings import Settings

from .features.folders.repository import FolderRepo
from .features.folders.store import FoldersStore
from .features.notes_list.repository import NotesRepo
from .features.notes_list.store import NotesListStore
from .features.editor.repository import EditorRepo
from .features.editor.controller import EditorController
from .features.tags.repository import TagRepo
from .features.tags.store import TagStore
from .features.search.store import SearchStore
from .features.pin_lock.store import PinLockStore

def _data_dir():
    # Flatpak vs host vs test isolation via XDG_DATA_HOME / NOTTY_DB
    if os.getenv("NOTTY_DB"): return Path(os.getenv("NOTTY_DB")).parent
    base = Path(os.getenv("XDG_DATA_HOME", Path.home()/".local"/"share"))
    return base / "notty"

class NottyApp:
    """Headless-capable core - GTK wiring only in build_ui(). Allows E2E logic tests without display."""
    def __init__(self, db_path=None):
        ddir=_data_dir(); ddir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path or os.getenv("NOTTY_DB") or str(ddir / "notes.db")
        self.db = Db(self.db_path)
        self.settings = Settings()
        # slices
        self.folders = FoldersStore(FolderRepo(self.db))
        self.notes = NotesListStore(NotesRepo(self.db))
        self.tags = TagStore(TagRepo(self.db))
        self.search = SearchStore()
        self.pin_lock = PinLockStore(self.db)
        self.editor_repo = EditorRepo(self.db)
        self.editor = EditorController(self.editor_repo, on_saved=lambda nid: self._on_saved())
        # app state
        self.selected_folder = "__all__"
        self.selected_nid = None
        self._current_text = ""
        # initial load
        self.notes.apply(folder=self.selected_folder)

    def _on_saved(self):
        self.notes.apply(folder=self.selected_folder, query=getattr(self.search,"query","") or "", tag=self.search.get_tag(), pinned_only=getattr(self.search,"pinned_only",False))
        self.tags.refresh()

    # ----- state transitions (all paths go through here) -----
    def select_folder(self, fid: str):
        self.selected_folder = fid or "__all__"
        self.notes.apply(folder=self.selected_folder, query=self.search.query if hasattr(self.search,"query") else "", tag=self.search.get_tag(), pinned_only=getattr(self.search,"pinned_only",False))

    def set_search(self, q: str, pinned_only: bool=False, tag=None):
        if hasattr(self.search,"query"): self.search.query=q
        else: self.search.query=q
        if hasattr(self.search,"pinned_only"): self.search.pinned_only=pinned_only
        if tag is not None or self.search.get_tag() is not None:
            if tag is not None: self.search.set_tag(tag)
        self.notes.apply(folder=self.selected_folder, query=q, tag=self.search.get_tag(), pinned_only=pinned_only)

    def select_tag(self, tag):
        self.search.set_tag(tag)
        self.notes.apply(folder=self.selected_folder, query=getattr(self.search,"query",""), tag=tag, pinned_only=getattr(self.search,"pinned_only",False))

    def create_note(self):
        nid=uuid.uuid4().hex[:8]
        fid=None if self.selected_folder=="__all__" else self.selected_folder
        ts=int(time.time())
        self.db.create_note(nid, fid, "Untitled", "", ts)
        self._on_saved()
        self.selected_nid=nid
        return nid

    def open_note(self, nid):
        self.selected_nid=nid
        if not nid: self._current_text=""; return ""
        row=self.db.get_note(nid)
        if not row: return ""
        # title + body stored separately but editor shows title\nbody
        body=row["body"] or ""
        # if body doesn't start with title, prepend for editor continuity
        text=body if body.startswith(row["title"]) else (row["title"]+"\n"+body if row["title"]!="Untitled" else body)
        self._current_text=text
        return text

    def on_editor_text(self, text: str):
        self._current_text=text
        if not self.selected_nid: return
        fid=None if self.selected_folder=="__all__" else self.selected_folder
        self.editor.request_save(self.selected_nid, fid, text)

    def delete_selected(self):
        if self.selected_nid:
            self.db.delete_note(self.selected_nid)
            self.selected_nid=None
            self._on_saved()

    def toggle_pin_selected(self):
        if self.selected_nid:
            self.db.toggle_pin(self.selected_nid)
            self._on_saved()

    def build_ui(self):
        """Only call when GTK stack available - returns Gtk Window."""
        try:
            import gi; gi.require_version('Gtk','4.0'); gi.require_version('Adw','1')
            from gi.repository import Gtk, Adw, Gio, GLib
        except Exception as e:
            print(f"GTK unavailable: {e} - running headless")
            return None

        Adw.init()
        win=Adw.ApplicationWindow()
        app_core=self

        # header
        header=Adw.HeaderBar()
        new_btn=Gtk.Button(label="New Note", css_classes=["suggested-action"])
        new_btn.connect("clicked", lambda *_: _new_note())
        header.pack_end(new_btn)

        # slices UI
        from .features.folders.view import build_sidebar
        from .features.notes_list.view import build_notes_list
        from .features.editor.view import build_editor
        from .features.search.view import build_search
        from .features.tags.view import build_tag_browser
        from .features.pin_lock.view import build_pin_lock_buttons

        # state holders for click handlers
        sel_ref={"nid": None}
        # stubs to avoid UnboundLocalError when lambdas are created before real defs
        def _refresh_notes(): pass
        def _new_note(): pass

        def on_folder(fid): app_core.select_folder(fid); _refresh_notes()
        sidebar=build_sidebar(app_core.folders, on_folder) or Gtk.Label(label="Folders")

        search_box, _entry = build_search(app_core.search, lambda q,p,t: app_core.set_search(q,p,t) or _refresh_notes()) or (Gtk.Box(), None)
        tag_browser=build_tag_browser(app_core.tags, lambda t: app_core.select_tag(t) or _refresh_notes()) or Gtk.Label(label="Tags")

        left=Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        left.set_size_request(240,-1)
        left.append(sidebar); left.append(Gtk.Separator()); left.append(tag_browser)

        def on_pick(nid):
            sel_ref["nid"]=nid; app_core.selected_nid=nid
            if nid:
                txt=app_core.open_note(nid)
                # avoid recursive changed signal
                try: buf.set_text(txt, -1)
                except Exception: pass
        notes_scroll, _sel = build_notes_list(app_core.notes, on_pick) or (Gtk.Label(label="Notes"), None)

        mid=Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, hexpand=True)
        mid.set_size_request(320,-1)
        mid.append(search_box); mid.append(notes_scroll)

        def _on_editor(text): app_core.on_editor_text(text)
        editor_box, buf, _tv = build_editor(_on_editor) or (Gtk.Label(label="Editor"), None, None)

        pin_box=build_pin_lock_buttons(app_core.pin_lock, lambda: sel_ref["nid"], lambda: _refresh_notes()) or Gtk.Box()
        word_lbl=Gtk.Label(label="0 words", xalign=1); word_lbl.add_css_class("dim-label")
        if buf:
            def _words(*_):
                txt=buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
                wc=len(txt.split()) if txt.strip() else 0
                word_lbl.set_text(f"{wc} words")
                _on_editor(txt)
            buf.connect("changed", _words)

        right=Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
        right.append(pin_box); right.append(editor_box); right.append(word_lbl)

        # panes
        paned1=Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL); paned1.set_start_child(left); paned1.set_end_child(mid); paned1.set_position(260)
        paned2=Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL); paned2.set_start_child(paned1); paned2.set_end_child(right); paned2.set_position(600)

        def _refresh_notes():
            # after any state change, keep selection
            pass

        def _new_note():
            nid=app_core.create_note()
            on_pick(nid)
            if buf: buf.set_text("", -1)

        # shortcuts
        def _key(ctrl, key):
            if key=="n": _new_note(); return True
            if key=="Delete" and sel_ref["nid"]: app_core.delete_selected(); return True
            return False
        keyc=Gtk.EventControllerKey()
        keyc.connect("key-pressed", lambda _,k,__,m: _key(None, chr(k)) if m & 4 else False)
        win.add_controller(keyc)

        content=Gtk.Box(orientation=Gtk.Orientation.VERTICAL); content.append(header); content.append(paned2)
        win.set_content(content)
        win.set_default_size(app_core.settings.get_int("window-width"), app_core.settings.get_int("window-height"))
        win.set_title("Notty")
        return win

def run():
    import sys
    # headless mode for CI: --headless prints ok
    if "--headless" in sys.argv:
        a=NottyApp(db_path=":memory:")
        a.create_note(); a.on_editor_text("Hello #test")
        print("headless ok", a.db.list_notes())
        return
    # try GUI, fallback to headless if no display
    try:
        import gi; gi.require_version('Adw','1'); gi.require_version('Gtk','4.0')
        from gi.repository import Adw, Gio
        app=Adw.Application(application_id="app.notty.Notty", flags=Gio.ApplicationFlags.FLAGS_NONE)
        core_holder={}
        def on_activate(app):
            core=NottyApp(); core_holder["c"]=core
            win=core.build_ui()
            if win: win.set_application(app); win.present()
        app.connect("activate", on_activate)
        app.run(sys.argv)
    except Exception as e:
        print(f"No GUI, headless fallback: {e}")
        NottyApp(db_path=":memory:")

if __name__=="__main__": run()
