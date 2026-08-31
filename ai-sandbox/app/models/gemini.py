from __future__ import annotations

import time
import os
import logging
from typing import AsyncIterator, List, Optional, Union, Dict, Any
import httpx

from app.models.base import ModelAdapter, ModelConfig, GenerationRequest, GenerationResponse
from app.models.key_pool import APIKeyPool, AllKeysRateLimitedError

logger = logging.getLogger(__name__)


class GeminiAdapter(ModelAdapter):
    def __init__(
        self,
        config: ModelConfig,
        api_key: Optional[Union[str, List[str], APIKeyPool]] = None
    ):
        self._config = config
        self._base = "https://generativelanguage.googleapis.com/v1beta"
        self._client: httpx.AsyncClient | None = None

        if isinstance(api_key, APIKeyPool):
            self._pool = api_key
        else:
            self._pool = APIKeyPool(default_cooldown=30.0)
            if api_key:
                self._pool.add_keys(api_key)
            else:
                env_keys = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY")
                if env_keys:
                    self._pool.add_keys(env_keys)
                else:
                    raise ValueError("GEMINI_API_KEY or GEMINI_API_KEYS must be set in environment or config")

    @property
    def key_pool(self) -> APIKeyPool:
        return self._pool

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._config.timeout_seconds)
        return self._client

    def _build_body(self, request: GenerationRequest) -> dict:
        contents = []
        for m in (request.messages or []):
            role = "model" if m["role"] == "assistant" else "user"
            parts = [{"text": m["content"]}]
            if "images" in m:
                for img_b64 in m["images"]:
                    parts.append({"inlineData": {"mimeType": "image/png", "data": img_b64}})
            contents.append({"role": role, "parts": parts})

        if request.prompt or request.images:
            parts = []
            if request.prompt:
                parts.append({"text": request.prompt})
            if request.images:
                for img_b64 in request.images:
                    parts.append({"inlineData": {"mimeType": "image/png", "data": img_b64}})
            contents.append({"role": "user", "parts": parts})

        body = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature if request.temperature is not None else self._config.temperature,
                "maxOutputTokens": request.max_tokens or self._config.max_output_tokens,
            },
        }
        if request.system_prompt:
            body["systemInstruction"] = {"parts": [{"text": request.system_prompt}]}
        return body

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        client = await self._ensure_client()
        start = time.time()
        max_retries = max(1, self._pool.total_keys)

        for attempt in range(max_retries):
            current_key = self._pool.get_next_key()
            url = f"{self._base}/models/{self._config.name}:generateContent?key={current_key}"
            try:
                resp = await client.post(url, json=self._build_body(request))
                
                # Check for rate limits
                if resp.status_code == 429:
                    error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                    logger.warning(
                        f"Gemini API key rate limited (429). Rotating key... ({error_data.get('error', {}).get('message', '')[:100]})"
                    )
                    self._pool.mark_rate_limited(current_key, cooldown_seconds=30.0)
                    continue

                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise RuntimeError(f"No candidates returned by Gemini: {data}")
                candidate = candidates[0]
                content = candidate.get("content", {})
                parts = content.get("parts", []) if isinstance(content, dict) else []
                text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
                if not text:
                    text = candidate.get("finishReason", "")
                
                self._pool.mark_success(current_key)
                return GenerationResponse(
                    text=text,
                    tokens_generated=data.get("usageMetadata", {}).get("candidatesTokenCount", 0),
                    finish_reason=candidate.get("finishReason", "STOP"),
                    latency_ms=(time.time() - start) * 1000,
                    model=self._config.name,
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    self._pool.mark_rate_limited(current_key, cooldown_seconds=30.0)
                    if attempt < max_retries - 1:
                        continue
                raise
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    self._pool.mark_rate_limited(current_key, cooldown_seconds=30.0)
                    if attempt < max_retries - 1:
                        continue
                raise

        # If loop finishes without returning, trigger key pool exhaustion error
        raise AllKeysRateLimitedError("All Gemini keys in pool have been exhausted", cooldown_remaining=30.0)

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        result = await self.generate(request)
        yield result.text

    async def count_tokens(self, text: str) -> int:
        client = await self._ensure_client()
        try:
            current_key = self._pool.get_next_key()
            url = f"{self._base}/models/{self._config.name}:countTokens?key={current_key}"
            resp = await client.post(url, json={"contents": [{"parts": [{"text": text}]}]})
            return resp.json().get("totalTokens", len(text) // 4)
        except Exception:
            return len(text) // 4

    async def health_check(self) -> bool:
        try:
            await self.count_tokens("ping")
            return True
        except Exception:
            return False

    def get_model_info(self) -> dict:
        info = {
            "name": self._config.name,
            "backend": "gemini",
            "context_window": self._config.context_window,
            "key_pool": self._pool.get_status()
        }
        return info

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
