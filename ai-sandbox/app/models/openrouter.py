from __future__ import annotations

import json
import os
import time
import logging
from typing import AsyncIterator, Dict, Any, List

import httpx

from app.models.base import ModelAdapter, ModelConfig, GenerationRequest, GenerationResponse

logger = logging.getLogger(__name__)

# Resilient pool of verified active models on OpenRouter
OPENROUTER_FALLBACK_MODELS = [
    "deepseek/deepseek-chat",
    "nvidia/nemotron-3.5-lightning:free",
    "minimax/minimax-m3:free",
    "inclusionai/ling-3.0-flash-fin:free"
]


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

    def _build_payload(self, request: GenerationRequest, model_name: str, stream: bool = False) -> dict:
        messages = request.messages or []
        if request.system_prompt:
            messages = [{"role": "system", "content": request.system_prompt}] + messages
        if request.prompt:
            messages.append({"role": "user", "content": request.prompt})
        
        payload = {
            "model": model_name,
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
            "HTTP-Referer": "https://github.com/google/ai-sandbox",
            "X-Title": "AI Sandbox Autonomous Multi-Agent Lab",
            "Content-Type": "application/json"
        }

        # Try primary model first, with fallbacks on rate-limit/upstream errors
        candidate_models = [self._config.name] + [m for m in OPENROUTER_FALLBACK_MODELS if m != self._config.name]
        last_error = None

        for model_to_try in candidate_models:
            try:
                payload = self._build_payload(request, model_name=model_to_try, stream=False)
                resp = await client.post(
                    self._base_url,
                    headers=headers,
                    json=payload
                )
                
                if resp.status_code in (404, 429):
                    logger.warning(f"OpenRouter model '{model_to_try}' returned status {resp.status_code}. Trying next available model...")
                    last_error = f"Status {resp.status_code}: {resp.text[:100]}"
                    continue

                resp.raise_for_status()
                data = resp.json()
                
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                text = (message.get("content") or "").strip()
                
                usage = data.get("usage", {})
                tokens_generated = usage.get("completion_tokens", 0)
                
                return GenerationResponse(
                    text=text,
                    tokens_generated=tokens_generated,
                    finish_reason=choice.get("finish_reason", "stop"),
                    latency_ms=(time.time() - start) * 1000,
                    model=data.get("model", model_to_try)
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(f"OpenRouter attempt with '{model_to_try}' failed: {e}. Trying fallback...")

        raise RuntimeError(f"All OpenRouter model candidates failed. Last error: {last_error}")

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        client = await self._ensure_client()
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": "https://github.com/google/ai-sandbox",
            "X-Title": "AI Sandbox Autonomous Multi-Agent Lab",
            "Content-Type": "application/json"
        }
        
        payload = self._build_payload(request, model_name=self._config.name, stream=True)
        async with client.stream("POST", self._base_url, headers=headers, json=payload) as resp:
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
