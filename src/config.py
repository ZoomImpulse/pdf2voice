import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen3:8b")
# Maximum context window (tokens) passed to Ollama.
# Keep this well below your GPU VRAM headroom: the KV cache for 48k tokens on a
# 8B model can exceed 6 GB, causing silent CPU offload and very slow generation.
# 16 384 is a safe default for 8-12 GB GPUs.  Increase if you have more VRAM.
LLM_CTX: int = int(os.getenv("LLM_CTX", "16384"))

# PDF Extraction: uses pymupdf4llm for reliable page-by-page text extraction.
# Install: pip install pymupdf4llm

# Phase 1: VoiceDesign — generates the voice anchor (short reference audio)
TTS_DESIGN_MODEL: str = os.getenv(
    "TTS_DESIGN_MODEL", "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
)

# Phase 2: Base — clones the anchor voice for all content chunks (consistent)
TTS_BASE_MODEL: str = os.getenv(
    "TTS_BASE_MODEL", "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
)

# Narrator gender (injected into the VoiceDesign instruction at runtime)
TTS_GENDER: str = os.getenv("TTS_GENDER", "female")  # "female" | "male"

# VoiceDesign instruction (base style without gender — extended at runtime)
TTS_VOICE_INSTRUCT: str = os.getenv(
    "TTS_VOICE_INSTRUCT",
    (
        "Speak as a professional audiobook narrator: warm, clear, and unhurried. "
        "Use a steady, measured pace with natural pauses at punctuation. "
        "Apply subtle emphasis on key words without theatrical exaggeration. "
        "Maintain a consistent, engaging tone — inviting the listener to follow along "
        "as if reading aloud from a well-loved book."
    ),
)

# Predefined TTS voice instructions per genre.
# The LLM picks one of these keys; the corresponding prompt is used for VoiceDesign.
GENRE_PROMPTS: dict[str, str] = {
    "novel": (
        "Speak as a warm, immersive storyteller. "
        "Vary your pace to build tension or tenderness as the narrative demands. "
        "Use gentle expressiveness — subtle emotion rather than theatrical drama."
    ),
    "thriller": (
        "Speak with understated urgency, keeping the listener on edge. "
        "Quicken your pace during tense passages and slow down for ominous moments. "
        "Maintain a cool, controlled tone — menace through restraint, not volume."
    ),
    "nonfiction": (
        "Speak as a calm, authoritative expert. "
        "Maintain a clear, measured pace that aids comprehension of complex ideas. "
        "Emphasise key terms with natural precision."
    ),
    "biography": (
        "Speak in a personal, intimate tone, as if recounting lived experience. "
        "Allow reflective pauses. "
        "The voice should feel honest and human, not performed."
    ),
    "selfhelp": (
        "Speak with warmth and clarity, like a trusted mentor. "
        "Keep an encouraging, steady pace. "
        "Emphasise actionable insights with calm confidence."
    ),
    "philosophy": (
        "Speak thoughtfully and deliberately, as if working through ideas aloud. "
        "Allow pauses for reflection. "
        "Tone is contemplative, never rushed."
    ),
    "technical": (
        "Speak clearly and neutrally, with a precise, even pace. "
        "Stress technical terms without inflection. "
        "Prioritise intelligibility over expressiveness."
    ),
    "history": (
        "Speak with measured gravitas, as if narrating a documentary. "
        "Keep a steady, authoritative pace with subtle weight on significant events. "
        "Tone is respectful and engaged, never dry."
    ),
    "children": (
        "Speak with a bright, playful energy and a gentle, welcoming tone. "
        "Use clear articulation and a lively pace that holds a child's attention. "
        "Bring characters to life with light, distinct expressiveness."
    ),
    "poetry": (
        "Speak with careful attention to rhythm, breath, and line breaks. "
        "Allow silence to carry meaning. "
        "The voice should be expressive but restrained — the words do the work."
    ),
}

# Gerät für TTS-Inferenz
TTS_DEVICE: str = os.getenv("TTS_DEVICE", "cuda")

OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "./output"))
TTS_CHUNK_SIZE: int = int(os.getenv("TTS_CHUNK_SIZE", "3000"))

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Audiobook Adaptation ──────────────────────────────────────────────────────
# Set ADAPTATION_ENABLED=false to skip LLM adaptation and use raw extracted text.
ADAPTATION_ENABLED: bool = os.getenv("ADAPTATION_ENABLED", "true").lower() == "true"

# "ollama" uses the local Ollama server; "openrouter" uses the cloud API.
ADAPTATION_PROVIDER: str = os.getenv("ADAPTATION_PROVIDER", "ollama")  # "ollama"|"openrouter"

# OpenRouter settings — only needed when ADAPTATION_PROVIDER=openrouter.
# Recommended cost-efficient model: anthropic/claude-haiku-4-5
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL:   str = os.getenv("OPENROUTER_MODEL",   "anthropic/claude-haiku-4-5")
