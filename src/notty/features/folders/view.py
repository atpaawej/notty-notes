"""Folders sidebar view - only loaded when GTK available."""
def build_sidebar(store, on_select):
    try:
        import gi; gi.require_version('Gtk','4.0'); gi.require_version('Adw','1')
        from gi.repository import Gtk, Adw, Gio
    except Exception: return None
    box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    box.set_margin_top(8); box.set_margin_start(8); box.set_margin_end(8)
    # All Notes row
    def _row(fid,name,icon="folder-symbolic"):
        r=Gtk.Box(spacing=8); r.append(Gtk.Image.new_from_icon_name(icon)); r.append(Gtk.Label(label=name, xalign=0, hexpand=True))
        btn=Gtk.ListBoxRow(child=r); btn._fid=fid; return btn
    lb=Gtk.ListBox(); lb.set_selection_mode(Gtk.SelectionMode.SINGLE)
    lb.add_css_class("navigation-sidebar")
    lb.append(_row("__all__","All Notes","view-pinned-symbolic"))
    for i in range(store.model.get_n_items()):
        it=store.model.get_item(i); lb.append(_row(it.fid, it.name))
    lb.connect("row-selected", lambda _, row: on_select(getattr(row,"_fid","__all__") if row else "__all__"))
    box.append(lb)
    # new folder entry
    entry=Gtk.Entry(placeholder_text="New folder…"); entry.set_visible(False)
    def _commit():
        name=entry.get_text().strip()
        if name: fid=store.create(name); lb.append(_row(fid,name)); entry.set_text(""); entry.set_visible(False)
    entry.connect("activate", lambda *_: _commit())
    btn=Gtk.Button(label="New Folder"); btn.add_css_class("pill")
    btn.connect("clicked", lambda *_: entry.set_visible(True) or entry.grab_focus())
    box.append(btn); box.append(entry)
    return box
