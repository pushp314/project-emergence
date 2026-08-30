from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional


@dataclass
class ModelConfig:
    name: str
    context_window: int = 4096
    max_output_tokens: int = 1024
    temperature: float = 0.7
    timeout_seconds: int = 120


@dataclass
class GenerationRequest:
    prompt: str = ""
    system_prompt: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream: bool = True
    stop_sequences: Optional[List[str]] = None


@dataclass
class GenerationResponse:
    text: str
    tokens_generated: int
    finish_reason: str
    latency_ms: float
    model: str


class ModelAdapter(ABC):
    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        pass
    
    @abstractmethod
    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def close(self) -> None:
        pass


class ModelRegistry:
    def __init__(self):
        self._adapters: Dict[str, ModelAdapter] = {}
        self._default_model: Optional[str] = None
    
    def register(self, name: str, adapter: ModelAdapter, is_default: bool = False) -> None:
        self._adapters[name] = adapter
        if is_default or self._default_model is None:
            self._default_model = name
    
    def get(self, name: Optional[str] = None) -> ModelAdapter:
        model_name = name or self._default_model
        if model_name is None:
            raise ValueError("No model specified and no default model set")
        if model_name not in self._adapters:
            raise ValueError(f"Model '{model_name}' not registered")
        return self._adapters[model_name]
    
    def list_models(self) -> List[str]:
        return list(self._adapters.keys())
    
    async def close_all(self) -> None:
        for adapter in self._adapters.values():
            await adapter.close()
        self._adapters.clear()
        self._default_model = None


_model_registry: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistry()
    return _model_registry