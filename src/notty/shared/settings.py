"""GSettings wrapper with headless fallback (JSON) for CI/no-GSettings envs."""
import json, os
from pathlib import Path

# Disable GSettings in CI/headless where schema not compiled - prevents fatal GLib-GIO-ERROR abort
_HAS_GIO = False
if os.getenv("NOTTY_USE_GSETTINGS") == "1":
    try:
        import gi
        gi.require_version('Gio', '2.0')
        from gi.repository import Gio
        if "app.notty.Notty" in Gio.Settings.list_schemas():
            _HAS_GIO = True
    except Exception:
        _HAS_GIO = False

_DEFAULTS = {"window-width":1100,"window-height":700,"sidebar-width":220,"notes-width":340,"color-scheme":"system"}

class Settings:
    def __init__(self, app_id="app.notty.Notty"):
        self._path = Path(os.getenv("XDG_CONFIG_HOME", Path.home()/".config")) / "notty" / "settings.json"
        self._mem = dict(_DEFAULTS)
        self._gio = None
        if _HAS_GIO:
            try:
                self._gio = Gio.Settings.new(app_id)
                return
            except Exception:
                self._gio = None
        if self._path.exists():
            try: self._mem.update(json.loads(self._path.read_text()))
            except Exception: pass

    def get_int(self,k): 
        return self._gio.get_int(k) if self._gio else int(self._mem.get(k,_DEFAULTS[k]))
    def get_string(self,k): 
        return self._gio.get_string(k) if self._gio else str(self._mem.get(k,_DEFAULTS[k]))
    def set_int(self,k,v):
        if self._gio: self._gio.set_int(k,v)
        else: self._mem[k]=int(v); self._save()
    def set_string(self,k,v):
        if self._gio: self._gio.set_string(k,v)
        else: self._mem[k]=str(v); self._save()
    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._mem))
