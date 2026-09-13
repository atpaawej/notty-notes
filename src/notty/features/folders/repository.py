"""Thin repo - delegates to shared.Db, kept for VSA extensibility."""
from src.notty.shared.db import Db
class FolderRepo:
    def __init__(self, db: Db): self.db=db
    def create(self,fid,name,ts): self.db.create_folder(fid,name,ts)
    def rename(self,fid,name): self.db.rename_folder(fid,name)
    def delete(self,fid): self.db.delete_folder(fid)
    def list(self): return self.db.list_folders()
