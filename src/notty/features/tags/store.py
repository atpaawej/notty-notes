from .repository import TagRepo
try:
    import gi; gi.require_version('GObject','2.0'); gi.require_version('Gio','2.0')
    from gi.repository import GObject, Gio
    HAS=True
except Exception: HAS=False
if HAS:
    class TagItem(GObject.Object):
        __gtype_name__="TagItem"
        name=GObject.Property(type=str); count=GObject.Property(type=int)
        def __init__(self,n,c): super().__init__(); self.name=n; self.count=c
    class TagStore(GObject.Object):
        def __init__(self,repo:TagRepo): super().__init__(); self.repo=repo; self.model=Gio.ListStore.new(TagItem); self.refresh()
        def refresh(self):
            self.model.remove_all()
            for r in self.repo.list(): self.model.append(TagItem(r["tag"], r["c"]))
else:
    class TagStore:
        def __init__(self,repo): self.repo=repo; self.items=[]
        def refresh(self): self.items=list(self.repo.list())
        @property
        def model(self): return self.items
