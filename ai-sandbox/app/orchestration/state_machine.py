from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    GENERATING = "generating"
    SPEAKING = "speaking"
    OBSERVING = "observing"
    NEXT_TURN = "next_turn"
    PAUSED = "paused"
    PROCESS_HUMAN_INPUT = "process_human_input"
    GRACEFUL_SHUTDOWN = "graceful_shutdown"


class StateMachine:
    def __init__(self):
        self._state = ConversationState.IDLE
        self._previous_state: Optional[ConversationState] = None
        self._transition_handlers: Dict[ConversationState, List[Callable]] = {}
        self._allowed_transitions: Dict[ConversationState, Set[ConversationState]] = {
            ConversationState.IDLE: {ConversationState.THINKING, ConversationState.GRACEFUL_SHUTDOWN},
            ConversationState.THINKING: {ConversationState.GENERATING, ConversationState.PAUSED, ConversationState.GRACEFUL_SHUTDOWN},
            ConversationState.GENERATING: {ConversationState.SPEAKING, ConversationState.PAUSED, ConversationState.GRACEFUL_SHUTDOWN},
            ConversationState.SPEAKING: {ConversationState.OBSERVING, ConversationState.PAUSED, ConversationState.GRACEFUL_SHUTDOWN},
            ConversationState.OBSERVING: {ConversationState.NEXT_TURN, ConversationState.PAUSED, ConversationState.GRACEFUL_SHUTDOWN},
            ConversationState.NEXT_TURN: {ConversationState.THINKING, ConversationState.IDLE, ConversationState.PAUSED, ConversationState.GRACEFUL_SHUTDOWN},
            ConversationState.PAUSED: {ConversationState.PROCESS_HUMAN_INPUT, ConversationState.THINKING, ConversationState.GRACEFUL_SHUTDOWN},
            ConversationState.PROCESS_HUMAN_INPUT: {ConversationState.THINKING, ConversationState.IDLE, ConversationState.GRACEFUL_SHUTDOWN},
            ConversationState.GRACEFUL_SHUTDOWN: set(),
        }
        self._resume_state: Optional[ConversationState] = None
    
    @property
    def state(self) -> ConversationState:
        return self._state
    
    @property
    def previous_state(self) -> Optional[ConversationState]:
        return self._previous_state
    
    def can_transition(self, target_state: ConversationState) -> bool:
        return target_state in self._allowed_transitions.get(self._state, set())
    
    def transition(self, target_state: ConversationState) -> bool:
        if not self.can_transition(target_state):
            logger.warning(f"Invalid transition: {self._state} -> {target_state}")
            return False
        
        self._previous_state = self._state
        old_state = self._state
        self._state = target_state
        
        logger.info(f"State transition: {old_state} -> {target_state}")
        
        if target_state in self._transition_handlers:
            for handler in self._transition_handlers[target_state]:
                try:
                    handler(old_state, target_state)
                except Exception as e:
                    logger.error(f"Transition handler error: {e}")
        
        return True
    
    def on_transition(self, state: ConversationState, handler: Callable[[ConversationState, ConversationState], None]) -> None:
        if state not in self._transition_handlers:
            self._transition_handlers[state] = []
        self._transition_handlers[state].append(handler)
    
    def pause(self) -> bool:
        if self._state not in (ConversationState.PAUSED, ConversationState.GRACEFUL_SHUTDOWN):
            self._resume_state = self._state
            return self.transition(ConversationState.PAUSED)
        return False
    
    def resume(self) -> bool:
        if self._state == ConversationState.PAUSED and self._resume_state:
            target = self._resume_state
            self._resume_state = None
            return self.transition(target)
        elif self._state == ConversationState.PROCESS_HUMAN_INPUT:
            return self.transition(ConversationState.THINKING)
        return False
    
    def interrupt(self) -> bool:
        if self._state not in (ConversationState.PAUSED, ConversationState.GRACEFUL_SHUTDOWN):
            self._resume_state = self._state
            return self.transition(ConversationState.PROCESS_HUMAN_INPUT)
        return False
    
    def shutdown(self) -> bool:
        if self._state == ConversationState.GRACEFUL_SHUTDOWN:
            return True
        return self.transition(ConversationState.GRACEFUL_SHUTDOWN)
    
    def reset(self) -> None:
        self._state = ConversationState.IDLE
        self._previous_state = None
        self._resume_state = None


@dataclass
class TurnContext:
    conversation_id: str
    turn_number: int
    current_speaker: str
    next_speaker: str
    state: ConversationState