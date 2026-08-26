from __future__ import annotations

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Awaitable
import json

from app.events.bus import EventBus, Event, EventType, get_event_bus
from app.events.schemas import ToolDefinition, ToolCall, ToolResult, PermissionLevel, RiskLevel

logger = logging.getLogger(__name__)


class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        pass
    
    @property
    @abstractmethod
    def permission(self) -> PermissionLevel:
        pass
    
    @property
    @abstractmethod
    def risk(self) -> RiskLevel:
        pass
    
    @property
    @abstractmethod
    def enabled(self) -> bool:
        pass
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        pass
    
    def to_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            permission=self.permission,
            risk=self.risk,
            enabled=self.enabled
        )


class ToolGateway:
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_event_bus()
        self._tools: Dict[str, Tool] = {}
        self._permission_checker: Optional[Callable[[str, PermissionLevel, RiskLevel], Awaitable[bool]]] = None
    
    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)
    
    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)
    
    def list_tools(self) -> List[ToolDefinition]:
        return [tool.to_definition() for tool in self._tools.values() if tool.enabled]
    
    def set_permission_checker(self, checker: Callable[[str, PermissionLevel, RiskLevel], Awaitable[bool]]) -> None:
        self._permission_checker = checker
    
    async def execute(self, call: ToolCall) -> ToolResult:
        tool = self._tools.get(call.tool_name)
        
        if not tool:
            return ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                success=False,
                error=f"Tool '{call.tool_name}' not found"
            )
        
        if not tool.enabled:
            return ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                success=False,
                error=f"Tool '{call.tool_name}' is disabled"
            )
        
        if self._permission_checker:
            allowed = await self._permission_checker(call.agent_id, tool.permission, tool.risk)
            if not allowed:
                return ToolResult(
                    call_id=call.call_id,
                    tool_name=call.tool_name,
                    success=False,
                    error=f"Permission denied for tool '{call.tool_name}' (requires {tool.permission.value}, risk: {tool.risk.value})"
                )
        
        await self.event_bus.publish_type(
            EventType.TOOL_STARTED,
            call.agent_id,
            {"call_id": call.call_id, "tool_name": call.tool_name, "arguments": call.arguments}
        )
        
        try:
            result = await tool.execute(call.arguments)
            
            tool_result = ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                success=True,
                result=result
            )
            
            await self.event_bus.publish_type(
                EventType.TOOL_COMPLETED,
                call.agent_id,
                {"call_id": call.call_id, "tool_name": call.tool_name, "result": result}
            )
            
            return tool_result
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            tool_result = ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                success=False,
                error=str(e)
            )
            
            await self.event_bus.publish_type(
                EventType.TOOL_FAILED,
                call.agent_id,
                {"call_id": call.call_id, "tool_name": call.tool_name, "error": str(e)}
            )
            
            return tool_result


_tool_gateway: Optional[ToolGateway] = None


def get_tool_gateway() -> ToolGateway:
    global _tool_gateway
    if _tool_gateway is None:
        _tool_gateway = ToolGateway()
    return _tool_gateway


def set_tool_gateway(gateway: ToolGateway) -> None:
    global _tool_gateway
    _tool_gateway = gateway