"""Pre-process Docling Markdown before LLM structuring — no LLM required.

Responsibilities:
- Clean artifacts: image placeholders, page numbers, URLs, footnotes, repeated headers/footers
- Detect language heuristically
- Expand common abbreviations (de / en) for TTS clarity
- Parse chapter boundaries from ## headings (Docling convention)
- Split chapter text into TTS-sized chunks at sentence boundaries
- Extract document title from # H1
- Infer subdivision_type from ## heading patterns (e.g. "Kapitel 1", "Chapter 3")

The output is a PreprocessResult that contains all chapter/chunk data ready for TTS,
plus a short `sample` string (~2 000 chars) for a fast LLM metadata call (language + genre only).
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable

from src.config import TTS_CHUNK_SIZE

_SILENCE_CHUNK_S: float = 0.6  # silence after a mid-paragraph chunk
_SILENCE_PARA_S:  float = 1.2  # silence after the last chunk of a paragraph

# ── Abbreviation dictionaries ─────────────────────────────────────────────────
# Keys are raw regex patterns (without word-boundary anchors — added dynamically).
# Values are plain replacement strings.

_ABBREV_DE: dict[str, str] = {
    r"bzw\.":        "beziehungsweise",
    r"d\.h\.":       "das heißt",
    r"z\.B\.":       "zum Beispiel",
    r"z\.\s*B\.":    "zum Beispiel",
    r"u\.a\.":       "unter anderem",
    r"u\.\s*a\.":    "unter anderem",
    r"usw\.":        "und so weiter",
    r"etc\.":        "et cetera",
    r"vs\.":         "versus",
    r"Nr\.":         "Nummer",
    r"Abb\.":        "Abbildung",
    r"ca\.":         "circa",
    r"inkl\.":       "inklusive",
    r"exkl\.":       "exklusive",
    r"sog\.":        "sogenannte",
    r"sogen\.":      "sogenannte",
    r"max\.":        "maximal",
    r"min\.":        "minimal",
    r"bzgl\.":       "bezüglich",
    r"ggf\.":        "gegebenenfalls",
    r"evtl\.":       "eventuell",
    r"o\.ä\.":       "oder ähnliches",
    r"o\.\s*ä\.":    "oder ähnliches",
    r"i\.d\.R\.":    "in der Regel",
    r"z\.T\.":       "zum Teil",
    r"z\.\s*T\.":    "zum Teil",
    r"entspr\.":     "entsprechend",
    r"vgl\.":        "vergleiche",
    r"Prof\.":       "Professor",
    r"Dr\.":         "Doktor",
    r"Hrsg\.":       "Herausgeber",
    r"Jh\.":         "Jahrhundert",
    r"Jhd\.":        "Jahrhundert",
    r"Bd\.":         "Band",
    r"Kap\.":        "Kapitel",
    r"Abs\.":        "Absatz",
    r"bes\.":        "besonders",
    r"allg\.":       "allgemein",
    r"bspw\.":       "beispielsweise",
    r"insb\.":       "insbesondere",
    r"zw\.":         "zwischen",
}

_ABBREV_EN: dict[str, str] = {
    r"etc\.":        "et cetera",
    r"vs\.":         "versus",
    r"e\.g\.":       "for example",
    r"i\.e\.":       "that is",
    r"approx\.":     "approximately",
    r"fig\.":        "figure",
    r"Fig\.":        "Figure",
    r"no\.":         "number",
    r"No\.":         "Number",
    r"vol\.":        "volume",
    r"Vol\.":        "Volume",
    r"ed\.":         "edition",
    r"Ed\.":         "Edition",
    r"pp\.":         "pages",
    r"cf\.":         "compare",
    r"ibid\.":       "in the same work",
    r"et\s+al\.":    "and others",
    r"Dr\.":         "Doctor",
    r"Prof\.":       "Professor",
    r"Mr\.":         "Mister",
    r"Mrs\.":        "Missus",
    r"Ms\.":         "Miss",
    r"Inc\.":        "Incorporated",
    r"Ltd\.":        "Limited",
    r"Corp\.":       "Corporation",
    r"dept\.":       "department",
    r"Dept\.":       "Department",
    r"avg\.":        "average",
    r"govt\.":       "government",
    r"Govt\.":       "Government",
    r"natl\.":       "national",
    r"intl\.":       "international",
    r"assn\.":       "association",
}


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class RawChapter:
    title: str
    chunks: list[str] = field(default_factory=list)
    chunk_pauses: list[float] = field(default_factory=list)


@dataclass
class PreprocessResult:
    title: str
    language: str                    # heuristic language detection ("de" | "en")
    subdivision_type: str            # e.g. "Kapitel" — empty if undetected
    chapters: list[RawChapter]
    sample: str                      # ≤2 500-char excerpt for LLM metadata call
    structure_suspect: bool = False  # True when Docling may have over-split chapters


# ── Public API ────────────────────────────────────────────────────────────────

def preprocess(
    markdown: str,
    toc: list[tuple[int, str, int]] | None = None,
    log_cb: Callable[[str], None] | None = None,
) -> PreprocessResult:
    """Clean, structure, and chunk Docling Markdown without calling any LLM.

    Args:
        markdown: Docling-produced Markdown text.
        toc: Optional PDF outline extracted by extractor.extract_toc().
             Each entry is (level, title, page_number).  When provided and
             reliable, chapter boundaries are determined by matching TOC
             titles to H2 headings rather than by heuristics alone.
    """
    cleaned = _clean(markdown)
    title = _extract_title(cleaned)
    subdivision_type = _detect_subdivision(cleaned)
    lang = _detect_language(cleaned[:4000])

    chapters_raw = _split_chapters(cleaned, toc, log_cb=log_cb)
    chapters: list[RawChapter] = []
    for ch_title, ch_text in chapters_raw:
        expanded = _expand_abbreviations(ch_text, lang)
        chunks: list[str] = []
        pauses: list[float] = []
        for para in re.split(r"\n{2,}", expanded):
            para = para.strip()
            if not para:
                continue
            para_chunks = _chunk_text(para)
            for i, chunk in enumerate(para_chunks):
                chunks.append(chunk)
                pauses.append(_SILENCE_PARA_S if i == len(para_chunks) - 1 else _SILENCE_CHUNK_S)
        if chunks:
            chapters.append(RawChapter(title=ch_title, chunks=chunks, chunk_pauses=pauses))

    # Build a compact sample for the LLM (language + genre detection only)
    sample_parts: list[str] = []
    if title:
        sample_parts.append(title)
    for ch in chapters[:4]:
        if ch.title:
            sample_parts.append(ch.title)
        if ch.chunks:
            sample_parts.append(ch.chunks[0][:600])
    sample = "\n\n".join(filter(None, sample_parts))[:2500]

    structure_suspect = _detect_suspect_structure(chapters)

    return PreprocessResult(
        title=title,
        language=lang,
        subdivision_type=subdivision_type,
        chapters=chapters,
        sample=sample,
        structure_suspect=structure_suspect,
    )


# ── Structure suspicion heuristics ───────────────────────────────────────────

# Patterns that indicate a chapter "title" is really a verse number, sub-heading,
# or other non-chapter heading that Docling promoted to ##.
_SUSPECT_TITLE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\d+$"),                                    # bare number: "42"
    re.compile(r"^\d+[:.]\d+"),                             # chapter:verse: "3:16"
    re.compile(r"^(verse|vers|psalm|absatz|strophe)\s+\d+", re.IGNORECASE),
    re.compile(r"^(section|abschnitt|paragraph|§)\s+\d+",   re.IGNORECASE),
    re.compile(r"^\d+\.\s+\w"),                             # "1. Something" (numbered subheading)
]

_SUSPECT_CHAPTER_THRESHOLD = 40       # more than this is probably over-split
_SUSPECT_TITLE_RATIO       = 0.30     # fraction of titles matching patterns to flag
_SUSPECT_MEDIAN_CHUNKS     = 2        # median chunks-per-chapter below this is thin


def _detect_suspect_structure(chapters: list[RawChapter]) -> bool:
    """Return True when Docling appears to have over-split the chapter structure."""
    if not chapters:
        return False

    # Too many chapters
    if len(chapters) > _SUSPECT_CHAPTER_THRESHOLD:
        return True

    # High fraction of titles that look like verse/section numbers
    if chapters:
        suspect_count = sum(
            1 for ch in chapters
            if any(p.match(ch.title.strip()) for p in _SUSPECT_TITLE_PATTERNS)
        )
        if suspect_count / len(chapters) >= _SUSPECT_TITLE_RATIO:
            return True

    # Median chunk count is suspiciously thin
    chunk_counts = sorted(len(ch.chunks) for ch in chapters)
    median = chunk_counts[len(chunk_counts) // 2]
    if median <= _SUSPECT_MEDIAN_CHUNKS:
        return True

    return False


# ── Cleaning ──────────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    # 1. Remove Docling image / figure / formula / table placeholders
    text = re.sub(r"<!--\s*(?:image|figure|formula|table)\s*-->", "", text, flags=re.IGNORECASE)

    # 2. Remove fenced code blocks (not meaningful as spoken audio)
    text = re.sub(r"```[\s\S]*?```", "", text)

    # 3. Strip markdown table separator rows (|---|---|)
    text = re.sub(r"^\|[\s\-:|]+\|\s*$", "", text, flags=re.MULTILINE)

    # 4. Strip table pipe delimiters from data rows — keep cell text, join with spaces
    text = re.sub(
        r"^\|(.+?)\|\s*$",
        lambda m: "  ".join(c.strip() for c in m.group(1).split("|") if c.strip()),
        text,
        flags=re.MULTILINE,
    )

    # 5. Remove bare URLs
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"www\.\S+", "", text)

    # 6. Remove footnote definitions:  [^1]: explanation text
    text = re.sub(r"^\[\^[^\]]+\]:.*$", "", text, flags=re.MULTILINE)

    # 7. Remove inline footnote references:  [^1]
    text = re.sub(r"\[\^[^\]]+\]", "", text)

    # 7b. Strip markdown links but preserve the link text: [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)

    # 7c. Strip editorial bracket annotations — keep inner text: [Job] → Job
    text = re.sub(r"\[([^\]]+)\]", r"\1", text)

    # 8. Strip H3–H6 heading markers (keep the heading text as readable prose)
    text = re.sub(r"^#{3,6}\s+", "", text, flags=re.MULTILINE)

    # 9. Strip bold/italic markers — longest pattern first to avoid partial matches
    text = re.sub(r"\*{3}(.+?)\*{3}", r"\1", text)  # ***bold italic***
    text = re.sub(r"\*{2}(.+?)\*{2}", r"\1", text)  # **bold**
    text = re.sub(r"_{2}(.+?)_{2}",   r"\1", text)  # __bold__
    text = re.sub(r"\*(.+?)\*",       r"\1", text)  # *italic*

    # 10. Strip inline code backticks (keep the code text itself)
    text = re.sub(r"`([^`\n]+)`", r"\1", text)

    # 11. Strip bullet list markers (-, *, +)
    text = re.sub(r"^[ \t]*[-*+]\s+", "", text, flags=re.MULTILINE)

    # 12. Strip ordered list markers (1. or 1))
    text = re.sub(r"^[ \t]*\d+[.)]\s+", "", text, flags=re.MULTILINE)

    # 13. Remove lines that are only a number (page numbers) or only Roman numerals
    text = re.sub(
        r"^\s*(?:M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})|\d+)\s*$",
        "",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    # 13b. Expand scripture chapter:verse notation for clean TTS: 38:4-7 → 38, 4 to 7
    text = re.sub(
        r"\b(\d+):(\d+)(?:[-–](\d+))?",
        lambda m: f"{m.group(1)}, {m.group(2)}" + (f" to {m.group(3)}" if m.group(3) else ""),
        text,
    )

    # 13c. Remove inline verse numbers between sentences: "earth? 5 Who" → "earth? Who"
    text = re.sub(r"(?<=[.!?])\s+\d{1,3}\s+(?=[A-Z])", " ", text)
    # Remove a leading verse number at paragraph start: "4 Where" → "Where"
    text = re.sub(r"(?m)^\d{1,3}\s+(?=[A-Z])", "", text)

    # 14. Remove frequently repeating lines (running headers / footers)
    text = _remove_repeated_lines(text, min_occurrences=3)

    # 15. Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def _remove_repeated_lines(text: str, min_occurrences: int = 3) -> str:
    """Delete lines that appear identically ≥ min_occurrences times (headers/footers)."""
    lines = text.splitlines()
    freq: Counter[str] = Counter(
        line.strip() for line in lines if line.strip() and not line.startswith("#")
    )
    repeated = {line for line, n in freq.items() if n >= min_occurrences}
    if not repeated:
        return text
    kept = [line for line in lines if line.strip() not in repeated]
    return "\n".join(kept)


# ── Title extraction ──────────────────────────────────────────────────────────

def _extract_title(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


# ── Subdivision-type detection ────────────────────────────────────────────────

_SUBDIVISION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^##\s+Kapitel\s+\d",   re.MULTILINE | re.IGNORECASE), "Kapitel"),
    (re.compile(r"^##\s+Teil\s+\d",      re.MULTILINE | re.IGNORECASE), "Teil"),
    (re.compile(r"^##\s+Abschnitt\s+\d", re.MULTILINE | re.IGNORECASE), "Abschnitt"),
    (re.compile(r"^##\s+Chapter\s+\d",   re.MULTILINE | re.IGNORECASE), "Chapter"),
    (re.compile(r"^##\s+Part\s+\d",      re.MULTILINE | re.IGNORECASE), "Part"),
    (re.compile(r"^##\s+Section\s+\d",   re.MULTILINE | re.IGNORECASE), "Section"),
    (re.compile(r"^##\s+Book\s+\d",      re.MULTILINE | re.IGNORECASE), "Book"),
    (re.compile(r"^##\s+Act\s+\d",       re.MULTILINE | re.IGNORECASE), "Act"),
    (re.compile(r"^##\s+Canto\s+\d",     re.MULTILINE | re.IGNORECASE), "Canto"),
]


def _detect_subdivision(text: str) -> str:
    for pattern, label in _SUBDIVISION_PATTERNS:
        if pattern.search(text):
            return label
    return ""  # LLM will fill this in from the sample


# ── Language detection ────────────────────────────────────────────────────────

def _detect_language(text: str) -> str:
    german = len(re.findall(
        r"\b(und|der|die|das|ist|mit|für|ein|eine|des|dem|den|ich|sie|er|wir|auf|von|aber|auch|noch|nicht)\b",
        text, re.IGNORECASE,
    ))
    english = len(re.findall(
        r"\b(the|and|is|with|for|a|an|of|in|to|it|that|was|has|are|be|this|at|by|from|or)\b",
        text, re.IGNORECASE,
    ))
    return "de" if german > english else "en"


# ── Chapter splitting ─────────────────────────────────────────────────────────

# Minimum fuzzy-match similarity to accept a TOC title → H2 heading match.
_TOC_MATCH_THRESHOLD = 0.55
# A TOC is considered reliable when this fraction of its entries match H2 headings.
_TOC_RELIABLE_RATIO  = 0.60


def _toc_similarity(a: str, b: str) -> float:
    """Return a 0–1 similarity score between two strings, normalised."""
    from difflib import SequenceMatcher
    a = re.sub(r"[^\w\s]", "", a.lower()).strip()
    b = re.sub(r"[^\w\s]", "", b.lower()).strip()
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _split_chapters(
    markdown: str,
    toc: list[tuple[int, str, int]] | None = None,
    log_cb: Callable[[str], None] | None = None,
) -> list[tuple[str, str]]:
    """Split at ## (H2) boundaries.  Returns list of (title, body) tuples.

    When *toc* is provided, first attempts to find TOC titles directly in the
    text and split there — bypassing H2 headings entirely.  Falls back to H2
    splitting if TOC matching is too unreliable.
    """
    # ── TOC-guided splitting (preferred when TOC available) ──────────────────
    if toc and len(toc) >= 2:
        result = _split_by_toc(markdown, toc, log_cb)
        if result is not None:
            return result
        if log_cb:
            log_cb("Preprocessing: TOC split unreliable — falling back to H2 heading split")

    # ── Baseline H2 split ────────────────────────────────────────────────────
    return _split_by_h2(markdown)


def _split_by_toc(
    markdown: str,
    toc: list[tuple[int, str, int]],
    log_cb: Callable[[str], None] | None = None,
) -> list[tuple[str, str]] | None:
    """Find each TOC chapter title in the document text and split there.

    Returns (title, body) list using the TOC title as authoritative chapter
    name, or None when hit rate is below _TOC_RELIABLE_RATIO.
    """
    lines = markdown.splitlines()
    toc_entries = [(title.strip(), page) for _, title, page in toc if title.strip()]
    if not toc_entries:
        return None

    # Detect the TOC page block in the extracted text and exclude it from
    # the chapter-boundary search — otherwise every title would match there first.
    toc_block_end = 0
    for i, line in enumerate(lines):
        if re.search(r"\b(contents|table of contents)\b", line, re.IGNORECASE):
            # Scan forward: skip lines until we hit a long content paragraph
            for j in range(i + 1, min(i + 80, len(lines))):
                # A content paragraph has many words and no leading digits/dots pattern
                stripped = lines[j].strip()
                if len(stripped.split()) > 15 and not re.match(r"^[\d\.\s]+$", stripped):
                    toc_block_end = j
                    break
            if toc_block_end:
                break

    # For each TOC title find the best-matching line in the document
    found: list[tuple[int, str]] = []  # (line_index, toc_title)
    for toc_title, _ in toc_entries:
        best_score = 0.0
        best_idx = -1
        for i, line in enumerate(lines):
            if i < toc_block_end:
                continue  # skip TOC page itself
            clean = re.sub(r"^#{1,6}\s+", "", line).strip()
            # Also strip single-underscore italic markers that pymupdf4llm emits
            clean = clean.strip("_").strip()
            if not clean:
                continue
            score = _toc_similarity(toc_title, clean)
            if score > best_score:
                best_score = score
                best_idx = i
        if best_score >= _TOC_MATCH_THRESHOLD and best_idx >= 0:
            found.append((best_idx, toc_title))

    hit_rate = len(found) / len(toc_entries)
    if log_cb:
        log_cb(
            f"Preprocessing: TOC text search — {len(found)}/{len(toc_entries)} "
            f"entries matched ({hit_rate:.0%})"
        )

    if hit_rate < _TOC_RELIABLE_RATIO:
        return None

    # Sort by document position and deduplicate overlapping matches
    found.sort(key=lambda x: x[0])
    deduped: list[tuple[int, str]] = []
    for idx, title in found:
        if deduped and idx == deduped[-1][0]:
            continue  # skip duplicate line matches
        deduped.append((idx, title))

    # Build chapters: body = lines between this title and the next
    chapters: list[tuple[str, str]] = []
    for i, (line_idx, toc_title) in enumerate(deduped):
        body_start = line_idx + 1
        body_end = deduped[i + 1][0] if i + 1 < len(deduped) else len(lines)
        body_lines = lines[body_start:body_end]
        # Strip heading markers left inside the body
        body_lines = [re.sub(r"^#{1,6}\s+", "", l) for l in body_lines]
        body = "\n".join(body_lines).strip()
        if body:
            chapters.append((toc_title, body))

    return chapters if chapters else None


def _split_by_h2(markdown: str) -> list[tuple[str, str]]:
    """Baseline: split at ## (H2) boundaries."""
    lines = markdown.splitlines()
    chapters: list[tuple[str, str]] = []
    current_title = ""
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            if current_lines or current_title:
                body = "\n".join(current_lines).strip()
                if body:
                    chapters.append((current_title, body))
            current_title = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Flush last chapter
    if current_lines or current_title:
        body = "\n".join(current_lines).strip()
        if body:
            chapters.append((current_title, body))

    # No ## headings — treat entire body as one chapter
    if not chapters:
        body = "\n".join(l for l in lines if not l.startswith("# ")).strip()
        if body:
            chapters = [("", body)]

    return chapters


