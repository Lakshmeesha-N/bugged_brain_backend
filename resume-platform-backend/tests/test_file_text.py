import io
from docx import Document
import pytest
from src.utils.file_text import FileTooLarge, NoTextFound, UnsupportedFileType, extract_text
from src.utils.pdf import html_to_pdf


def create_sample_pdf(text: str) -> bytes:
    html = f"<html><body><p>{text}</p></body></html>"
    return html_to_pdf(html)


def create_sample_docx(text: str) -> bytes:
    doc = Document()
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_extract_text_pdf_success():
    long_text = "This is a detailed and complete software engineering resume with lots of text exceeding one hundred characters easily for testing PDF extraction."
    pdf_bytes = create_sample_pdf(long_text)
    extracted = extract_text("resume.pdf", pdf_bytes)
    assert "software engineering" in extracted
    assert len(extracted) >= 100


def test_extract_text_docx_success():
    long_text = "This is a detailed and complete software engineering resume with lots of text exceeding one hundred characters easily for testing DOCX extraction."
    docx_bytes = create_sample_docx(long_text)
    extracted = extract_text("resume.docx", docx_bytes)
    assert "software engineering" in extracted
    assert len(extracted) >= 100


def test_extract_text_unsupported_file_type():
    with pytest.raises(UnsupportedFileType):
        extract_text("resume.txt", b"some plain text content")


def test_extract_text_file_too_large():
    oversized = b"a" * (5 * 1024 * 1024 + 10)
    with pytest.raises(FileTooLarge):
        extract_text("resume.pdf", oversized)


def test_extract_text_no_text_found():
    short_text = "Too short"
    docx_bytes = create_sample_docx(short_text)
    with pytest.raises(NoTextFound):
        extract_text("short.docx", docx_bytes)
