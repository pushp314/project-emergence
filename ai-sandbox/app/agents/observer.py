from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json
import logging

from app.agents.base import BaseAgent, AgentContext, AgentConfig
from app.events.bus import EventBus, Event, EventType, get_event_bus
from app.models.base import ModelAdapter, GenerationRequest, get_model_registry

logger = logging.getLogger(__name__)


@dataclass
class ObserverState:
    current_topic: str = ""
    important_discoveries: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    repetition_score: float = 0.0
    conversation_health: float = 1.0
    last_intervention_turn: int = 0


OBSERVER_ANALYSIS_PROMPT = """You are the Observer analyzing a conversation between two autonomous AI agents.

Current conversation state:
- Topic: {topic}
- Turn: {turn_number}
- Recent messages: {recent_messages}

Your task: Analyze and update the observer state. Respond ONLY with JSON:
{{
    "current_topic": "string",
    "important_discoveries": ["string"],
    "contradictions": ["string"],
    "open_questions": ["string"],
    "repetition_score": 0.0,
    "conversation_health": 1.0,
    "should_intervene": false,
    "intervention_reason": "",
    "intervention_content": ""
}}

Intervention criteria (should_intervene = true):
- Repetition score > 0.7
- Important new insight discovered
- Direct contradiction between agents
- Conversation health < 0.3 (directionless)
- Useful new direction emerges
- Human input needs interpretation

Repetition indicators: same phrases, circular arguments, re-stating same points
Contradiction indicators: "I agree" followed by opposing view, factual conflicts
Health indicators: engagement, novelty, progress, depth"""


OBSERVER_INTERVENTION_PROMPT = """You are the Observer intervening in an autonomous AI conversation.

Reason for intervention: {reason}
Current topic: {topic}
Analysis: {analysis}

Provide a concise observational intervention (2-3 sentences max). Do not participate in the discussion - only observe and guide."""


