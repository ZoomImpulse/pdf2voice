from __future__ import annotations

from pathlib import Path
from typing import Callable


def extract_pdf(
    pdf_path: str | Path,
    progress_cb: Callable[[int, int], None] | None = None,
) -> str:
    """Extract text from a PDF as Markdown, preserving heading structure."""
    import pymupdf4llm
    import fitz  # pymupdf

    path = str(pdf_path)

    try:
        doc = fitz.open(path)
        total_pages = len(doc)
        doc.close()

        def _page_cb(page_num: int) -> None:
            if progress_cb:
                progress_cb(page_num + 1, total_pages)

        md = pymupdf4llm.to_markdown(
            path,
            page_chunks=False,
            show_progress=False,
        )

        if progress_cb:
            progress_cb(total_pages, total_pages)

        return md

    except Exception as exc:
        raise RuntimeError(f"PDF extraction failed: {exc}") from exc


def count_pages(pdf_path: str | Path) -> int:
    import fitz
    doc = fitz.open(str(pdf_path))
    n = len(doc)
    doc.close()
    return n
