from __future__ import annotations
import time, os, logging
from typing import AsyncIterator
import httpx
from app.models.base import ModelAdapter, ModelConfig, GenerationRequest, GenerationResponse

logger = logging.getLogger(__name__)

class GeminiAdapter(ModelAdapter):
    def __init__(self, config: ModelConfig, api_key: str | None = None):
        self._config = config
        self._api_key = api_key or os.environ["GEMINI_API_KEY"]
        self._base = "https://generativelanguage.googleapis.com/v1beta"
        self._client: httpx.AsyncClient | None = None

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
        url = f"{self._base}/models/{self._config.name}:generateContent?key={self._api_key}"
        resp = await client.post(url, json=self._build_body(request))
        resp.raise_for_status()
        data = resp.json()
        candidate = data["candidates"][0]
        text = "".join(p.get("text", "") for p in candidate["content"]["parts"])
        return GenerationResponse(
            text=text,
            tokens_generated=data.get("usageMetadata", {}).get("candidatesTokenCount", 0),
            finish_reason=candidate.get("finishReason", "STOP"),
            latency_ms=(time.time() - start) * 1000,
            model=self._config.name,
        )

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        # Simplest correct version: no true streaming yet, yield once.
        # Add streamGenerateContent + SSE parsing later if you need token-by-token UI updates.
        result = await self.generate(request)
        yield result.text

    async def count_tokens(self, text: str) -> int:
        client = await self._ensure_client()
        url = f"{self._base}/models/{self._config.name}:countTokens?key={self._api_key}"
        resp = await client.post(url, json={"contents": [{"parts": [{"text": text}]}]})
        return resp.json().get("totalTokens", len(text) // 4)

    async def health_check(self) -> bool:
        try:
            await self.count_tokens("ping")
            return True
        except Exception:
            return False

    def get_model_info(self) -> dict:
        return {"name": self._config.name, "backend": "gemini", "context_window": self._config.context_window}

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
