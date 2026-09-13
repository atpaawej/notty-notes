"""AppShell — clean, uncluttered 3-pane, proper empty/selected states."""
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
    if os.getenv("NOTTY_DB"):
        return Path(os.getenv("NOTTY_DB")).parent
    base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "notty"

class NottyApp:
    """Headless core + GTK build_ui(). E2E drives core directly."""
    def __init__(self, db_path=None):
        ddir = _data_dir(); ddir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path or os.getenv("NOTTY_DB") or str(ddir / "notes.db")
        self.db = Db(self.db_path)
        self.settings = Settings()
        self.folders = FoldersStore(FolderRepo(self.db))
        self.notes = NotesListStore(NotesRepo(self.db))
        self.tags = TagStore(TagRepo(self.db))
        self.search = SearchStore()
        self.pin_lock = PinLockStore(self.db)
        self.editor_repo = EditorRepo(self.db)
        self.editor = EditorController(self.editor_repo, on_saved=lambda nid: self._on_saved())
        self.selected_folder = "__all__"
        self.selected_nid = None
        self._current_text = ""
        self.notes.apply(folder=self.selected_folder)

    def _on_saved(self):
        self.notes.apply(folder=self.selected_folder, query=getattr(self.search, "query", "") or "", tag=self.search.get_tag(), pinned_only=getattr(self.search, "pinned_only", False))
        try: self.tags.refresh()
        except Exception: pass

    def select_folder(self, fid: str):
        self.selected_folder = fid or "__all__"
        self.notes.apply(folder=self.selected_folder, query=getattr(self.search, "query", "") or "", tag=self.search.get_tag(), pinned_only=getattr(self.search, "pinned_only", False))

    def set_search(self, q: str, pinned_only: bool = False, tag=None):
        if hasattr(self.search, "query"): self.search.query = q
        else: self.search.query = q
        if hasattr(self.search, "pinned_only"): self.search.pinned_only = pinned_only
        if tag is not None: self.search.set_tag(tag)
        self.notes.apply(folder=self.selected_folder, query=q, tag=self.search.get_tag(), pinned_only=pinned_only)

    def select_tag(self, tag):
        self.search.set_tag(tag)
        self.notes.apply(folder=self.selected_folder, query=getattr(self.search, "query", "") or "", tag=tag, pinned_only=getattr(self.search, "pinned_only", False))

    def create_note(self):
        nid = uuid.uuid4().hex[:8]
        fid = None if self.selected_folder == "__all__" else self.selected_folder
        ts = int(time.time())
        self.db.create_note(nid, fid, "Untitled", "", ts)
        self._on_saved()
        self.selected_nid = nid
        return nid

    def open_note(self, nid):
        self.selected_nid = nid
        if not nid: self._current_text = ""; return ""
        row = self.db.get_note(nid)
        if not row: return ""
        body = row["body"] or ""
        text = body if body.startswith(row["title"]) else (row["title"] + "\n" + body if row["title"] != "Untitled" else body)
        self._current_text = text
        return text

    def on_editor_text(self, text: str):
        self._current_text = text
        if not self.selected_nid: return
        fid = None if self.selected_folder == "__all__" else self.selected_folder
        self.editor.request_save(self.selected_nid, fid, text)

    def delete_selected(self):
        if self.selected_nid:
            self.db.delete_note(self.selected_nid)
            self.selected_nid = None
            self._on_saved()

    # ---------- UI ----------
    def build_ui(self):
        try:
            import gi
            gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1')
            from gi.repository import Gtk, Adw, Gio, GLib, Gdk, Pango
        except Exception as e:
            print(f"GTK unavailable: {e} - headless")
            return None

        Adw.init()
        # load css
        try:
            css = Gtk.CssProvider()
            for p in [Path(__file__).parent / "../../data/style.css", Path("/usr/share/notty/style.css"), Path("data/style.css")]:
                pp = Path(p).resolve()
                if pp.exists():
                    css.load_from_path(str(pp)); break
            Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        except Exception:
            pass

        win = Adw.ApplicationWindow()
        win.set_title("Notty")
        win.set_default_size(self.settings.get_int("window-width"), self.settings.get_int("window-height"))
        # icon from data/notty.png or hicolor
        try:
            icon = Path(__file__).parent / "../../data/notty.png"
            if icon.exists():
                win.set_default_icon_name(str(icon))
        except Exception:
            pass

        core = self
        sel_ref = {"nid": None}

        # ---- header ----
        header = Adw.HeaderBar()
        # left title with logo
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        try:
            logo = Gtk.Image.new_from_file(str(Path(__file__).parent / "../../data/notty.png"))
            logo.set_pixel_size(22)
            title_box.append(logo)
        except Exception:
            title_box.append(Gtk.Image.new_from_icon_name("note-symbolic"))
        title_box.append(Gtk.Label(label="Notty", css_classes=["title"]))
        header.set_title_widget(title_box)

        new_btn = Gtk.Button(label="New Note", css_classes=["suggested-action", "pill"])
        new_btn.set_tooltip_text("Create new note (Ctrl+N)")
        header.pack_end(new_btn)

        # ---- slices ----
        from .features.folders.view import build_sidebar
        from .features.notes_list.view import build_notes_list
        from .features.editor.view import build_editor
        from .features.search.view import build_search
        from .features.tags.view import build_tag_browser
        from .features.pin_lock.view import build_pin_lock_buttons

        # state helpers — defined BEFORE use to avoid UnboundLocalError
        notes_wrapper = {"w": None, "sel": None}
        editor_root = {"box": None, "buf": None, "stack": None}
        footer = {"label": None, "date": None}

        def _refresh_notes():
            # recompute empty states
            try:
                w = notes_wrapper["w"]
                if w and hasattr(w, "_update_empty"): w._update_empty()
            except Exception: pass
            # if selected note not in new filtered list, clear editor
            try:
                nid = sel_ref["nid"]
                if nid:
                    rows = core.db.list_notes(folder_id=core.selected_folder, query=getattr(core.search, "query", "") or "", tag=core.search.get_tag(), pinned_only=getattr(core.search, "pinned_only", False))
                    if nid not in [r["id"] for r in rows]:
                        sel_ref["nid"] = None; core.selected_nid = None
                        _show_empty()
            except Exception: pass
            # refresh tags
            try:
                if hasattr(core.tags, "refresh"): core.tags.refresh()
            except: pass
            # update word count footer
            _update_footer()

        def _show_empty():
            try: editor_root["stack"].set_visible_child_name("empty")
            except: pass
            sel_ref["nid"] = None

        def _show_editor():
            try: editor_root["stack"].set_visible_child_name("editor")
            except: pass

        def _update_footer():
            try:
                buf = editor_root["buf"]
                txt = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False) if buf else ""
                wc = len(txt.split()) if txt.strip() else 0
                footer["label"].set_text(f"{wc} words" if wc else "Empty note")
                # date
                nid = sel_ref["nid"]
                if nid:
                    row = core.db.get_note(nid)
                    if row:
                        import datetime
                        dt = datetime.datetime.fromtimestamp(row["updated_at"])
                        footer["date"].set_text(dt.strftime("Edited %b %d, %H:%M"))
                    else:
                        footer["date"].set_text("")
                else:
                    footer["date"].set_text("")
            except Exception:
                pass

        def on_folder(fid):
            core.select_folder(fid)
            _refresh_notes()

        sidebar = build_sidebar(core.folders, on_folder) or Gtk.Label(label="Folders")

        search_box, _entry = build_search(core.search, lambda q, p, t: (core.set_search(q, p, t), _refresh_notes())) or (Gtk.Box(), None)
        tag_browser = build_tag_browser(core.tags, lambda t: (core.select_tag(t), _refresh_notes())) or Gtk.Label(label="Tags")

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0, vexpand=True)
        left.set_size_request(250, -1)
        left.append(sidebar)
        left.append(Gtk.Separator())
        # tags scroll
        tag_scroll = Gtk.ScrolledWindow(child=tag_browser, vexpand=True, hexpand=True, vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)
        tag_scroll.set_min_content_height(120)
        left.append(tag_scroll)

        def on_pick(nid):
            sel_ref["nid"] = nid; core.selected_nid = nid
            if not nid:
                _show_empty(); _update_footer(); return
            txt = core.open_note(nid)
            buf = editor_root["buf"]
            if buf:
                # block signal to avoid double save
                buf.set_text(txt or "", -1)
            _show_editor(); _update_footer()
            # sync pin/lock toggles
            try:
                row = core.db.get_note(nid)
                if row:
                    pin_box._pin.set_active(bool(row["pinned"]))
                    pin_box._lock.set_active(bool(row["locked"]))
                else:
                    pin_box._pin.set_active(False); pin_box._lock.set_active(False)
            except Exception:
                pass

        notes_area, sel = build_notes_list(core.notes, on_pick) or (Gtk.Label(label="Notes"), None)
        notes_wrapper["w"] = notes_area; notes_wrapper["sel"] = sel

        mid = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0, hexpand=True, vexpand=True)
        mid.set_size_request(340, -1)
        mid.append(search_box)
        mid.append(Gtk.Separator())
        mid.append(notes_area)

        # editor
        def _on_editor(text):
            core.on_editor_text(text)
            _update_footer()

        ebox, buf, _tv = build_editor(_on_editor) or (Gtk.Box(), None, None)
        # ebox is root Box with toolbar + stack
        if ebox and hasattr(ebox, "_stack"):
            editor_root["box"] = ebox; editor_root["buf"] = buf; editor_root["stack"] = ebox._stack
            editor_root["buf"] = buf
        else:
            # fallback if view didn't expose stack
            editor_root["box"] = ebox; editor_root["buf"] = buf; editor_root["stack"] = Gtk.Stack()

        # footer + pin/lock
        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bottom.add_css_class("notty-footer")
        bottom.set_margin_top(6); bottom.set_margin_start(8); bottom.set_margin_end(8); bottom.set_margin_bottom(4)
        date_lbl = Gtk.Label(xalign=0, hexpand=True); date_lbl.add_css_class("dim-label")
        word_lbl = Gtk.Label(xalign=1); word_lbl.add_css_class("dim-label")
        footer["label"] = word_lbl; footer["date"] = date_lbl

        pin_box = build_pin_lock_buttons(core.pin_lock, lambda: sel_ref["nid"], _refresh_notes) or Gtk.Box()
        # pin_box was created with deferred _refresh_notes already fixed

        bottom.append(date_lbl); bottom.append(word_lbl); bottom.append(pin_box)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0, hexpand=True, vexpand=True)
        right.append(ebox); right.append(bottom)

        # hook buffer word count + save
        if buf:
            def _on_changed(*_):
                txt = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
                _on_editor(txt)
            buf.connect("changed", _on_changed)

        # panes
        paned1 = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned1.set_start_child(left); paned1.set_end_child(mid); paned1.set_position(270); paned1.set_shrink_start_child(False)
        paned2 = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned2.set_start_child(paned1); paned2.set_end_child(right); paned2.set_position(620); paned2.set_shrink_start_child(False)

        def _new_note():
            nid = core.create_note()
            _refresh_notes()
            on_pick(nid)
            if buf:
                buf.set_text("", -1); buf.place_cursor(buf.get_start_iter())
                # focus editor
                try: editor_root["box"].get_parent().get_parent().grab_focus()
                except: pass

        new_btn.connect("clicked", lambda *_: _new_note())

        # keyboard
        ctrl = Gtk.EventControllerKey()
        def _key(_, keyval, keycode, state):
            # Ctrl+N
            if state & Gdk.ModifierType.CONTROL_MASK and keyval == Gdk.KEY_n:
                _new_note(); return True
            if keyval == Gdk.KEY_Delete and sel_ref["nid"] and (state & Gdk.ModifierType.CONTROL_MASK):
                core.delete_selected(); sel_ref["nid"] = None; _show_empty(); _refresh_notes(); return True
            return False
        ctrl.connect("key-pressed", _key)
        win.add_controller(ctrl)

        # initial empty
        _show_empty(); _update_footer()

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.append(header); content.append(paned2)
        win.set_content(content)
        try:
            win.set_icon_name("app.notty.Notty")
        except: pass
        return win

def run():
    import sys
    if "--headless" in sys.argv:
        a = NottyApp(db_path=":memory:")
        a.create_note(); a.on_editor_text("Hello #test")
        print("headless ok", a.db.list_notes())
        return
    try:
        import gi; gi.require_version('Adw', '1'); gi.require_version('Gtk', '4.0')
        from gi.repository import Adw, Gio
        app = Adw.Application(application_id="app.notty.Notty", flags=Gio.ApplicationFlags.FLAGS_NONE)
        def on_activate(app):
            core = NottyApp()
            win = core.build_ui()
            if win: win.set_application(app); win.present()
        app.connect("activate", on_activate)
        app.run(sys.argv)
    except Exception as e:
        print(f"No GUI, headless fallback: {e}")
        NottyApp(db_path=":memory:")

if __name__ == "__main__":
    run()
