from dataclasses import dataclass
@dataclass(slots=True)
class EditorState:
    note_id: str | None = None
    dirty: bool = False
    locked: bool = False
