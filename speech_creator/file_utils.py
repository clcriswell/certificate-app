"""File utilities for extracting text from uploaded files."""
from __future__ import annotations

from typing import IO
from pathlib import Path
import io

import fitz  # PyMuPDF
from docx import Document


def extract_text(uploaded_file) -> str:
    """Extract text from an uploaded file (txt, pdf, docx)."""
    if not uploaded_file:
        return ""

    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)
    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix == ".txt":
        return file_bytes.decode("utf-8", errors="ignore")
    if suffix == ".pdf":
        try:
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                return "\n".join(page.get_text() for page in doc)
        except Exception:
            return ""
    if suffix == ".docx":
        with io.BytesIO(file_bytes) as buf:
            doc = Document(buf)
            return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError(f"Unsupported file type: {suffix}")
