from __future__ import annotations
import logging
from typing import AsyncIterator, Dict, Any

from app.models.base import ModelAdapter, GenerationRequest, GenerationResponse

logger = logging.getLogger(__name__)

class FallbackAdapter(ModelAdapter):
    def __init__(self, primary: ModelAdapter, fallback: ModelAdapter):
        self.primary = primary
        self.fallback = fallback

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        try:
            return await self.primary.generate(request)
        except Exception as e:
            logger.warning(f"Primary model generation failed: {e}. Falling back to secondary.")
            return await self.fallback.generate(request)

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        try:
            # We attempt to start the stream. 
            # Note: if it fails halfway, we can't easily fallback transparently for the whole stream.
            # But we can at least catch initial connection/quota errors.
            iterator = self.primary.generate_stream(request)
            first_chunk = await iterator.__anext__()
            yield first_chunk
            async for chunk in iterator:
                yield chunk
        except Exception as e:
            logger.warning(f"Primary model stream failed: {e}. Falling back to secondary stream.")
            async for chunk in self.fallback.generate_stream(request):
                yield chunk

    async def count_tokens(self, text: str) -> int:
        try:
            return await self.primary.count_tokens(text)
        except Exception as e:
            logger.warning(f"Primary model token count failed: {e}. Falling back to secondary.")
            return await self.fallback.count_tokens(text)

    async def health_check(self) -> bool:
        # A fallback adapter is healthy if at least one underlying adapter is healthy
        if await self.primary.health_check():
            return True
        return await self.fallback.health_check()

    def get_model_info(self) -> Dict[str, Any]:
        info = self.primary.get_model_info()
        info["fallback"] = self.fallback.get_model_info()
        return info

    async def close(self) -> None:
        await self.primary.close()
        # Fallback adapter doesn't own the fallback model (it might be used directly elsewhere),
        # but in our registry, close_all handles all adapters. 
        # So we don't strictly need to close the fallback here.