class ObserverAgent(BaseAgent):
    def __init__(
        self,
        agent_id: str,
        config: AgentConfig,
        event_bus: Optional[EventBus] = None,
        model_adapter: Optional[ModelAdapter] = None
    ):
        super().__init__(agent_id, config, event_bus, model_adapter)
        self.state = ObserverState()
        self._last_analyzed_turn = 0
        self._message_buffer: List[str] = []
    
    async def analyze_conversation(self, context: AgentContext) -> None:
        if not context.recent_messages:
            return
        
        recent_text = "\n".join([f"[{m.agent_identity}] {m.content}" for m in context.recent_messages[-6:]])
        
        request = GenerationRequest(
            prompt=OBSERVER_ANALYSIS_PROMPT.format(
                topic=self.state.current_topic or "Unknown",
                turn_number=context.turn_number,
                recent_messages=recent_text
            ),
            max_tokens=512,
            temperature=0.3,
            stream=False
        )
        
        try:
            response = await self.model.generate(request)
            result = json.loads(response.text)
            
            self.state.current_topic = result.get("current_topic", self.state.current_topic)
            self.state.important_discoveries = result.get("important_discoveries", self.state.important_discoveries)
            self.state.contradictions = result.get("contradictions", self.state.contradictions)
            self.state.open_questions = result.get("open_questions", self.state.open_questions)
            self.state.repetition_score = float(result.get("repetition_score", self.state.repetition_score))
            self.state.conversation_health = float(result.get("conversation_health", self.state.conversation_health))
            
            should_intervene = result.get("should_intervene", False)
            intervention_reason = result.get("intervention_reason", "")
            intervention_content = result.get("intervention_content", "")
            
            if should_intervene and intervention_content:
                await self._emit_intervention(intervention_reason, intervention_content, context.conversation_id, context.turn_number)
            
        except json.JSONDecodeError:
            logger.warning("Observer analysis: failed to parse JSON, using fallback analysis")
            # Fallback: simple heuristic analysis
            await self._fallback_analysis(context)
        except Exception as e:
            logger.error(f"Observer analysis error: {e}")
        finally:
            # Always update last analyzed turn to prevent repeated analysis attempts
            self._last_analyzed_turn = context.turn_number
    
    async def _fallback_analysis(self, context: AgentContext) -> None:
        """Fallback analysis when JSON parsing fails."""
        # Simple heuristic analysis based on message content
        recent_messages = context.recent_messages[-6:] if context.recent_messages else []
        
        # Check for repetition (similar content)
        contents = [m.content.lower() for m in recent_messages]
        repetition_score = 0.0
        if len(contents) >= 2:
            # Simple similarity check
            for i in range(len(contents) - 1):
                if contents[i] == contents[i + 1]:
                    repetition_score += 0.3
        
        # Check for contradictions (simple keyword detection)
        contradictions = []
        for msg in recent_messages:
            content_lower = msg.content.lower()
            if ("but" in content_lower or "however" in content_lower or 
                "disagree" in content_lower or "wrong" in content_lower):
                contradictions.append(msg.content[:100])
        
        # Check for questions
        open_questions = []
        for msg in recent_messages:
            if "?" in msg.content:
                open_questions.append(msg.content[:100])
        
        # Update state
        self.state.repetition_score = min(repetition_score, 1.0)
        self.state.contradictions = contradictions
        self.state.open_questions = open_questions
        self.state.conversation_health = max(0.3, 1.0 - repetition_score)
        
        # Determine if intervention needed
        should_intervene = False
        intervention_reason = ""
        
        if self.state.repetition_score > 0.7:
            should_intervene = True
            intervention_reason = f"High repetition detected (score: {self.state.repetition_score:.2f})"
        elif self.state.conversation_health < 0.3:
            should_intervene = True
            intervention_reason = f"Low conversation health (score: {self.state.conversation_health:.2f})"
        elif self.state.contradictions:
            should_intervene = True
            intervention_reason = f"Contradictions detected: {len(self.state.contradictions)}"
        
        if should_intervene:
            await self._emit_intervention(intervention_reason, "", context.conversation_id, context.turn_number)

    async def _emit_intervention(self, reason: str, content: str, conversation_id: str, turn_number: int) -> None:
        intervention_text = f"[OBSERVER INTERVENTION: {reason}]\n{content}"
        
        await self.emit_message(
            conversation_id,
            intervention_text,
            turn_number,
            {"intervention": True, "reason": reason}
        )
        
        await self.event_bus.publish_type(
            EventType.OBSERVER_INTERVENTION,
            conversation_id,
            {
                "reason": reason,
                "content": content,
                "topic": self.state.current_topic,
                "turn_number": turn_number
            }
        )
        
        logger.info(f"Observer intervened: {reason}")
        self.state.last_intervention_turn = turn_number
    
    def evaluate_intervention(self, context: AgentContext) -> tuple[bool, str]:
        if context.turn_number - self._last_analyzed_turn >= 5:
            return True, "Periodic analysis"
        
        if self.state.repetition_score > 0.7:
            return True, f"High repetition detected (score: {self.state.repetition_score:.2f})"
        
        if self.state.conversation_health < 0.3:
            return True, f"Low conversation health (score: {self.state.conversation_health:.2f})"
        
        if self.state.contradictions:
            return True, f"Contradictions detected: {len(self.state.contradictions)}"
        
        return False, ""
    
    async def think(self, context: AgentContext) -> str:
        await self.analyze_conversation(context)
        
        should_intervene, reason = self.evaluate_intervention(context)
        if should_intervene:
            request = GenerationRequest(
                prompt=OBSERVER_INTERVENTION_PROMPT.format(
                    reason=reason,
                    topic=self.state.current_topic or "Unknown",
                    analysis=f"Repetition: {self.state.repetition_score:.2f}, Health: {self.state.conversation_health:.2f}, Contradictions: {len(self.state.contradictions)}, Questions: {len(self.state.open_questions)}"
                ),
                max_tokens=256,
                temperature=0.5,
                stream=False
            )
            
            try:
                response = await self.model.generate(request)
                return response.text.strip()
            except Exception as e:
                logger.error(f"Observer intervention generation failed: {e}")
        
        return ""
    
    def get_state(self) -> ObserverState:
        return self.state


def create_observer_agent(
    agent_id: str = "agent_c",
    model: str = "hf.co/nbpedro315/Dolphin3-Cyber-8B-GGUF:Q4_K_M",
    temperature: float = 0.5,
    max_tokens: int = 512
) -> ObserverAgent:
    config = AgentConfig(
        agent_identity="observer",
        name="Observer",
        system_prompt="""You are an autonomous AI observer designed for conversation analysis and intervention.

You maintain:
- Current topic
- Important discoveries
- Contradictions
- Open questions
- Repetition score
- Conversation health

You normally remain SILENT and watch the conversation.

You ONLY intervene (speak) when:
- Conversation becomes repetitive
- An important insight appears
- Agents contradict themselves
- Discussion becomes directionless
- A useful new direction emerges
- Human intervention needs interpretation

When you do speak, emit an observer_intervention event with your analysis.

Your responses should be concise analytical observations, not participation in the discussion.""",
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return ObserverAgent(agent_id, config)