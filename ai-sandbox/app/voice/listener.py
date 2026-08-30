import asyncio
import logging
import pyaudio
import wave
import io
import collections
try:
    import webrtcvad
except ImportError:
    webrtcvad = None
from app.voice.engine import get_voice_engine
from app.main import SandboxApp

logger = logging.getLogger(__name__)

class ContinuousVoiceListener:
    def __init__(self, sandbox_app: SandboxApp, wake_word: str = "jarvis", status_callback = None):
        self.sandbox_app = sandbox_app
        self.wake_word = wake_word.lower()
        self.status_callback = status_callback
        self.is_listening = False
        
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK_DURATION_MS = 30  # WebRTC VAD needs 10, 20, or 30 ms chunks
        self.CHUNK_SIZE = int(self.RATE * self.CHUNK_DURATION_MS / 1000)  # 480 frames
        
        self.vad = webrtcvad.Vad(3)  # Aggressiveness mode from 0 to 3 (3 is most aggressive)
        
    def start(self):
        if self.is_listening:
            return
        self.is_listening = True
        logger.info(f"Started Continuous Voice Listener. Wake word: '{self.wake_word}'")
        asyncio.create_task(self._listen_loop())
        
    def stop(self):
        self.is_listening = False
        logger.info("Stopped Continuous Voice Listener.")
        
    async def _listen_loop(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._record_and_process_sync, loop)

    def _record_and_process_sync(self, event_loop):
        pa = pyaudio.PyAudio()
        stream = pa.open(format=self.FORMAT,
                         channels=self.CHANNELS,
                         rate=self.RATE,
                         input=True,
                         frames_per_buffer=self.CHUNK_SIZE)

        # Ring buffer to keep some audio *before* speech was detected (to not cut off first syllables)
        num_padding_chunks = int(300 / self.CHUNK_DURATION_MS)
        ring_buffer = collections.deque(maxlen=num_padding_chunks)
        
        triggered = False
        voiced_frames = []
        
        while self.is_listening:
            try:
                chunk = stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
            except Exception as e:
                logger.error(f"Audio read error: {e}")
                continue
                
            is_speech = self.vad.is_speech(chunk, self.RATE)

            if not triggered:
                ring_buffer.append((chunk, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                
                # Trigger if > 90% of ring buffer is speech
                if num_voiced > 0.9 * ring_buffer.maxlen:
                    triggered = True
                    if self.status_callback:
                        event_loop.call_soon_threadsafe(self.status_callback, True)
                    for f, s in ring_buffer:
                        voiced_frames.append(f)
                    ring_buffer.clear()
            else:
                voiced_frames.append(chunk)
                ring_buffer.append((chunk, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                
                # Stop if > 90% of ring buffer is NOT speech (silence detected)
                if num_unvoiced > 0.9 * ring_buffer.maxlen:
                    triggered = False
                    if self.status_callback:
                        event_loop.call_soon_threadsafe(self.status_callback, False)
                    audio_data = b''.join(voiced_frames)
                    voiced_frames = []
                    ring_buffer.clear()
                    
                    # Offload transcription so we don't block the audio loop
                    asyncio.run_coroutine_threadsafe(
                        self._process_audio(audio_data), event_loop
                    )

        stream.stop_stream()
        stream.close()
        pa.terminate()

    async def _process_audio(self, raw_pcm_data: bytes):
        # Convert raw PCM to WAV byte stream
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            import pyaudio
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(raw_pcm_data)
            
        audio_bytes = wav_io.getvalue()
        
        # Transcribe
        engine = get_voice_engine()
        text = await engine.transcribe(audio_bytes)
        
        if not text:
            return
            
        logger.info(f"🎙️ Heard: '{text}'")
            
        text_lower = text.lower()
        
        # Check wake word
        if self.wake_word in text_lower:
            # Check for stop/pause commands
            if "stop" in text_lower or "pause" in text_lower or "quiet" in text_lower or "shut up" in text_lower:
                logger.info("Voice command: INTERRUPT/STOP")
                await self.sandbox_app.conversation_engine.interrupt()
                # Stop any currently playing audio if we had access to the TTS engine here
                
                # Optionally, broadcast a system message so the UI sees it
                # self.sandbox_app.event_bus.publish(...)
            else:
                # Strip the wake word and punctuation, dispatch the rest
                command = text_lower.split(self.wake_word, 1)[-1].strip(" ,.!?:")
                logger.info(f"Voice command: {text}")
                await self.sandbox_app.conversation_engine.inject_human_message(text)
