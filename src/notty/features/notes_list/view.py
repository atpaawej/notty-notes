def build_notes_list(store, on_select):
    try:
        import gi; gi.require_version('Gtk','4.0')
        from gi.repository import Gtk, GObject, Gio, Pango
    except Exception: return None
    # factory renders title + preview efficiently (recycled)
    factory=Gtk.SignalListItemFactory()
    def setup(_, item):
        box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2); box.set_margin_top(6); box.set_margin_bottom(6); box.set_margin_start(8); box.set_margin_end(8)
        title=Gtk.Label(xalign=0, ellipsize=Pango.EllipsizeMode.END); title.add_css_class("heading"); title.set_use_markup(True)
        preview=Gtk.Label(xalign=0, ellipsize=Pango.EllipsizeMode.END); preview.add_css_class("dim-label"); preview.add_css_class("caption")
        box.append(title); box.append(preview); item.set_child(box); item._title=title; item._preview=preview
    def bind(_, item):
        row=item.get_item(); title=f"📌 {row.title}" if row.pinned else row.title
        item._title.set_markup(f"<b>{title}</b>" if row.pinned else title); item._preview.set_text(row.preview or "")
    factory.connect("setup",setup); factory.connect("bind",bind)
    sel=Gtk.SingleSelection.new(store.model)
    lv=Gtk.ListView.new(sel, factory); lv.add_css_class("boxed-list")
    sel.connect("notify::selected-item", lambda s,_: on_select(s.get_selected_item().nid if s.get_selected_item() else None))
    scroll=Gtk.ScrolledWindow(child=lv, vexpand=True, hexpand=True)
    return scroll, sel
