from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Awaitable

from app.events.bus import EventBus, Event, EventType, get_event_bus

logger = logging.getLogger(__name__)


class A2AMessageType(str, Enum):
    TASK_REQUEST = "task/request"
    TASK_RESPONSE = "task/response"
    TASK_CANCEL = "task/cancel"
    TASK_STATUS = "task/status"
    AGENT_CARD = "agent/card"
    AGENT_DISCOVERY = "agent/discovery"
    MESSAGE_SEND = "message/send"
    MESSAGE_RECEIVE = "message/receive"
    STREAM_CHUNK = "stream/chunk"
    STREAM_END = "stream/end"


@dataclass
class A2AMessage:
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: A2AMessageType = A2AMessageType.MESSAGE_SEND
    sender_id: str = ""
    recipient_id: str = ""
    conversation_id: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_json(self) -> str:
        return json.dumps({
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "conversation_id": self.conversation_id,
            "payload": self.payload,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        })
    
    @classmethod
    def from_json(cls, data: str) -> A2AMessage:
        d = json.loads(data)
        return cls(
            message_id=d.get("message_id", str(uuid.uuid4())),
            message_type=A2AMessageType(d["message_type"]),
            sender_id=d.get("sender_id", ""),
            recipient_id=d.get("recipient_id", ""),
            conversation_id=d.get("conversation_id", ""),
            payload=d.get("payload", {}),
            metadata=d.get("metadata", {}),
            timestamp=d.get("timestamp", datetime.utcnow().isoformat())
        )


@dataclass
class AgentCard:
    agent_id: str
    name: str
    description: str
    version: str = "1.0.0"
    capabilities: List[str] = field(default_factory=list)
    supported_message_types: List[A2AMessageType] = field(default_factory=list)
    endpoint: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class A2AProtocol:
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        agent_card: Optional[AgentCard] = None
    ):
        self.event_bus = event_bus or get_event_bus()
        self.agent_card = agent_card
        self._peers: Dict[str, AgentCard] = {}
        self._message_handlers: Dict[A2AMessageType, List[Callable[[A2AMessage], Awaitable[None]]]] = {}
        self._conversations: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._server_task: Optional[asyncio.Task] = None
    
    def register_handler(self, msg_type: A2AMessageType, handler: Callable[[A2AMessage], Awaitable[None]]) -> None:
        if msg_type not in self._message_handlers:
            self._message_handlers[msg_type] = []
        self._message_handlers[msg_type].append(handler)
    
    def register_peer(self, peer: AgentCard) -> None:
        self._peers[peer.agent_id] = peer
        logger.info(f"Registered A2A peer: {peer.agent_id} ({peer.name})")
    
    def get_peer(self, agent_id: str) -> Optional[AgentCard]:
        return self._peers.get(agent_id)
    
    def list_peers(self) -> List[AgentCard]:
        return list(self._peers.values())
    
    async def send_message(self, message: A2AMessage) -> None:
        await self.event_bus.publish_type(
            EventType.AGENT_MESSAGE,
            message.conversation_id,
            {
                "agent_id": message.sender_id,
                "role": "a2a",
                "content": json.dumps({
                    "a2a_message": message.to_json()
                }),
                "turn_number": 0
            }
        )
        
        handlers = self._message_handlers.get(message.message_type, [])
        for handler in handlers:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"A2A handler error: {e}")
    
    async def send_task_request(
        self,
        sender_id: str,
        recipient_id: str,
        task_type: str,
        parameters: Dict[str, Any],
        conversation_id: Optional[str] = None
    ) -> str:
        conv_id = conversation_id or str(uuid.uuid4())
        
        message = A2AMessage(
            message_type=A2AMessageType.TASK_REQUEST,
            sender_id=sender_id,
            recipient_id=recipient_id,
            conversation_id=conv_id,
            payload={
                "task_type": task_type,
                "parameters": parameters
            }
        )
        
        self._conversations[conv_id] = {
            "task_type": task_type,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        await self.send_message(message)
        return conv_id
    
    async def send_task_response(
        self,
        sender_id: str,
        recipient_id: str,
        conversation_id: str,
        result: Any,
        success: bool = True
    ) -> None:
        message = A2AMessage(
            message_type=A2AMessageType.TASK_RESPONSE,
            sender_id=sender_id,
            recipient_id=recipient_id,
            conversation_id=conversation_id,
            payload={
                "result": result,
                "success": success
            }
        )
        
        if conversation_id in self._conversations:
            self._conversations[conversation_id]["status"] = "completed" if success else "failed"
            self._conversations[conversation_id]["result"] = result
            self._conversations[conversation_id]["completed_at"] = datetime.utcnow().isoformat()
        
        await self.send_message(message)
    
    async def broadcast_agent_card(self) -> None:
        if not self.agent_card:
            return
        
        for peer_id in self._peers:
            message = A2AMessage(
                message_type=A2AMessageType.AGENT_CARD,
                sender_id=self.agent_card.agent_id,
                recipient_id=peer_id,
                conversation_id="discovery",
                payload=self.agent_card.__dict__
            )
            await self.send_message(message)
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return self._conversations.get(conversation_id)
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        return [{"conversation_id": k, **v} for k, v in self._conversations.items()]


_a2a_protocol: Optional[A2AProtocol] = None


def get_a2a_protocol() -> A2AProtocol:
    global _a2a_protocol
    if _a2a_protocol is None:
        _a2a_protocol = A2AProtocol()
    return _a2a_protocol


def set_a2a_protocol(protocol: A2AProtocol) -> None:
    global _a2a_protocol
    _a2a_protocol = protocol