from typing import List

import pytesseract
from PIL import Image

from app.models.document_model import DocumentModel, TextBlock


def parse_images(images: List[Image.Image], lang: str) -> DocumentModel:
    blocks = []
    offset = 0

    for idx, image in enumerate(images):
        raw_text = pytesseract.image_to_string(image, lang=lang) or ""
        text = raw_text.rstrip() + "\n"
        blocks.append(TextBlock(page=idx + 1, text=text, start_offset=offset))
        offset += len(text)

    return DocumentModel.from_blocks(blocks)
