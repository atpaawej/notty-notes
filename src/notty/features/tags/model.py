from dataclasses import dataclass
@dataclass(slots=True)
class Tag:
    name: str
    count: int
