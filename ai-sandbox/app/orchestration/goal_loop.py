import logging
import asyncio
import json
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from app.events.bus import EventBus, EventType, get_event_bus
from app.models.base import get_model_registry, GenerationRequest

logger = logging.getLogger(__name__)

class GoalState(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    ACTING = "acting"
    CRITIQUING = "critiquing"
    DONE = "done"
    FAILED = "failed"


@dataclass
class GoalContext:
    objective: str
    plan: List[str] = field(default_factory=list)
    current_step: int = 0
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    critique_history: List[str] = field(default_factory=list)
    is_satisfied: bool = False
    retry_count: int = 0


class GoalEngine:
    def __init__(self, conversation_engine=None, max_iterations: int = 5, max_retries: int = 3):
        self.state = GoalState.IDLE
        self.max_iterations = max_iterations
        self.max_retries = max_retries
        self.current_iteration = 0
        self.context: Optional[GoalContext] = None
        self.conversation_engine = conversation_engine
        self.event_bus = get_event_bus()
        self._running = False
        self._step_completed_event = asyncio.Event()
        self.event_bus.subscribe(EventType.TOOL_REQUEST, self._on_tool_request)
        self.event_bus.subscribe(EventType.MASTER_COMMAND_RECEIVED, self._on_master_command)

    async def _on_master_command(self, event) -> None:
        command_type = event.payload.get("command_type")
        if command_type == "SET_OBJECTIVE":
            payload = event.payload.get("payload", {})
            objective = payload.get("objective", "")
            if objective:
                self.start_goal(objective)

    async def _on_tool_request(self, event) -> None:
        if event.payload.get("tool_name") == "submit_task_result":
            # The manager agent submitted a result.
            arguments = event.payload.get("arguments", {})
            if self.context:
                self.context.actions_taken.append({
                    "step": self.context.current_step,
                    "result": arguments.get("result", "")
                })
            self._step_completed_event.set()

    def start_goal(self, objective: str) -> None:
        self.context = GoalContext(objective=objective)
        self.state = GoalState.PLANNING
        self.current_iteration = 0
        logger.info(f"Goal started: {objective}")

    async def run(self) -> None:
        self._running = True
        logger.info("GoalEngine background task started.")
        while self._running:
            if self.state in (GoalState.DONE, GoalState.FAILED, GoalState.IDLE):
                await asyncio.sleep(1.0)
                continue
            
            try:
                await self.step()
            except Exception as e:
                logger.error(f"GoalEngine step failed: {e}")
                self.state = GoalState.FAILED
                
            await asyncio.sleep(0.1)

    def stop(self) -> None:
        self._running = False

    async def step(self) -> None:
        if not self.context:
            return

        if self.state == GoalState.PLANNING:
            await self._do_planning()
        elif self.state == GoalState.ACTING:
            await self._do_acting()
        elif self.state == GoalState.CRITIQUING:
            await self._do_critiquing()

    async def _do_planning(self) -> None:
        logger.info("GoalEngine: PLANNING")
        registry = get_model_registry()
        planning_model = registry.get("planning") if "planning" in registry._adapters else registry.get("default")
        
        prompt = f"""You are a master planner. Break down the following objective into a logical sequence of high-level tasks.
Objective: {self.context.objective}

Return ONLY a valid JSON array of strings, where each string is a task description. Do not use markdown blocks.
Example: ["Task 1", "Task 2"]"""
        
        try:
            req = GenerationRequest(prompt=prompt, max_tokens=1024)
            resp = await planning_model.generate(req)
            
            # Clean up the response if it has markdown blocks
            text = resp.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            plan = json.loads(text.strip())
            if isinstance(plan, list) and all(isinstance(x, str) for x in plan):
                self.context.plan = plan
                self.context.current_step = 0
                self.context.retry_count = 0
                logger.info(f"GoalEngine: Generated plan with {len(plan)} steps.")
                self.state = GoalState.ACTING
            else:
                raise ValueError("Plan is not a list of strings.")
        except Exception as e:
            logger.error(f"GoalEngine PLANNING failed: {e}")
            self.state = GoalState.FAILED

    async def _do_acting(self) -> None:
        logger.info("GoalEngine: ACTING")
        if self.context.current_step >= len(self.context.plan):
            self.context.is_satisfied = True
            self.state = GoalState.DONE
            return
            
        task = self.context.plan[self.context.current_step]
        logger.info(f"GoalEngine: Executing step {self.context.current_step + 1}/{len(self.context.plan)}: {task}")
        
        if self.conversation_engine:
            # Inject task into conversation for Manager
            await self.conversation_engine.inject_human_message(f"Master Task Assigned: {task}\nPlease complete this task and then use the `submit_task_result` tool to report completion.")
            
            # Ensure the conversation is running
            if self.conversation_engine.state_machine.state.value == "paused":
                await self.conversation_engine.resume()
                
            # Wait for the task to be completed (signaled by submit_task_result)
            self._step_completed_event.clear()
            
            try:
                # Wait for completion, with a safety timeout (e.g. 10 minutes)
                await asyncio.wait_for(self._step_completed_event.wait(), timeout=600.0)
            except asyncio.TimeoutError:
                logger.warning("GoalEngine: Timed out waiting for task completion.")
                # We'll just move to critiquing anyway
        else:
            logger.warning("No ConversationEngine attached to GoalEngine!")
            
        self.state = GoalState.CRITIQUING

    async def _do_critiquing(self) -> None:
        logger.info("GoalEngine: CRITIQUING")
        self.current_iteration += 1
        
        registry = get_model_registry()
        observer_model = registry.get("observer") if "observer" in registry._adapters else registry.get("default")
        
        task = self.context.plan[self.context.current_step]
        last_result = self.context.actions_taken[-1]["result"] if self.context.actions_taken else "No result submitted."
        
        prompt = f"""You are a strict task evaluator.
Objective: {self.context.objective}
Current Task: {task}
Submitted Result: {last_result}

Did the agent successfully complete the task? Reply with exactly 'YES' or 'NO'. If 'NO', explain briefly on the next line."""
        
        try:
            req = GenerationRequest(prompt=prompt, max_tokens=256)
            resp = await observer_model.generate(req)
            
            evaluation = resp.text.strip().upper()
            self.context.critique_history.append(resp.text)
            
            if evaluation.startswith("YES"):
                logger.info("GoalEngine: Task satisfied!")
                self.context.current_step += 1
                self.context.retry_count = 0
                if self.context.current_step >= len(self.context.plan):
                    self.context.is_satisfied = True
                    self.state = GoalState.DONE
                else:
                    self.state = GoalState.ACTING
            else:
                logger.warning("GoalEngine: Task NOT satisfied.")
                self.context.retry_count += 1
                if self.context.retry_count >= self.max_retries:
                    logger.error("GoalEngine: Max retries reached for task.")
                    self.state = GoalState.FAILED
                else:
                    # Inject feedback
                    if self.conversation_engine:
                        feedback = resp.text[3:].strip() if len(resp.text) > 3 else "Evaluation failed."
                        await self.conversation_engine.inject_human_message(f"Task Evaluation Failed. Feedback: {feedback}\nPlease try again and submit the result.")
                    self.state = GoalState.ACTING
                    
        except Exception as e:
            logger.error(f"GoalEngine CRITIQUING failed: {e}")
            self.state = GoalState.FAILED
