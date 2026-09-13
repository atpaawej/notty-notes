from src.notty.shared.db import Db
class EditorRepo:
    def __init__(self,db:Db): self.db=db
    def load(self,nid): return self.db.get_note(nid)
    def save(self,nid,title,body,ts): self.db.update_note(nid,title,body,ts)
    def create(self,nid,folder_id,title,body,ts): self.db.create_note(nid,folder_id,title,body,ts)
