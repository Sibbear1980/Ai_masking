from dataclasses import dataclass
from typing import List


@dataclass
class SensitiveEntity:
    type: str
    text: str
    start: int
    end: int


@dataclass
class MaskingOptions:
    style: str = "asterisks"  # asterisks or tags

    def render_mask(self, entity: SensitiveEntity) -> str:
        if self.style == "tags":
            return f"[{entity.type}]"
        return "*" * max(len(entity.text), entity.end - entity.start)


def sort_entities(entities: List[SensitiveEntity]) -> List[SensitiveEntity]:
    return sorted(entities, key=lambda item: (item.start, item.end))
