"""AppShell — Apple Notes 3-pane, all states, pixel-perfect."""
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
        # load css — Apple polish
        try:
            css = Gtk.CssProvider()
            candidates = [
                Path(__file__).parent / "../../data/style.css",
                Path("/usr/share/notty/style.css"),
                Path("data/style.css"),
            ]
            for p in candidates:
                pp = Path(p).resolve()
                if pp.exists():
                    css.load_from_path(str(pp)); break
            Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        except Exception:
            pass

        win = Adw.ApplicationWindow()
        win.set_title("Notty")
        win.set_default_size(self.settings.get_int("window-width"), self.settings.get_int("window-height"))

        core = self
        sel_ref = {"nid": None}

        # ---- HeaderBar: Apple minimal ----
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(True)
        header.set_show_start_title_buttons(True)
        # centered logo + wordmark
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, halign=Gtk.Align.CENTER)
        try:
            logo = Gtk.Image.new_from_file(str((Path(__file__).parent / "../../data/notty.png").resolve()))
            logo.set_pixel_size(20)
            title_box.append(logo)
        except Exception:
            title_box.append(Gtk.Image.new_from_icon_name("note-symbolic"))
        t = Gtk.Label(label="Notty")
        t.add_css_class("title")
        title_box.append(t)
        header.set_title_widget(title_box)

        new_btn = Gtk.Button(label="New Note")
        new_btn.add_css_class("suggested-action"); new_btn.add_css_class("pill")
        new_btn.set_tooltip_text("Create new note (Ctrl+N)")
        new_btn.set_icon_name("list-add-symbolic")
        header.pack_end(new_btn)

        # delete button (dim, only active when note selected)
        del_btn = Gtk.Button(icon_name="user-trash-symbolic")
        del_btn.add_css_class("flat"); del_btn.add_css_class("circular")
        del_btn.set_tooltip_text("Delete note (Ctrl+Delete)")
        del_btn.set_sensitive(False)
        header.pack_end(del_btn)

        # ---- Slices ----
        from .features.folders.view import build_sidebar
        from .features.notes_list.view import build_notes_list
        from .features.editor.view import build_editor
        from .features.search.view import build_search
        from .features.tags.view import build_tag_browser
        from .features.pin_lock.view import build_pin_lock_buttons

        # State refs — defined before use
        notes_wrapper = {"w": None, "sel": None}
        editor_root = {"box": None, "buf": None, "stack": None, "tv": None}
        footer = {"words": None, "date": None, "pin_box": None}
        search_ref = {"box": None, "entry": None}

        # ---- Helpers: all states ----
        def _refresh_notes():
            try:
                w = notes_wrapper["w"]
                if w and hasattr(w, "_update_empty"): w._update_empty()
            except Exception: pass
            # if selected nid filtered out → clear
            try:
                nid = sel_ref["nid"]
                if nid:
                    rows = core.db.list_notes(folder_id=core.selected_folder, query=getattr(core.search, "query", "") or "", tag=core.search.get_tag(), pinned_only=getattr(core.search, "pinned_only", False))
                    if nid not in [r["id"] for r in rows]:
                        _show_empty()
                        sel_ref["nid"] = None
                        core.selected_nid = None
            except Exception: pass
            try:
                if hasattr(core.tags, "refresh"): core.tags.refresh()
            except: pass
            _update_footer()
            _sync_delete_btn()

        def _show_empty():
            try: editor_root["stack"].set_visible_child_name("empty")
            except: pass
            sel_ref["nid"] = None
            # disable editor actions
            try: editor_root["tv"].set_editable(False); editor_root["tv"].set_can_focus(False)
            except: pass
            _sync_pin_lock(None)

        def _show_locked():
            try: editor_root["stack"].set_visible_child_name("locked")
            except: pass
            _sync_pin_lock(sel_ref["nid"])

        def _show_editor():
            try: editor_root["stack"].set_visible_child_name("editor")
            except: pass
            try: editor_root["tv"].set_editable(True); editor_root["tv"].set_can_focus(True)
            except: pass

        def _sync_delete_btn():
            try: del_btn.set_sensitive(bool(sel_ref["nid"]))
            except: pass

        def _sync_pin_lock(nid):
            try:
                pb = footer.get("pin_box")
                if not pb:
                    return
                row = core.db.get_note(nid) if nid else None
                if row:
                    is_pinned = bool(row["pinned"])
                    is_locked = bool(row["locked"])
                    # use helpers that block signals
                    if hasattr(pb, "_set_pin"):
                        pb._set_pin(is_pinned)
                        pb._set_lock(is_locked)
                    else:
                        pb._pin.set_active(is_pinned)
                        pb._lock.set_active(is_locked)
                    if is_locked:
                        _show_locked()
                else:
                    if hasattr(pb, "_set_pin"):
                        pb._set_pin(False)
                        pb._set_lock(False)
                    else:
                        try: pb._pin.set_active(False)
                        except: pass
                        try: pb._lock.set_active(False)
                        except: pass
            except Exception:
                pass

        def _update_footer():
            try:
                buf = editor_root["buf"]
                txt = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False) if buf else ""
                wc = len(txt.split()) if txt.strip() else 0
                footer["words"].set_text(f"{wc} words" if wc else "Empty note")
                footer["words"].add_css_class("notty-word-count")
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

        # Build sidebar + tags
        sidebar = build_sidebar(core.folders, on_folder) or Gtk.Label(label="Folders")

        search_box, _entry = build_search(core.search, lambda q, p, t: (core.set_search(q, p, t), _refresh_notes())) or (Gtk.Box(), None)
        search_ref["box"] = search_box; search_ref["entry"] = _entry
        tag_browser = build_tag_browser(core.tags, lambda t: (core.select_tag(t), _refresh_notes())) or Gtk.Label(label="Tags")

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0, vexpand=True)
        left.set_size_request(240, -1)
        left.append(sidebar)
        left.append(Gtk.Separator())
        tag_scroll = Gtk.ScrolledWindow(child=tag_browser, vexpand=True, hexpand=True, vscrollbar_policy=Gtk.PolicyType.AUTOMATIC, hscrollbar_policy=Gtk.PolicyType.NEVER)
        tag_scroll.set_min_content_height(120)
        tag_scroll.set_vexpand(True)
        left.append(tag_scroll)
        left.add_css_class("notty-sidebar")

        # Notes list — Apple: search on top, header count, polished empty states
        def on_pick(nid):
            # locked check
            if nid:
                row = core.db.get_note(nid)
                if row and row["locked"]:
                    sel_ref["nid"] = nid; core.selected_nid = nid
                    # load empty to avoid leaking
                    _show_locked()
                    _sync_pin_lock(nid)
                    _update_footer()
                    _sync_delete_btn()
                    return
            sel_ref["nid"] = nid; core.selected_nid = nid
            _sync_delete_btn()
            if not nid:
                _show_empty(); _update_footer(); return
            txt = core.open_note(nid)
            buf = editor_root["buf"]
            if buf:
                # block changed signal to avoid double save
                try: buf.handler_block_by_func(_on_editor_changed)
                except: pass
                buf.set_text(txt or "", -1)
                try: buf.handler_unblock_by_func(_on_editor_changed)
                except: pass
            _show_editor(); _update_footer()
            _sync_pin_lock(nid)

        notes_area, sel = build_notes_list(core.notes, on_pick) or (Gtk.Label(label="Notes"), None)
        notes_wrapper["w"] = notes_area; notes_wrapper["sel"] = sel

        # wire filtered-empty clear → reset search/tag
        def _clear_filters():
            try:
                if search_ref["entry"]:
                    search_ref["entry"].set_text("")
                core.select_tag(None)
                core.set_search("", False, None)
                _refresh_notes()
            except: pass
        try:
            notes_area._clear_btn.connect("clicked", lambda *_: _clear_filters())
        except: pass

        mid = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0, hexpand=True, vexpand=True)
        mid.set_size_request(320, -1)
        mid.append(search_box)
        mid.append(Gtk.Separator())
        mid.append(notes_area)

        # Editor
        def _on_editor(text):
            core.on_editor_text(text)
            _update_footer()

        def _on_editor_changed(*_):
            try:
                txt = editor_root["buf"].get_text(editor_root["buf"].get_start_iter(), editor_root["buf"].get_end_iter(), False)
                _on_editor(txt)
            except: pass

        ebox, buf, _tv = build_editor(_on_editor) or (Gtk.Box(), None, None)
        if ebox and hasattr(ebox, "_stack"):
            editor_root["box"] = ebox; editor_root["buf"] = buf; editor_root["stack"] = ebox._stack; editor_root["tv"] = _tv
        else:
            editor_root["box"] = ebox; editor_root["buf"] = buf; editor_root["stack"] = Gtk.Stack(); editor_root["tv"] = _tv

        def _unlock_current():
            nid = sel_ref["nid"]
            if not nid: return
            core.db.toggle_lock(nid)
            _sync_pin_lock(nid)
            # re-open
            on_pick(nid)
            _refresh_notes()

        # Footer: date • words • pin/lock
        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        bottom.add_css_class("notty-footer")
        bottom.set_margin_top(6); bottom.set_margin_start(12); bottom.set_margin_end(12); bottom.set_margin_bottom(8)
        date_lbl = Gtk.Label(xalign=0, hexpand=True); date_lbl.add_css_class("dim-label"); date_lbl.add_css_class("notty-editor-meta")
        word_lbl = Gtk.Label(xalign=1); word_lbl.add_css_class("dim-label"); word_lbl.add_css_class("notty-editor-meta")
        footer["words"] = word_lbl; footer["date"] = date_lbl

        pin_box = build_pin_lock_buttons(core.pin_lock, lambda: sel_ref["nid"], _refresh_notes) or Gtk.Box()
        footer["pin_box"] = pin_box

        bottom.append(date_lbl); bottom.append(word_lbl); bottom.append(pin_box)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0, hexpand=True, vexpand=True)
        right.append(ebox); right.append(bottom)

        # Connect buffer changed (once)
        if buf:
            buf.connect("changed", _on_editor_changed)

        # — Paned: Apple proportions, smooth —
        paned_left = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned_left.set_start_child(left); paned_left.set_end_child(mid)
        paned_left.set_position(260); paned_left.set_shrink_start_child(False); paned_left.set_shrink_end_child(False)
        paned_left.set_resize_start_child(False); paned_left.set_resize_end_child(False)

        paned_main = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned_main.set_start_child(paned_left); paned_main.set_end_child(right)
        paned_main.set_position(600); paned_main.set_shrink_start_child(False); paned_main.set_shrink_end_child(False)
        paned_main.set_resize_start_child(False); paned_main.set_resize_end_child(True)
        paned_main.set_hexpand(True); paned_main.set_vexpand(True)

        def _new_note():
            nid = core.create_note()
            _refresh_notes()
            on_pick(nid)
            # select in list view
            try:
                # find index
                for i in range(core.notes.model.get_n_items()):
                    if core.notes.model.get_item(i).nid == nid:
                        notes_wrapper["sel"].set_selected(i); break
            except: pass
            if buf:
                # clear for typing
                try: buf.handler_block_by_func(_on_editor_changed)
                except: pass
                buf.set_text("", -1)
                try: buf.handler_unblock_by_func(_on_editor_changed)
                except: pass
                buf.place_cursor(buf.get_start_iter())
                # focus editor
                try: editor_root["tv"].grab_focus()
                except: pass
            _show_editor()

        new_btn.connect("clicked", lambda *_: _new_note())
        del_btn.connect("clicked", lambda *_: _delete_current())
        try:
            notes_area._cta.connect("clicked", lambda *_: _new_note())
        except: pass
        try:
            ebox._create_btn.connect("clicked", lambda *_: _new_note())
        except: pass
        try:
            ebox._unlock_btn.connect("clicked", lambda *_: _unlock_current())
        except: pass

        def _delete_current():
            nid = sel_ref["nid"]
            if not nid: return
            core.delete_selected()
            sel_ref["nid"] = None
            _show_empty()
            _refresh_notes()
            _sync_delete_btn()

        # Keyboard — like Apple
        ctrl = Gtk.EventControllerKey()
        ctrl.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        def _key(_, keyval, keycode, state):
            is_ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
            is_cmd = bool(state & Gdk.ModifierType.CONTROL_MASK)  # treat Ctrl as Cmd on Linux
            # Ctrl/Cmd + N
            if is_cmd and keyval == Gdk.KEY_n:
                _new_note(); return True
            # Ctrl/Cmd + F → focus search
            if is_cmd and keyval == Gdk.KEY_f:
                try: search_ref["entry"].grab_focus(); return True
                except: pass
            # Cmd/Ctrl + Backspace/Delete
            if nid := sel_ref["nid"]:
                if keyval == Gdk.KEY_Delete and is_ctrl:
                    _delete_current(); return True
                if keyval == Gdk.KEY_BackSpace and is_ctrl:
                    _delete_current(); return True
            # Escape → clear selection
            if keyval == Gdk.KEY_Escape:
                if sel_ref["nid"]:
                    try: notes_wrapper["sel"].set_selected(Gtk.INVALID_LIST_POSITION)
                    except: pass
                    sel_ref["nid"] = None; core.selected_nid = None
                    _show_empty(); _update_footer(); _sync_delete_btn(); return True
            return False
        ctrl.connect("key-pressed", _key)
        win.add_controller(ctrl)

        # initial state: empty editor, update counts
        _show_empty(); _update_footer(); _refresh_notes(); _sync_delete_btn()

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True)
        content.append(header); content.append(paned_main)
        win.set_content(content)
        try: win.set_icon_name("app.notty.Notty")
        except: pass
        # save window size on close
        try:
            win.connect("close-request", lambda *_: (core.settings.set_int("window-width", win.get_width()), core.settings.set_int("window-height", win.get_height())))
        except: pass
        return win

def run():
    import sys
    if "--headless" in sys.argv:
        a = NottyApp(db_path=":memory:")
        a.create_note(); a.on_editor_text("Hello #test")
        a.editor.flush_now()
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
