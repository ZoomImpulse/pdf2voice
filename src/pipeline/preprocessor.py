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

from src.config import TTS_CHUNK_SIZE


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


@dataclass
class PreprocessResult:
    title: str
    language: str                    # heuristic language detection ("de" | "en")
    subdivision_type: str            # e.g. "Kapitel" — empty if undetected
    chapters: list[RawChapter]
    sample: str                      # ≤2 500-char excerpt for LLM metadata call


# ── Public API ────────────────────────────────────────────────────────────────

def preprocess(markdown: str) -> PreprocessResult:
    """Clean, structure, and chunk Docling Markdown without calling any LLM."""
    cleaned = _clean(markdown)
    title = _extract_title(cleaned)
    subdivision_type = _detect_subdivision(cleaned)
    lang = _detect_language(cleaned[:4000])

    chapters_raw = _split_chapters(cleaned)
    chapters: list[RawChapter] = []
    for ch_title, ch_text in chapters_raw:
        expanded = _expand_abbreviations(ch_text, lang)
        chunks = _chunk_text(expanded)
        if chunks:
            chapters.append(RawChapter(title=ch_title, chunks=chunks))

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

    return PreprocessResult(
        title=title,
        language=lang,
        subdivision_type=subdivision_type,
        chapters=chapters,
        sample=sample,
    )


# ── Cleaning ──────────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    # 1. Remove Docling image / figure / formula / table placeholders
    text = re.sub(r"<!--\s*(?:image|figure|formula|table)\s*-->", "", text, flags=re.IGNORECASE)

    # 2. Remove bare URLs
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"www\.\S+", "", text)

    # 3. Remove footnote definitions:  [^1]: explanation text
    text = re.sub(r"^\[\^[^\]]+\]:.*$", "", text, flags=re.MULTILINE)

    # 4. Remove inline footnote references:  [^1]
    text = re.sub(r"\[\^[^\]]+\]", "", text)

    # 5. Remove lines that are only a number (page numbers) or only Roman numerals
    text = re.sub(
        r"^\s*(?:M{0,4}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})|\d+)\s*$",
        "",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    # 6. Remove frequently repeating lines (running headers / footers)
    text = _remove_repeated_lines(text, min_occurrences=3)

    # 7. Collapse excessive blank lines
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

def _split_chapters(markdown: str) -> list[tuple[str, str]]:
    """Split at ## (H2) boundaries. Returns list of (title, body) tuples."""
    lines = markdown.splitlines()
    chapters: list[tuple[str, str]] = []
    current_title = ""
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("# "):
            # Document title — not a chapter boundary; skip
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
