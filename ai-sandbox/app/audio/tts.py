from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Optional
import queue
import threading

logger = logging.getLogger(__name__)


@dataclass
class TTSConfig:
    model: str = "tts_models/en/ljspeech/tacotron2-DDC"
    voice: str = "default"
    speed: float = 1.0
    sample_rate: int = 22050


class TTSAdapter(ABC):
    @abstractmethod
    async def speak(self, text: str) -> None:
        pass
    
    @abstractmethod
    async def speak_stream(self, text_stream: AsyncIterator[str]) -> None:
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        pass
    
    @abstractmethod
    def is_speaking(self) -> bool:
        pass


class Pyttsx3TTS(TTSAdapter):
    def __init__(self, config: TTSConfig):
        self._config = config
        self._engine = None
        self._speaking = False
        self._stop_event = threading.Event()
        self._audio_queue: queue.Queue = queue.Queue()
        self._playback_thread: Optional[threading.Thread] = None
    
    async def _init_engine(self) -> None:
        if self._engine is None:
            try:
                import pyttsx3
                self._engine = pyttsx3.init()
                self._engine.setProperty('rate', int(200 * self._config.speed))
                voices = self._engine.getProperty('voices')
                if voices:
                    self._engine.setProperty('voice', voices[0].id)
            except ImportError:
                logger.warning("pyttsx3 not installed, TTS disabled")
                self._engine = None
    
    async def speak(self, text: str) -> None:
        await self._init_engine()
        if not self._engine:
            return
        
        self._speaking = True
        self._stop_event.clear()
        
        def _speak():
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as e:
                logger.error(f"TTS error: {e}")
            finally:
                self._speaking = False
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _speak)
    
    async def speak_stream(self, text_stream: AsyncIterator[str]) -> None:
        await self._init_engine()
        if not self._engine:
            async for _ in text_stream:
                pass
            return
        
        self._speaking = True
        self._stop_event.clear()
        
        buffer = ""
        async for chunk in text_stream:
            if self._stop_event.is_set():
                break
            buffer += chunk
            if any(c in buffer for c in '.!?。！？\n'):
                sentences = buffer.split('.')
                for sentence in sentences[:-1]:
                    if sentence.strip() and not self._stop_event.is_set():
                        await self.speak(sentence.strip() + '.')
                buffer = sentences[-1]
        
        if buffer.strip() and not self._stop_event.is_set():
            await self.speak(buffer.strip())
        
        self._speaking = False
    
    async def stop(self) -> None:
        self._stop_event.set()
        if self._engine:
            try:
                self._engine.stop()
            except Exception:
                pass
        self._speaking = False
    
    def is_speaking(self) -> bool:
        return self._speaking


class EdgeTTS(TTSAdapter):
    def __init__(self, config: TTSConfig):
        self._config = config
        self._speaking = False
        self._stop_event = asyncio.Event()
    
    async def speak(self, text: str) -> None:
        try:
            import edge_tts
            import tempfile
            import os
            import subprocess
            import atexit
            import signal
            
            self._speaking = True
            self._stop_event.clear()
            
            communicate = edge_tts.Communicate(text, self._config.voice if self._config.voice != "default" else "en-US-AriaNeural")
            
            # Save to temporary mp3
            fd, temp_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            
            await communicate.save(temp_path)
            
            if not self._stop_event.is_set():
                # Play using macOS afplay
                process = await asyncio.create_subprocess_exec(
                    'afplay', temp_path,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                
                # Register atexit handler to kill orphaned afplay if app crashes
                pid = process.pid
                def cleanup_audio():
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except OSError:
                        pass
                atexit.register(cleanup_audio)
                
                # Wait for playback or stop event
                while process.returncode is None:
                    if self._stop_event.is_set():
                        process.terminate()
                        break
                    await asyncio.sleep(0.1)
                
                atexit.unregister(cleanup_audio)
            
            # Cleanup
            try:
                os.unlink(temp_path)
            except OSError:
                pass
                
        except ImportError:
            logger.warning("edge-tts not installed")
        except Exception as e:
            logger.error(f"Edge TTS error: {e}")
        finally:
            self._speaking = False
    
    async def speak_stream(self, text_stream: AsyncIterator[str]) -> None:
        buffer = ""
        async for chunk in text_stream:
            if self._stop_event.is_set():
                break
            buffer += chunk
            if any(c in buffer for c in '.!?。！？\n'):
                sentences = buffer.split('.')
                for sentence in sentences[:-1]:
                    if sentence.strip() and not self._stop_event.is_set():
                        await self.speak(sentence.strip() + '.')
                buffer = sentences[-1]
        
        if buffer.strip() and not self._stop_event.is_set():
            await self.speak(buffer.strip())
    
    async def stop(self) -> None:
        self._stop_event.set()
        self._speaking = False
    
    def is_speaking(self) -> bool:
        return self._speaking


class NullTTS(TTSAdapter):
    def __init__(self, config: TTSConfig):
        self._config = config
        self._speaking = False
    
    async def speak(self, text: str) -> None:
        logger.debug(f"[TTS Disabled] Would speak: {text[:50]}...")
    
    async def speak_stream(self, text_stream: AsyncIterator[str]) -> None:
        async for _ in text_stream:
            pass
    
    async def stop(self) -> None:
        pass
    
    def is_speaking(self) -> bool:
        return False


def create_tts_adapter(config: TTSConfig, enabled: bool = True) -> TTSAdapter:
    if not enabled:
        return NullTTS(config)
    
    # Prioritize high-quality EdgeTTS first
    try:
        import edge_tts
        logger.info("Using EdgeTTS for high-quality human voice")
        return EdgeTTS(config)
    except ImportError:
        try:
            import pyttsx3
            logger.info("Using Pyttsx3 for offline voice")
            return Pyttsx3TTS(config)
        except ImportError:
            logger.warning("No TTS backend available, using null TTS")
            return NullTTS(config)