# ── Abbreviation expansion ────────────────────────────────────────────────────

def _expand_abbreviations(text: str, lang: str = "en") -> str:
    """Replace known abbreviations with their spoken forms."""
    abbrevs = _ABBREV_DE if lang == "de" else _ABBREV_EN
    for pattern, replacement in abbrevs.items():
        # Add a negative look-behind for word chars so we don't match mid-word
        text = re.sub(r"(?<![A-Za-zÄÖÜäöüß])" + pattern, replacement, text)
    return text


# ── TTS chunking ──────────────────────────────────────────────────────────────

def _chunk_text(text: str) -> list[str]:
    """Split text into TTS-sized chunks at sentence boundaries."""
    # Split after sentence-ending punctuation when followed by whitespace + uppercase
    sentences = re.split(r'(?<=[.!?…])\s+(?=[A-ZÄÖÜ"\'\u201e\u201c])', text.strip())
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 > TTS_CHUNK_SIZE and current:
            chunks.append(current.strip())
            current = sentence
        else:
            current = (current + " " + sentence).strip() if current else sentence
    if current.strip():
        chunks.append(current.strip())
    return [c for c in chunks if c.strip()]


# Public aliases for external callers (e.g. chapter text editor re-chunking)
chunk_text      = _chunk_text
SILENCE_PARA_S  = _SILENCE_PARA_S
SILENCE_CHUNK_S = _SILENCE_CHUNK_S
