from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.events.bus import EventBus, Event, EventType, get_event_bus
from app.models.base import GenerationRequest, get_model_registry
from app.tools.gateway import ToolGateway, get_tool_gateway
from app.research.manager import get_research_manager

logger = logging.getLogger(__name__)


class MacSystemController:
    """
    Autonomous Mac Operating Agent that accepts natural language instructions,
    plans execution, uses tools (terminal, filesystem, research, web, system),
    and streams thoughts & execution results in real-time.
    """

    def __init__(
        self,
        tool_gateway: Optional[ToolGateway] = None,
        event_bus: Optional[EventBus] = None
    ):
        self.tool_gateway = tool_gateway or get_tool_gateway()
        self.event_bus = event_bus or get_event_bus()
        self.research_manager = get_research_manager()

    async def execute_task(
        self,
        task: str,
        conversation_id: str = "default",
        max_steps: int = 8,
        mode: str = "24/7"
    ) -> Dict[str, Any]:
        logger.info(f"MacSystemController received task: '{task}' (mode={mode})")

        tools_desc = []
        for name, tool in self.tool_gateway._tools.items():
            if tool.enabled:
                tools_desc.append(f"- **{name}**: {tool.description} (Schema: {json.dumps(tool.input_schema)})")

        tools_prompt_str = "\n".join(tools_desc)

        system_prompt = f"""You are Antigravity Mac Autonomous Operator, an elite AI assistant with direct access to execute commands and manage files on the user's macOS system.
Your mission is to satisfy the user's request thoroughly, accurately, and autonomously.

AVAILABLE MAC TOOLS:
{tools_prompt_str}
- **research**: (Special Tool) Conduct deep multi-source research and automatically publish publication-grade Markdown documentation to ~/Desktop/Research_Reports/. Schema: {{"question": "string"}}

OPERATING RULES:
1. Always analyze the user's intent and formulate a clear, step-by-step plan.
2. In each turn, you can either call a tool or provide the final answer.
3. To call a tool, respond with ONLY a JSON block formatted exactly as:
```json
{{
  "thought": "Your internal reasoning explaining why you are taking this action and what you expect to learn.",
  "action": "tool_name",
  "action_input": {{ "param1": "value1" }}
}}
```
4. When you have completed the task, respond with:
```json
{{
  "thought": "All necessary actions have been executed and verified.",
  "final_response": "Your comprehensive, beautifully formatted Markdown response to the user with all results, file paths, and summaries."
}}
```
5. You have full permission to inspect system status, run terminal commands, write/edit files, and perform research. Be decisive, autonomous, and safe.
"""

        history: List[Dict[str, str]] = [
            {"role": "user", "content": f"Task: {task}"}
        ]

        steps_record: List[Dict[str, Any]] = []
        overall_thought = ""
        final_text = ""
        desktop_path = None

        registry = get_model_registry()
        model = registry.get("default")

        images: List[str] = []

        for step_idx in range(max_steps):
            prompt = "\n\n".join([f"[{m['role'].upper()}]:\n{m['content']}" for m in history])
            prompt += f"\n\n[SYSTEM]: Provide your next action or final_response JSON for Step {step_idx + 1}/{max_steps}:"

            try:
                raw_text = ""
                async for chunk in model.generate_stream(GenerationRequest(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    images=images,
                    temperature=0.2,
                    max_tokens=2500
                )):
                    raw_text += chunk
                    await self.event_bus.publish_type(
                        EventType.AGENT_CHUNK,
                        conversation_id,
                        {"chunk": chunk, "step": step_idx + 1}
                    )
                raw_text = raw_text.strip()
                # Clear images after use so we don't keep sending them
                images = []
            except Exception as e:
                logger.error(f"Model generation failed during step {step_idx + 1}: {e}")
                final_text = f"An error occurred while generating next action: {e}"
                break

            # Parse JSON action
            parsed_action = self._parse_json_action(raw_text)
            if not parsed_action:
                # If model directly outputted plain text
                final_text = raw_text
                break

            thought = parsed_action.get("thought", "")
            if thought:
                overall_thought += f"\n• {thought}" if overall_thought else thought
                # Emit live thinking event
                await self.event_bus.publish_type(
                    EventType.AGENT_STARTED,
                    conversation_id,
                    {"thought": thought, "step": step_idx + 1}
                )

            if "final_response" in parsed_action:
                final_text = parsed_action["final_response"]
                break

            action_name = parsed_action.get("action", "")
            action_input = parsed_action.get("action_input", {})

            if not action_name:
                final_text = parsed_action.get("thought", raw_text)
                break

            # Execute tool
            logger.info(f"Executing tool '{action_name}' with args {action_input}")
            
            # Emit tool started event
            await self.event_bus.publish_type(
                EventType.TOOL_STARTED,
                conversation_id,
                {"tool_name": action_name, "arguments": action_input}
            )

            step_data = {
                "step": step_idx + 1,
                "thought": thought,
                "action": action_name,
                "action_input": action_input,
                "status": "running"
            }

            tool_result = None
            try:
                if action_name == "research":
                    q = action_input.get("question") or task
                    sess = await self.research_manager.research(
                        agent_id="mac_operator",
                        question=q,
                        max_sources=5,
                        export_desktop=True
                    )
                    desktop_path = sess.metadata.get("desktop_path")
                    tool_result = {
                        "status": "completed",
                        "desktop_path": desktop_path,
                        "report_path": sess.metadata.get("report_path"),
                        "summary": sess.metadata.get("summary", "")[:500]
                    }
                else:
                    tool_obj = self.tool_gateway.get_tool(action_name)
                    if tool_obj:
                        action_input["_conversation_id"] = conversation_id
                        tool_result = await tool_obj.execute(action_input)
                    else:
                        tool_result = {"error": f"Tool '{action_name}' not found"}

                step_data["status"] = "success"
                step_data["result"] = tool_result

                # Check if file was written to desktop
                if action_name == "filesystem":
                    path_arg = action_input.get("path", "")
                    if "Desktop" in path_arg:
                        desktop_path = str(os.path.expanduser(path_arg))

            except Exception as e:
                logger.error(f"Tool '{action_name}' execution error: {e}")
                step_data["status"] = "failed"
                step_data["error"] = str(e)
                tool_result = {"error": str(e)}

            steps_record.append(step_data)

            # Emit tool completed event
            await self.event_bus.publish_type(
                EventType.TOOL_COMPLETED,
                conversation_id,
                {"tool_name": action_name, "arguments": action_input, "result": tool_result}
            )

            # Feed observation back to model
            history.append({
                "role": "assistant",
                "content": f"Action: {action_name}\nInput: {json.dumps(action_input)}\nThought: {thought}"
            })
            
            # Extract image if present
            if isinstance(tool_result, dict) and "image_base64" in tool_result:
                img_b64 = tool_result.pop("image_base64")
                if img_b64:
                    images.append(img_b64)
                    tool_result["image_status"] = "Image attached to prompt successfully"
            
            obs_str = json.dumps(tool_result, default=str)
            if len(obs_str) > 3000:
                obs_str = obs_str[:3000] + "... [truncated]"
            history.append({
                "role": "system",
                "content": f"Observation from {action_name}:\n{obs_str}"
            })

        if not final_text:
            final_text = "I have completed all requested operations on your Mac."

        # Emit agent final message
        await self.event_bus.publish_type(
            EventType.AGENT_MESSAGE,
            conversation_id,
            {"content": final_text, "tools_count": len(steps_record)}
        )

        return {
            "success": True,
            "task": task,
            "thought": overall_thought,
            "steps": steps_record,
            "final_response": final_text,
            "desktop_path": desktop_path,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }

    def _parse_json_action(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            
            # Find first { and last }
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start:end+1])
        except Exception:
            pass
        return None


_mac_controller: Optional[MacSystemController] = None


def get_mac_controller() -> MacSystemController:
    global _mac_controller
    if _mac_controller is None:
        _mac_controller = MacSystemController()
    return _mac_controller
