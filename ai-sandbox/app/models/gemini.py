from __future__ import annotations

import time
import os
import logging
from typing import AsyncIterator, List, Optional, Union, Dict, Any
import httpx

from app.models.base import ModelAdapter, ModelConfig, GenerationRequest, GenerationResponse
from app.models.key_pool import APIKeyPool, AllKeysRateLimitedError

logger = logging.getLogger(__name__)

# Verified active models available on Gemini Developer API
GEMINI_FALLBACK_MODELS = [
    "gemini-3.1-flash-lite-preview",
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it",
    "gemini-2.5-flash"
]


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

        candidate_models = [self._config.name] + [m for m in GEMINI_FALLBACK_MODELS if m != self._config.name]

        for attempt in range(max_retries):
            current_key = self._pool.get_next_key()
            
            for model_name in candidate_models:
                url = f"{self._base}/models/{model_name}:generateContent?key={current_key}"
                try:
                    resp = await client.post(url, json=self._build_body(request))
                    
                    # If specific model is 404 (unavailable/deprecated) or 429 quota reached, try other model in family
                    if resp.status_code in (404, 429):
                        logger.warning(
                            f"Gemini model '{model_name}' returned status {resp.status_code}. Checking alternative Gemini models..."
                        )
                        continue

                    if resp.status_code != 200:
                        logger.warning(f"Gemini API error ({resp.status_code}): {resp.text[:150]}")
                        continue

                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        continue

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
                        model=model_name,
                    )
                except httpx.TimeoutException:
                    logger.warning(f"Gemini request for '{model_name}' timed out. Trying next model...")
                    continue
                except Exception as e:
                    logger.warning(f"Gemini error with '{model_name}': {e}")
                    continue

            # If all candidate models for this key failed due to rate limiting
            self._pool.mark_rate_limited(current_key, cooldown_seconds=30.0)

        # If loop finishes without returning, trigger key pool exhaustion error
        raise AllKeysRateLimitedError("All Gemini keys and model variants have been exhausted", cooldown_remaining=30.0)

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        result = await self.generate(request)
        yield result.text

    async def count_tokens(self, text: str) -> int:
        client = await self._ensure_client()
        try:
            current_key = self._pool.get_next_key()
            url = f"{self._base}/models/{self._config.name}:countTokens?key={current_key}"
            resp = await client.post(url, json={"contents": [{"parts": [{"text": text}]}]})
            if resp.status_code == 200:
                data = resp.json()
                return data.get("totalTokens", len(text) // 4)
        except Exception:
            pass
        return len(text) // 4

    async def health_check(self) -> bool:
        return self._pool.has_active_keys()

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self._config.name,
            "backend": "gemini",
            "context_window": self._config.context_window,
            "key_pool": self._pool.get_status(),
        }

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
