"""Search — Apple Notes: rounded field, filter pill, hint."""
def build_search(store, on_change):
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gtk
    except Exception:
        return None

    root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    root.add_css_class("notty-search")

    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    entry = Gtk.SearchEntry(placeholder_text="Search notes…", hexpand=True)
    entry.set_margin_start(2); entry.set_margin_end(2)
    pin = Gtk.ToggleButton(label="Pinned")
    pin.add_css_class("pill"); pin.add_css_class("notty-filter-pill")
    pin.set_tooltip_text("Show pinned only")
    pin.set_icon_name("view-pin-symbolic")
    row.append(entry); row.append(pin)
    root.append(row)

    hint = Gtk.Label(xalign=0)
    hint.add_css_class("dim-label"); hint.add_css_class("caption")
    hint.set_visible(False)
    hint.set_margin_start(4)
    root.append(hint)

    def _emit(*_):
        q = entry.get_text()
        pinned = pin.get_active()
        tag = store.get_tag() if hasattr(store, "get_tag") else None
        on_change(q, pinned, tag)
        # hint
        if q.strip() or pinned or tag:
            parts = []
            if q.strip(): parts.append(f'“{q.strip()}”')
            if tag: parts.append(f"#{tag}")
            if pinned: parts.append("Pinned")
            hint.set_text("Filter: " + " • ".join(parts))
            hint.set_visible(True)
        else:
            hint.set_visible(False)

    entry.connect("search-changed", _emit)
    pin.connect("toggled", _emit)
    entry.connect("activate", _emit)

    # expose for external reset
    root._entry = entry
    root._pin = pin
    root._emit = _emit
    def _set_hint(txt):
        if txt:
            hint.set_text(txt); hint.set_visible(True)
        else:
            hint.set_visible(False)
    root._hint = _set_hint
    return root, entry
