from __future__ import annotations

from io import BytesIO

import pdfplumber


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """
    Extract plain text from a PDF file represented as bytes.

    This function is intentionally simple and deterministic:
    - Reads every page in order
    - Concatenates text with double newlines between pages
    - Strips leading/trailing whitespace
    """
    if not file_bytes:
        return ""

    text_chunks: list[str] = []

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            page_text = page_text.strip()
            if page_text:
                text_chunks.append(page_text)

    return "\n\n".join(text_chunks).strip()


def extract_text_from_plain_bytes(file_bytes: bytes, encoding: str = "utf-8") -> str:
    """
    Decode a plain-text resume from raw bytes.

    Uses a forgiving decoder to avoid errors on slightly malformed text.
    """
    if not file_bytes:
        return ""

    return file_bytes.decode(encoding, errors="ignore").strip()

