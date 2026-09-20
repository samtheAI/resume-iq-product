"""Safe text extraction helpers for supported resume file types."""

from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


class ResumeReadError(ValueError):
    """Raised when usable text cannot be extracted from a resume."""


def _normalize_text(text: str) -> str:
    """Remove unnecessary whitespace while preserving separate text lines."""
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def _read_pdf(content: bytes) -> str:
    """Read text from every page of a text-based PDF."""
    try:
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as error:
        raise ResumeReadError("The PDF could not be read.") from error


def _read_docx(content: bytes) -> str:
    """Read and join all paragraphs from a Word document."""
    try:
        document = Document(BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    except Exception as error:
        raise ResumeReadError("The DOCX file could not be read.") from error


def _read_txt(content: bytes) -> str:
    """Decode a text file, with Latin-1 as a fallback encoding."""
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return content.decode("latin-1")
        except UnicodeDecodeError as error:
            raise ResumeReadError("The text file encoding is not supported.") from error


def extract_resume_text(filename: str, content: bytes) -> str:
    """Extract and validate text from one PDF, DOCX, or TXT resume."""
    suffix = Path(filename).suffix.lower()
    # Select the correct reader based on the uploaded file extension.
    readers = {".pdf": _read_pdf, ".docx": _read_docx, ".txt": _read_txt}

    if suffix not in readers:
        raise ResumeReadError("Only PDF, DOCX, and TXT resumes are supported.")

    text = _normalize_text(readers[suffix](content))
    if len(text) < 100:
        raise ResumeReadError(
            "Very little text was extracted. The file may be scanned, empty, "
            "or image-based. Please upload a text-based resume."
        )

    # Limit the prompt size before sending text to the language model.
    return text[:50_000]
