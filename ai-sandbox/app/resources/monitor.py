from __future__ import annotations

import asyncio
import logging
import platform
import psutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Awaitable

from app.events.bus import EventBus, Event, EventType, get_event_bus

logger = logging.getLogger(__name__)


class ResourceLevel(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ResourceMetrics:
    ram_used_gb: float
    ram_total_gb: float
    ram_percent: float
    cpu_percent: float
    gpu_percent: float = 0.0
    generation_latency_ms: float = 0.0
    active_model: str = ""
    queue_length: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    @property
    def ram_available_gb(self) -> float:
        return self.ram_total_gb - self.ram_used_gb


@dataclass
class ResourceThresholds:
    memory_warning_gb: float = 12.0
    memory_critical_gb: float = 14.0
    cpu_warning_percent: float = 80.0
    cpu_critical_percent: float = 95.0
    latency_warning_ms: float = 5000.0
    check_interval_seconds: float = 5.0


@dataclass
class ResourceState:
    level: ResourceLevel = ResourceLevel.NORMAL
    metrics: Optional[ResourceMetrics] = None
    warnings: List[str] = field(default_factory=list)
    last_check: Optional[str] = None


class ResourceManager:
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        thresholds: Optional[ResourceThresholds] = None,
        evidence_manager=None
    ):
        self.event_bus = event_bus or get_event_bus()
        self.thresholds = thresholds or ResourceThresholds()
        self._state = ResourceState()
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._callbacks: Dict[ResourceLevel, List[Callable[[ResourceState], Awaitable[None]]]] = {
            ResourceLevel.NORMAL: [],
            ResourceLevel.WARNING: [],
            ResourceLevel.CRITICAL: []
        }
        self._generation_latencies: List[float] = []
        self._max_latency_samples = 10
        self._evidence_manager = evidence_manager
    
    def add_callback(self, level: ResourceLevel, callback: Callable[[ResourceState], Awaitable[None]]) -> None:
        self._callbacks[level].append(callback)
    
    def record_generation_latency(self, latency_ms: float, model: str = "") -> None:
        self._generation_latencies.append(latency_ms)
        if len(self._generation_latencies) > self._max_latency_samples:
            self._generation_latencies.pop(0)
        
        if self._state.metrics:
            self._state.metrics.generation_latency_ms = latency_ms
            self._state.metrics.active_model = model
    
    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Resource manager started")
    
    async def stop(self) -> None:
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Resource manager stopped")
    
    async def _monitor_loop(self) -> None:
        while self._running:
            try:
                await self._check_resources()
            except Exception as e:
                logger.error(f"Resource check error: {e}")
            
            await asyncio.sleep(self.thresholds.check_interval_seconds)
    
    async def _check_resources(self) -> None:
        try:
            ram = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.1)
            
            ram_used_gb = ram.used / (1024 ** 3)
            ram_total_gb = ram.total / (1024 ** 3)
            
            avg_latency = 0.0
            if self._generation_latencies:
                avg_latency = sum(self._generation_latencies) / len(self._generation_latencies)
            
            metrics = ResourceMetrics(
                ram_used_gb=ram_used_gb,
                ram_total_gb=ram_total_gb,
                ram_percent=ram.percent,
                cpu_percent=cpu,
                generation_latency_ms=avg_latency,
                active_model=self._state.metrics.active_model if self._state.metrics else ""
            )
            
            # Persist metrics to evidence manager
            if self._evidence_manager:
                self._evidence_manager.record_resource_metrics({
                    "ram_used_gb": ram_used_gb,
                    "ram_total_gb": ram_total_gb,
                    "cpu_percent": cpu,
                    "gpu_percent": 0.0,
                    "inference_latency_ms": avg_latency,
                    "tokens_per_second": 0.0,
                    "context_tokens": 0,
                    "active_agents": 0,
                    "active_model": self._state.metrics.active_model if self._state.metrics else "",
                    "queue_depth": 0
                })
            
            old_level = self._state.level
            new_level = self._evaluate_level(metrics)
            warnings = self._generate_warnings(metrics)
            
            self._state = ResourceState(
                level=new_level,
                metrics=metrics,
                warnings=warnings,
                last_check=datetime.now(timezone.utc).isoformat()
            )
            
            if new_level != old_level:
                await self._trigger_callbacks(new_level)
                
                if new_level == ResourceLevel.WARNING:
                    await self.event_bus.publish_type(
                        EventType.RESOURCE_WARNING,
                        "system",
                        {"level": "warning", "metrics": self._metrics_to_dict(metrics), "warnings": warnings}
                    )
                elif new_level == ResourceLevel.CRITICAL:
                    await self.event_bus.publish_type(
                        EventType.RESOURCE_CRITICAL,
                        "system",
                        {"level": "critical", "metrics": self._metrics_to_dict(metrics), "warnings": warnings}
                    )
            
        except Exception as e:
            logger.error(f"Resource monitoring error: {e}")
    
    def _evaluate_level(self, metrics: ResourceMetrics) -> ResourceLevel:
        if (metrics.ram_used_gb >= self.thresholds.memory_critical_gb or
            metrics.cpu_percent >= self.thresholds.cpu_critical_percent or
            metrics.generation_latency_ms >= self.thresholds.latency_warning_ms * 2):
            return ResourceLevel.CRITICAL
        
        if (metrics.ram_used_gb >= self.thresholds.memory_warning_gb or
            metrics.cpu_percent >= self.thresholds.cpu_warning_percent or
            metrics.generation_latency_ms >= self.thresholds.latency_warning_ms):
            return ResourceLevel.WARNING
        
        return ResourceLevel.NORMAL
    
    def _generate_warnings(self, metrics: ResourceMetrics) -> List[str]:
        warnings = []
        
        if metrics.ram_used_gb >= self.thresholds.memory_critical_gb:
            warnings.append(f"Critical memory: {metrics.ram_used_gb:.1f}GB / {metrics.ram_total_gb:.1f}GB")
        elif metrics.ram_used_gb >= self.thresholds.memory_warning_gb:
            warnings.append(f"High memory: {metrics.ram_used_gb:.1f}GB / {metrics.ram_total_gb:.1f}GB")
        
        if metrics.cpu_percent >= self.thresholds.cpu_critical_percent:
            warnings.append(f"Critical CPU: {metrics.cpu_percent:.1f}%")
        elif metrics.cpu_percent >= self.thresholds.cpu_warning_percent:
            warnings.append(f"High CPU: {metrics.cpu_percent:.1f}%")
        
        if metrics.generation_latency_ms >= self.thresholds.latency_warning_ms * 2:
            warnings.append(f"Critical latency: {metrics.generation_latency_ms:.0f}ms")
        elif metrics.generation_latency_ms >= self.thresholds.latency_warning_ms:
            warnings.append(f"High latency: {metrics.generation_latency_ms:.0f}ms")
        
        return warnings
    
    def _metrics_to_dict(self, metrics: ResourceMetrics) -> Dict[str, Any]:
        return {
            "ram_used_gb": metrics.ram_used_gb,
            "ram_total_gb": metrics.ram_total_gb,
            "ram_percent": metrics.ram_percent,
            "cpu_percent": metrics.cpu_percent,
            "gpu_percent": metrics.gpu_percent,
            "generation_latency_ms": metrics.generation_latency_ms,
            "active_model": metrics.active_model,
            "queue_length": metrics.queue_length
        }
    
    async def _trigger_callbacks(self, level: ResourceLevel) -> None:
        for callback in self._callbacks.get(level, []):
            try:
                await callback(self._state)
            except Exception as e:
                logger.error(f"Resource callback error: {e}")
        
        for callback in self._callbacks.get(ResourceLevel.NORMAL, []):
            try:
                await callback(self._state)
            except Exception as e:
                logger.error(f"Resource callback error: {e}")
    
    def get_state(self) -> ResourceState:
        return self._state
    
    def get_metrics(self) -> Optional[ResourceMetrics]:
        return self._state.metrics
    
    def should_throttle(self) -> bool:
        return self._state.level in (ResourceLevel.WARNING, ResourceLevel.CRITICAL)
    
    def should_pause_observer(self) -> bool:
        return self._state.level == ResourceLevel.CRITICAL
    
    def get_throttle_factor(self) -> float:
        if self._state.level == ResourceLevel.CRITICAL:
            return 0.5
        elif self._state.level == ResourceLevel.WARNING:
            return 0.75
        return 1.0


_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager


def set_resource_manager(manager: ResourceManager) -> None:
    global _resource_manager
    _resource_manager = manager