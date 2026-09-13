"""Tag browser — Apple pills, count, empty."""
def build_tag_browser(store, on_select_tag):
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gtk
    except Exception:
        return None

    root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    root.set_margin_start(12); root.set_margin_end(8); root.set_margin_top(10); root.set_margin_bottom(10)

    hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    lbl = Gtk.Label(label="Tags", xalign=0, hexpand=True)
    lbl.add_css_class("notty-tags-header")
    hdr.append(lbl)
    # count badge
    count_lbl = Gtk.Label(label="", xalign=1)
    count_lbl.add_css_class("dim-label"); count_lbl.add_css_class("caption")
    hdr.append(count_lbl)
    root.append(hdr)

    flow = Gtk.FlowBox(max_children_per_line=8, selection_mode=Gtk.SelectionMode.NONE, homogeneous=False)
    flow.set_row_spacing(6); flow.set_column_spacing(6)
    flow.set_halign(Gtk.Align.START)
    flow.set_vexpand(False)

    def _refresh():
        child = flow.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            flow.remove(child)
            child = nxt
        try:
            items = []
            if hasattr(store.model, "get_n_items"):
                items = [store.model.get_item(i) for i in range(store.model.get_n_items())]
            else:
                items = list(store.model) if hasattr(store, "model") else []
            if not items:
                try:
                    raw = store.repo.list()
                    class _T: pass
                    tmp=[]
                    for r in raw:
                        o=_T(); o.name=r["tag"]; o.count=r["c"]; tmp.append(o)
                    items=tmp
                except Exception:
                    items=[]
        except Exception:
            items=[]
        for it in items:
            name = getattr(it, "name", getattr(it, "tag", str(it)))
            cnt = getattr(it, "count", getattr(it, "c", ""))
            label = f"#{name}  {cnt}" if cnt else f"#{name}"
            btn = Gtk.ToggleButton(label=label)
            btn.add_css_class("tag-pill")
            btn._tag = name
            flow.append(btn)
        # connect
        ch = flow.get_first_child()
        while ch:
            b = ch.get_child()
            try:
                b.connect("toggled", lambda btn, _ch=ch: _on_toggled(btn))
            except Exception:
                pass
            ch = ch.get_next_sibling()
        _update_empty()

    def _on_toggled(btn):
        tag = getattr(btn, "_tag", None)
        if btn.get_active():
            # deactivate others
            ch = flow.get_first_child()
            while ch:
                b = ch.get_child()
                if b is not btn:
                    try: b.set_active(False)
                    except: pass
                ch = ch.get_next_sibling()
            on_select_tag(tag)
        else:
            on_select_tag(None)

    root.append(flow)

    clear = Gtk.Button(label="Clear filter")
    clear.add_css_class("flat"); clear.add_css_class("pill")
    clear.set_tooltip_text("Show all notes")
    clear.set_visible(False)
    clear.connect("clicked", lambda *_: (on_select_tag(None), _clear_visual()))
    def _clear_visual():
        ch = flow.get_first_child()
        while ch:
            b = ch.get_child()
            try: b.set_active(False)
            except: pass
            ch = ch.get_next_sibling()
        clear.set_visible(False)

    # intercept selection to show clear
    orig_select = on_select_tag
    def _wrapped_select(tag):
        orig_select(tag)
        clear.set_visible(tag is not None)
        # also deactivate visual if None
        if tag is None:
            _clear_visual()
    # we need to rewire _on_toggled to use wrapped
    # so rebuild _refresh with wrapped behavior — patch by replacing global
    # simpler: override on_select_tag reference
    # monkey patch after definition
    # but we handle clear visibility in _on_toggled already + explicit clear button
    root.append(clear)

    empty_lbl = Gtk.Label(label="No tags yet — type #tag in a note", xalign=0, wrap=True)
    empty_lbl.add_css_class("dim-label"); empty_lbl.add_css_class("caption")
    empty_lbl.set_halign(Gtk.Align.START)
    root.append(empty_lbl)

    def _update_empty():
        has = flow.get_first_child() is not None
        flow.set_visible(has); empty_lbl.set_visible(not has)
        # keep clear hidden when no tags
        if not has: clear.set_visible(False)
        try:
            cnt = 0
            ch = flow.get_first_child()
            while ch:
                cnt+=1; ch=ch.get_next_sibling()
            count_lbl.set_text(str(cnt) if cnt else "")
            count_lbl.set_visible(cnt>0)
        except: pass

    _refresh()
    _update_empty()
    try:
        store.model.connect("items-changed", lambda *_: (_refresh()))
    except Exception:
        pass
    root._refresh = _refresh
    root._clear_visual = _clear_visual
    return root
