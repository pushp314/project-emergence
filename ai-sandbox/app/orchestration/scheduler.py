from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Iterator
import itertools
import logging

logger = logging.getLogger(__name__)


class TurnPolicy(ABC):
    @abstractmethod
    def get_next_speaker(self, current_speaker: str, agents: List[str]) -> str:
        pass
    
    @abstractmethod
    def reset(self) -> None:
        pass


class RoundRobinPolicy(TurnPolicy):
    def __init__(self, agents: List[str], initial_speaker: Optional[str] = None):
        self._agents = agents
        self._cycle = itertools.cycle(agents)
        if initial_speaker and initial_speaker in agents:
            while next(self._cycle) != initial_speaker:
                pass
    
    def get_next_speaker(self, current_speaker: str, agents: List[str]) -> str:
        return next(self._cycle)
    
    def reset(self) -> None:
        self._cycle = itertools.cycle(self._agents)


class AdaptivePolicy(TurnPolicy):
    def __init__(self, agents: List[str]):
        self._agents = agents
        self._turn_counts = {a: 0 for a in agents}
        self._last_speaker: Optional[str] = None
    
    def get_next_speaker(self, current_speaker: str, agents: List[str]) -> str:
        self._turn_counts[current_speaker] += 1
        self._last_speaker = current_speaker
        
        min_turns = min(self._turn_counts.values())
        candidates = [a for a, c in self._turn_counts.items() if c == min_turns]
        
        if len(candidates) == 1:
            return candidates[0]
        
        for agent in self._agents:
            if agent in candidates and agent != current_speaker:
                return agent
        
        return candidates[0]
    
    def reset(self) -> None:
        self._turn_counts = {a: 0 for a in self._agents}
        self._last_speaker = None


class Scheduler:
    def __init__(self, agents: List[str], policy: TurnPolicy):
        self._agents = agents
        self._policy = policy
        self._turn_number = 0
        self._current_speaker: Optional[str] = None
    
    @property
    def turn_number(self) -> int:
        return self._turn_number
    
    @property
    def current_speaker(self) -> Optional[str]:
        return self._current_speaker
    
    @property
    def agents(self) -> List[str]:
        return self._agents.copy()
    
    def start(self, initial_speaker: Optional[str] = None) -> str:
        self._turn_number = 1
        if initial_speaker and initial_speaker in self._agents:
            self._current_speaker = initial_speaker
        else:
            self._current_speaker = self._agents[0]
        return self._current_speaker
    
    def next_turn(self) -> str:
        if self._current_speaker is None:
            raise RuntimeError("Scheduler not started")
        
        self._turn_number += 1
        self._current_speaker = self._policy.get_next_speaker(self._current_speaker, self._agents)
        return self._current_speaker
    
    def get_next_speaker(self) -> str:
        if self._current_speaker is None:
            return self._agents[0]
        return self._policy.get_next_speaker(self._current_speaker, self._agents)
    
    def reset(self) -> None:
        self._turn_number = 0
        self._current_speaker = None
        self._policy.reset()


def create_scheduler(
    agents: List[str],
    policy_name: str = "round_robin",
    initial_speaker: Optional[str] = None
) -> Scheduler:
    if policy_name == "round_robin":
        policy = RoundRobinPolicy(agents, initial_speaker)
    elif policy_name == "adaptive":
        policy = AdaptivePolicy(agents)
    else:
        raise ValueError(f"Unknown policy: {policy_name}")
    
    return Scheduler(agents, policy)