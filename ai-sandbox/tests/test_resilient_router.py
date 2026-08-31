import asyncio
import time
import os
import unittest
from unittest.mock import AsyncMock, patch

from app.models.base import ModelConfig, GenerationRequest, GenerationResponse
from app.models.key_pool import APIKeyPool, KeyStatusEnum, AllKeysRateLimitedError
from app.models.circuit_breaker import ResilientRouter, CircuitState
from app.models.ollama import list_available_ollama_models, discover_best_ollama_model


class DummyAdapter:
    def __init__(self, name: str, should_fail: bool = False, is_rate_limit: bool = False):
        self.name = name
        self.should_fail = should_fail
        self.is_rate_limit = is_rate_limit
        self.calls = 0

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        self.calls += 1
        if self.is_rate_limit:
            raise Exception("429 Too Many Requests: Rate limit exceeded")
        if self.should_fail:
            raise Exception(f"{self.name} simulated connection failure")
        return GenerationResponse(text=f"Response from {self.name}", tokens_generated=10, finish_reason="stop", latency_ms=50.0, model=self.name)

    async def generate_stream(self, request: GenerationRequest):
        res = await self.generate(request)
        yield res.text

    async def count_tokens(self, text: str) -> int:
        return len(text) // 4

    async def health_check(self) -> bool:
        return not self.should_fail

    def get_model_info(self) -> dict:
        return {"name": self.name}

    async def close(self) -> None:
        pass


class TestResilientRouter(unittest.IsolatedAsyncioTestCase):
    def test_key_pool_rotation_and_cooldown(self):
        pool = APIKeyPool(["KEY1", "KEY2"], default_cooldown=1.0)
        self.assertEqual(pool.total_keys, 2)
        
        # Round robin
        k1 = pool.get_next_key()
        k2 = pool.get_next_key()
        self.assertNotEqual(k1, k2)

        # Mark KEY1 rate limited
        pool.mark_rate_limited("KEY1", cooldown_seconds=0.5)
        # Should now return KEY2
        k = pool.get_next_key()
        self.assertEqual(k, "KEY2")

        # Mark KEY2 rate limited as well
        pool.mark_rate_limited("KEY2", cooldown_seconds=0.5)
        # Now both are rate limited
        with self.assertRaises(AllKeysRateLimitedError):
            pool.get_next_key()

        # Wait for cooldown to expire
        time.sleep(0.6)
        # Now key should be active again
        k_recovered = pool.get_next_key()
        self.assertIn(k_recovered, ["KEY1", "KEY2"])

    async def test_router_circuit_breaker_failover(self):
        primary = DummyAdapter("gemini", is_rate_limit=True)
        fallback = DummyAdapter("ollama_local", should_fail=False)

        switches = []
        def on_switch(prev, curr, reason):
            switches.append((prev, curr))

        router = ResilientRouter(
            tiers=[("gemini", primary), ("ollama_local", fallback)],
            cooldown_seconds=1.0,
            on_switch_callback=on_switch
        )

        req = GenerationRequest(prompt="Hello")
        resp = await router.generate(req)

        self.assertEqual(resp.text, "Response from ollama_local")
        self.assertEqual(router.tiers[0].state, CircuitState.OPEN)
        self.assertEqual(router.active_tier, "ollama_local")

        # Second request should FAST-BYPASS tier 0 (gemini) directly to tier 1 (ollama_local)
        calls_before = primary.calls
        resp2 = await router.generate(req)
        self.assertEqual(resp2.text, "Response from ollama_local")
        self.assertEqual(primary.calls, calls_before)  # Zero calls made to gemini while open!

    async def test_ollama_auto_discovery(self):
        models = await list_available_ollama_models()
        if models:
            best = await discover_best_ollama_model(role="coder")
            self.assertIsNotNone(best)
            print(f"Discovered Ollama models: {models}, selected best: {best}")


if __name__ == "__main__":
    unittest.main()
