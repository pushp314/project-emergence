import os
import tempfile
import asyncio
from typing import Optional

class VoiceEngine:
    def __init__(self):
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
        except ImportError:
            self.model = None

    async def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio bytes to text using faster-whisper."""
        if not self.model:
            return "Speech-to-text is not available."
            
        # Write bytes to a temporary wav file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name
            
        try:
            segments, info = self.model.transcribe(temp_path, beam_size=5)
            text = " ".join([segment.text for segment in segments])
            return text.strip()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    async def synthesize(self, text: str) -> Optional[bytes]:
        """Synthesize text to speech using edge-tts."""
        try:
            import edge_tts
        except ImportError:
            return None
            
        communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name
            
        try:
            await communicate.save(temp_path)
            with open(temp_path, "rb") as f:
                return f.read()
        except Exception as e:
            return None
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

_engine = None

def get_voice_engine() -> VoiceEngine:
    global _engine
    if _engine is None:
        _engine = VoiceEngine()
    return _engine
