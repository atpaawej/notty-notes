class PinLockStore:
    def __init__(self, db): self.db=db
    def toggle_pin(self, nid): return self.db.toggle_pin(nid)
    def toggle_lock(self, nid): return self.db.toggle_lock(nid)
