"""Editor — paper card, grouped toolbar, proper empty state."""
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

    root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, hexpand=True, vexpand=True)
    root.set_margin_top(8); root.set_margin_start(8); root.set_margin_end(8); root.set_margin_bottom(8)

    # toolbar — grouped, not floating pills
    bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    bar.add_css_class("notty-toolbar")
    # helper to create markdown-wrapping buttons
    def _btn(icon, tip, wrap_fn):
        b = Gtk.Button(icon_name=icon)
        b.add_css_class("flat"); b.set_tooltip_text(tip)
        b.connect("clicked", lambda *_: wrap_fn())
        bar.append(b)
        return b

    # will be bound after buffer created
    buf_ref = {"buf": None}

    def _wrap(prefix, suffix=""):
        buf = buf_ref["buf"]
        if not buf: return
        bounds = buf.get_selection_bounds()
        if bounds:
            s, e = bounds
            txt = buf.get_text(s, e, False)
            buf.delete(s, e)
            buf.insert(s, f"{prefix}{txt}{suffix}")
        else:
            it = buf.get_iter_at_mark(buf.get_insert())
            buf.insert(it, prefix)

    # toolbar groups
    _btn("format-text-bold-symbolic", "Bold", lambda: _wrap("**", "**"))
    _btn("format-text-italic-symbolic", "Italic", lambda: _wrap("*", "*"))
    _btn("format-text-strikethrough-symbolic", "Strikethrough", lambda: _wrap("~~", "~~"))
    sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL); bar.append(sep)
    _btn("format-text-heading-symbolic", "Heading", lambda: _wrap("# "))
    _btn("view-list-bullet-symbolic", "Bulleted list", lambda: _wrap("- "))
    _btn("view-list-ordered-symbolic", "Numbered", lambda: _wrap("1. "))
    _btn("checkbox-symbolic", "Checklist", lambda: _wrap("- [ ] "))
    sep2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL); bar.append(sep2)
    _btn("view-pinned-symbolic", "Highlight", lambda: _wrap("==", "=="))

    root.append(bar)

    # editor card
    if HAS_SOURCE:
        buf = GtkSource.Buffer()
        tv = GtkSource.View.new_with_buffer(buf)
        tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        tv.set_top_margin(18); tv.set_bottom_margin(18); tv.set_left_margin(18); tv.set_right_margin(18)
        tv.add_css_class("notty-editor")
        lang = GtkSource.LanguageManager.get_default().get_language("markdown")
        if lang:
            buf.set_language(lang); buf.set_highlight_syntax(True)
        # line spacing
        tv.set_pixels_below_lines(4)
    else:
        buf = Gtk.TextBuffer()
        tv = Gtk.TextView.new_with_buffer(buf)
        tv.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        tv.set_top_margin(18); tv.set_left_margin(18); tv.set_right_margin(18)
        tv.add_css_class("notty-editor")

    tv.set_vexpand(True); tv.set_hexpand(True)
    tv.set_accepts_tab(False)
    buf_ref["buf"] = buf

    # stack: editor vs empty placeholder
    stack = Gtk.Stack(vexpand=True, hexpand=True)
    scroll = Gtk.ScrolledWindow(child=tv, vexpand=True, hexpand=True)
    scroll.add_css_class("notty-editor")
    stack.add_named(scroll, "editor")

    empty = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, vexpand=True)
    empty.add_css_class("notty-empty")
    eimg = Gtk.Image.new_from_icon_name("document-edit-symbolic"); eimg.set_pixel_size(56)
    et = Gtk.Label(label="Select a note"); et.set_markup("<b>Select a note to start writing</b>"); et.add_css_class("title")
    es = Gtk.Label(label="or create a new one with +"); es.add_css_class("dim-label")
    empty.append(eimg); empty.append(et); empty.append(es)
    stack.add_named(empty, "empty")
    stack.set_visible_child_name("empty")

    root.append(stack)

    # signal
    buf.connect("changed", lambda *_: on_text_changed(buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)))

    # helper to switch stack from outside
    root._stack = stack
    root._buf = buf
    root._tv = tv
    return root, buf, tv
