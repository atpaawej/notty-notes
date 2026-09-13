def build_editor(on_text_changed):
    try:
        import gi; gi.require_version('Gtk','4.0'); gi.require_version('GtkSource','5')
        from gi.repository import Gtk, GtkSource
        HAS_SOURCE=True
    except Exception:
        HAS_SOURCE=False
        try:
            import gi; gi.require_version('Gtk','4.0')
            from gi.repository import Gtk
        except Exception: return None
    if HAS_SOURCE:
        buf=GtkSource.Buffer(); tv=GtkSource.View.new_with_buffer(buf)
        tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR); tv.set_top_margin(12); tv.set_left_margin(12); tv.set_right_margin(12)
        lang=GtkSource.LanguageManager.get_default().get_language("markdown")
        if lang: buf.set_language(lang); buf.set_highlight_syntax(True)
    else:
        buf=Gtk.TextBuffer(); tv=Gtk.TextView.new_with_buffer(buf)
        tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR); tv.set_top_margin(12); tv.set_left_margin(12)
    tv.add_css_class("card"); tv.set_vexpand(True); tv.set_hexpand(True)
    # formatting popover
    pop=Gtk.Box(spacing=4)
    for label, markup in [("B","<b>B</b>"),("I","<i>I</i>"),("•","•"),("☑","☑")]:
        b=Gtk.Button(label=label); pop.append(b)
        def _fmt(btn, m=markup):
            bnd=buf.get_selection_bounds()
            if bnd: s,e=bnd; txt=buf.get_text(s,e,False); buf.delete(s,e); buf.insert(s, f"**{txt}**" if m=="<b>B</b>" else f"*{txt}*" if m=="<i>I</i>" else f"- {txt}" if m=="•" else f"- [ ] {txt}")
        b.connect("clicked", _fmt)
    scroll=Gtk.ScrolledWindow(child=tv, vexpand=True, hexpand=True)
    container=Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    container.append(pop); container.append(scroll)
    # signal
    buf.connect("changed", lambda *_: on_text_changed(buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)))
    # drag-drop image placeholder -> markdown ![image](path)
    try:
        drop=Gtk.DropTarget.new(type=object, actions=2)
        container.add_controller(drop)
    except Exception: pass
    return container, buf, tv
