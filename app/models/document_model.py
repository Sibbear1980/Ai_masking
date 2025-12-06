from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TextBlock:
    page: Optional[int]
    text: str
    start_offset: int


@dataclass
class DocumentModel:
    blocks: List[TextBlock]
    full_text: str

    @classmethod
    def from_blocks(cls, blocks: List[TextBlock]) -> "DocumentModel":
        full_text = "".join(block.text for block in blocks)
        return cls(blocks=blocks, full_text=full_text)
