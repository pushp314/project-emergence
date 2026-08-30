import json
import logging
import time
import os
from typing import Any, AsyncIterator, Dict

import httpx

from app.models.base import GenerationRequest, GenerationResponse, ModelAdapter, ModelConfig

logger = logging.getLogger(__name__)


class OpenAIAdapter(ModelAdapter):
    def __init__(self, config: ModelConfig, api_key: str = ""):
        self.config = config
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = "https://api.openai.com/v1"
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.config.timeout_seconds),
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        start_time = time.time()
        
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        
        if request.messages:
            messages.extend(request.messages)
        elif request.prompt:
            messages.append({"role": "user", "content": request.prompt})
        
        payload = {
            "model": self.config.name,
            "messages": messages,
            "temperature": request.temperature if request.temperature is not None else self.config.temperature,
            "stream": False
        }
        
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
            
        if request.stop_sequences:
            payload["stop"] = request.stop_sequences
            
        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            finish_reason = data["choices"][0].get("finish_reason", "stop")
            
            tokens_generated = data.get("usage", {}).get("completion_tokens", 0)
            
            return GenerationResponse(
                text=content,
                tokens_generated=tokens_generated,
                finish_reason=finish_reason,
                latency_ms=(time.time() - start_time) * 1000,
                model=self.config.name
            )
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        # Simple non-streaming fallback for now
        response = await self.generate(request)
        yield response.text

    async def count_tokens(self, text: str) -> int:
        return len(text) // 4

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            response = await self.client.get("/models")
            return response.status_code == 200
        except Exception:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "name": self.config.name,
            "family": "openai",
            "context_window": self.config.context_window
        }

    async def close(self) -> None:
        await self.client.aclose()
