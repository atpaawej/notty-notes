def build_pin_lock_buttons(store, get_selected_nid, on_pin_toggled):
    try:
        import gi; gi.require_version('Gtk','4.0')
        from gi.repository import Gtk
    except Exception: return None
    box=Gtk.Box(spacing=6)
    pin=Gtk.Button(icon_name="view-pin-symbolic", tooltip_text="Pin")
    lock=Gtk.Button(icon_name="system-lock-screen-symbolic", tooltip_text="Lock")
    def _pin(*_):
        nid=get_selected_nid()
        if nid: store.toggle_pin(nid); on_pin_toggled()
    def _lock(*_):
        nid=get_selected_nid()
        if nid: store.toggle_lock(nid); on_pin_toggled()
    pin.connect("clicked", _pin); lock.connect("clicked", _lock)
    box.append(pin); box.append(lock)
    return box
