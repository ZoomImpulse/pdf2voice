"""Audiobook text adaptation — rewrites chapter prose for audio listening.

Providers:
  ollama      — local Ollama server (uses OLLAMA_URL + LLM_MODEL)
  openrouter  — cloud API via https://openrouter.ai/api/v1 (OpenAI-compatible)

The adapter takes raw TTS chunks joined as prose and returns adapted text
suitable for narration: visual references removed, lists converted to prose,
abbreviations expanded, footnotes stripped, etc.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Callable

_SYSTEM_PROMPT = """\
You are an expert audiobook adaptation editor.
Rewrite the following chapter text so it works as spoken audio narration.

Rules:
- Convert all bullet lists and numbered lists to natural flowing prose
- Replace visual references ("see Figure 3", "refer to Table 2", "as shown above", \
"see page X") with natural spoken alternatives or omit them if they add no value
- Remove page numbers, footnote markers ([1], ¹) and footnote text entirely
- Clarify ambiguous pronoun references that rely on visual layout context
- Expand abbreviations that sound awkward when read aloud
- Keep ALL meaningful content — do NOT summarise or skip paragraphs
- Maintain the author's voice, style, and tone throughout
- Return ONLY the adapted text — no commentary, no markdown, no headings
"""

_USER_TEMPLATE = "Chapter: {title}\n\n{text}"

# Safe batch size in characters — keeps requests within most LLM context windows
_MAX_BATCH_CHARS = 6_000


def adapt_chapter(
    title: str,
    chunks: list[str],
    provider: str,
    model: str,
    api_key: str = "",
    ollama_base_url: str = "http://localhost:11434",
    log_cb: Callable[[str], None] | None = None,
) -> str:
    """Return LLM-adapted prose for a single chapter.

    Long chapters are split into paragraph batches to stay within context limits,
    then the results are re-joined.
    """
    raw_text = "\n\n".join(chunks)
    if len(raw_text) <= _MAX_BATCH_CHARS:
        return _adapt_single(title, raw_text, provider, model, api_key, ollama_base_url, log_cb)

    # Split into paragraph batches
    paragraphs = raw_text.split("\n\n")
    batches: list[list[str]] = [[]]
    current_len = 0
    for para in paragraphs:
        if current_len + len(para) > _MAX_BATCH_CHARS and batches[-1]:
            batches.append([])
            current_len = 0
        batches[-1].append(para)
        current_len += len(para)

    parts: list[str] = []
    for i, batch in enumerate(batches):
        if log_cb and len(batches) > 1:
            log_cb(f"  Batch {i + 1}/{len(batches)} …")
        parts.append(
            _adapt_single(
                title, "\n\n".join(batch), provider, model, api_key, ollama_base_url, log_cb
            )
        )
    return "\n\n".join(parts)


# ── Internal ──────────────────────────────────────────────────────────────────

def _adapt_single(
    title: str,
    text: str,
    provider: str,
    model: str,
    api_key: str,
    ollama_base_url: str,
    log_cb: Callable[[str], None] | None,
) -> str:
    user_msg = _USER_TEMPLATE.format(title=title, text=text)
    if provider == "openrouter":
        return _call_openrouter(user_msg, model, api_key)
    return _call_ollama(user_msg, model, ollama_base_url)


def _call_ollama(user_msg: str, model: str, base_url: str) -> str:
    import ollama as _ollama  # already in requirements.txt
    client = _ollama.Client(host=base_url)
    response = client.chat(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        options={"temperature": 0.3},
        think=False,
    )
    return response.message.content.strip()


def _call_openrouter(
    user_msg: str,
    model: str,
    api_key: str,
    system_prompt: str | None = None,
) -> str:
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is required when ADAPTATION_PROVIDER=openrouter"
        )
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt if system_prompt is not None else _SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        "temperature": 0.3,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
            "HTTP-Referer":  "https://github.com/ZoomImpulse/pdf2voice",
            "X-Title":       "pdf2voice",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:  # nosec B310 — fixed HTTPS URL
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


# ── Voice spec fill ───────────────────────────────────────────────────────────

_FILL_SYSTEM_PROMPT = """\
You are a voice casting assistant. Given a short description of a desired narrator \
voice, return a JSON object with exactly these 12 fields filled in:

  gender       — one of: Female, Male, Neutral
  age          — one of: Child, Teen, Young Adult, Adult, Middle-aged, Senior
  pitch        — short description of pitch quality (1 sentence)
  speed        — short description of speaking pace (1 sentence)
  volume       — short description of volume / projection (1 sentence)
  clarity      — short description of diction / articulation (1 sentence)
  fluency      — short description of flow and pausing (1 sentence)
  accent       — accent or dialect (e.g. Neutral American, British RP, etc.)
  texture      — short description of vocal texture / timbre (1 sentence)
  emotion      — short description of emotional warmth / expressiveness (1 sentence)
  tone         — overall tone (e.g. authoritative, intimate, warm) (1 sentence)
  personality  — short description of narrator personality (1 sentence)

Return ONLY a valid JSON object — no markdown fences, no commentary.
"""


def fill_voice_spec(
    prompt: str,
    provider: str,
    model: str,
    api_key: str = "",
    ollama_base_url: str = "http://localhost:11434",
) -> dict:
    """Ask the LLM to fill all 12 voice spec fields from a short natural-language prompt.

    Returns a dict with the 12 field keys.  The caller should validate
    gender/age against their allowed option lists before applying values.
    """
    user_msg = f"Voice description: {prompt.strip()}"
    if provider == "openrouter":
        raw = _call_openrouter_fill(user_msg, model, api_key)
    else:
        raw = _call_ollama_fill(user_msg, model, ollama_base_url)

    # Strip markdown code fences that some models add
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0].strip()

    return json.loads(raw)


def _call_ollama_fill(user_msg: str, model: str, base_url: str) -> str:
    import ollama as _ollama
    client = _ollama.Client(host=base_url)
    response = client.chat(
        model=model,
        messages=[
            {"role": "system", "content": _FILL_SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        options={"temperature": 0.7},
        think=False,
    )
    return response.message.content.strip()


def _call_openrouter_fill(user_msg: str, model: str, api_key: str) -> str:
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is required when ADAPTATION_PROVIDER=openrouter"
        )
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": _FILL_SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        "temperature": 0.7,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
            "HTTP-Referer":  "https://github.com/ZoomImpulse/pdf2voice",
            "X-Title":       "pdf2voice",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:  # nosec B310 — fixed HTTPS URL
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()
