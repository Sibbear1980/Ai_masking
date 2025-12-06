from pathlib import Path

from docx import Document

from app.models.document_model import DocumentModel, TextBlock


def parse_docx(path: Path) -> DocumentModel:
    doc = Document(path)
    blocks = []
    offset = 0

    for para in doc.paragraphs:
        text = para.text or ""
        text_with_break = text + "\n"
        blocks.append(TextBlock(page=None, text=text_with_break, start_offset=offset))
        offset += len(text_with_break)

    return DocumentModel.from_blocks(blocks)
