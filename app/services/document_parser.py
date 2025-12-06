from pathlib import Path
from typing import Iterable

from PIL import Image

from app.models.document_model import DocumentModel
from app.services.parser_docx import parse_docx
from app.services.parser_pdf import parse_pdf
from app.services.parser_ocr import parse_images

SUPPORTED_EXTENSIONS = {".docx", ".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}


class UnsupportedFile(Exception):
    pass


def is_supported(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS


def parse_document(path: Path, mime_type: str | None = None, ocr_lang: str = "rus+eng") -> DocumentModel:
    suffix = path.suffix.lower()

    if suffix == ".docx":
        return parse_docx(path)

    if suffix == ".pdf":
        return parse_pdf(path, ocr_lang=ocr_lang)

    if suffix in IMAGE_EXTENSIONS:
        return _parse_image(path, ocr_lang)

    raise UnsupportedFile(f"Unsupported file type: {suffix}")


def _parse_image(path: Path, ocr_lang: str) -> DocumentModel:
    image = Image.open(path)
    return parse_images([image], lang=ocr_lang)
