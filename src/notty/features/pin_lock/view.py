"""Pin / Lock — Apple subtle toggles with active states."""
def build_pin_lock_buttons(store, get_selected_nid, on_pin_toggled):
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gtk
    except Exception:
        return None

    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    box.set_halign(Gtk.Align.END)
    box.set_valign(Gtk.Align.CENTER)

    pin = Gtk.ToggleButton(icon_name="view-pin-symbolic")
    pin.add_css_class("flat"); pin.add_css_class("circular")
    pin.set_tooltip_text("Pin to top")
    lock = Gtk.ToggleButton(icon_name="system-lock-screen-symbolic")
    lock.add_css_class("flat"); lock.add_css_class("circular")
    lock.set_tooltip_text("Lock note")

    def _pin(*_):
        nid = get_selected_nid()
        if not nid:
            # revert visual without recursion
            pin.handler_block_by_func(_pin)
            pin.set_active(False)
            pin.handler_unblock_by_func(_pin)
            return
        store.toggle_pin(nid)
        on_pin_toggled()

    def _lock(*_):
        nid = get_selected_nid()
        if not nid:
            lock.handler_block_by_func(_lock)
            lock.set_active(False)
            lock.handler_unblock_by_func(_lock)
            return
        store.toggle_lock(nid)
        on_pin_toggled()

    pin_id = pin.connect("toggled", _pin)
    lock_id = lock.connect("toggled", _lock)

    box.append(pin); box.append(lock)
    box._pin = pin; box._lock = lock
    box._pin_id = pin_id; box._lock_id = lock_id
    # helpers to sync without re-triggering toggle
    def _set_pin(active: bool):
        try: pin.handler_block(pin_id)
        except: pass
        try: pin.set_active(bool(active))
        finally:
            try: pin.handler_unblock(pin_id)
            except: pass
    def _set_lock(active: bool):
        try: lock.handler_block(lock_id)
        except: pass
        try: lock.set_active(bool(active))
        finally:
            try: lock.handler_unblock(lock_id)
            except: pass
    box._set_pin = _set_pin
    box._set_lock = _set_lock
    return box
