from __future__ import annotations

import time
import logging
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class KeyStatusEnum(str, Enum):
    ACTIVE = "active"
    COOLING = "cooling"
    DISABLED = "disabled"


class AllKeysRateLimitedError(Exception):
    def __init__(self, message: str, cooldown_remaining: float):
        super().__init__(message)
        self.cooldown_remaining = cooldown_remaining


@dataclass
class KeyInfo:
    key: str
    status: KeyStatusEnum = KeyStatusEnum.ACTIVE
    cooldown_until: float = 0.0
    consecutive_errors: int = 0
    total_requests: int = 0
    total_errors: int = 0

    @property
    def masked_key(self) -> str:
        if len(self.key) <= 8:
            return "***"
        return f"{self.key[:4]}...{self.key[-4:]}"

    def is_available(self, now: float) -> bool:
        if self.status == KeyStatusEnum.DISABLED:
            return False
        if self.status == KeyStatusEnum.COOLING:
            if now >= self.cooldown_until:
                self.status = KeyStatusEnum.ACTIVE
                self.consecutive_errors = 0
                return True
            return False
        return True

    def remaining_cooldown(self, now: float) -> float:
        if self.status == KeyStatusEnum.COOLING and self.cooldown_until > now:
            return self.cooldown_until - now
        return 0.0


class APIKeyPool:
    def __init__(self, keys: Optional[List[str] | str] = None, default_cooldown: float = 30.0):
        self._keys: List[KeyInfo] = []
        self._current_index: int = 0
        self.default_cooldown = default_cooldown

        if keys:
            self.add_keys(keys)

    def add_keys(self, keys: List[str] | str) -> None:
        if isinstance(keys, str):
            # Split comma, semicolon, or newline separated strings
            raw_keys = [k.strip() for k in keys.replace(";", ",").replace("\n", ",").split(",") if k.strip()]
        else:
            raw_keys = [k.strip() for k in keys if k and k.strip()]

        for k in raw_keys:
            if not any(info.key == k for info in self._keys):
                self._keys.append(KeyInfo(key=k))
                logger.info(f"Registered API key in pool: {self._keys[-1].masked_key}")

    @property
    def total_keys(self) -> int:
        return len(self._keys)

    def get_next_key(self) -> str:
        if not self._keys:
            raise ValueError("API Key pool is empty")

        now = time.time()
        n = len(self._keys)

        # Check round-robin from current index
        for i in range(n):
            idx = (self._current_index + i) % n
            key_info = self._keys[idx]
            if key_info.is_available(now):
                self._current_index = (idx + 1) % n
                key_info.total_requests += 1
                return key_info.key

        # If none are available, find the shortest remaining cooldown
        cooldowns = [k.remaining_cooldown(now) for k in self._keys if k.status == KeyStatusEnum.COOLING]
        min_cd = min(cooldowns) if cooldowns else self.default_cooldown
        raise AllKeysRateLimitedError(
            f"All {len(self._keys)} API keys in pool are rate-limited (cooldown remaining: {min_cd:.1f}s)",
            cooldown_remaining=min_cd
        )

    def mark_rate_limited(self, key: str, cooldown_seconds: Optional[float] = None) -> None:
        now = time.time()
        cd = cooldown_seconds if cooldown_seconds is not None else self.default_cooldown
        for k in self._keys:
            if k.key == key:
                k.status = KeyStatusEnum.COOLING
                k.cooldown_until = now + cd
                k.consecutive_errors += 1
                k.total_errors += 1
                logger.warning(
                    f"API Key {k.masked_key} marked COOLING for {cd}s (errors={k.consecutive_errors})"
                )
                break

    def mark_success(self, key: str) -> None:
        for k in self._keys:
            if k.key == key:
                k.status = KeyStatusEnum.ACTIVE
                k.consecutive_errors = 0
                break

    def get_status(self) -> Dict[str, Any]:
        now = time.time()
        active_count = sum(1 for k in self._keys if k.is_available(now))
        cooling_count = sum(1 for k in self._keys if k.status == KeyStatusEnum.COOLING and not k.is_available(now))
        return {
            "total_keys": len(self._keys),
            "active_keys": active_count,
            "cooling_keys": cooling_count,
            "keys": [
                {
                    "masked": k.masked_key,
                    "status": "active" if k.is_available(now) else k.status.value,
                    "cooldown_remaining": round(k.remaining_cooldown(now), 1),
                    "total_requests": k.total_requests,
                    "total_errors": k.total_errors
                }
                for k in self._keys
            ]
        }
