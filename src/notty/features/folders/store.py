"""FoldersStore - Gio.ListStore backed, emits signals for AppState."""
import time, uuid
try:
    import gi; gi.require_version('GObject','2.0'); gi.require_version('Gio','2.0')
    from gi.repository import GObject, Gio
    HAS_GIO=True
except Exception:
    HAS_GIO=False
    GObject=Gio=None

from .repository import FolderRepo
from .model import Folder

if HAS_GIO:
    class FolderItem(GObject.Object):
        __gtype_name__="FolderItem"
        fid=GObject.Property(type=str); name=GObject.Property(type=str)
        def __init__(self,fid,name): super().__init__(); self.fid=fid; self.name=name
    class FoldersStore(GObject.Object):
        __gtype_name__="FoldersStore"
        def __init__(self,repo:FolderRepo):
            super().__init__(); self.repo=repo; self.model=Gio.ListStore.new(FolderItem)
            self._load()
        def _load(self):
            self.model.remove_all()
            for r in self.repo.list(): self.model.append(FolderItem(r["id"], r["name"]))
        def create(self,name:str)->str:
            fid=uuid.uuid4().hex[:8]; self.repo.create(fid,name,int(time.time())); self.model.append(FolderItem(fid,name)); return fid
        def rename(self,fid,name):
            self.repo.rename(fid,name)
            for i in range(self.model.get_n_items()):
                it=self.model.get_item(i)
                if it.fid==fid: it.name=name; break
        def delete(self,fid):
            self.repo.delete(fid)
            for i in range(self.model.get_n_items()):
                if self.model.get_item(i).fid==fid: self.model.remove(i); break
else:
    # headless fallback for E2E logic tests
    class FoldersStore:
        def __init__(self,repo):
            self.repo=repo; self.items=[]
            for r in repo.list(): self.items.append(Folder(r["id"],r["name"],r["created_at"]))
        def create(self,name):
            import uuid,time
            fid=uuid.uuid4().hex[:8]; self.repo.create(fid,name,int(time.time())); self.items.append(Folder(fid,name,int(time.time()))); return fid
        def rename(self,fid,name): self.repo.rename(fid,name); [setattr(x,"name",name) for x in self.items if x.id==fid]
        def delete(self,fid): self.repo.delete(fid); self.items=[x for x in self.items if x.id!=fid]
        @property
        def model(self): return self.items
