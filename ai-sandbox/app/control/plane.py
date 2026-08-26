from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from app.events.bus import EventBus, Event, EventType, get_event_bus

logger = logging.getLogger(__name__)


class SystemStatus(str, Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    EMERGENCY_STOP = "emergency_stop"


class InterventionLevel(str, Enum):
    NONE = "none"
    ADVISORY = "advisory"
    OVERRIDE = "override"
    EMERGENCY = "emergency"


@dataclass
class Command:
    command_id: str = ""
    target_agent: str = ""
    action: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "human"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    requires_auth: bool = True


@dataclass
class SystemState:
    status: SystemStatus = SystemStatus.RUNNING
    intervention_level: InterventionLevel = InterventionLevel.NONE
    active_agents: List[str] = field(default_factory=list)
    paused_agents: List[str] = field(default_factory=list)
    commands_sent: int = 0
    interventions: int = 0
    uptime_seconds: float = 0.0
    last_command: Optional[Command] = None


class MasterControlPlane:
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_event_bus()
        self._state = SystemState()
        self._state.started_at = datetime.utcnow()
        self._command_handlers: Dict[str, Callable] = {}
        self._intervention_handlers: List[Callable] = []
        self._lock = asyncio.Lock()
        self._command_history: List[Command] = []
        self._max_history = 1000

    async def emergency_stop(self) -> SystemState:
        async with self._lock:
            self._state.status = SystemStatus.EMERGENCY_STOP
            self._state.paused_agents = list(self._state.active_agents)
            self._state.intervention_level = InterventionLevel.EMERGENCY

        await self.event_bus.publish_type(
            EventType.SYSTEM_STOP,
            "",
            {
                "reason": "emergency_stop",
                "agents_affected": self._state.active_agents,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        logger.critical("EMERGENCY STOP activated - all agents halted")
        return self._state

    async def pause_all(self) -> SystemState:
        async with self._lock:
            if self._state.status == SystemStatus.STOPPED:
                return self._state
            self._state.status = SystemStatus.PAUSED
            self._state.paused_agents = list(self._state.active_agents)

        await self.event_bus.publish_type(
            EventType.SYSTEM_PAUSE,
            "",
            {"agents_paused": self._state.paused_agents},
        )
        logger.info("All agents paused")
        return self._state

    async def resume_all(self) -> SystemState:
        async with self._lock:
            self._state.status = SystemStatus.RUNNING
            self._state.paused_agents.clear()
            self._state.intervention_level = InterventionLevel.NONE

        await self.event_bus.publish_type(
            EventType.SYSTEM_RESUME,
            "",
            {"timestamp": datetime.utcnow().isoformat()},
        )
        logger.info("All agents resumed")
        return self._state

    async def get_system_status(self) -> SystemState:
        if hasattr(self._state, "started_at"):
            delta = (datetime.utcnow() - self._state.started_at).total_seconds()
            self._state.uptime_seconds = delta
        return self._state

    async def register_agent(self, agent_id: str) -> None:
        async with self._lock:
            if agent_id not in self._state.active_agents:
                self._state.active_agents.append(agent_id)
        logger.info(f"Agent registered: {agent_id}")

    async def unregister_agent(self, agent_id: str) -> None:
        async with self._lock:
            if agent_id in self._state.active_agents:
                self._state.active_agents.remove(agent_id)
            if agent_id in self._state.paused_agents:
                self._state.paused_agents.remove(agent_id)
        logger.info(f"Agent unregistered: {agent_id}")

    async def send_command(self, command: Command) -> Dict[str, Any]:
        if self._state.status == SystemStatus.EMERGENCY_STOP:
            return {"success": False, "error": "System in emergency stop"}

        if self._state.status == SystemStatus.PAUSED and command.action != "resume":
            return {"success": False, "error": "System is paused"}

        async with self._lock:
            self._command_history.append(command)
            if len(self._command_history) > self._max_history:
                self._command_history = self._command_history[-self._max_history:]
            self._state.commands_sent += 1
            self._state.last_command = command

        handler = self._command_handlers.get(command.action)
        if handler:
            try:
                result = await handler(command)
                return {"success": True, "result": result}
            except Exception as e:
                logger.error(f"Command handler error: {e}")
                return {"success": False, "error": str(e)}

        await self.event_bus.publish_type(
            EventType.AGENT_MESSAGE,
            "",
            {
                "agent_id": command.target_agent,
                "content": f"Command: {command.action}",
                "command": command.__dict__,
            },
        )
        return {"success": True, "dispatched": True}

    def register_command_handler(self, action: str, handler: Callable) -> None:
        self._command_handlers[action] = handler

    async def human_intervention(
        self,
        level: InterventionLevel,
        reason: str,
        target_agent: Optional[str] = None,
    ) -> SystemState:
        async with self._lock:
            self._state.intervention_level = level
            self._state.interventions += 1

        await self.event_bus.publish_type(
            EventType.OBSERVER_INTERVENTION,
            "",
            {
                "level": level.value,
                "reason": reason,
                "target_agent": target_agent,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        if level == InterventionLevel.EMERGENCY:
            await self.emergency_stop()
        elif level == InterventionLevel.OVERRIDE:
            await self.pause_all()

        for handler in self._intervention_handlers:
            try:
                await handler(level, reason, target_agent)
            except Exception as e:
                logger.error(f"Intervention handler error: {e}")

        logger.warning(f"Human intervention [{level.value}]: {reason}")
        return self._state

    def register_intervention_handler(self, handler: Callable) -> None:
        self._intervention_handlers.append(handler)

    def get_command_history(self, limit: int = 50) -> List[Command]:
        return self._command_history[-limit:]


_control_plane: Optional[MasterControlPlane] = None


def get_control_plane() -> MasterControlPlane:
    global _control_plane
    if _control_plane is None:
        _control_plane = MasterControlPlane()
    return _control_plane


def set_control_plane(plane: MasterControlPlane) -> None:
    global _control_plane
    _control_plane = plane
