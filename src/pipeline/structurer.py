from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Callable

import ollama

from src.config import GENRE_PROMPTS, LLM_MODEL, OLLAMA_URL, OPENROUTER_API_KEY, OPENROUTER_MODEL, TTS_VOICE_INSTRUCT
from src.pipeline.extractor import extract_toc as _extract_toc, extract_toc_from_pages as _extract_toc_vision
from src.pipeline.preprocessor import preprocess as _preprocess

# Genre keys exposed to the LLM — must stay in sync with GENRE_PROMPTS in config.py.
_GENRE_KEYS = list(GENRE_PROMPTS.keys())  # e.g. ["novel", "thriller", ...]

# Maps LLM free-text language responses to ISO-639-1 codes used for anchor filenames.
_LANG_ALIASES: dict[str, str] = {
    "de": "de", "german": "de", "deutsch": "de", "ger": "de",
    "en": "en", "english": "en", "eng": "en",
    "fr": "fr", "french": "fr", "français": "fr",
    "es": "es", "spanish": "es", "español": "es",
    "it": "it", "italian": "it", "italiano": "it",
    "pt": "pt", "portuguese": "pt", "português": "pt",
    "nl": "nl", "dutch": "nl",
    "pl": "pl", "polish": "pl",
    "ru": "ru", "russian": "ru",
    "zh": "zh", "chinese": "zh",
    "ja": "ja", "japanese": "ja",
}


def _normalize_lang(raw: str) -> str:
    """Return a canonical ISO-639-1 code for *raw*; fall back to the stripped lowercase value."""
    key = raw.strip().lower()
    if key in _LANG_ALIASES:
        return _LANG_ALIASES[key]
    # Also try just the first word, e.g. "German language" → "german"
    first_word = key.split()[0] if key else key
    return _LANG_ALIASES.get(first_word, first_word)

# ── Lightweight metadata-only prompt ─────────────────────────────────────────
# The structurer no longer sends the full document to the LLM.
# Text cleaning, chapter detection, and TTS chunking are done by preprocessor.py.
# The LLM only receives a short excerpt (~2 500 chars) and returns metadata.
METADATA_PROMPT = """\
You receive a short excerpt from a document. Return ONLY metadata as JSON.
No explanation, no markdown fences, no extra keys.

JSON format:
{{
  "title": "Document title",
  "language": "de or en",
  "genre": "one of: {genre_keys}",
  "subdivision_type": "word the book uses for chapters, e.g. Kapitel, Teil, Chapter, Part, Section — or empty string if unclear"
}}
"""
# Appended to METADATA_PROMPT when the heuristic suspects over-splitting.
STRUCTURE_FIX_ADDENDUM = """\
The chapter detector may have over-split this document (e.g. verse numbers or
sub-headings were mistaken for chapter boundaries).

The detected chapter titles (0-based index) are listed below.
Add a "merge_groups" key to your JSON: a list of lists, where each inner list
contains the 0-based indices of chapters that belong to the same true chapter
and should be merged. Use the first chapter\'s title as the merged title.
If the structure looks correct, return \"merge_groups\": [].

Example (merging verses 0-3 into one chapter, 4-7 into another):
  \"merge_groups\": [[0,1,2,3],[4,5,6,7]]

Detected chapter titles:
{chapter_titles}
"""

@dataclass
class Chapter:
    index: int
    title: str
    chunks: list[str] = field(default_factory=list)
    chunk_pauses: list[float] = field(default_factory=list)
    adapted_text: str | None = None   # LLM-adapted prose; None = use chunks as-is


@dataclass
class StructuredBook:
    title: str
    language: str
    voice_instruct: str
    genre: str = ""
    subdivision_type: str = "Chapter"
    chapters: list[Chapter] = field(default_factory=list)
    metadata_sample: str = ""  # short excerpt used for LLM metadata; empty for resumed sessions

    @property
    def total_chunks(self) -> int:
        return sum(len(c.chunks) for c in self.chapters)


