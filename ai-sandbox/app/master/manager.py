from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.events.bus import Event, EventBus, EventType, get_event_bus

logger = logging.getLogger(__name__)


@dataclass
class MasterCommand:
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    command_type: str = ""
    target: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: str = "P1"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MasterController:
    """
    Master Control Plane for human oversight, intervention, and emergency overrides.
    """
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_event_bus()
        self._auth_pin: str = "0000"  # Default PIN for CLI authentication
        self._authenticated: bool = False
    
    def authenticate(self, pin: str) -> bool:
        if pin == self._auth_pin:
            self._authenticated = True
            logger.info("Master Control Plane authenticated.")
            return True
        logger.warning("Failed Master authentication attempt.")
        return False
    
    def is_authenticated(self) -> bool:
        return self._authenticated

    async def emit_command(self, command: MasterCommand) -> bool:
        if not self.is_authenticated():
            logger.error("Attempted to emit Master command without authentication.")
            return False

        event_type = EventType.MASTER_COMMAND_RECEIVED
        if command.command_type == "EMERGENCY_STOP":
            event_type = EventType.EMERGENCY_STOP_TRIGGERED

        event = Event(
            type=event_type,
            conversation_id=command.session_id,
            payload={
                "command_id": command.command_id,
                "command_type": command.command_type,
                "target": command.target,
                "payload": command.payload,
                "priority": command.priority
            },
            metadata={"master_identity": "human_operator"}
        )
        await self.event_bus.publish(event)
        logger.info(f"Master command emitted: {command.command_type} target={command.target}")
        return True


_instance: Optional[MasterController] = None


def get_master_controller() -> MasterController:
    global _instance
    if _instance is None:
        _instance = MasterController()
    return _instance
