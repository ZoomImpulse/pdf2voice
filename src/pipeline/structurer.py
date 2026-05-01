from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Callable

import ollama

from src.config import LLM_MODEL, TTS_CHUNK_SIZE, TTS_VOICE_INSTRUCT

SYSTEM_PROMPT = """\
You are an assistant that prepares PDF content for text-to-speech (TTS) synthesis.

Your tasks:
1. Detect the chapter structure from Markdown (# H1, ## H2 as chapter boundaries).
2. Clean the text: remove page numbers, headers/footers, footnotes, URLs, and image captions.
3. Expand abbreviations to their full form (e.g. → for example, etc. → et cetera, vs. → versus).
4. Split each chapter into chunks of at most {chunk_size} characters (break only at sentence boundaries).
5. Detect the primary language (de/en).
6. Detect the subdivision label the book uses for its top-level divisions (e.g. "Kapitel", "Teil",
   "Abschnitt", "Part", "Chapter", "Section", "Book", "Act", "Canto"). Use exactly the word the book
   itself uses. If the divisions have no label (just numbers or no heading at all), use the most natural
   word for the detected language ("Kapitel" for German, "Chapter" for English).
   A division may also have no title — only a number or nothing. In that case set "title" to "".
7. Analyse the style and genre of the text and formulate a "voice_instruct" in English (2-3 sentences)
   for a VoiceDesign TTS system. Describe pace, tone, expression and voice character so the TTS model
   chooses the best reading style for this text.

   Examples by genre:
   - Novel/Fiction → "Speak as a warm, immersive storyteller. Vary your pace to build tension or
     tenderness as the narrative demands. Use gentle expressiveness — subtle emotion rather than
     theatrical drama."
   - Non-fiction/Science → "Speak as a calm, authoritative expert. Maintain a clear, measured pace
     that aids comprehension of complex ideas. Emphasise key terms with natural precision."
   - Biography/Memoir → "Speak in a personal, intimate tone, as if recounting lived experience.
     Allow reflective pauses. The voice should feel honest and human, not performed."
   - Self-help/Guide → "Speak with warmth and clarity, like a trusted mentor. Keep an encouraging,
     steady pace. Emphasise actionable insights with calm confidence."
   - Philosophy/Essay → "Speak thoughtfully and deliberately, as if working through ideas aloud.
     Allow pauses for reflection. Tone is contemplative, never rushed."
   - Technical manual → "Speak clearly and neutrally, with a precise, even pace. Stress technical
     terms without inflection. Prioritise intelligibility over expressiveness."

Respond ONLY with valid JSON — no Markdown code fences, no explanations:
{{
  "title": "Document title",
  "language": "de",
  "genre": "Short genre label in English",
  "subdivision_type": "Kapitel",
  "voice_instruct": "2-3 sentences in English describing the ideal reading style",
  "chapters": [
    {{
      "index": 1,
      "title": "Chapter name or empty string if untitled",
      "chunks": ["Chunk text 1", "Chunk text 2"]
    }}
  ]
}}
"""


@dataclass
class Chapter:
    index: int
    title: str
    chunks: list[str] = field(default_factory=list)


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
    model: str = LLM_MODEL,
) -> StructuredBook:
    system = SYSTEM_PROMPT.format(chunk_size=TTS_CHUNK_SIZE)

    if log_cb:
        log_cb(f"LLM: Sending {len(markdown):,} characters to {model} ...")

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": markdown},
        ],
        options={"temperature": 0.2, "num_ctx": 32768},
        stream=False,
    )

    raw = _strip_code_fences(response["message"]["content"].strip())

    if log_cb:
        log_cb("LLM: Response received, parsing JSON ...")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = _fallback_parse(markdown)
        if log_cb:
            log_cb("LLM: JSON parsing failed — using fallback structure")

    seen_indices: set[int] = set()
    chapters: list[Chapter] = []
    for i, ch in enumerate(data.get("chapters", [])):
        if not (ch.get("chunks") or ch.get("text")):
            continue
        idx = ch.get("index", i + 1)
        if idx in seen_indices:
            if log_cb:
                log_cb(f"LLM: Duplicate chapter index {idx} skipped")
            continue
        seen_indices.add(idx)
        chapters.append(Chapter(
            index=idx,
            title=ch.get("title", f"Chapter {i + 1}"),
            chunks=ch.get("chunks", [ch.get("text", "")]),
        ))

    if not chapters:
        chapters = _split_into_chunks(markdown)
        if log_cb:
            log_cb("LLM: No chapters detected — treating document as one chapter")

    voice_instruct   = data.get("voice_instruct", "").strip() or TTS_VOICE_INSTRUCT
    genre            = data.get("genre", "").strip()
    language         = data.get("language", "en")
    subdivision_type = data.get("subdivision_type", "").strip()
    if not subdivision_type:
        subdivision_type = "Kapitel" if language == "de" else "Chapter"

    if log_cb and genre:
        log_cb(f"LLM: Detected genre: {genre}")
    if log_cb:
        log_cb(f"LLM: Subdivision type: {subdivision_type}")
    if log_cb and voice_instruct:
        log_cb(f"LLM: Voice instruction: {voice_instruct}")

    return StructuredBook(
        title=data.get("title", "Document"),
        language=language,
        genre=genre,
        subdivision_type=subdivision_type,
        voice_instruct=voice_instruct,
        chapters=chapters,
    )


def _strip_code_fences(text: str) -> str:
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$",          "", text, flags=re.MULTILINE)
    return text.strip()


def _fallback_parse(markdown: str) -> dict:
    chapters: list[dict] = []
    current_title = "Document"
    current_text: list[str] = []

    for line in markdown.splitlines():
        if line.startswith("# "):
            if current_text:
                chapters.append({
                    "index": len(chapters) + 1,
                    "title": current_title,
                    "chunks": _chunk_text("\n".join(current_text)),
                })
                current_text = []
            current_title = line.lstrip("# ").strip()
        else:
            current_text.append(line)

    if current_text:
        chapters.append({
            "index": len(chapters) + 1,
            "title": current_title,
            "chunks": _chunk_text("\n".join(current_text)),
        })

    return {"title": "Document", "language": "en", "genre": "", "subdivision_type": "Chapter", "voice_instruct": "", "chapters": chapters}


def _split_into_chunks(text: str) -> list[Chapter]:
    return [Chapter(index=1, title="Document", chunks=_chunk_text(text))]


def _chunk_text(text: str) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 > TTS_CHUNK_SIZE and current:
            chunks.append(current.strip())
            current = sentence
        else:
            current = (current + " " + sentence).strip() if current else sentence
    if current:
        chunks.append(current.strip())
    return [c for c in chunks if c.strip()]
