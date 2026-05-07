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

# TTS backend:
#   "fish_speech_cpp"  — Fish Speech S2 Pro via s2.exe (GGUF/GGML) — requires s2.cpp build
#   "qwen_tts_clone"   — Qwen3-TTS-Base pure-Python clone (no external binaries needed)
TTS_BACKEND: str = os.getenv("TTS_BACKEND", "fish_speech_cpp")

# Phase 2 (qwen_tts_clone backend): clones the voice anchor for content synthesis.
TTS_CLONE_MODEL: str = os.getenv(
    "TTS_CLONE_MODEL", "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
)

# ── Fish Speech s2.cpp (GGUF engine) ─────────────────────────────────────────
# Path to the compiled s2.exe binary.
FISH_SPEECH_CPP_EXE: str = os.getenv(
    "FISH_SPEECH_CPP_EXE", str(Path("D:/GIT/s2.cpp/build/Release/s2.exe"))
)
# Path to the pre-quantised GGUF model file (q8_0, ~5.6 GB — from fishaudio/s2-pro-gguf on HF).
FISH_SPEECH_CPP_MODEL: str = os.getenv(
    "FISH_SPEECH_CPP_MODEL", str(Path("D:/GIT/s2.cpp/checkpoints/s2-pro-gguf/s2-pro-q8_0.gguf"))
)
# Path to tokenizer.json (from the same GGUF repo).
FISH_SPEECH_CPP_TOKENIZER: str = os.getenv(
    "FISH_SPEECH_CPP_TOKENIZER", str(Path("D:/GIT/s2.cpp/checkpoints/s2-pro-gguf/tokenizer.json"))
)
# Vulkan GPU index: 0 = first GPU (RTX 4070), -1 = CPU only.
FISH_SPEECH_CPP_VULKAN: int = int(os.getenv("FISH_SPEECH_CPP_VULKAN", "0"))
# HTTP server port used in batch mode (model loads once, all chunks served via POST).
FISH_SPEECH_CPP_PORT: int = int(os.getenv("FISH_SPEECH_CPP_PORT", "3031"))

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

# Ordered spec fields used by the Voice Designer and the TTS instruction formatter.
VOICE_SPEC_FIELDS: list[str] = [
    "gender", "pitch", "speed", "volume", "age",
    "clarity", "fluency", "accent", "texture",
    "emotion", "tone", "personality",
]


def format_voice_spec(spec: dict[str, str]) -> str:
    """Compose a spec dict into the Qwen3-TTS structured instruction string."""
    lines = []
    for field in VOICE_SPEC_FIELDS:
        value = spec.get(field, "").strip().rstrip(".")
        if value:
            lines.append(f"{field}: {value}.")
    return "\n".join(lines)


