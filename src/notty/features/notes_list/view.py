"""Notes list — Apple Notes: cards, selected accent, all empty/filter states."""
def build_notes_list(store, on_select):
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gtk, Pango
    except Exception:
        return None

    factory = Gtk.SignalListItemFactory()

    def setup(_, item):
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.add_css_class("notty-note-row")
        # header: title + pinned icon
        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title = Gtk.Label(xalign=0, hexpand=True, ellipsize=Pango.EllipsizeMode.END)
        title.add_css_class("note-title")
        pin = Gtk.Image.new_from_icon_name("view-pin-symbolic")
        pin.add_css_class("notty-pin-icon")
        pin.set_visible(False)
        pin.set_pixel_size(13)
        pin.set_tooltip_text("Pinned")
        head.append(title)
        head.append(pin)
        # preview 2 lines
        preview = Gtk.Label(xalign=0, ellipsize=Pango.EllipsizeMode.END, lines=2, wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR)
        preview.add_css_class("note-preview")
        preview.add_css_class("dim-label")
        # footer: date + locked icon
        foot = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        date = Gtk.Label(xalign=0, hexpand=True)
        date.add_css_class("note-date")
        date.add_css_class("dim-label")
        lock = Gtk.Image.new_from_icon_name("system-lock-screen-symbolic")
        lock.set_visible(False)
        lock.set_pixel_size(12)
        foot.append(date)
        foot.append(lock)
        card.append(head)
        card.append(preview)
        card.append(foot)
        item.set_child(card)
        item._title = title
        item._preview = preview
        item._date = date
        item._pin = pin
        item._lock = lock
        item._card = card

    def bind(_, item):
        row = item.get_item()
        if not row:
            return
        try:
            title = row.title
            preview = row.preview
            pinned = row.pinned
            raw = getattr(row, "_raw", None)
            ts = raw["updated_at"] if raw is not None else 0
            locked = raw["locked"] if raw is not None and "locked" in raw.keys() else 0
        except Exception:
            title = row["title"] or "Untitled"
            preview = row["preview"] or ""
            pinned = row["pinned"]
            ts = row["updated_at"]
            locked = row["locked"] if "locked" in row.keys() else 0
        item._title.set_text(title or "Untitled")
        # hide preview if same as title or empty
        if preview and preview.strip() and preview.strip() != (title or "").strip():
            item._preview.set_text(preview)
            item._preview.set_visible(True)
        else:
            item._preview.set_text("")
            item._preview.set_visible(False)
        try:
            from datetime import datetime
            dt = datetime.fromtimestamp(int(ts)) if ts else None
            if dt:
                # Apple style: Today / Yesterday / date
                from datetime import date as ddate
                today = ddate.today()
                note_d = dt.date()
                if note_d == today:
                    txt = dt.strftime("%H:%M")
                elif (today - note_d).days == 1:
                    txt = "Yesterday"
                elif dt.year == today.year:
                    txt = dt.strftime("%b %d")
                else:
                    txt = dt.strftime("%b %d, %Y")
            else:
                txt = ""
            item._date.set_text(txt)
        except Exception:
            item._date.set_text("")
        item._pin.set_visible(bool(pinned))
        item._lock.set_visible(bool(locked))
        # classes
        if pinned:
            item._card.add_css_class("pinned")
        else:
            item._card.remove_css_class("pinned")
        if locked:
            item._card.add_css_class("locked")
        else:
            item._card.remove_css_class("locked")

    factory.connect("setup", setup)
    factory.connect("bind", bind)

    sel = Gtk.SingleSelection.new(store.model)
    sel.set_can_unselect(True)
    sel.set_autoselect(False)
    lv = Gtk.ListView.new(sel, factory)
    lv.add_css_class("boxed-list")
    lv.set_single_click_activate(True)
    lv.set_hexpand(True)
    lv.set_vexpand(True)

    # --- Stack: list / empty / filtered-empty ---
    stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE, vexpand=True, hexpand=True)

    scroll = Gtk.ScrolledWindow(child=lv, vexpand=True, hexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
    scroll.add_css_class("notty-notes-list")
    scroll.set_vexpand(True)
    stack.add_named(scroll, "list")

    # empty: no notes at all
    empty = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, vexpand=True, hexpand=True)
    empty.add_css_class("notty-empty")
    empty.set_margin_top(32); empty.set_margin_bottom(32)
    eimg = Gtk.Image.new_from_icon_name("note-symbolic")
    eimg.set_pixel_size(56)
    et = Gtk.Label(label="No notes yet")
    et.add_css_class("title")
    et.set_markup("<b>No notes yet</b>")
    es = Gtk.Label(label="Capture ideas as fast as they come")
    es.add_css_class("subtitle")
    es.add_css_class("dim-label")
    es.set_wrap(True)
    es.set_justify(Gtk.Justification.CENTER)
    cta = Gtk.Button(label="Create Note")
    cta.add_css_class("suggested-action")
    cta.add_css_class("pill")
    cta.add_css_class("notty-empty-cta")
    empty.append(eimg); empty.append(et); empty.append(es); empty.append(cta)
    stack.add_named(empty, "empty")

    # filtered empty: no results
    filtered = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, vexpand=True, hexpand=True)
    filtered.add_css_class("notty-empty")
    fimg = Gtk.Image.new_from_icon_name("edit-find-symbolic")
    fimg.set_pixel_size(48)
    ft = Gtk.Label(label="No results")
    ft.add_css_class("title")
    ft.set_markup("<b>No results</b>")
    fs = Gtk.Label(label="Try a different search or clear filters")
    fs.add_css_class("subtitle")
    fs.add_css_class("dim-label")
    fs.set_wrap(True)
    fs.set_justify(Gtk.Justification.CENTER)
    clear_btn = Gtk.Button(label="Clear Search")
    clear_btn.add_css_class("pill")
    filtered.append(fimg); filtered.append(ft); filtered.append(fs); filtered.append(clear_btn)
    stack.add_named(filtered, "filtered")

    # header label for count
    header = Gtk.Label(xalign=0)
    header.add_css_class("notty-notes-header")
    header.add_css_class("dim-label")
    header.set_visible(False)

    def _update_empty():
        try:
            n = store.model.get_n_items() if hasattr(store.model, "get_n_items") else len(store.model)
        except Exception:
            n = 0
        # detect if filtered (store has query/tag/pinned_only)
        is_filtered = False
        try:
            is_filtered = bool((getattr(store, "query", "") or "").strip() or getattr(store, "tag", None) or getattr(store, "pinned_only", False) or (getattr(store, "folder", "__all__") != "__all__"))
        except Exception:
            pass
        if n == 0:
            if is_filtered:
                stack.set_visible_child_name("filtered")
                header.set_visible(False)
            else:
                stack.set_visible_child_name("empty")
                header.set_visible(False)
        else:
            stack.set_visible_child_name("list")
            header.set_visible(True)
            try:
                header.set_text(f"{n} {'note' if n==1 else 'notes'}")
            except Exception:
                pass

    _update_empty()
    try:
        store.model.connect("items-changed", lambda *_: _update_empty())
    except Exception:
        pass

    # selection handling — FIX: use both selection and activation, robust nid extraction
    def _emit_selection(selected_item):
        if selected_item is None:
            on_select(None)
            return
        nid = None
        # Gio NoteRow
        if hasattr(selected_item, "nid"):
            nid = selected_item.nid
        elif hasattr(selected_item, "_raw"):
            try: nid = selected_item._raw["id"]
            except Exception: pass
        else:
            try: nid = selected_item["id"]
            except Exception: nid = str(selected_item)
        on_select(nid)

    def _on_selection_changed(sel_obj, _pspec):
        item = sel_obj.get_selected_item()
        _emit_selection(item)

    def _on_activate(_lv, pos):
        try:
            item = sel.get_item(pos) if hasattr(sel, "get_item") else store.model.get_item(pos)
            sel.set_selected(pos)
            _emit_selection(item)
        except Exception:
            pass

    sel.connect("notify::selected-item", _on_selection_changed)
    lv.connect("activate", _on_activate)

    # expose clear handlers for outer wiring
    wrapper = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True, hexpand=True, spacing=0)
    wrapper.append(header)
    wrapper.append(stack)
    wrapper._update_empty = _update_empty
    wrapper._stack = stack
    wrapper._clear_btn = clear_btn
    wrapper._cta = cta
    wrapper._sel = sel
    wrapper._lv = lv
    # allow outer to hook clear (only filtered clear, not empty CTA)
    def _set_clear_callback(cb):
        try:
            clear_btn.connect("clicked", lambda *_: cb())
        except Exception:
            pass
    wrapper._set_clear = _set_clear_callback

    return wrapper, sel
