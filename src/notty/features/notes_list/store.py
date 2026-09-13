"""NotesListStore - single filtered query, no in-memory filtering (DB does it)."""
import time
try:
    import gi; gi.require_version('GObject','2.0'); gi.require_version('Gio','2.0')
    from gi.repository import GObject, Gio
    HAS=True
except Exception: HAS=False; GObject=Gio=None

from .repository import NotesRepo

if HAS:
    class NoteRow(GObject.Object):
        __gtype_name__="NoteRow"
        nid=GObject.Property(type=str); title=GObject.Property(type=str)
        preview=GObject.Property(type=str); pinned=GObject.Property(type=int)
        def __init__(self,r): super().__init__(); self.nid=r["id"]; self.title=r["title"] or "Untitled"; self.preview=r["preview"]; self.pinned=r["pinned"]; self._raw=r
    class NotesListStore(GObject.Object):
        def __init__(self, repo:NotesRepo):
            super().__init__(); self.repo=repo; self.model=Gio.ListStore.new(NoteRow)
            self.folder="__all__"; self.query=""; self.tag=None; self.pinned_only=False
        def apply(self, folder="__all__", query="", tag=None, pinned_only=False):
            self.folder,self.query,self.tag,self.pinned_only=folder,query,tag,pinned_only
            rows=self.repo.list(folder_id=folder, query=query, tag=tag, pinned_only=pinned_only)
            self.model.remove_all()
            for r in rows: self.model.append(NoteRow(r))
        def delete(self,nid):
            self.repo.delete(nid)
            for i in range(self.model.get_n_items()):
                if self.model.get_item(i).nid==nid: self.model.remove(i); break
        def toggle_pin(self,nid):
            v=self.repo.toggle_pin(nid); self.apply(self.folder,self.query,self.tag,self.pinned_only); return v
else:
    class NotesListStore:
        def __init__(self,repo): self.repo=repo; self.rows=[]
        def apply(self,folder="__all__",query="",tag=None,pinned_only=False):
            self.folder,self.query,self.tag,self.pinned_only=folder,query,tag,pinned_only
            self.rows=list(self.repo.list(folder_id=folder,query=query,tag=tag,pinned_only=pinned_only))
        def delete(self,nid): self.repo.delete(nid); self.apply(self.folder,self.query,self.tag,self.pinned_only)
        def toggle_pin(self,nid): return self.repo.toggle_pin(nid) or self.apply(self.folder,self.query,self.tag,self.pinned_only)
        @property
        def model(self): return self.rows
