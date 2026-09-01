from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable

from app.events.bus import EventBus, Event, EventType, get_event_bus
from app.events.schemas import PermissionRequest, PermissionDecision, PermissionLevel, RiskLevel

logger = logging.getLogger(__name__)


class PermissionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


@dataclass
class PendingPermission:
    request: PermissionRequest
    status: PermissionStatus = PermissionStatus.PENDING
    decided_by: Optional[str] = None
    decided_at: Optional[str] = None
    future: Optional[asyncio.Future] = None


class PermissionManager:
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        timeout_seconds: int = 30,
        auto_approve_low_risk: bool = False
    ):
        self.event_bus = event_bus or get_event_bus()
        self.timeout_seconds = timeout_seconds
        self.auto_approve_low_risk = auto_approve_low_risk
        self._pending: Dict[str, PendingPermission] = {}
        self._history: List[PermissionRequest] = []
        self._approval_callback: Optional[Callable[[PermissionRequest], Awaitable[bool]]] = None
    
    def set_approval_callback(self, callback: Callable[[PermissionRequest], Awaitable[bool]]) -> None:
        self._approval_callback = callback
    
    async def request_permission(
        self,
        agent_id: str,
        action: str,
        command: str,
        reason: str,
        risk: RiskLevel = RiskLevel.MEDIUM,
        scope: PermissionLevel = PermissionLevel.READ,
        duration: str = "once",
        timeout: Optional[int] = None
    ) -> bool:
        request = PermissionRequest(
            agent_id=agent_id,
            action=action,
            command=command,
            reason=reason,
            risk=risk,
            scope=scope,
            duration=duration
        )
        
        if self.auto_approve_low_risk and risk == RiskLevel.LOW:
            return await self._auto_approve(request)
        
        pending = PendingPermission(request=request)
        pending.future = asyncio.get_event_loop().create_future()
        self._pending[request.request_id] = pending
        
        await self.event_bus.publish_type(
            EventType.PERMISSION_REQUEST,
            agent_id,
            {
                "request_id": request.request_id,
                "agent_id": agent_id,
                "action": action,
                "command": command,
                "reason": reason,
                "risk": risk.value,
                "scope": scope.value,
                "duration": duration
            }
        )
        
        try:
            result = await asyncio.wait_for(pending.future, timeout=timeout or self.timeout_seconds)
            return result
        except asyncio.TimeoutError:
            pending.status = PermissionStatus.EXPIRED
            await self.event_bus.publish_type(
                EventType.PERMISSION_DENIED,
                agent_id,
                {"request_id": request.request_id, "reason": "Timeout"}
            )
            return False
        finally:
            self._history.append(request)
            self._pending.pop(request.request_id, None)
    
    async def _auto_approve(self, request: PermissionRequest) -> bool:
        request.status = "approved"
        await self.event_bus.publish_type(
            EventType.PERMISSION_APPROVED,
            request.agent_id,
            {"request_id": request.request_id, "auto_approved": True}
        )
        self._history.append(request)
        return True
    
    async def approve(self, request_id: str, decided_by: str = "human") -> bool:
        pending = self._pending.get(request_id)
        if not pending:
            return False
        
        pending.status = PermissionStatus.APPROVED
        pending.decided_by = decided_by
        pending.decided_at = datetime.now(timezone.utc).isoformat()
        
        if pending.future and not pending.future.done():
            pending.future.set_result(True)
        
        await self.event_bus.publish_type(
            EventType.PERMISSION_APPROVED,
            pending.request.agent_id,
            {"request_id": request_id, "decided_by": decided_by}
        )
        
        return True
    
    async def deny(self, request_id: str, decided_by: str = "human", reason: str = "") -> bool:
        pending = self._pending.get(request_id)
        if not pending:
            return False
        
        pending.status = PermissionStatus.DENIED
        pending.decided_by = decided_by
        pending.decided_at = datetime.now(timezone.utc).isoformat()
        
        if pending.future and not pending.future.done():
            pending.future.set_result(False)
        
        await self.event_bus.publish_type(
            EventType.PERMISSION_DENIED,
            pending.request.agent_id,
            {"request_id": request_id, "decided_by": decided_by, "reason": reason}
        )
        
        return True
    
    def get_pending(self) -> List[PendingPermission]:
        return list(self._pending.values())
    
    def get_history(self, limit: int = 100) -> List[PermissionRequest]:
        return self._history[-limit:]
    
    def get_pending_for_agent(self, agent_id: str) -> List[PendingPermission]:
        return [p for p in self._pending.values() if p.request.agent_id == agent_id]


_permission_manager: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager()
    return _permission_manager


def set_permission_manager(manager: PermissionManager) -> None:
    global _permission_manager
    _permission_manager = manager