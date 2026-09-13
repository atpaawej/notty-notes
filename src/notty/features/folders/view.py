"""Folders sidebar — Apple Notes: grouped sections, counts, all states."""
def build_sidebar(store, on_select):
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gtk
    except Exception:
        return None

    root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0, vexpand=True)
    root.add_css_class("notty-sidebar")

    # — Header —
    hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    hdr.set_margin_top(14); hdr.set_margin_start(12); hdr.set_margin_end(8); hdr.set_margin_bottom(4)
    title = Gtk.Label(label="Notty", xalign=0, hexpand=True)
    title.set_markup('<b>Notty</b>')
    title.add_css_class("heading")
    hdr.append(title)
    add_btn = Gtk.Button(icon_name="list-add-symbolic")
    add_btn.add_css_class("flat"); add_btn.add_css_class("circular")
    add_btn.set_tooltip_text("New Folder")
    hdr.append(add_btn)
    root.append(hdr)

    # — Section label —
    sec = Gtk.Label(label="Folders", xalign=0)
    sec.add_css_class("notty-sidebar-header")
    sec.set_margin_start(12); sec.set_margin_end(8)
    root.append(sec)

    lb = Gtk.ListBox()
    lb.set_selection_mode(Gtk.SelectionMode.SINGLE)
    lb.add_css_class("navigation-sidebar")
    lb.set_vexpand(False)

    def _make_row(fid, name, icon="folder-symbolic", count=None):
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row_box.set_margin_top(2); row_box.set_margin_bottom(2)
        img = Gtk.Image.new_from_icon_name(icon)
        img.add_css_class("folder-icon")
        img.set_pixel_size(16)
        row_box.append(img)
        lbl = Gtk.Label(label=name, xalign=0, hexpand=True, ellipsize=3)
        lbl.set_max_width_chars(14)
        row_box.append(lbl)
        if count is not None and count != "":
            pill = Gtk.Label(label=str(count))
            pill.add_css_class("count-pill")
            row_box.append(pill)
        row = Gtk.ListBoxRow(child=row_box)
        row._fid = fid
        row.add_css_class("notty-sidebar-row")
        return row

    # All Notes — always first, with count placeholder
    all_row = _make_row("__all__", "All Notes", "folder-symbolic", None)
    lb.append(all_row)

    def _populate():
        # clear except first
        child = lb.get_first_child()
        # keep all_row
        to_remove = []
        c = lb.get_first_child()
        while c:
            if c is not all_row:
                to_remove.append(c)
            c = c.get_next_sibling()
        for r in to_remove:
            lb.remove(r)
        # repopulate from store
        try:
            n = store.model.get_n_items() if hasattr(store.model, "get_n_items") else len(store.items) if hasattr(store, "items") else 0
            for i in range(n):
                it = store.model.get_item(i) if hasattr(store.model, "get_item") else store.items[i]
                fid = getattr(it, "fid", getattr(it, "id", str(i)))
                name = getattr(it, "name", str(it))
                lb.append(_make_row(fid, name, "folder-symbolic"))
        except Exception:
            for f in getattr(store, "items", []):
                lb.append(_make_row(getattr(f, "id", ""), getattr(f, "name", "")))

    _populate()

    # — Inline new folder entry (Apple inline) —
    entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    entry_box.add_css_class("notty-new-folder")
    entry_box.set_margin_start(8); entry_box.set_margin_end(8); entry_box.set_margin_top(6); entry_box.set_margin_bottom(6)
    entry_box.set_visible(False)
    entry = Gtk.Entry(placeholder_text="Folder name…", hexpand=True)
    entry.add_css_class("rounded")
    ok = Gtk.Button(icon_name="emblem-ok-symbolic")
    ok.add_css_class("suggested-action"); ok.add_css_class("circular"); ok.set_tooltip_text("Create")
    cancel = Gtk.Button(icon_name="window-close-symbolic")
    cancel.add_css_class("flat"); cancel.add_css_class("circular"); cancel.set_tooltip_text("Cancel")
    entry_box.append(entry); entry_box.append(ok); entry_box.append(cancel)
    root.append(lb)
    root.append(entry_box)

    # empty hint
    empty_hint = Gtk.Label(label="No custom folders yet", xalign=0)
    empty_hint.add_css_class("dim-label"); empty_hint.add_css_class("caption")
    empty_hint.set_margin_start(16); empty_hint.set_margin_top(8)
    empty_hint.set_visible(False)
    root.append(empty_hint)

    def _update_empty():
        try:
            n = store.model.get_n_items() if hasattr(store.model, "get_n_items") else len(getattr(store, "items", []))
            empty_hint.set_visible(n == 0)
        except Exception:
            pass
    _update_empty()

    def _show_entry(*_):
        entry_box.set_visible(True)
        entry.set_text("")
        entry.grab_focus()
    def _hide_entry(*_):
        entry_box.set_visible(False)
        entry.set_text("")
    def _commit(*_):
        name = entry.get_text().strip()
        if not name:
            _hide_entry()
            return
        if len(name) > 32:
            name = name[:32]
        try:
            fid = store.create(name)
            lb.append(_make_row(fid, name))
            _hide_entry()
            _update_empty()
            # select new row
            last = None
            row = lb.get_first_child()
            while row:
                last = row; row = row.get_next_sibling()
            if last:
                lb.select_row(last)
            # notify
            on_select(fid)
        except Exception as e:
            # duplicate name — shake hint
            entry.add_css_class("error")
            entry.set_tooltip_text(str(e))

    add_btn.connect("clicked", _show_entry)
    ok.connect("clicked", _commit)
    cancel.connect("clicked", _hide_entry)
    entry.connect("activate", _commit)
    try:
        from gi.repository import Gdk
        ec = Gtk.EventControllerKey()
        def _esc(_c, keyval, *_):
            if keyval == Gdk.KEY_Escape:
                _hide_entry()
                return True
            return False
        entry.add_controller(ec)
        ec.connect("key-pressed", _esc)
    except Exception:
        pass

    def _on_select(_lb, row):
        fid = getattr(row, "_fid", "__all__") if row else "__all__"
        on_select(fid)
    lb.connect("row-selected", _on_select)
    # select All Notes initially
    lb.select_row(all_row)

    # expose refresh
    root._refresh = lambda: (_populate(), _update_empty())
    root._listbox = lb
    return root
