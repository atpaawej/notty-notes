try:
    import gi; gi.require_version('GObject','2.0')
    from gi.repository import GObject
    HAS=True
except Exception: HAS=False; GObject=None
if HAS:
    class SearchStore(GObject.Object):
        __gtype_name__="SearchStore"
        query=GObject.Property(type=str, default=""); pinned_only=GObject.Property(type=bool, default=False)
        def __init__(self): super().__init__(); self._tag=None
        def set_tag(self,t): self._tag=t; self.notify("query")
        def get_tag(self): return self._tag
else:
    class SearchStore:
        def __init__(self): self.query=""; self.pinned_only=False; self._tag=None
        def set_tag(self,t): self._tag=t
        def get_tag(self): return self._tag
