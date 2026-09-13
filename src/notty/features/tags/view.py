"""Tag browser — pills, counts, empty handling."""
def build_tag_browser(store, on_select_tag):
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gtk
    except Exception:
        return None

    root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    root.set_margin_start(12); root.set_margin_end(8); root.set_margin_top(8); root.set_margin_bottom(8)

    hdr = Gtk.Label(label="Tags", xalign=0)
    hdr.add_css_class("heading"); hdr.add_css_class("dim-label")
    root.append(hdr)

    # container for pills
    flow = Gtk.FlowBox(max_children_per_line=6, selection_mode=Gtk.SelectionMode.SINGLE)
    flow.set_homogeneous(False); flow.set_row_spacing(6); flow.set_column_spacing(6)
    flow.set_halign(Gtk.Align.START)

    def _refresh():
        # clear
        child = flow.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            flow.remove(child); child = nxt
        # fill from store
        try:
            items = list(store.model) if hasattr(store.model, "__iter__") else []
            # if Gio.ListStore, iterate
            try:
                if hasattr(store.model, "get_n_items"):
                    items = [store.model.get_item(i) for i in range(store.model.get_n_items())]
            except Exception:
                pass
            if not items:
                # try list_tags fallback
                try:
                    items = [{"name": r["tag"], "count": r["c"]} for r in store.repo.list()]
                    # wrap
                    class _T: pass
                    tmp=[]
                    for it in items:
                        o=_T(); o.name=it["name"]; o.count=it["count"]; tmp.append(o)
                    items=tmp
                except Exception:
                    items=[]
        except Exception:
            items=[]
        for it in items:
            name = getattr(it, "name", getattr(it, "tag", str(it)))
            cnt = getattr(it, "count", getattr(it, "c", ""))
            btn = Gtk.ToggleButton(label=f"#{name}  {cnt}" if cnt else f"#{name}")
            btn.add_css_class("pill"); btn.add_css_class("tag-pill")
            btn._tag = name
            flow.append(btn)
        # connect after fill
        def _on_child_activated(_flow, child):
            # find toggle inside
            btn = child.get_child()
            tag = getattr(btn, "_tag", None)
            # toggle logic: if active select, else clear
            if btn.get_active():
                # ensure single selection visual
                for c in range(flow.get_first_child().__len__() if False else 0): pass
                # deactivate others
                ch = flow.get_first_child()
                while ch:
                    b = ch.get_child()
                    if b is not btn: b.set_active(False)
                    ch = ch.get_next_sibling()
                on_select_tag(tag)
            else:
                on_select_tag(None)
        # use clicked on each button instead of flow activation for simplicity
        # rebind clicked
        ch = flow.get_first_child()
        while ch:
            b = ch.get_child()
            # disconnect previous if any, connect new
            try:
                b.connect("toggled", lambda btn, _ch=ch: on_select_tag(btn._tag if btn.get_active() else None))
            except Exception:
                pass
            ch = ch.get_next_sibling()

    _refresh()
    root.append(flow)

    # clear button subtle
    clear = Gtk.Button(label="Clear filter")
    clear.add_css_class("flat"); clear.add_css_class("pill")
    clear.set_tooltip_text("Show all notes")
    clear.connect("clicked", lambda *_: (on_select_tag(None), _clear_visual()))
    def _clear_visual():
        ch = flow.get_first_child()
        while ch:
            b = ch.get_child()
            try: b.set_active(False)
            except: pass
            ch = ch.get_next_sibling()
    root.append(clear)

    # empty hint
    empty_lbl = Gtk.Label(label="No tags yet — type #tag in a note", xalign=0)
    empty_lbl.add_css_class("dim-label"); empty_lbl.add_css_class("caption")
    empty_lbl.set_wrap(True)
    root.append(empty_lbl)

    def _update_empty():
        has = flow.get_first_child() is not None
        flow.set_visible(has); empty_lbl.set_visible(not has); clear.set_visible(has)
    _update_empty()
    # store hook
    try:
        store.model.connect("items-changed", lambda *_: (_refresh(), _update_empty()))
    except Exception:
        pass
    root._refresh = _refresh
    return root
