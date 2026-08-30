from __future__ import annotations
import time, json, logging
from typing import AsyncIterator
import httpx
from app.models.base import ModelAdapter, ModelConfig, GenerationRequest, GenerationResponse

logger = logging.getLogger(__name__)

class MLXServerAdapter(ModelAdapter):
    def __init__(self, config: ModelConfig, host: str = "http://127.0.0.1:8081"):
        self._config = config
        self._host = host.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._config.timeout_seconds)
        return self._client

    def _build_messages(self, request: GenerationRequest) -> list[dict]:
        msgs = list(request.messages or [])
        if request.system_prompt:
            msgs = [{"role": "system", "content": request.system_prompt}] + msgs
        if request.prompt:
            msgs.append({"role": "user", "content": request.prompt})
        return msgs

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        client = await self._ensure_client()
        start = time.time()
        resp = await client.post(f"{self._host}/v1/chat/completions", json={
            "model": self._config.name,
            "messages": self._build_messages(request),
            "max_tokens": request.max_tokens or self._config.max_output_tokens,
            "temperature": request.temperature if request.temperature is not None else self._config.temperature,
            "stream": False,
        })
        resp.raise_for_status()
        data = resp.json()
        choice = data["choices"][0]
        return GenerationResponse(
            text=choice["message"]["content"],
            tokens_generated=data.get("usage", {}).get("completion_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
            latency_ms=(time.time() - start) * 1000,
            model=self._config.name,
        )

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        client = await self._ensure_client()
        async with client.stream("POST", f"{self._host}/v1/chat/completions", json={
            "model": self._config.name,
            "messages": self._build_messages(request),
            "max_tokens": request.max_tokens or self._config.max_output_tokens,
            "temperature": request.temperature if request.temperature is not None else self._config.temperature,
            "stream": True,
        }) as resp:
            async for line in resp.aiter_lines():
                if not line.startswith("data: ") or line.strip() == "data: [DONE]":
                    continue
                chunk = json.loads(line[6:])
                delta = chunk["choices"][0]["delta"].get("content")
                if delta:
                    yield delta

    async def count_tokens(self, text: str) -> int:
        return len(text) // 4  # rough estimate; mlx_lm server has no tokenize endpoint by default

    async def health_check(self) -> bool:
        try:
            client = await self._ensure_client()
            r = await client.get(f"{self._host}/v1/models", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def get_model_info(self) -> dict:
        return {"name": self._config.name, "backend": "mlx", "context_window": self._config.context_window}

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
