import html
from typing import List

from app.models.entity_model import MaskingOptions, SensitiveEntity, sort_entities

CLASS_MAP = {
    "PERSON": "entity-person",
    "COMPANY": "entity-company",
    "PROJECT": "entity-project",
    "REKVIZIT": "entity-rekvizit",
}


def mask_text(full_text: str, entities: List[SensitiveEntity], options: MaskingOptions) -> str:
    masked_parts: list[str] = []
    cursor = 0

    for entity in sort_entities(entities):
        if entity.start < cursor:
            continue
        masked_parts.append(full_text[cursor : entity.start])
        masked_parts.append(options.render_mask(entity))
        cursor = max(cursor, entity.end)

    masked_parts.append(full_text[cursor:])
    return "".join(masked_parts)


def highlight_text(full_text: str, entities: List[SensitiveEntity]) -> str:
    highlighted: list[str] = []
    cursor = 0

    for entity in sort_entities(entities):
        if entity.start < cursor:
            continue
        highlighted.append(html.escape(full_text[cursor : entity.start]))
        css_class = CLASS_MAP.get(entity.type.upper(), "entity-default")
        entity_html = html.escape(full_text[entity.start : entity.end])
        highlighted.append(f'<span class="{css_class}">{entity_html}</span>')
        cursor = max(cursor, entity.end)

    highlighted.append(html.escape(full_text[cursor:]))
    return "".join(highlighted)
