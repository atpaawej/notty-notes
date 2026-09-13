from notty.shared.db import Db
class TagRepo:
    def __init__(self, db:Db): self.db=db
    def list(self): return self.db.list_tags()
