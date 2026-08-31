from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx
import logging

from app.models.base import ModelAdapter, ModelConfig, GenerationRequest, GenerationResponse

logger = logging.getLogger(__name__)

# Priority ranking for local models
DEFAULT_MODEL_PRIORITIES = [
    "qwen2.5-coder:7b",
    "deepseek-r1:7b-qwen-distill-q4_K_M",
    "huihui_ai/qwen3-abliterated:8b",
    "dolphin-llama3:latest",
    "dolphin-llama3:8b",
    "hf.co/nbpedro315/Dolphin3-Cyber-8B-GGUF:Q4_K_M",
]


async def list_available_ollama_models(host: str = "http://127.0.0.1:11434") -> List[str]:
    """Query Ollama API to fetch all locally downloaded models."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{host.rstrip('/')}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                return models
    except Exception as e:
        logger.debug(f"Failed to query Ollama tags at {host}: {e}")
    return []


async def discover_best_ollama_model(
    host: str = "http://127.0.0.1:11434",
    role: Optional[str] = None,
    preferred_model: Optional[str] = None
) -> Optional[str]:
    """Auto-detect and rank the best available model in local Ollama library."""
    available = await list_available_ollama_models(host)
    if not available:
        return None

    # If preferred model is explicitly available, use it
    if preferred_model and preferred_model in available:
        return preferred_model

    # Match role-specific preferences
    if role in ("developer", "coder"):
        coder_models = [m for m in available if "coder" in m.lower()]
        if coder_models:
            return coder_models[0]
    elif role in ("planning", "architect", "observer"):
        reasoning_models = [m for m in available if "r1" in m.lower() or "reasoning" in m.lower()]
        if reasoning_models:
            return reasoning_models[0]

    # Check priority list
    for candidate in DEFAULT_MODEL_PRIORITIES:
        for av in available:
            if candidate == av or candidate.split(":")[0] == av.split(":")[0]:
                return av

    # Return first available model
    return available[0]


class OllamaAdapter(ModelAdapter):
    def __init__(self, config: ModelConfig, host: str = "http://127.0.0.1:11434"):
        self._config = config
        self._host = host.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None
        self._model_loaded = False
    
    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._config.timeout_seconds)
        return self._client
    
    async def _ensure_model_loaded(self) -> None:
        if not self._model_loaded:
            self._model_loaded = True
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        await self._ensure_model_loaded()
        client = await self._ensure_client()
        
        start_time = time.time()
        
        messages = request.messages or []
        if request.system_prompt:
            messages = [{"role": "system", "content": request.system_prompt}] + messages
        if request.prompt:
            messages.append({"role": "user", "content": request.prompt})
        
        payload = {
            "model": self._config.name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request.temperature or self._config.temperature,
                "num_predict": request.max_tokens or self._config.max_output_tokens,
                "num_ctx": self._config.context_window,
            }
        }
        
        if request.stop_sequences:
            payload["options"]["stop"] = request.stop_sequences
        
        try:
            resp = await client.post(f"{self._host}/api/chat", json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Ollama API error {resp.status_code}: {resp.text}")
            
            data = resp.json()
            latency_ms = (time.time() - start_time) * 1000
            
            message = data.get("message", {})
            text = message.get("content", "")
            tokens = data.get("eval_count", 0)
            
            return GenerationResponse(
                text=text,
                tokens_generated=tokens,
                finish_reason=data.get("done_reason", "stop"),
                latency_ms=latency_ms,
                model=self._config.name
            )
        except httpx.TimeoutException:
            raise TimeoutError(f"Ollama generation timed out after {self._config.timeout_seconds}s")
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        await self._ensure_model_loaded()
        client = await self._ensure_client()
        
        messages = request.messages or []
        if request.system_prompt:
            messages = [{"role": "system", "content": request.system_prompt}] + messages
        if request.prompt:
            messages.append({"role": "user", "content": request.prompt})
        
        payload = {
            "model": self._config.name,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": request.temperature or self._config.temperature,
                "num_predict": request.max_tokens or self._config.max_output_tokens,
                "num_ctx": self._config.context_window,
            }
        }
        
        if request.stop_sequences:
            payload["options"]["stop"] = request.stop_sequences
        
        try:
            async with client.stream("POST", f"{self._host}/api/chat", json=payload) as resp:
                if resp.status_code != 200:
                    await resp.aread()
                    raise RuntimeError(f"Ollama API error {resp.status_code}: {resp.text}")
                
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            chunk = data["message"]["content"]
                            if chunk:
                                yield chunk
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
        except httpx.TimeoutException:
            raise TimeoutError(f"Ollama streaming timed out after {self._config.timeout_seconds}s")
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            raise
    
    async def count_tokens(self, text: str) -> int:
        return len(text) // 4
    
    async def health_check(self) -> bool:
        try:
            client = await self._ensure_client()
            resp = await client.get(f"{self._host}/api/tags")
            return resp.status_code == 200
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self._config.name,
            "backend": "ollama",
            "context_window": self._config.context_window,
            "max_output_tokens": self._config.max_output_tokens,
            "temperature": self._config.temperature,
            "host": self._host,
            "loaded": self._model_loaded
        }
    
    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        self._model_loaded = False


async def create_ollama_adapter(
    config: ModelConfig,
    host: str = "http://127.0.0.1:11434",
    auto_detect: bool = True
) -> OllamaAdapter:
    if auto_detect:
        detected = await discover_best_ollama_model(host, preferred_model=config.name)
        if detected:
            logger.info(f"Ollama auto-detected local model: {detected}")
            config.name = detected

    adapter = OllamaAdapter(config, host)
    healthy = await adapter.health_check()
    if not healthy:
        logger.warning(f"Ollama at {host} not responding, but continuing anyway")
    return adapter