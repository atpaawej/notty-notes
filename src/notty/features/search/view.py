def build_search(store, on_change):
    try:
        import gi; gi.require_version('Gtk','4.0')
        from gi.repository import Gtk
    except Exception: return None
    box=Gtk.Box(spacing=6)
    entry=Gtk.SearchEntry(placeholder_text="Search notes…", hexpand=True)
    pin=Gtk.ToggleButton(label="📌 Pinned")
    def _emit(*_): on_change(entry.get_text(), pin.get_active(), store.get_tag())
    entry.connect("search-changed", _emit); pin.connect("toggled", _emit)
    box.append(entry); box.append(pin)
    return box, entry
