from __future__ import annotations

import os
from pathlib import Path
from typing import Callable


def extract_pdf(
    pdf_path: str | Path,
    progress_cb: Callable[[int, int], None] | None = None,
) -> str:
    """Extract text from a PDF as Markdown, preserving heading structure.

    Uses pymupdf4llm for reliable page-by-page extraction with real progress.
    Falls back to raw PyMuPDF text extraction if pymupdf4llm is unavailable.
    """
    return extract_pdf_pymupdf4llm(pdf_path, progress_cb)


def extract_pdf_pymupdf4llm(
    pdf_path: str | Path,
    progress_cb: Callable[[int, int], None] | None = None,
) -> str:
    """Extract PDF using pymupdf4llm — reliable, page-by-page, with real progress."""
    import pymupdf4llm
    import fitz  # pymupdf

    path = str(pdf_path)

    try:
        doc = fitz.open(path)
        total_pages = len(doc)
        doc.close()

        # Use page_chunks=True so we get one dict per page and can emit
        # per-page progress instead of a single silent blocking call.
        page_dicts = pymupdf4llm.to_markdown(
            path,
            page_chunks=True,
            show_progress=False,
        )

        parts: list[str] = []
        for i, page in enumerate(page_dicts):
            parts.append(page["text"] if isinstance(page, dict) else page)
            if progress_cb:
                progress_cb(i + 1, total_pages)

        return "\n".join(parts)

    except Exception as exc:
        raise RuntimeError(f"PDF extraction failed (pymupdf4llm): {exc}") from exc




def extract_toc(pdf_path: str | Path) -> list[tuple[int, str, int]]:
    """Extract the PDF's internal outline/bookmarks via PyMuPDF.

    Returns a list of (level, title, page_number) tuples where level 1 means
    top-level entry.  Returns an empty list when the PDF has no embedded
    outline or when PyMuPDF is unavailable.

    Only entries at level 1 (or, if the outline is exclusively level 2+, at
    the minimum level present) are returned so that callers always get the
    primary chapter tier rather than sub-sections.
    """
    try:
        import fitz
    except ImportError:
        return []

    try:
        doc = fitz.open(str(pdf_path))
        raw: list[tuple[int, str, int]] = doc.get_toc(simple=True)  # [(level, title, page), …]
        doc.close()
    except Exception:
        return []

    if not raw:
        return []

    # Determine the top tier (usually 1, but some PDFs start at 2)
    min_level = min(entry[0] for entry in raw)
    top_tier = [(lvl, title.strip(), page) for lvl, title, page in raw if lvl == min_level]
    return top_tier


def extract_toc_from_pages(
    pdf_path: str | Path,
    max_pages: int = 8,
    log_cb = None,
) -> list[tuple[int, str, int]]:
    """Extract TOC from the first pages of a PDF using text extraction + LLM parsing.

    Extracts raw text from the first pages using PyMuPDF, finds the page that looks
    like a table of contents, then asks the configured LLM to parse chapter names.
    Returns (level, title, page_number) tuples. Returns empty list on failure.
    """
    try:
        import fitz
    except ImportError:
        if log_cb:
            log_cb("TOC Text: PyMuPDF (fitz) not installed")
        return []
    import re

    try:
        from src.config import OPENROUTER_API_KEY, OPENROUTER_MODEL
        from src.pipeline.adapter import _call_openrouter
    except Exception as e:
        if log_cb:
            log_cb(f"TOC Text: Config/adapter import failed ({e})")
        return []

    try:
        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)
        pages_to_scan = min(max_pages, total_pages)

        if log_cb:
            log_cb(f"TOC Text: Scanning first {pages_to_scan} pages for TOC …")

        toc_page_text: str | None = None
        toc_page_num: int = -1

        for page_num in range(pages_to_scan):
            text = doc[page_num].get_text()
            text_lower = text.lower()
            has_contents_heading = any(
                kw in text_lower for kw in ("contents", "table of contents", "inhaltsverzeichnis")
            )
            line_count = len([l for l in text.splitlines() if l.strip()])
            if has_contents_heading and line_count >= 3:
                if log_cb:
                    log_cb(f"TOC Text: Found TOC candidate on page {page_num + 1}")
                toc_page_text = text
                toc_page_num = page_num + 1
                break

        doc.close()

        if toc_page_text is None:
            if log_cb:
                log_cb("TOC Text: No TOC page found in first pages")
            return []

        if log_cb:
            log_cb(f"TOC Text: Sending page {toc_page_num} text to {OPENROUTER_MODEL} for parsing …")

        prompt = f"""The following is the text content of a Table of Contents page from a book.
Extract every chapter or top-level section. For each entry output exactly one line:
TITLE | NUMBER

Where NUMBER is the chapter number or page number shown (use 0 if none).
Output only the list, no explanations.

Text:
{toc_page_text}"""

        raw = _call_openrouter(prompt, OPENROUTER_MODEL, OPENROUTER_API_KEY)

        if log_cb:
            log_cb(f"TOC Text: Raw LLM response: {raw[:300]}")

        # Parse "TITLE | NUMBER" lines
        toc: list[tuple[int, str, int]] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" in line:
                parts = line.split("|", 1)
                title = parts[0].strip().lstrip("-•*0123456789. ")
                num_str = parts[1].strip() if len(parts) > 1 else "0"
                num_match = re.search(r"\d+", num_str)
                num = int(num_match.group()) if num_match else 0
                if title:
                    toc.append((1, title, num))

        if log_cb and toc:
            log_cb(f"TOC Text: Extracted {len(toc)} TOC entries")
        elif log_cb:
            log_cb("TOC Text: Could not parse any entries from LLM response")

        return toc

    except Exception as e:
        if log_cb:
            log_cb(f"TOC Text: Extraction failed ({e})")
        return []


def count_pages(pdf_path: str | Path) -> int:
    """Count pages in PDF (works with both extraction methods)."""
    import fitz
    doc = fitz.open(str(pdf_path))
    n = len(doc)
    doc.close()
    return n
