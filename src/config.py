import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen3:8b")

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

# Gerät für TTS-Inferenz
TTS_DEVICE: str = os.getenv("TTS_DEVICE", "cuda")

OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "./output"))
TTS_CHUNK_SIZE: int = int(os.getenv("TTS_CHUNK_SIZE", "3000"))

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
