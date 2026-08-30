import logging
from typing import Any, Dict, List, Optional
import json

from app.agents.base import BaseAgent, AgentContext
from app.models.base import GenerationRequest

logger = logging.getLogger(__name__)

class ReflectiveAgent(BaseAgent):
    """
    An agent that uses reflection and tree-of-thoughts before taking action.
    """
    async def think(self, context: AgentContext) -> str:
        # Determine if we are about to make a tool call that is high-risk, or just generating a response.
        # For simplicity in this demo, we generate a response, critique it, and regenerate.
        initial_response = await self.generate_response(context)
        
        # Fast path if it's a simple greeting or very short response
        if len(initial_response.split()) < 20 and "<tool_call>" not in initial_response:
            return initial_response
            
        logger.info(f"Agent {self.agent_id} is reflecting on its intended response.")
        
        # Critique phase
        critique_prompt = (
            "You are a peer reviewer. Review the following intended response to the conversation. "
            "Identify any logical flaws, hallucinations, or inefficient tool usage. "
            "Keep the critique extremely concise.\n\n"
            f"Intended Response:\n{initial_response}"
        )
        critique_req = GenerationRequest(
            messages=[{"role": "user", "content": critique_prompt}],
            max_tokens=self.config.max_tokens,
            temperature=0.3,
            stream=False
        )
        critique = await self.model.generate(critique_req)
        
        if "looks good" in critique.text.lower() or "no issues" in critique.text.lower():
            return initial_response
            
        # Revision phase
        revision_prompt = (
            "You previously generated a response, but a peer reviewer found some issues.\n"
            f"Original Response:\n{initial_response}\n\n"
            f"Critique:\n{critique.text}\n\n"
            "Please provide an updated and corrected response."
        )
        revision_req = GenerationRequest(
            messages=[{"role": "user", "content": revision_prompt}],
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            stream=False
        )
        revised = await self.model.generate(revision_req)
        return revised.text
