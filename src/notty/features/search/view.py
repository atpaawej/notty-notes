"""Search — spacious, clear, filter chips."""
def build_search(store, on_change):
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gtk
    except Exception:
        return None

    root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    root.set_margin_top(8); root.set_margin_start(8); root.set_margin_end(8)

    # search row
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    entry = Gtk.SearchEntry(placeholder_text="Search notes…", hexpand=True)
    entry.add_css_class("rounded")
    # pinned toggle as subtle chip
    pin = Gtk.ToggleButton(label="📌 Pinned")
    pin.add_css_class("pill")
    pin.set_tooltip_text("Show pinned only")
    row.append(entry); row.append(pin)
    root.append(row)

    # helper: emit combined state
    def _emit(*_):
        q = entry.get_text()
        pinned = pin.get_active()
        tag = store.get_tag() if hasattr(store, "get_tag") else None
        on_change(q, pinned, tag)

    entry.connect("search-changed", _emit)
    pin.connect("toggled", _emit)
    entry.connect("activate", _emit)

    # subtle hint below when filtering
    hint = Gtk.Label(xalign=0); hint.add_css_class("dim-label"); hint.add_css_class("caption"); hint.set_visible(False)
    root.append(hint)

    def _set_hint(txt):
        if txt:
            hint.set_text(txt); hint.set_visible(True)
        else:
            hint.set_visible(False)
    root._hint = _set_hint
    return root, entry
