from pathlib import Path

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def export_masked(masked_text: str, original_path: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = original_path.suffix.lower()
    name = f"{original_path.stem}_masked{suffix if suffix in {'.docx', '.pdf'} else '.pdf'}"
    destination = target_dir / name

    if suffix == ".docx":
        _write_docx(masked_text, destination)
    else:
        _write_pdf(masked_text, destination)

    return destination


def _write_docx(masked_text: str, destination: Path) -> None:
    doc = Document()
    for line in masked_text.splitlines():
        doc.add_paragraph(line)
    doc.save(destination)


def _write_pdf(masked_text: str, destination: Path) -> None:
    pdf = canvas.Canvas(str(destination), pagesize=A4)
    width, height = A4
    margin = 40
    max_width = width - 2 * margin
    y = height - margin
    for line in masked_text.splitlines():
        if y < margin:
            pdf.showPage()
            y = height - margin
        pdf.drawString(margin, y, line[: int(max_width // 7)])
        y -= 15
    pdf.save()
