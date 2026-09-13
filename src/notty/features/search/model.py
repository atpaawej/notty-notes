from dataclasses import dataclass
@dataclass(slots=True)
class SearchState:
    query: str = ""
    pinned_only: bool = False
    tag: str | None = None
