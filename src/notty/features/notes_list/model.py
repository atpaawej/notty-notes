from dataclasses import dataclass
from typing import Optional
@dataclass(slots=True)
class NoteItem:
    id: str
    folder_id: Optional[str]
    title: str
    preview: str
    pinned: int
    updated_at: int