def structure_content(
    markdown: str,
    log_cb: Callable[[str], None] | None = None,
    chapters_cb: Callable[[list[Chapter]], None] | None = None,
    check_pause: Callable[[], None] | None = None,
    progress_cb: Callable[[int], None] | None = None,
    model: str = LLM_MODEL,
    pdf_path: str | None = None,
    provider: str = "ollama",
    api_key: str = "",
    ollama_base_url: str = OLLAMA_URL,
) -> StructuredBook:
    """Structure markdown content for TTS generation.

    Pipeline:
    1. preprocessor.py cleans the text, detects chapters, expands abbreviations,
       and produces TTS chunks — all without any LLM call.
       When pdf_path is given the PDF outline (TOC) is extracted first and used
       to guide chapter splitting, overriding pure H2-heuristics where reliable.
    2. A short excerpt (~2 500 chars) is sent to the LLM to detect language and genre.
    3. Results are merged into a StructuredBook.
    """
    # ── Step 1: pre-process (no LLM) ─────────────────────────────────────────
    if log_cb:
        log_cb("Preprocessing: Cleaning text and extracting chapter structure …")

    # Try to extract the PDF's embedded outline for reliable chapter boundaries
    toc: list[tuple[int, str, int]] = []
    if pdf_path:
        toc = _extract_toc(pdf_path)
        if log_cb:
            if toc:
                log_cb(f"Preprocessing: PDF table of contents found ({len(toc)} entries) — using for chapter boundaries")
            else:
                log_cb("Preprocessing: No embedded TOC found — trying text TOC extraction via LLM …")
                toc = _extract_toc_vision(pdf_path, log_cb=log_cb)
                if not toc and log_cb:
                    log_cb("Preprocessing: Text TOC extraction found no entries — falling back to heading detection")

    pre = _preprocess(markdown, toc=toc or None, log_cb=log_cb)

    chapters: list[Chapter] = [
        Chapter(index=i + 1, title=raw.title, chunks=raw.chunks, chunk_pauses=raw.chunk_pauses)
        for i, raw in enumerate(pre.chapters)
    ]
    if not chapters:
        # Fallback: treat the whole document as one chapter
        from src.pipeline.preprocessor import _chunk_text as _pp_chunk, _SILENCE_PARA_S
        fallback_chunks = _pp_chunk(markdown)
        chapters = [Chapter(index=1, title="", chunks=fallback_chunks,
                            chunk_pauses=[_SILENCE_PARA_S] * len(fallback_chunks))]

    # Stream all chapters to the UI immediately — no need to wait for the LLM
    if chapters_cb and chapters:
        chapters_cb(chapters)

    if log_cb:
        total_chunks = sum(len(ch.chunks) for ch in chapters)
        log_cb(
            f"Preprocessing: {len(chapters)} chapters, {total_chunks} chunks "
            f"({len(markdown):,} → {sum(len(c) for ch in chapters for c in ch.chunks):,} chars)"
        )

    # ── Step 2: LLM metadata detection (tiny sample only) ────────────────────
    title            = pre.title
    language         = pre.language          # heuristic — overridden by LLM if available
    genre            = ""
    subdivision_type = pre.subdivision_type  # pattern-detected — overridden by LLM if needed

    if log_cb:
        log_cb(f"LLM: Detecting metadata via {model} ({len(pre.sample):,} chars) …")

    meta = _call_llm_for_metadata(
        pre.sample, model, log_cb, check_pause, progress_cb,
        structure_suspect=pre.structure_suspect,
        chapters=chapters,
        provider=provider,
        api_key=api_key,
        ollama_base_url=ollama_base_url,
    )
    if meta:
        title            = meta.get("title", title) or title
        language         = _normalize_lang(meta.get("language", language) or language)
        genre            = meta.get("genre", "").strip().lower()
        llm_subdiv       = meta.get("subdivision_type", "").strip()
        if llm_subdiv and not subdivision_type:
            subdivision_type = llm_subdiv

        # ── Apply merge_groups if present ──────────────────────────────
        merge_groups: list[list[int]] = meta.get("merge_groups", [])
        if merge_groups and pre.structure_suspect:
            chapters = _apply_merge_groups(chapters, merge_groups, log_cb)

    if not subdivision_type:
        subdivision_type = "Kapitel" if language == "de" else "Chapter"

    # Strip "Kapitel 3 " prefixes that the preprocessor may have left in titles
    chapters = [
        Chapter(
            index=ch.index,
            title=_strip_label_prefix(ch.title, ch.index, subdivision_type),
            chunks=ch.chunks,
            chunk_pauses=ch.chunk_pauses,
        )
        for ch in chapters
    ]

    voice_instruct = GENRE_PROMPTS.get(genre, TTS_VOICE_INSTRUCT)

    if log_cb and genre:
        log_cb(f"LLM: Genre detected: {genre}")
    if log_cb:
        log_cb(f"LLM: Subdivision type: {subdivision_type}")
    if log_cb and voice_instruct:
        log_cb(f"LLM: Voice instruction: {voice_instruct[:60]}…")

    return StructuredBook(
        title=title,
        language=language,
        genre=genre,
        subdivision_type=subdivision_type,
        voice_instruct=voice_instruct,
        chapters=chapters,
        metadata_sample=pre.sample,
    )


# ── LLM helper (metadata only) ────────────────────────────────────────────────

_LOG_TOKEN_INTERVAL = 50  # small — metadata responses are short


