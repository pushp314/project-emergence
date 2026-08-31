from __future__ import annotations

import time
import asyncio
import logging
from enum import Enum
from dataclasses import dataclass
from typing import AsyncIterator, Dict, Any, List, Optional, Callable

from app.models.base import ModelAdapter, GenerationRequest, GenerationResponse
from app.models.key_pool import AllKeysRateLimitedError

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"        # Healthy, taking requests
    OPEN = "open"            # Rate-limited/failed, bypassing requests
    HALF_OPEN = "half_open"  # Cooldown elapsed, testing with single probe


@dataclass
class TierInfo:
    name: str
    adapter: ModelAdapter
    state: CircuitState = CircuitState.CLOSED
    cooldown_until: float = 0.0
    cooldown_duration: float = 30.0
    consecutive_failures: int = 0
    total_requests: int = 0
    total_fallbacks: int = 0
    last_error: str = ""

    def is_available(self, now: float) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if now >= self.cooldown_until:
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit for provider '{self.name}' transitioned to HALF_OPEN (probing)")
                return True
            return False
        if self.state == CircuitState.HALF_OPEN:
            return True
        return False

    def remaining_cooldown(self, now: float) -> float:
        if self.state == CircuitState.OPEN and self.cooldown_until > now:
            return self.cooldown_until - now
        return 0.0

    def trip(self, error_message: str, cooldown: Optional[float] = None) -> None:
        now = time.time()
        cd = cooldown if cooldown is not None else self.cooldown_duration
        self.state = CircuitState.OPEN
        self.cooldown_until = now + cd
        self.consecutive_failures += 1
        self.total_fallbacks += 1
        self.last_error = error_message
        logger.warning(
            f"Circuit breaker TRIPPED for provider '{self.name}' -> OPEN for {cd}s (failures={self.consecutive_failures}): {error_message[:100]}"
        )

    def mark_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit probe for provider '{self.name}' SUCCEEDED -> CLOSED (fully recovered)")
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.last_error = ""


class ResilientRouter(ModelAdapter):
    """
    Multi-tier resilient model router with circuit breakers,
    automatic fast-bypass during cooldowns, and real-time telemetry.
    """
    def __init__(
        self,
        tiers: List[tuple[str, ModelAdapter]],
        cooldown_seconds: float = 30.0,
        on_switch_callback: Optional[Callable[[str, str, str], None]] = None
    ):
        if not tiers:
            raise ValueError("ResilientRouter requires at least one model tier")

        self.tiers: List[TierInfo] = [
            TierInfo(name=name, adapter=adapter, cooldown_duration=cooldown_seconds)
            for name, adapter in tiers
        ]
        self.on_switch_callback = on_switch_callback
        self._active_tier_name = self.tiers[0].name

    @property
    def active_tier(self) -> str:
        return self._active_tier_name

    def _is_rate_limit_error(self, e: Exception) -> bool:
        if isinstance(e, AllKeysRateLimitedError):
            return True
        err_str = str(e).lower()
        return (
            "429" in err_str
            or "too many requests" in err_str
            or "resource_exhausted" in err_str
            or "quota" in err_str
        )

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        now = time.time()
        last_exception = None

        for idx, tier in enumerate(self.tiers):
            if not tier.is_available(now):
                logger.debug(
                    f"Skipping tier '{tier.name}' (Circuit OPEN, {tier.remaining_cooldown(now):.1f}s cooldown remaining)"
                )
                continue

            # If we are failing over to a non-primary tier, trigger callback/notification
            if tier.name != self._active_tier_name:
                prev_tier = self._active_tier_name
                self._active_tier_name = tier.name
                if self.on_switch_callback:
                    try:
                        self.on_switch_callback(prev_tier, tier.name, tier.last_error)
                    except Exception:
                        pass

            tier.total_requests += 1
            try:
                response = await tier.adapter.generate(request)
                tier.mark_success()
                return response
            except Exception as e:
                last_exception = e
                is_rate_limit = self._is_rate_limit_error(e)
                cooldown = 30.0 if is_rate_limit else 15.0
                tier.trip(str(e), cooldown=cooldown)
                logger.warning(
                    f"Tier '{tier.name}' generation failed: {e}. Falling back to next available tier."
                )

        raise RuntimeError(
            f"All {len(self.tiers)} model tiers failed in ResilientRouter. Last error: {last_exception}"
        )

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        now = time.time()
        last_exception = None

        for idx, tier in enumerate(self.tiers):
            if not tier.is_available(now):
                continue

            if tier.name != self._active_tier_name:
                prev_tier = self._active_tier_name
                self._active_tier_name = tier.name
                if self.on_switch_callback:
                    try:
                        self.on_switch_callback(prev_tier, tier.name, tier.last_error)
                    except Exception:
                        pass

            tier.total_requests += 1
            try:
                stream_iter = tier.adapter.generate_stream(request)
                first_chunk = await stream_iter.__anext__()
                tier.mark_success()
                yield first_chunk
                async for chunk in stream_iter:
                    yield chunk
                return
            except StopAsyncIteration:
                tier.mark_success()
                return
            except Exception as e:
                last_exception = e
                is_rate_limit = self._is_rate_limit_error(e)
                cooldown = 30.0 if is_rate_limit else 15.0
                tier.trip(str(e), cooldown=cooldown)
                logger.warning(
                    f"Tier '{tier.name}' streaming failed: {e}. Falling back to next available tier."
                )

        raise RuntimeError(
            f"All {len(self.tiers)} model tiers failed streaming. Last error: {last_exception}"
        )

    async def count_tokens(self, text: str) -> int:
        for tier in self.tiers:
            try:
                return await tier.adapter.count_tokens(text)
            except Exception:
                continue
        return len(text) // 4

    async def health_check(self) -> bool:
        for tier in self.tiers:
            if await tier.adapter.health_check():
                return True
        return False

    def get_model_info(self) -> Dict[str, Any]:
        info = self.get_telemetry()
        # Find active tier adapter info
        active_adapter = next((t.adapter for t in self.tiers if t.name == self._active_tier_name), self.tiers[0].adapter)
        info["name"] = getattr(getattr(active_adapter, "_config", None), "name", self._active_tier_name)
        info["context_window"] = getattr(getattr(active_adapter, "_config", None), "context_window", 8192)
        return info

    def get_telemetry(self) -> Dict[str, Any]:
        now = time.time()
        tiers_data = []
        for t in self.tiers:
            adapter_info = t.adapter.get_model_info() if hasattr(t.adapter, "get_model_info") else {}
            tiers_data.append({
                "name": t.name,
                "model_name": getattr(getattr(t.adapter, "_config", None), "name", t.name),
                "state": t.state.value if t.is_available(now) and t.state != CircuitState.OPEN else "open",
                "cooldown_remaining": round(t.remaining_cooldown(now), 1),
                "total_requests": t.total_requests,
                "total_fallbacks": t.total_fallbacks,
                "last_error": t.last_error,
                "details": adapter_info
            })

        active_adapter = next((t.adapter for t in self.tiers if t.name == self._active_tier_name), self.tiers[0].adapter)
        return {
            "name": getattr(getattr(active_adapter, "_config", None), "name", self._active_tier_name),
            "active_tier": self._active_tier_name,
            "total_tiers": len(self.tiers),
            "tiers": tiers_data
        }

    async def close(self) -> None:
        for tier in self.tiers:
            try:
                await tier.adapter.close()
            except Exception:
                pass
