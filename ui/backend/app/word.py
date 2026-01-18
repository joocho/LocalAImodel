from pathlib import Path


def write_docx(text: str, out_path: Path) -> None:
    from docx import Document

    doc = Document()
    for line in text.splitlines():
        # Keep empty lines as blank paragraphs
        doc.add_paragraph(line)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
