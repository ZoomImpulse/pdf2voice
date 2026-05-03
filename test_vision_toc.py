#!/usr/bin/env python3
"""Manual test for vision-based TOC extraction."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline.extractor import extract_toc_from_pages, extract_toc


def test_vision_toc(pdf_path: str):
    """Test both embedded and vision TOC extraction."""
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print(f"📄 Testing: {pdf_path.name}\n")
    
    # Test embedded TOC
    print("1️⃣  Testing embedded TOC extraction…")
    embedded_toc = extract_toc(str(pdf_path))
    
    if embedded_toc:
        print(f"✅ Embedded TOC found ({len(embedded_toc)} entries):")
        for level, title, page in embedded_toc[:5]:  # Show first 5
            print(f"   [{page:3d}] {title}")
        if len(embedded_toc) > 5:
            print(f"   ... and {len(embedded_toc) - 5} more")
    else:
        print("⚠️  No embedded TOC found")
    
    print()
    
    # Test vision TOC
    print("2️⃣  Testing vision-based TOC extraction…")
    print("   (Rendering pages and sending to llava:7b)\n")

    # Quick sanity check: is Ollama reachable?
    try:
        import ollama
        models = ollama.list()
        model_names = [m.get("name", "") if isinstance(m, dict) else str(m) for m in models.get("models", [])]
        clean_names = [m.split("'")[1] if "model=" in m else m for m in model_names]
        print(f"   📦 Ollama models: {clean_names}")
    except Exception as e:
        print(f"   ❌ Ollama not reachable: {e}")
        print("   Make sure Ollama is running: ollama serve")
        return

    # Save rendered images so we can verify what the model sees
    import fitz, base64
    doc = fitz.open(str(pdf_path))
    pages_to_render = min(8, len(doc))
    print(f"\n   🖼️  Saving rendered pages to output/debug_page_*.png …")
    Path("output").mkdir(exist_ok=True)
    for i in range(pages_to_render):
        pix = doc[i].get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        out_path = f"output/debug_page_{i+1:02d}.png"
        pix.save(out_path)
        print(f"   Saved: {out_path}")
    doc.close()
    print()

    def log_cb(msg):
        print(f"   💬 {msg}")

    vision_toc = extract_toc_from_pages(str(pdf_path), max_pages=8, log_cb=log_cb)
    
    if vision_toc:
        print(f"\n✅ Vision TOC found ({len(vision_toc)} entries):")
        for level, title, page in vision_toc:
            print(f"   [{page:3d}] {title}")
    else:
        print("\n⚠️  No vision TOC extracted")
    
    print()
    print("=" * 60)
    print("Summary:")
    print(f"  Embedded: {len(embedded_toc)} entries" if embedded_toc else "  Embedded: None")
    print(f"  Vision:   {len(vision_toc)} entries" if vision_toc else "  Vision:   None")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_vision_toc.py <pdf_path>")
        print()
        print("Example: python test_vision_toc.py input/sample.pdf")
        sys.exit(1)
    
    test_vision_toc(sys.argv[1])
