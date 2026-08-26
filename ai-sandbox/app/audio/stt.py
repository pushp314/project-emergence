from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Optional, Callable, Awaitable
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class STTConfig:
    model: str = "base"
    language: str = "en"
    vad_threshold: float = 0.5
    sample_rate: int = 16000
    chunk_duration_ms: int = 30


@dataclass
class TranscriptionResult:
    text: str
    confidence: float
    is_final: bool
    language: str


class STTAdapter(ABC):
    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        pass
    
    @abstractmethod
    async def transcribe_stream(self, audio_stream: AsyncIterator[bytes]) -> AsyncIterator[TranscriptionResult]:
        pass
    
    @abstractmethod
    async def start_listening(self, callback: Callable[[TranscriptionResult], Awaitable[None]]) -> None:
        pass
    
    @abstractmethod
    async def stop_listening(self) -> None:
        pass


class FasterWhisperSTT(STTAdapter):
    def __init__(self, config: STTConfig):
        self._config = config
        self._model = None
        self._listening = False
        self._vad = None
    
    async def _init_model(self) -> None:
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(self._config.model, device="cpu", compute_type="int8")
                logger.info(f"Loaded Whisper model: {self._config.model}")
            except ImportError:
                logger.warning("faster-whisper not installed")
                self._model = None
    
    async def _init_vad(self) -> None:
        if self._vad is None:
            try:
                import webrtcvad
                self._vad = webrtcvad.Vad(3)
            except ImportError:
                logger.warning("webrtcvad not installed, VAD disabled")
    
    async def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        await self._init_model()
        if not self._model:
            return TranscriptionResult(text="", confidence=0.0, is_final=True, language=self._config.language)
        
        try:
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            segments, info = self._model.transcribe(audio_np, language=self._config.language)
            text = " ".join([seg.text for seg in segments])
            return TranscriptionResult(
                text=text.strip(),
                confidence=1.0 - info.no_speech_prob if hasattr(info, 'no_speech_prob') else 0.9,
                is_final=True,
                language=info.language if hasattr(info, 'language') else self._config.language
            )
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return TranscriptionResult(text="", confidence=0.0, is_final=True, language=self._config.language)
    
    async def transcribe_stream(self, audio_stream: AsyncIterator[bytes]) -> AsyncIterator[TranscriptionResult]:
        await self._init_model()
        if not self._model:
            async for _ in audio_stream:
                yield TranscriptionResult(text="", confidence=0.0, is_final=False, language=self._config.language)
            return
        
        buffer = bytearray()
        async for chunk in audio_stream:
            buffer.extend(chunk)
            if len(buffer) >= self._config.sample_rate * 2:
                audio_bytes = bytes(buffer)
                buffer.clear()
                result = await self.transcribe(audio_bytes)
                yield result
        
        if buffer:
            result = await self.transcribe(bytes(buffer))
            yield result
    
    async def start_listening(self, callback: Callable[[TranscriptionResult], Awaitable[None]]) -> None:
        await self._init_vad()
        await self._init_model()
        
        if not self._model:
            logger.warning("STT model not available")
            return
        
        self._listening = True
        
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self._config.sample_rate,
                input=True,
                frames_per_buffer=int(self._config.sample_rate * self._config.chunk_duration_ms / 1000)
            )
            
            logger.info("STT listening started")
            
            while self._listening:
                data = await asyncio.get_event_loop().run_in_executor(
                    None, stream.read, int(self._config.sample_rate * self._config.chunk_duration_ms / 1000)
                )
                
                if self._vad and not self._vad.is_speech(data, self._config.sample_rate):
                    continue
                
                result = await self.transcribe(data)
                if result.text.strip():
                    await callback(result)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except ImportError:
            logger.warning("pyaudio not installed, microphone input unavailable")
        except Exception as e:
            logger.error(f"STT listening error: {e}")
        finally:
            self._listening = False
    
    async def stop_listening(self) -> None:
        self._listening = False


class NullSTT(STTAdapter):
    def __init__(self, config: STTConfig):
        self._config = config
    
    async def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        return TranscriptionResult(text="", confidence=0.0, is_final=True, language=self._config.language)
    
    async def transcribe_stream(self, audio_stream: AsyncIterator[bytes]) -> AsyncIterator[TranscriptionResult]:
        async for _ in audio_stream:
            yield TranscriptionResult(text="", confidence=0.0, is_final=False, language=self._config.language)
    
    async def start_listening(self, callback: Callable[[TranscriptionResult], Awaitable[None]]) -> None:
        pass
    
    async def stop_listening(self) -> None:
        pass


def create_stt_adapter(config: STTConfig, enabled: bool = True) -> STTAdapter:
    if not enabled:
        return NullSTT(config)
    
    try:
        import faster_whisper
        return FasterWhisperSTT(config)
    except ImportError:
        logger.warning("faster-whisper not installed, using null STT")
        return NullSTT(config)