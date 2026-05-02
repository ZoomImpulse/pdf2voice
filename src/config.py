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

# PDF Extraction: Uses Docling with OCR disabled for layout-aware, memory-efficient extraction.
# No system dependencies required — uses Docling's native layout models.
# Install: pip install docling
PDF_EXTRACTOR: str = "docling"  # Layout-aware PDF parsing, OCR disabled

# Phase 1: VoiceDesign — generiert den Stimm-Anker (kurze Referenz-Audio)
TTS_DESIGN_MODEL: str = os.getenv(
    "TTS_DESIGN_MODEL", "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
)

# Phase 2: Base — klont die Anker-Stimme für alle Content-Chunks (konsistent)
TTS_BASE_MODEL: str = os.getenv(
    "TTS_BASE_MODEL", "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
)

# Geschlecht des Sprechers (wird in die VoiceDesign-Instruction eingebaut)
TTS_GENDER: str = os.getenv("TTS_GENDER", "female")  # "female" | "male"

# VoiceDesign-Instruction (Basisstil ohne Geschlecht — wird zur Laufzeit ergänzt)
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
