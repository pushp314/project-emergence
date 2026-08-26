"""
Structured JSONL Logging Configuration

Provides structured logging for the Evidence Plane and audit trail.
"""
from __future__ import annotations

import json
import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from app.events.bus import EventBus, Event, EventType, get_event_bus


class JSONLFormatter(logging.Formatter):
    """Format log records as JSONL (JSON Lines)."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, "event_type"):
            log_data["event_type"] = record.event_type
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "agent_id"):
            log_data["agent_id"] = record.agent_id
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """Wrapper for structured logging with context."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _log(self, level: int, message: str, **kwargs) -> None:
        extra = {k: v for k, v in kwargs.items() if k not in ["exc_info"]}
        self.logger.log(level, message, extra=extra, **{k: v for k, v in kwargs.items() if k in ["exc_info"]})
    
    def debug(self, message: str, **kwargs) -> None:
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        self._log(logging.CRITICAL, message, **kwargs)
    
    def log_event(self, event: Event) -> None:
        """Log an event from the Event Bus."""
        self.info(
            f"Event: {event.type.value}",
            event_type=event.type.value,
            session_id=event.payload.get("session_id"),
            agent_id=event.payload.get("agent_id"),
            correlation_id=event.payload.get("correlation_id"),
            event_id=event.event_id
        )


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "./logs",
    jsonl: bool = True,
    console: bool = True
) -> logging.Logger:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        jsonl: Whether to use JSONL format for file logs
        console: Whether to log to console
    
    Returns:
        Root logger
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # JSONL file handler for all events
    if jsonl:
        events_handler = logging.handlers.RotatingFileHandler(
            log_path / "events.jsonl",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        events_handler.setFormatter(JSONLFormatter())
        events_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(events_handler)
        
        # Separate error log
        error_handler = logging.handlers.RotatingFileHandler(
            log_path / "errors.jsonl",
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )
        error_handler.setFormatter(JSONLFormatter())
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
        
        # Performance metrics log
        perf_handler = logging.handlers.RotatingFileHandler(
            log_path / "performance.jsonl",
            maxBytes=10 * 1024 * 1024,
            backupCount=5
        )
        perf_handler.setFormatter(JSONLFormatter())
        perf_handler.setLevel(logging.INFO)
        perf_handler.addFilter(lambda r: "performance" in getattr(r, "tags", []))
        root_logger.addHandler(perf_handler)
    
    # Human-readable console output
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%H:%M:%S"
            )
        )
        console_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(console_handler)
    
    # Reduce noise from third-party loggers
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    return root_logger


class EventBusLogger:
    """Logs all Event Bus events to structured logs."""
    
    def __init__(self, event_bus: EventBus, logger: Optional[logging.Logger] = None):
        self.event_bus = event_bus
        self.logger = logger or logging.getLogger("eventbus")
        self._subscriptions = []
    
    def start(self) -> None:
        """Start logging all events."""
        event_types = [
            EventType.AGENT_MESSAGE,
            EventType.AGENT_STARTED,
            EventType.AGENT_COMPLETED,
            EventType.AGENT_ERROR,
            EventType.HUMAN_MESSAGE,
            EventType.HUMAN_INTERRUPT,
            EventType.TOOL_REQUEST,
            EventType.TOOL_STARTED,
            EventType.TOOL_COMPLETED,
            EventType.TOOL_FAILED,
            EventType.PERMISSION_REQUEST,
            EventType.PERMISSION_APPROVED,
            EventType.PERMISSION_DENIED,
            EventType.MEMORY_UPDATED,
            EventType.OBSERVER_INTERVENTION,
            EventType.RESOURCE_WARNING,
            EventType.RESOURCE_CRITICAL,
            EventType.SYSTEM_PAUSE,
            EventType.SYSTEM_RESUME,
            EventType.SYSTEM_STOP,
            EventType.CONVERSATION_TURN_START,
            EventType.CONVERSATION_TURN_END,
        ]
        
        for event_type in event_types:
            self._subscriptions.append(
                self.event_bus.subscribe(event_type, self._on_event)
            )
    
    def stop(self) -> None:
        """Stop logging events."""
        # Note: EventBus doesn't have unsubscribe by callback, would need to track
        pass
    
    async def _on_event(self, event: Event) -> None:
        """Handle an event by logging it."""
        log_data = {
            "event_type": event.type.value,
            "event_id": event.event_id,
            "conversation_id": event.conversation_id,
            "timestamp": event.timestamp,
            "payload": event.payload,
            "metadata": event.metadata,
        }
        
        self.logger.info(
            f"Event: {event.type.value}",
            extra={
                "event_type": event.type.value,
                "event_data": log_data,
            }
        )


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    **kwargs
) -> None:
    """Log a performance metric."""
    logger.info(
        f"Performance: {operation}",
        extra={
            "performance": True,
            "operation": operation,
            "duration_ms": duration_ms,
            **kwargs
        },
        tags=["performance"]
    )