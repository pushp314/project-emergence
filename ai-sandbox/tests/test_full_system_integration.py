import unittest
import asyncio
from app.agents.base import BaseAgent, AgentConfig, AgentContext
from app.events.schemas import ToolCall, ToolResult
from app.models.base import ModelAdapter, GenerationRequest, GenerationResponse


class DummyModel(ModelAdapter):
    async def generate(self, req: GenerationRequest) -> GenerationResponse:
        return GenerationResponse(text="dummy", tokens_generated=1, finish_reason="stop", latency_ms=1.0, model="dummy")
    async def generate_stream(self, req: GenerationRequest):
        yield "dummy"
    async def count_tokens(self, text: str) -> int:
        return 1
    async def health_check(self) -> bool:
        return True
    def get_model_info(self) -> dict:
        return {"name": "dummy"}
    async def close(self) -> None:
        pass


class DummyAgent(BaseAgent):
    async def think(self, context: AgentContext) -> str:
        return "Hello"


class TestFullSystemIntegration(unittest.IsolatedAsyncioTestCase):
    def test_tool_call_regex_extraction(self):
        agent = DummyAgent(
            "test_agent",
            AgentConfig(agent_identity="test", name="test", system_prompt="", model="dummy"),
            model_adapter=DummyModel()
        )

        # Test 1: Standard single-line tool call
        text1 = 'I will run a command: [TOOL:terminal:{"command": "ls -la"}] to check files.'
        calls1 = agent._extract_tool_calls(text1)
        self.assertEqual(len(calls1), 1)
        self.assertEqual(calls1[0][0], "terminal")
        self.assertEqual(calls1[0][1], {"command": "ls -la"})

        # Test 2: Multi-line JSON with nested objects
        text2 = '''Let me write a file:
[TOOL:filesystem:{
  "operation": "write",
  "path": "test.txt",
  "options": {
    "overwrite": true,
    "encoding": "utf-8"
  }
}]
Done!'''
        calls2 = agent._extract_tool_calls(text2)
        self.assertEqual(len(calls2), 1)
        self.assertEqual(calls2[0][0], "filesystem")
        self.assertEqual(calls2[0][1]["options"]["overwrite"], True)

        # Test 3: Multiple tools in one turn
        text3 = '''[TOOL:terminal:{"command": "pwd"}] and also [TOOL:system:{"action": "metrics"}]'''
        calls3 = agent._extract_tool_calls(text3)
        self.assertEqual(len(calls3), 2)
        self.assertEqual(calls3[0][0], "terminal")
        self.assertEqual(calls3[1][0], "system")


if __name__ == "__main__":
    unittest.main()