def _call_llm_for_metadata(
    sample: str,
    model: str,
    log_cb: Callable[[str], None] | None = None,
    check_pause: Callable[[], None] | None = None,
    progress_cb: Callable[[int], None] | None = None,
    structure_suspect: bool = False,
    chapters: list | None = None,
    provider: str = "ollama",
    api_key: str = "",
    ollama_base_url: str = OLLAMA_URL,
    max_attempts: int = 3,
) -> dict | None:
    """Send a short sample to the LLM and return metadata dict.

    When structure_suspect=True the chapter title list is appended and the
    response may additionally contain a 'merge_groups' key.
    Retries up to max_attempts times on JSON parse failures.
    """
    if check_pause:
        check_pause()
    system = METADATA_PROMPT.format(
        genre_keys=", ".join(f'"{k}"' for k in _GENRE_KEYS),
    )
    if structure_suspect and chapters:
        title_list = "\n".join(
            f"{i}: {ch.title}" for i, ch in enumerate(chapters)
        )
        system = system.rstrip() + "\n\n" + STRUCTURE_FIX_ADDENDUM.format(
            chapter_titles=title_list
        )
    # Use a larger context window when the title list is included
    ctx_size = 8192 if structure_suspect else 4096

    for attempt in range(1, max_attempts + 1):
        attempt_label = f" (attempt {attempt}/{max_attempts})" if attempt > 1 else ""
        try:
            if log_cb:
                if attempt == 1 and structure_suspect:
                    log_cb("LLM: Structure check active (too many/thin chapters detected) …")
                log_cb(f"LLM: Waiting for {model} response{attempt_label} …")

            if provider == "openrouter":
                from src.pipeline.adapter import _call_openrouter as _or_call
                raw = _or_call(sample, model, api_key, system_prompt=system)
                if log_cb:
                    log_cb("LLM: Metadata received")
                raw = _strip_code_fences(raw.strip())
                return json.loads(raw)

            stream = ollama.Client(host=ollama_base_url).chat(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": sample},
                ],
                options={
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "top_k": 20,
                    "min_p": 0,
                    "num_ctx": ctx_size,
                    "num_gpu": 99,
                },
                think=False,
                stream=True,
            )
            parts: list[str] = []
            token_count = 0
            last_logged = 0
            for chunk in stream:
                if check_pause:
                    check_pause()
                token = chunk["message"]["content"]
                parts.append(token)
                token_count += 1
                if progress_cb:
                    progress_cb(token_count)
                if log_cb and token_count - last_logged >= _LOG_TOKEN_INTERVAL:
                    log_cb(f"LLM: {token_count} tokens received …")
                    last_logged = token_count
            if log_cb:
                log_cb(f"LLM: Metadata received ({token_count} tokens)")
            raw = _strip_code_fences("".join(parts).strip())
            return json.loads(raw)

        except (json.JSONDecodeError, KeyError) as e:
            if attempt < max_attempts:
                if log_cb:
                    log_cb(f"LLM: Metadata parse failed ({e}) — retrying …")
            else:
                if log_cb:
                    log_cb(f"LLM: Metadata parse failed after {max_attempts} attempts ({e}) — using defaults")
                return None
        except Exception as e:
            if log_cb:
                log_cb(f"LLM: Metadata detection failed ({e}) — using defaults")
            return None

    return None


# ── Utilities ─────────────────────────────────────────────────────────────────

def _strip_label_prefix(title: str, index: int, subdivision_type: str) -> str:
    """Remove leading '{subdivision_type} {index}' from a chapter title."""
    if not title or not subdivision_type:
        return title
    pattern = re.compile(
        r"^" + re.escape(subdivision_type) + r"\s+" + re.escape(str(index)) + r"[\s:.\-–—]*",
        re.IGNORECASE,
    )
    return pattern.sub("", title).strip()


def _strip_code_fences(text: str) -> str:
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$",          "", text, flags=re.MULTILINE)
    return text.strip()


def _apply_merge_groups(
    chapters: list[Chapter],
    merge_groups: list[list[int]],
    log_cb: Callable[[str], None] | None = None,
) -> list[Chapter]:
    """Merge chapters according to groups returned by the LLM.

    Any chapter index not mentioned in merge_groups is kept as a standalone
    single-item group, preserving the full chapter set.
    """
    n = len(chapters)
    # Validate indices — silently clamp to valid range
    clean_groups: list[list[int]] = []
    seen: set[int] = set()
    for group in merge_groups:
        valid = [i for i in group if 0 <= i < n and i not in seen]
        if valid:
            clean_groups.append(valid)
            seen.update(valid)

    # Any chapter not mentioned becomes its own group
    ungrouped = [i for i in range(n) if i not in seen]

    # Re-order: merged groups in the order of their first index, then ungrouped
    all_groups: list[list[int]] = sorted(
        clean_groups + [[i] for i in ungrouped],
        key=lambda g: g[0],
    )

    if log_cb:
        log_cb(
            f"LLM: Chapter structure corrected — {n} sections → {len(all_groups)} chapters"
        )

    merged: list[Chapter] = []
    for new_idx, group in enumerate(all_groups, start=1):
        primary = chapters[group[0]]
        combined_chunks: list[str] = []
        combined_pauses: list[float] = []
        for i in group:
            combined_chunks.extend(chapters[i].chunks)
            combined_pauses.extend(chapters[i].chunk_pauses)
        merged.append(Chapter(
            index=new_idx,
            title=primary.title,
            chunks=combined_chunks,
            chunk_pauses=combined_pauses,
        ))
    return merged

