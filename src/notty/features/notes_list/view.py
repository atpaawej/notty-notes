"""Notes list — cards, proper selected/pinned/empty states."""
def build_notes_list(store, on_select):
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gtk, Pango
    except Exception:
        return None

    # factory with recycled rows
    factory = Gtk.SignalListItemFactory()

    def setup(_, item):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        card.add_css_class("notty-note-row")
        card.set_margin_top(4); card.set_margin_bottom(4)
        # title row
        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title = Gtk.Label(xalign=0, hexpand=True, ellipsize=Pango.EllipsizeMode.END)
        title.add_css_class("note-title")
        pin = Gtk.Image.new_from_icon_name("view-pin-symbolic")
        pin.set_visible(False); pin.set_pixel_size(14)
        head.append(title); head.append(pin)
        # preview
        preview = Gtk.Label(xalign=0, ellipsize=Pango.EllipsizeMode.END, lines=2, wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR)
        preview.add_css_class("note-preview"); preview.add_css_class("dim-label")
        # footer date
        date = Gtk.Label(xalign=0); date.add_css_class("note-date"); date.add_css_class("dim-label")
        card.append(head); card.append(preview); card.append(date)
        item.set_child(card)
        item._title = title; item._preview = preview; item._date = date; item._pin = pin; item._card = card

    def bind(_, item):
        row = item.get_item()
        if not row:
            return
        # row may be Gio NoteRow or sqlite Row
        try:
            title = row.title
            preview = row.preview
            pinned = row.pinned
            ts = row._raw["updated_at"] if hasattr(row, "_raw") else 0
        except Exception:
            title = row["title"] or "Untitled"
            preview = row["preview"] or ""
            pinned = row["pinned"]
            ts = row["updated_at"]
        item._title.set_text(title or "Untitled")
        item._preview.set_text(preview or "")
        # date
        try:
            import time
            from datetime import datetime
            dt = datetime.fromtimestamp(int(ts)) if ts else None
            txt = dt.strftime("%b %d") if dt else ""
            item._date.set_text(txt)
        except Exception:
            item._date.set_text("")
        item._pin.set_visible(bool(pinned))
        if pinned:
            item._card.add_css_class("pinned")
        else:
            item._card.remove_css_class("pinned")

    factory.connect("setup", setup); factory.connect("bind", bind)

    # selection model
    sel = Gtk.SingleSelection.new(store.model)
    sel.set_can_unselect(False)
    sel.set_autoselect(False)
    lv = Gtk.ListView.new(sel, factory)
    lv.add_css_class("boxed-list")
    lv.set_single_click_activate(True)

    # empty overlay
    stack = Gtk.Stack()
    scroll = Gtk.ScrolledWindow(child=lv, vexpand=True, hexpand=True)
    scroll.add_css_class("notty-notes-list")
    stack.add_named(scroll, "list")

    empty = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, vexpand=True)
    empty.add_css_class("notty-empty")
    img = Gtk.Image.new_from_icon_name("note-symbolic"); img.set_pixel_size(48)
    t = Gtk.Label(label="No notes yet"); t.add_css_class("title"); t.set_markup("<b>No notes yet</b>")
    s = Gtk.Label(label="Create your first note"); s.add_css_class("dim-label")
    empty.append(img); empty.append(t); empty.append(s)
    stack.add_named(empty, "empty")

    def _update_empty():
        try:
            n = store.model.get_n_items() if hasattr(store.model, "get_n_items") else len(store.model)
        except Exception:
            n = 0
        stack.set_visible_child_name("empty" if n == 0 else "list")
    # initial + listen
    _update_empty()
    try:
        store.model.connect("items-changed", lambda *_: _update_empty())
    except Exception:
        pass

    sel.connect("notify::selected-item", lambda s,_: on_select(s.get_selected_item().nid if s.get_selected_item() else (s.get_selected_item()["id"] if s.get_selected_item() else None)))

    # wrap stack as scroll target, return stack + sel for external refresh
    wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True, hexpand=True)
    wrapper.append(stack)
    # expose helper to refresh empty after external apply
    wrapper._update_empty = _update_empty
    return wrapper, sel
