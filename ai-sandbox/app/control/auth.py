from __future__ import annotations

import hashlib
import logging
import secrets
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class AuthConfig:
    enabled: bool = False
    api_keys: Dict[str, str] = field(default_factory=dict)


class AuthManager:
    def __init__(self, config: Optional[AuthConfig] = None):
        self._config = config or AuthConfig()

    @property
    def enabled(self) -> bool:
        return self._config.enabled

    def enable(self) -> None:
        self._config.enabled = True
        logger.info("Auth enabled")

    def disable(self) -> None:
        self._config.enabled = False
        logger.info("Auth disabled")

    def check_auth(self, key: str) -> bool:
        if not self._config.enabled:
            return True

        if not key:
            return False

        hashed = hashlib.sha256(key.encode()).hexdigest()
        return hashed in self._config.api_keys

    def generate_key(self) -> str:
        raw_key = secrets.token_urlsafe(32)
        hashed = hashlib.sha256(raw_key.encode()).hexdigest()
        self._config.api_keys[hashed] = f"key_{len(self._config.api_keys) + 1}"
        logger.info("New API key generated")
        return raw_key

    def revoke_key(self, hashed_key: str) -> bool:
        if hashed_key in self._config.api_keys:
            del self._config.api_keys[hashed_key]
            logger.info(f"Key revoked: {hashed_key[:8]}...")
            return True
        return False

    def load_keys(self, keys: Dict[str, str]) -> None:
        self._config.api_keys.update(keys)

    def get_key_count(self) -> int:
        return len(self._config.api_keys)


_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


def set_auth_manager(manager: AuthManager) -> None:
    global _auth_manager
    _auth_manager = manager
