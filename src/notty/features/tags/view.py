def build_tag_browser(store, on_select_tag):
    try:
        import gi; gi.require_version('Gtk','4.0')
        from gi.repository import Gtk, Pango
    except Exception: return None
    box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
    box.append(Gtk.Label(label="Tags", xalign=0))
    # simple list
    try:
        from gi.repository import Gio
        factory=Gtk.SignalListItemFactory()
        def setup(_, it):
            h=Gtk.Box(spacing=6); l=Gtk.Label(xalign=0, hexpand=True, ellipsize=Pango.EllipsizeMode.END); c=Gtk.Label(); h.append(l); h.append(c)
            row=Gtk.ListBoxRow(child=h); it.set_child(row); it._l=l; it._c=c
        def bind(_, it):
            tag=it.get_item(); it._l.set_text(f"#{tag.name}"); it._c.set_text(str(tag.count))
        factory.connect("setup",setup); factory.connect("bind",bind)
        lv=Gtk.ListView.new(Gtk.SingleSelection.new(store.model), factory)
        lv.set_size_request(-1, 120)
        def _sel(sel,_):
            it=sel.get_selected_item()
            on_select_tag(it.name if it else None)
        lv.get_model().connect("notify::selected-item", _sel)
        box.append(lv)
    except Exception:
        pass
    btn=Gtk.Button(label="Clear tag filter"); btn.connect("clicked", lambda *_: on_select_tag(None))
    box.append(btn)
    return box
