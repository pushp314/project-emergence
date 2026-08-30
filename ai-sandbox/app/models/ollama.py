from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx
import logging

from app.models.base import ModelAdapter, ModelConfig, GenerationRequest, GenerationResponse

logger = logging.getLogger(__name__)


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
            await self._pull_model()
            self._model_loaded = True
    
    async def _pull_model(self) -> None:
        client = await self._ensure_client()
        try:
            resp = await client.post(
                f"{self._host}/api/pull",
                json={"name": self._config.name, "stream": False}
            )
            if resp.status_code != 200:
                logger.warning(f"Model pull returned {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.warning(f"Failed to pull model {self._config.name}: {e}")
    
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
        client = await self._ensure_client()
        try:
            resp = await client.post(
                f"{self._host}/api/embeddings",
                json={"model": self._config.name, "prompt": text}
            )
            if resp.status_code == 200:
                data = resp.json()
                return len(data.get("embedding", []))
        except Exception:
            pass
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


async def create_ollama_adapter(config: ModelConfig, host: str = "http://127.0.0.1:11434") -> OllamaAdapter:
    adapter = OllamaAdapter(config, host)
    healthy = await adapter.health_check()
    if not healthy:
        logger.warning(f"Ollama at {host} not responding, but continuing anyway")
    return adapter