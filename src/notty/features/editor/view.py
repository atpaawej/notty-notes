"""Editor — Apple Notes: centered paper, floating toolbar, all states."""
def build_editor(on_text_changed):
    try:
        import gi
        gi.require_version('Gtk', '4.0')
        try:
            gi.require_version('GtkSource', '5')
            from gi.repository import Gtk, GtkSource, Pango
            HAS_SOURCE = True
        except Exception:
            from gi.repository import Gtk, Pango
            GtkSource = None
            HAS_SOURCE = False
    except Exception:
        return None

    root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0, hexpand=True, vexpand=True)
    root.add_css_class("notty-editor-wrap")

    # — Toolbar: Apple grouped pill —
    bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3, halign=Gtk.Align.CENTER)
    bar.add_css_class("notty-toolbar")

    buf_ref = {"buf": None}

    def _wrap(prefix, suffix=""):
        buf = buf_ref["buf"]
        if not buf:
            return
        try:
            bounds = buf.get_selection_bounds()
        except Exception:
            bounds = None
        if bounds and len(bounds) == 2:
            s, e = bounds
            txt = buf.get_text(s, e, False)
            buf.delete(s, e)
            buf.insert(s, f"{prefix}{txt}{suffix}")
        else:
            it = buf.get_iter_at_mark(buf.get_insert())
            buf.insert(it, prefix + suffix)
            # place cursor between if suffix
            if suffix:
                cur = buf.get_iter_at_mark(buf.get_insert())
                cur.backward_chars(len(suffix))
                buf.place_cursor(cur)

    def _btn(icon, tip, fn):
        b = Gtk.Button(icon_name=icon)
        b.add_css_class("flat")
        b.add_css_class("circular")
        b.set_tooltip_text(tip)
        b.connect("clicked", lambda *_: fn())
        bar.append(b)
        return b

    _btn("format-text-bold-symbolic", "Bold (⌘B)", lambda: _wrap("**", "**"))
    _btn("format-text-italic-symbolic", "Italic (⌘I)", lambda: _wrap("*", "*"))
    _btn("format-text-strikethrough-symbolic", "Strikethrough", lambda: _wrap("~~", "~~"))
    sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
    bar.append(sep)
    _btn("format-indent-more-symbolic", "Heading", lambda: _wrap("# "))
    _btn("view-list-bullet-symbolic", "Bullet list", lambda: _wrap("- "))
    _btn("view-list-ordered-symbolic", "Numbered list", lambda: _wrap("1. "))
    _btn("checkbox-symbolic", "Checklist", lambda: _wrap("- [ ] "))
    sep2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
    bar.append(sep2)
    _btn("mail-mark-important-symbolic", "Highlight", lambda: _wrap("==", "=="))
    _btn("insert-link-symbolic", "Link", lambda: _wrap("[", "](url)"))

    root.append(bar)

    # — Editor card centered via clamp —
    # Use Gtk.ScrolledWindow + margins for centering
    if HAS_SOURCE:
        buf = GtkSource.Buffer()
        tv = GtkSource.View.new_with_buffer(buf)
        tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        tv.set_top_margin(22); tv.set_bottom_margin(28); tv.set_left_margin(26); tv.set_right_margin(26)
        tv.add_css_class("notty-editor")
        lang = GtkSource.LanguageManager.get_default().get_language("markdown")
        if lang:
            buf.set_language(lang)
            buf.set_highlight_syntax(True)
        # nicer font
        tv.set_pixels_below_lines(5)
        tv.set_pixels_inside_wrap(2)
    else:
        buf = Gtk.TextBuffer()
        tv = Gtk.TextView.new_with_buffer(buf)
        tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        tv.set_top_margin(22); tv.set_left_margin(26); tv.set_right_margin(26); tv.set_bottom_margin(28)
        tv.add_css_class("notty-editor")

    tv.set_vexpand(True); tv.set_hexpand(True)
    tv.set_accepts_tab(False)
    tv.set_left_margin(28); tv.set_right_margin(28)
    buf_ref["buf"] = buf

    # clamp scroll
    scroll = Gtk.ScrolledWindow(child=tv, vexpand=True, hexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
    scroll.add_css_class("notty-editor-card")
    scroll.set_vexpand(True)
    # Center with max width via margins: wrap in box with alignment
    clamp_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, hexpand=True, vexpand=True, halign=Gtk.Align.FILL)
    clamp_box.append(scroll)
    clamp_box.add_css_class("notty-editor-clamp")

    outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True, vexpand=True, halign=Gtk.Align.FILL)
    outer.set_halign(Gtk.Align.FILL)
    # center clamp: use CenterBox
    center = Gtk.CenterBox(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True, vexpand=True)
    center.set_center_widget(clamp_box)
    center.set_hexpand(True)

    stack = Gtk.Stack(vexpand=True, hexpand=True, transition_type=Gtk.StackTransitionType.CROSSFADE)
    stack.add_named(center, "editor")

    # — Empty states: 3 variants —
    # 1. No note selected
    empty_select = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, vexpand=True, hexpand=True)
    empty_select.add_css_class("notty-empty")
    eimg = Gtk.Image.new_from_icon_name("document-edit-symbolic")
    eimg.set_pixel_size(64)
    et = Gtk.Label(label="No Note Selected")
    et.set_markup('<b>No Note Selected</b>')
    et.add_css_class("title")
    es = Gtk.Label(label="Choose a note from the list\nor create a new one")
    es.add_css_class("subtitle"); es.add_css_class("dim-label")
    es.set_justify(Gtk.Justification.CENTER)
    es.set_wrap(True)
    create_btn = Gtk.Button(label="New Note")
    create_btn.add_css_class("suggested-action"); create_btn.add_css_class("pill"); create_btn.add_css_class("notty-empty-cta")
    create_btn.set_icon_name("list-add-symbolic")
    empty_select.append(eimg); empty_select.append(et); empty_select.append(es); empty_select.append(create_btn)
    stack.add_named(empty_select, "empty")

    # 2. Locked note
    locked_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, vexpand=True, hexpand=True)
    locked_box.add_css_class("notty-empty")
    limg = Gtk.Image.new_from_icon_name("system-lock-screen-symbolic")
    limg.set_pixel_size(64)
    lt = Gtk.Label(label="Note Locked")
    lt.set_markup('<b>Note Locked</b>')
    lt.add_css_class("title")
    ls = Gtk.Label(label="Unlock to view and edit this note")
    ls.add_css_class("subtitle"); ls.add_css_class("dim-label")
    unlock_btn = Gtk.Button(label="Unlock Note")
    unlock_btn.add_css_class("pill")
    locked_box.append(limg); locked_box.append(lt); locked_box.append(ls); locked_box.append(unlock_btn)
    stack.add_named(locked_box, "locked")

    stack.set_visible_child_name("empty")
    root.append(stack)

    # signal
    def _changed(*_):
        try:
            txt = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
            on_text_changed(txt)
        except Exception:
            pass
    buf.connect("changed", _changed)

    root._stack = stack
    root._buf = buf
    root._tv = tv
    root._create_btn = create_btn
    root._unlock_btn = unlock_btn
    root._empty_select = empty_select
    root._locked_box = locked_box
    return root, buf, tv
