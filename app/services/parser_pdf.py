from pathlib import Path
from typing import Optional

import pdfplumber
from pdf2image import convert_from_path

from app.models.document_model import DocumentModel, TextBlock
from app.services import parser_ocr


def parse_pdf(path: Path, ocr_lang: str = "rus+eng") -> DocumentModel:
    blocks = []
    offset = 0

    with pdfplumber.open(path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            cleaned = text.rstrip()
            if cleaned:
                page_text = cleaned + "\n"
                blocks.append(
                    TextBlock(page=page_index + 1, text=page_text, start_offset=offset)
                )
                offset += len(page_text)

    if blocks:
        return DocumentModel.from_blocks(blocks)

    ocr_document = _parse_pdf_with_ocr(path, ocr_lang)
    if ocr_document:
        return ocr_document

    return DocumentModel(blocks=[], full_text="")


def _parse_pdf_with_ocr(path: Path, ocr_lang: str) -> Optional[DocumentModel]:
    try:
        images = convert_from_path(path)
    except Exception:
        return None

    return parser_ocr.parse_images(images, lang=ocr_lang)
