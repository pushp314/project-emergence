from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
import logging

from app.events.bus import EventBus, Event, EventType, get_event_bus
from app.events.schemas import AgentMessage, ConversationState
from app.agents.base import BaseAgent, AgentContext
from app.orchestration.scheduler import Scheduler, create_scheduler
from app.orchestration.state_machine import StateMachine, ConversationState as SMState
from app.memory import MemoryManager, ContextManager

logger = logging.getLogger(__name__)


@dataclass
class ConversationConfig:
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    max_turns: int = 1000
    turn_timeout_seconds: int = 120
    short_term_turns: int = 8
    initial_speaker: str = "agent_a"
    scheduler_policy: str = "round_robin"


class ConversationEngine:
    def __init__(
        self,
        config: ConversationConfig,
        agents: Dict[str, BaseAgent],
        event_bus: Optional[EventBus] = None,
        context_manager: Optional[ContextManager] = None
    ):
        self.config = config
        self.agents = agents
        self.event_bus = event_bus or get_event_bus()
        self.context_manager = context_manager
        
        self.state_machine = StateMachine()
        self.scheduler = create_scheduler(
            agents=list(agents.keys()),
            policy_name=config.scheduler_policy,
            initial_speaker=config.initial_speaker
        )
        
        self._message_history: List[AgentMessage] = []
        self._running = False
        self._shutdown_requested = False
        self._turn_callbacks: List[Callable[[AgentMessage], None]] = []
        self._interrupt_callbacks: List[Callable[[], None]] = []
    
    @property
    def conversation_id(self) -> str:
        return self.config.conversation_id
    
    @property
    def turn_number(self) -> int:
        return self.scheduler.turn_number
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    def add_turn_callback(self, callback: Callable[[AgentMessage], None]) -> None:
        self._turn_callbacks.append(callback)
    
    def add_interrupt_callback(self, callback: Callable[[], None]) -> None:
        self._interrupt_callbacks.append(callback)
    
    async def start(self) -> None:
        if self._running:
            logger.warning("Conversation already running")
            return
        
        self._running = True
        self._shutdown_requested = False
        
        self.scheduler.start(self.config.initial_speaker)
        
        await self.event_bus.publish_type(
            EventType.CONVERSATION_TURN_START,
            self.conversation_id,
            {"turn_number": 1, "speaker": self.scheduler.current_speaker}
        )
        
        await self._run_conversation()
    
    async def stop(self) -> None:
        self._shutdown_requested = True
        self.state_machine.shutdown()
        self._running = False
        logger.info("Conversation stopped")
    
    async def pause(self) -> None:
        self.state_machine.pause()
        await self.event_bus.publish_type(
            EventType.SYSTEM_PAUSE,
            self.conversation_id,
            {"turn_number": self.turn_number}
        )
    
    async def resume(self) -> None:
        self.state_machine.resume()
        await self.event_bus.publish_type(
            EventType.SYSTEM_RESUME,
            self.conversation_id,
            {"turn_number": self.turn_number}
        )
    
    async def interrupt(self) -> None:
        self.state_machine.interrupt()
        for callback in self._interrupt_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Interrupt callback error: {e}")
        
        await self.event_bus.publish_type(
            EventType.HUMAN_INTERRUPT,
            self.conversation_id,
            {"turn_number": self.turn_number}
        )
    
    async def inject_human_message(self, content: str) -> None:
        message = AgentMessage(
            agent_id="human",
            agent_identity="human",
            content=content,
            turn_number=self.turn_number
        )
        self._message_history.append(message)
        await self.event_bus.publish_type(
            EventType.HUMAN_MESSAGE,
            self.conversation_id,
            {"content": content, "turn_number": self.turn_number}
        )
    
    async def _run_conversation(self) -> None:
        try:
            while self._running and not self._shutdown_requested:
                if self.turn_number > self.config.max_turns:
                    logger.info(f"Max turns ({self.config.max_turns}) reached")
                    break
                
                if self.state_machine.state == SMState.GRACEFUL_SHUTDOWN:
                    break
                
                if self.state_machine.state == SMState.PAUSED:
                    await asyncio.sleep(0.5)
                    continue
                
                await self._process_turn()
                
                # Check for shutdown after each turn completes
                if self._shutdown_requested or self.state_machine.state == SMState.GRACEFUL_SHUTDOWN:
                    break
                
        except asyncio.CancelledError:
            logger.info("Conversation cancelled")
        except Exception as e:
            logger.error(f"Conversation error: {e}")
            await self.event_bus.publish_type(
                EventType.AGENT_ERROR,
                self.conversation_id,
                {"error": str(e), "turn_number": self.turn_number}
            )
        finally:
            self._running = False
            await self.event_bus.publish_type(
                EventType.SYSTEM_STOP,
                self.conversation_id,
                {"turn_number": self.turn_number}
            )
    
    async def _process_turn(self) -> None:
        # Check for shutdown before starting turn
        if self._shutdown_requested or self.state_machine.state == SMState.GRACEFUL_SHUTDOWN:
            return
            
        speaker_id = self.scheduler.current_speaker
        agent = self.agents.get(speaker_id)
        
        if not agent:
            logger.error(f"Agent {speaker_id} not found")
            self.scheduler.next_turn()
            return
        
        self.state_machine.transition(SMState.THINKING)
        
        # Check for shutdown after state transition
        if self._shutdown_requested or self.state_machine.state == SMState.GRACEFUL_SHUTDOWN:
            return
        
        context = self._build_context(speaker_id)
        
        self.state_machine.transition(SMState.GENERATING)
        
        # Check for shutdown before generation
        if self._shutdown_requested or self.state_machine.state == SMState.GRACEFUL_SHUTDOWN:
            return
        
        try:
            response = await asyncio.wait_for(
                agent.think(context),
                timeout=self.config.turn_timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.warning(f"Agent {speaker_id} timed out")
            response = f"[Agent {speaker_id} timed out after {self.config.turn_timeout_seconds}s]"
        except Exception as e:
            logger.error(f"Agent {speaker_id} error: {e}")
            response = f"[Agent {speaker_id} error: {e}]"
        
        # Check for shutdown after generation
        if self._shutdown_requested or self.state_machine.state == SMState.GRACEFUL_SHUTDOWN:
            return
        
        self.state_machine.transition(SMState.SPEAKING)
        
        message = AgentMessage(
            agent_id=speaker_id,
            agent_identity=agent.config.agent_identity,
            content=response,
            turn_number=self.turn_number
        )
        self._message_history.append(message)
        
        await agent.emit_message(self.conversation_id, response, self.turn_number)
        
        if self.context_manager:
            await self.context_manager.update_from_message(message, self.turn_number)
        
        for callback in self._turn_callbacks:
            try:
                callback(message)
            except Exception as e:
                logger.error(f"Turn callback error: {e}")
        
        await self.event_bus.publish_type(
            EventType.CONVERSATION_TURN_END,
            self.conversation_id,
            {
                "turn_number": self.turn_number,
                "speaker": speaker_id,
                "content": response
            }
        )
        
        # Check for shutdown before observer
        if self._shutdown_requested or self.state_machine.state == SMState.GRACEFUL_SHUTDOWN:
            return
        
        self.state_machine.transition(SMState.OBSERVING)
        
        await self._maybe_trigger_observer()
        
        # Summarization is now handled by ContextManager internally within update_from_message
        
        # Check for shutdown before next turn
        if self._shutdown_requested or self.state_machine.state == SMState.GRACEFUL_SHUTDOWN:
            return
        
        self.state_machine.transition(SMState.NEXT_TURN)
        
        self.scheduler.next_turn()
        
        await self.event_bus.publish_type(
            EventType.CONVERSATION_TURN_START,
            self.conversation_id,
            {"turn_number": self.turn_number + 1, "speaker": self.scheduler.current_speaker}
        )
    
    def _build_context(self, speaker_id: str) -> AgentContext:
        recent = self._message_history[-self.config.short_term_turns:] if self._message_history else []
        
        memory_summary = ""
        if self.context_manager:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    context_data = asyncio.run_coroutine_threadsafe(
                        self.context_manager.get_context_for_llm(),
                        loop
                    ).result(timeout=5)
                    memory_summary = context_data.get("summary", "")
            except Exception as e:
                logger.debug(f"Could not fetch memory context: {e}")
        
        return AgentContext(
            conversation_id=self.conversation_id,
            turn_number=self.turn_number,
            recent_messages=recent,
            memory_summary=memory_summary,
            available_tools=[],
            pending_permissions=[]
        )
    
    async def _maybe_trigger_observer(self) -> None:
        observer = self.agents.get("agent_c")
        if not observer or not isinstance(observer, BaseAgent):
            return
        
        if self.turn_number % 10 == 0:
            context = self._build_context("agent_c")
            should_intervene, reason = observer.evaluate_intervention(context)
            
            if should_intervene:
                response = await observer.think(context)
                if response.strip():
                    await observer.emit_message(
                        self.conversation_id,
                        f"[OBSERVER INTERVENTION: {reason}]\n{response}",
                        self.turn_number,
                        {"intervention": True, "reason": reason}
                    )
    
    def get_history(self, limit: Optional[int] = None) -> List[AgentMessage]:
        if limit:
            return self._message_history[-limit:]
        return self._message_history.copy()
    
    def get_state(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "turn_number": self.turn_number,
            "state": self.state_machine.state.value,
            "current_speaker": self.scheduler.current_speaker,
            "next_speaker": self.scheduler.get_next_speaker(),
            "running": self._running,
            "message_count": len(self._message_history)
        }