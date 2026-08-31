from __future__ import annotations

import json
import os
import time
import logging
from typing import AsyncIterator, Dict, Any

import httpx

from app.models.base import ModelAdapter, ModelConfig, GenerationRequest, GenerationResponse

logger = logging.getLogger(__name__)

class OpenRouterAdapter(ModelAdapter):
    def __init__(self, config: ModelConfig, api_key: str | None = None):
        self._config = config
        self._api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self._api_key:
            raise ValueError("OPENROUTER_API_KEY is not set in environment")
        self._base_url = "https://openrouter.ai/api/v1/chat/completions"
        self._client: httpx.AsyncClient | None = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._config.timeout_seconds)
        return self._client

    def _build_payload(self, request: GenerationRequest, stream: bool = False) -> dict:
        messages = request.messages or []
        if request.system_prompt:
            messages = [{"role": "system", "content": request.system_prompt}] + messages
        if request.prompt:
            messages.append({"role": "user", "content": request.prompt})
        
        payload = {
            "model": self._config.name,
            "messages": messages,
            "stream": stream,
            "temperature": request.temperature if request.temperature is not None else self._config.temperature,
            "max_tokens": request.max_tokens or self._config.max_output_tokens,
        }
        if request.stop_sequences:
            payload["stop"] = request.stop_sequences
            
        return payload

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        client = await self._ensure_client()
        start = time.time()
        
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "AI Sandbox"
        }
        
        resp = await client.post(
            self._base_url,
            headers=headers,
            json=self._build_payload(request, stream=False)
        )
        resp.raise_for_status()
        data = resp.json()
        
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        text = message.get("content", "")
        
        usage = data.get("usage", {})
        tokens_generated = usage.get("completion_tokens", 0)
        
        return GenerationResponse(
            text=text,
            tokens_generated=tokens_generated,
            finish_reason=choice.get("finish_reason", "stop"),
            latency_ms=(time.time() - start) * 1000,
            model=self._config.name
        )

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        client = await self._ensure_client()
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "AI Sandbox"
        }
        
        async with client.stream("POST", self._base_url, headers=headers, json=self._build_payload(request, stream=True)) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    choices = data.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                except json.JSONDecodeError:
                    continue

    async def count_tokens(self, text: str) -> int:
        return len(text) // 4

    async def health_check(self) -> bool:
        return True

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self._config.name,
            "backend": "openrouter",
            "context_window": self._config.context_window
        }

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
