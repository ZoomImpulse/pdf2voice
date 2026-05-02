from __future__ import annotations

import os
from pathlib import Path
from typing import Callable


def extract_pdf(
    pdf_path: str | Path,
    progress_cb: Callable[[int, int], None] | None = None,
) -> str:
    """Extract text from a PDF as Markdown, preserving heading structure.
    
    Uses Docling for layout-aware extraction (OCR disabled for memory efficiency).
    Preserves document structure, tables, and reading order.
    Requires: pip install docling
    """
    return extract_pdf_docling(pdf_path, progress_cb)


def extract_pdf_pymupdf4llm(
    pdf_path: str | Path,
    progress_cb: Callable[[int, int], None] | None = None,
) -> str:
    """Extract PDF using pymupdf4llm (lightweight, structure-light)."""
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


def extract_pdf_docling(
    pdf_path: str | Path,
    progress_cb: Callable[[int, int], None] | None = None,
) -> str:
    """Extract PDF using Docling (layout-aware, by IBM).
    
    Requires Python deps: pip install docling
    No system dependencies needed. OCR disabled to save memory.
    
    Returns Markdown with preserved layout, tables, and document structure.
    Uses Docling's layout analysis without text recognition (OCR).
    """
    try:
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import ConversionStatus, InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        import fitz  # For page count
    except ImportError as e:
        raise RuntimeError(
            f"Docling not installed. Run: pip install docling"
        ) from e

    path = str(pdf_path)

    try:
        # Count pages for progress reporting
        doc = fitz.open(path)
        total_pages = len(doc)
        doc.close()

        # Disable OCR to prevent memory overload (std::bad_alloc) on large PDFs.
        # PdfPipelineOptions.do_ocr=False skips RapidOCR models entirely.
        pipeline_options = PdfPipelineOptions(do_ocr=False)
        pdf_format_option = PdfFormatOption(pipeline_options=pipeline_options)
        converter = DocumentConverter(
            format_options={InputFormat.PDF: pdf_format_option}
        )
        
        # Emit initial progress
        if progress_cb:
            progress_cb(0, total_pages)
        
        # Convert PDF to DoclingDocument
        conversion_result = converter.convert(path)
        
        # Check conversion status
        if conversion_result.status != ConversionStatus.SUCCESS:
            raise RuntimeError(f"Docling conversion failed: {conversion_result.status}")
        
        # Export to Markdown (Docling preserves layout, tables, reading order)
        markdown = conversion_result.document.export_to_markdown()
        
        # Emit completion progress
        if progress_cb:
            progress_cb(total_pages, total_pages)
        
        return markdown.strip()

    except Exception as exc:
        raise RuntimeError(f"PDF extraction failed (Docling): {exc}") from exc




def count_pages(pdf_path: str | Path) -> int:
    """Count pages in PDF (works with both extraction methods)."""
    import fitz
    doc = fitz.open(str(pdf_path))
    n = len(doc)
    doc.close()
    return n
