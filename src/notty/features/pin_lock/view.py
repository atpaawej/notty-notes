"""Pin / Lock — subtle icon toggles, proper states."""
def build_pin_lock_buttons(store, get_selected_nid, on_pin_toggled):
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gtk
    except Exception:
        return None

    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    box.set_halign(Gtk.Align.END)

    pin = Gtk.ToggleButton(icon_name="view-pin-symbolic")
    pin.add_css_class("flat"); pin.add_css_class("circular")
    pin.set_tooltip_text("Pin to top")
    lock = Gtk.ToggleButton(icon_name="system-lock-screen-symbolic")
    lock.add_css_class("flat"); lock.add_css_class("circular")
    lock.set_tooltip_text("Lock note")

    def _pin(*_):
        nid = get_selected_nid()
        if not nid:
            pin.set_active(False); return
        store.toggle_pin(nid)
        # keep visual sync with db
        on_pin_toggled()

    def _lock(*_):
        nid = get_selected_nid()
        if not nid:
            lock.set_active(False); return
        store.toggle_lock(nid)
        on_pin_toggled()

    pin.connect("toggled", _pin)
    lock.connect("toggled", _lock)

    box.append(pin); box.append(lock)
    # expose for external sync
    box._pin = pin; box._lock = lock
    return box
