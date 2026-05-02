from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Callable

import ollama

from src.config import GENRE_PROMPTS, LLM_MODEL, TTS_VOICE_INSTRUCT
from src.pipeline.preprocessor import preprocess as _preprocess

# Genre keys exposed to the LLM — must stay in sync with GENRE_PROMPTS in config.py.
_GENRE_KEYS = list(GENRE_PROMPTS.keys())  # e.g. ["novel", "thriller", ...]

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


@dataclass
class Chapter:
    index: int
    title: str
    chunks: list[str] = field(default_factory=list)
    chunk_pauses: list[float] = field(default_factory=list)


@dataclass
class StructuredBook:
    title: str
    language: str
    voice_instruct: str
    genre: str = ""
    subdivision_type: str = "Chapter"
    chapters: list[Chapter] = field(default_factory=list)

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
) -> StructuredBook:
    """Structure markdown content for TTS generation.

    Pipeline:
    1. preprocessor.py cleans the text, detects chapters, expands abbreviations,
       and produces TTS chunks — all without any LLM call.
    2. A short excerpt (~2 500 chars) is sent to the LLM to detect language and genre.
    3. Results are merged into a StructuredBook.
    """
    # ── Step 1: pre-process (no LLM) ─────────────────────────────────────────
    if log_cb:
        log_cb("Preprocessing: Text wird bereinigt und Kapitelstruktur extrahiert …")

    pre = _preprocess(markdown)

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
            f"Preprocessing: {len(chapters)} Kapitel, {total_chunks} Chunks "
            f"({len(markdown):,} → {sum(len(c) for ch in chapters for c in ch.chunks):,} Zeichen)"
        )

    # ── Step 2: LLM metadata detection (tiny sample only) ────────────────────
    title            = pre.title
    language         = pre.language          # heuristic — overridden by LLM if available
    genre            = ""
    subdivision_type = pre.subdivision_type  # pattern-detected — overridden by LLM if needed

    if log_cb:
        log_cb(f"LLM: Metadaten werden erkannt ({len(pre.sample):,} Zeichen) …")

    meta = _call_llm_for_metadata(pre.sample, model, log_cb, check_pause, progress_cb)
    if meta:
        title            = meta.get("title", title) or title
        language         = meta.get("language", language) or language
        genre            = meta.get("genre", "").strip().lower()
        llm_subdiv       = meta.get("subdivision_type", "").strip()
        if llm_subdiv and not subdivision_type:
            subdivision_type = llm_subdiv

    if not subdivision_type:
        subdivision_type = "Kapitel" if language == "de" else "Chapter"

    # Strip "Kapitel 3 " prefixes that the preprocessor may have left in titles
    chapters = [
        Chapter(
            index=ch.index,
            title=_strip_label_prefix(ch.title, ch.index, subdivision_type),
            chunks=ch.chunks,
        )
        for ch in chapters
    ]

    voice_instruct = GENRE_PROMPTS.get(genre, TTS_VOICE_INSTRUCT)

    if log_cb and genre:
        log_cb(f"LLM: Genre erkannt: {genre}")
    if log_cb:
        log_cb(f"LLM: Unterteilungstyp: {subdivision_type}")
    if log_cb and voice_instruct:
        log_cb(f"LLM: Stimmanweisung: {voice_instruct[:60]}…")

    return StructuredBook(
        title=title,
        language=language,
        genre=genre,
        subdivision_type=subdivision_type,
        voice_instruct=voice_instruct,
        chapters=chapters,
    )


# ── LLM helper (metadata only) ────────────────────────────────────────────────

_LOG_TOKEN_INTERVAL = 50  # small — metadata responses are short


def _call_llm_for_metadata(
    sample: str,
    model: str,
    log_cb: Callable[[str], None] | None = None,
    check_pause: Callable[[], None] | None = None,
    progress_cb: Callable[[int], None] | None = None,
) -> dict | None:
    """Send a short sample to the LLM and return {title, language, genre, subdivision_type}."""
    if check_pause:
        check_pause()
    system = METADATA_PROMPT.format(
        genre_keys=", ".join(f'"{k}"' for k in _GENRE_KEYS),
    )
    try:
        if log_cb:
            log_cb("LLM: Warte auf Modellantwort …")
        stream = ollama.chat(
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
                "num_ctx": 4096,   # tiny context — sample is ≤2 500 chars
                "num_gpu": 99,
            },
            think=False,
            stream=True,
        )
        parts: list[str] = []
        token_count = 0
        last_logged = 0
        for chunk in stream:
            token = chunk["message"]["content"]
            parts.append(token)
            token_count += 1
            if progress_cb:
                progress_cb(token_count)
            if log_cb and token_count - last_logged >= _LOG_TOKEN_INTERVAL:
                log_cb(f"LLM: {token_count} Tokens empfangen …")
                last_logged = token_count
        if log_cb:
            log_cb(f"LLM: Metadaten empfangen ({token_count} Tokens)")
        raw = _strip_code_fences("".join(parts).strip())
        return json.loads(raw)
    except (json.JSONDecodeError, KeyError) as e:
        if log_cb:
            log_cb(f"LLM: Metadaten-Parse fehlgeschlagen ({e}) — Standardwerte werden verwendet")
        return None
    except Exception as e:
        if log_cb:
            log_cb(f"LLM: Metadaten-Erkennung fehlgeschlagen ({e}) — Standardwerte werden verwendet")
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

