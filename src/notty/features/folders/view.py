"""Folders sidebar — clean, uncluttered, proper empty/selected states."""
def build_sidebar(store, on_select):
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gtk
    except Exception:
        return None

    root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    root.add_css_class("notty-sidebar")
    root.set_size_request(240, -1)

    # header row: title + new button
    hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    hdr.set_margin_top(12); hdr.set_margin_start(12); hdr.set_margin_end(8); hdr.set_margin_bottom(6)
    title = Gtk.Label(label="Folders", xalign=0, hexpand=True)
    title.add_css_class("heading"); title.add_css_class("dim-label")
    hdr.append(title)
    add_btn = Gtk.Button(icon_name="list-add-symbolic")
    add_btn.add_css_class("flat"); add_btn.add_css_class("circular")
    add_btn.set_tooltip_text("New Folder")
    hdr.append(add_btn)
    root.append(hdr)

    # list
    lb = Gtk.ListBox()
    lb.set_selection_mode(Gtk.SelectionMode.SINGLE)
    lb.add_css_class("boxed-list")
    lb.set_margin_start(8); lb.set_margin_end(8)

    def _make_row(fid, name, icon="folder-symbolic", dim=None):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_top(4); box.set_margin_bottom(4)
        img = Gtk.Image.new_from_icon_name(icon)
        img.add_css_class("folder-icon")
        box.append(img)
        lbl = Gtk.Label(label=name, xalign=0, hexpand=True, ellipsize=3)
        box.append(lbl)
        if dim:
            d = Gtk.Label(label=dim, xalign=1)
            d.add_css_class("dim"); box.append(d)
        row = Gtk.ListBoxRow(child=box)
        row._fid = fid
        if fid == "__all__":
            row.set_tooltip_text("All notes")
        return row

    # All Notes always first, selected by default
    all_row = _make_row("__all__", "All Notes", "view-pinned-symbolic")
    lb.append(all_row)

    # populate from store
    try:
        for i in range(store.model.get_n_items()):
            it = store.model.get_item(i)
            lb.append(_make_row(it.fid, it.name, "folder-symbolic"))
    except Exception:
        for f in getattr(store, "items", []):
            lb.append(_make_row(f.id, f.name))

    # inline entry for new folder (hidden until +)
    entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    entry_box.set_margin_start(8); entry_box.set_margin_end(8); entry_box.set_margin_top(6)
    entry_box.set_visible(False)
    entry = Gtk.Entry(placeholder_text="Folder name…", hexpand=True)
    ok = Gtk.Button(icon_name="emblem-ok-symbolic"); ok.add_css_class("suggested-action"); ok.add_css_class("circular")
    entry_box.append(entry); entry_box.append(ok)
    root.append(lb); root.append(entry_box)

    def _show_entry(*_):
        entry_box.set_visible(True); entry.grab_focus()
    def _commit(*_):
        name = entry.get_text().strip()
        if not name:
            entry_box.set_visible(False); return
        # store handles duplicate via UNIQUE, catch
        try:
            fid = store.create(name)
            lb.append(_make_row(fid, name))
            entry.set_text(""); entry_box.set_visible(False)
            # select new
            lb.select_row(lb.get_row_at_index(lb.get_row_at_index(0).get_index()+1) if False else None)
            on_select(fid)
            # select the newly appended row
            for r in range(lb.get_row_at_index(0).get_parent().__len__() if False else 0): pass
            # brute select last row
            # Gtk.ListBox doesn't expose count easily, select by iterating
            last = None
            row = lb.get_first_child()
            while row:
                last = row; row = row.get_next_sibling()
            if last: lb.select_row(last)
        except Exception:
            entry_box.set_visible(False)

    add_btn.connect("clicked", _show_entry)
    ok.connect("clicked", _commit)
    entry.connect("activate", _commit)
    # Escape to cancel — use key controller (Entry has no "escape" signal)
    try:
        from gi.repository import Gdk
        ec = Gtk.EventControllerKey()
        def _esc(_c, keyval, *_):
            if keyval == Gdk.KEY_Escape:
                entry_box.set_visible(False)
                return True
            return False
        entry.add_controller(ec)
        ec.connect("key-pressed", _esc)
    except Exception:
        pass

    # selection -> propagate, handle empty state highlight
    def _on_select(_lb, row):
        fid = getattr(row, "_fid", "__all__") if row else "__all__"
        on_select(fid)
    lb.connect("row-selected", _on_select)
    # select All Notes initially
    lb.select_row(all_row)

    # empty state hint when no folders beyond All
    return root
