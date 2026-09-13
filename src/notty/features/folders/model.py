from dataclasses import dataclass

@dataclass(slots=True)
class Folder:
    id: str
    name: str
    created_at: int