# Structured voice specs per genre — shown and edited in the Voice Designer.
GENRE_VOICE_SPECS: dict[str, dict[str, str]] = {
    "novel": {
        "gender": "Female",
        "pitch": "Warm, moderate pitch with gentle variation to match narrative mood",
        "speed": "Moderate and unhurried — slowing for tender moments, building for tension",
        "volume": "Consistent and natural, never theatrical",
        "age": "Adult",
        "clarity": "Clear and naturally articulated",
        "fluency": "Highly fluent with natural pauses at punctuation",
        "accent": "Neutral",
        "texture": "Warm and rounded",
        "emotion": "Subtle and expressive — feeling conveyed without drama",
        "tone": "Immersive and storytelling",
        "personality": "Engaging, empathetic, and gently expressive",
    },
    "thriller": {
        "gender": "Male",
        "pitch": "Low to mid pitch with controlled tension",
        "speed": "Measured — quickening during tense passages, slowing for ominous moments",
        "volume": "Restrained and controlled, with quiet intensity",
        "age": "Middle-aged adult",
        "clarity": "Crisp and precise",
        "fluency": "Very fluent with deliberate, weighted pauses",
        "accent": "Neutral",
        "texture": "Dry and slightly gravelly",
        "emotion": "Understated urgency and cool menace",
        "tone": "Tense, controlled, and suspenseful",
        "personality": "Reserved, calculating, and quietly menacing",
    },
    "nonfiction": {
        "gender": "Male",
        "pitch": "Steady mid pitch, clear and authoritative",
        "speed": "Measured and consistent to aid comprehension",
        "volume": "Moderate and clear",
        "age": "Middle-aged adult",
        "clarity": "Highly articulate with careful emphasis on key terms",
        "fluency": "Very fluent with minimal hesitation",
        "accent": "Neutral",
        "texture": "Clean and focused",
        "emotion": "Calm and neutral",
        "tone": "Authoritative and informative",
        "personality": "Expert, reliable, and measured",
    },
    "biography": {
        "gender": "Female",
        "pitch": "Warm, moderate pitch with personal inflection",
        "speed": "Thoughtful pace with reflective pauses",
        "volume": "Intimate and moderate",
        "age": "Adult",
        "clarity": "Clear and natural",
        "fluency": "Fluent with natural, reflective pauses",
        "accent": "Neutral",
        "texture": "Warm and personal",
        "emotion": "Honest, intimate, and occasionally reflective",
        "tone": "Personal, warm, and genuine",
        "personality": "Empathetic, thoughtful, and sincere",
    },
    "selfhelp": {
        "gender": "Female",
        "pitch": "Bright, moderate pitch with an encouraging lilt",
        "speed": "Clear and steady with emphasis on actionable phrases",
        "volume": "Warm and projecting — friendly and accessible",
        "age": "Young adult to middle-aged adult",
        "clarity": "Very clear and easy to follow",
        "fluency": "Very fluent with deliberate emphasis",
        "accent": "Neutral",
        "texture": "Warm and clear",
        "emotion": "Encouraging, warm, and confident",
        "tone": "Motivational and supportive",
        "personality": "Trusted mentor — warm, direct, and empowering",
    },
    "philosophy": {
        "gender": "Male",
        "pitch": "Low to moderate pitch, deliberate and thoughtful",
        "speed": "Slow and contemplative with generous pauses",
        "volume": "Quiet and focused",
        "age": "Middle-aged to older adult",
        "clarity": "Measured and precise",
        "fluency": "Deliberate — pauses used as rhetorical space",
        "accent": "Neutral",
        "texture": "Deep and resonant",
        "emotion": "Contemplative and searching",
        "tone": "Philosophical, reflective, and unhurried",
        "personality": "Thoughtful, intellectual, and patient",
    },
    "technical": {
        "gender": "Male",
        "pitch": "Steady, neutral mid pitch",
        "speed": "Clear and even — never rushed",
        "volume": "Consistent and clear",
        "age": "Adult",
        "clarity": "Highly articulate with precise stress on technical terms",
        "fluency": "Very fluent with no hesitations",
        "accent": "Neutral",
        "texture": "Clean and focused",
        "emotion": "Neutral and objective",
        "tone": "Precise, neutral, and informative",
        "personality": "Professional, reliable, and direct",
    },
    "history": {
        "gender": "Male",
        "pitch": "Mid to low pitch with measured gravitas",
        "speed": "Steady, authoritative — weighting significant events",
        "volume": "Full and projecting, documentary style",
        "age": "Middle-aged to older adult",
        "clarity": "Clear and deliberate",
        "fluency": "Very fluent with purposeful pauses",
        "accent": "British English",
        "texture": "Rich and resonant",
        "emotion": "Engaged and respectful — never dry",
        "tone": "Authoritative and documentary",
        "personality": "Knowledgeable, dignified, and captivating",
    },
    "children": {
        "gender": "Female",
        "pitch": "Bright, higher pitch with lively variation",
        "speed": "Lively and energetic with clear pronunciation",
        "volume": "Warm and projecting, friendly and inviting",
        "age": "Young adult",
        "clarity": "Very clear articulation for young listeners",
        "fluency": "Fluent and expressive",
        "accent": "Neutral",
        "texture": "Bright, warm, and playful",
        "emotion": "Joyful, playful, and gently dramatic",
        "tone": "Warm, playful, and inviting",
        "personality": "Enthusiastic, kind, and imaginative storyteller",
    },
    "poetry": {
        "gender": "Female",
        "pitch": "Expressive pitch that honours rhythm and line breaks",
        "speed": "Slow and deliberate, respecting the poem's breath and pauses",
        "volume": "Intimate and moderate — allowing silence to carry meaning",
        "age": "Adult",
        "clarity": "Clear but with poetic softness",
        "fluency": "Measured — silence and pauses are intentional",
        "accent": "Neutral",
        "texture": "Soft and expressive",
        "emotion": "Expressive yet restrained — the words do the work",
        "tone": "Lyrical, contemplative, and sensitively expressive",
        "personality": "Artistic, attentive, and quietly passionate",
    },
}

# Derived instruction strings used as fallback by the TTS engine.
GENRE_PROMPTS: dict[str, str] = {
    genre: format_voice_spec(spec)
    for genre, spec in GENRE_VOICE_SPECS.items()
}

OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "./output"))
TTS_CHUNK_SIZE: int = int(os.getenv("TTS_CHUNK_SIZE", "3000"))
TTS_DEVICE: str = os.getenv("TTS_DEVICE", "cuda")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Sub-folder for session JSON files and voice anchors (not part of final output)
SESSIONS_DIR: Path = OUTPUT_DIR / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# Sub-folder inside SESSIONS_DIR for temporary per-chunk WAV files (chunk-level resume)
TEMP_DIR: Path = SESSIONS_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Sub-folder for persistent per-genre voice anchors saved via the Voice Designer
VOICE_ANCHORS_DIR: Path = SESSIONS_DIR / "voice_anchors"
VOICE_ANCHORS_DIR.mkdir(parents=True, exist_ok=True)

# Short representative texts played back in the Voice Designer for each genre
GENRE_SAMPLE_TEXTS: dict[str, str] = {
    "novel": (
        "She stood at the edge of the forest, the lantern swinging in her hand. "
        "Something moved between the trees — a shadow that breathed, that waited. "
        "She told herself it was the wind, or a deer, or nothing at all. "
        "But her feet had already stopped moving, and the lantern flame had gone very still, "
        "as if the air itself was holding its breath along with her."
    ),
    "thriller": (
        "The call came at 2 a.m. Three words, then silence. "
        "He was already reaching for his coat before the line went dead. "
        "Twelve years on the job had taught him that silence after three words "
        "was never just silence — it was a door left open, "
        "and something on the other side was already walking through."
    ),
    "nonfiction": (
        "The evidence, examined carefully, points in only one direction. "
        "What we assumed to be settled science turns out to be a working hypothesis, "
        "revised every decade by the very researchers who proposed it. "
        "This is not a failure of knowledge — it is knowledge doing exactly what it should: "
        "correcting itself, slowly and honestly, in the direction of truth."
    ),
    "biography": (
        "She never spoke about those years — not to her children, not to the journalists "
        "who came later with their recorders and their careful questions. "
        "But the letters she kept, folded in a tin box under her bed, told a different story. "
        "A story of choices made under pressure, of loyalties tested, "
        "and of a life that was far larger, and far stranger, than anyone around her ever knew."
    ),
    "selfhelp": (
        "Change begins not with grand gestures but with a single decision made quietly, "
        "before anyone is watching. "
        "You already know what that decision is. You have known for some time. "
        "The only question left is whether today is the day you stop waiting "
        "for the right moment and accept that the moment you are in right now is the only one available."
    ),
    "philosophy": (
        "To ask what is real is to ask what we mean by asking. "
        "Every answer shapes the question that comes after it, "
        "and the shape of the question determines what we are able to find. "
        "Philosophy does not solve problems so much as reveal the assumptions "
        "hidden inside them — and sometimes, that is the more difficult and more necessary work."
    ),
    "technical": (
        "A hash collision occurs when two distinct inputs produce the same output value. "
        "In SHA-256, the probability of a collision is approximately two to the power of negative 128 — "
        "negligible for all practical purposes, but not zero. "
        "Understanding why that distinction matters is the foundation of modern cryptographic design, "
        "and the reason we do not treat negligible and impossible as the same thing."
    ),
    "history": (
        "On the morning of the fourteenth of July, 1789, a crowd gathered outside "
        "the Bastille — not yet an army, not yet a revolution, but something between "
        "the two that the old order had no name for. "
        "By afternoon, the name would come. "
        "By evening, the world those people had been born into would already be ending, "
        "though most of them would not understand that until much later."
    ),
    "children": (
        "The little fox had never seen snow before. "
        "She pressed her nose against it and sneezed loudly, then looked around to see if anyone had noticed. "
        "The rabbit had. He was already laughing. "
        "'It tickles,' she said, very seriously. "
        "'Everything tickles the first time,' said the rabbit, "
        "and somehow that made her feel much better about the whole situation."
    ),
    "poetry": (
        "I have been here before — in the hinge of a door, "
        "in the pause between one breath and the next. "
        "The world does not wait. Neither do I. "
        "There is a kind of courage in simply continuing, "
        "in placing one word after another when the silence is so wide "
        "it seems to ask you to stop."
    ),
}

# ── Audiobook Adaptation ──────────────────────────────────────────────────────
# Set ADAPTATION_ENABLED=false to skip LLM adaptation and use raw extracted text.
ADAPTATION_ENABLED: bool = os.getenv("ADAPTATION_ENABLED", "true").lower() == "true"

# "ollama" uses the local Ollama server; "openrouter" uses the cloud API.
ADAPTATION_PROVIDER: str = os.getenv("ADAPTATION_PROVIDER", "ollama")  # "ollama"|"openrouter"

# OpenRouter settings — only needed when ADAPTATION_PROVIDER=openrouter.
# Recommended cost-efficient model: anthropic/claude-haiku-4-5
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL:   str = os.getenv("OPENROUTER_MODEL",   "anthropic/claude-haiku-4-5")
