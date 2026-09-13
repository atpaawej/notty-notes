from notty.shared.db import Db
class NotesRepo:
    def __init__(self, db:Db): self.db=db
    def list(self, **kw): return self.db.list_notes(**kw)
    def delete(self,nid): self.db.delete_note(nid)
    def toggle_pin(self,nid): return self.db.toggle_pin(nid)
