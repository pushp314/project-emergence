from __future__ import annotations

from typing import Any, Dict
from app.tools.gateway import Tool
from app.events.schemas import PermissionLevel, RiskLevel
from app.memory.vector_store import VectorMemoryStore

class KnowledgeTool(Tool):
    def __init__(self, vector_store: VectorMemoryStore):
        self.vector_store = vector_store

    @property
    def name(self) -> str:
        return "knowledge_search"

    @property
    def description(self) -> str:
        return "Search the RAG Vector Database for information from uploaded PDFs and documents."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look for in the ingested documents."
                },
                "n_results": {
                    "type": "integer",
                    "description": "Number of results to return. Default 3."
                }
            },
            "required": ["query"]
        }

    @property
    def permission(self) -> PermissionLevel:
        return PermissionLevel.READ

    @property
    def risk(self) -> RiskLevel:
        return RiskLevel.LOW

    @property
    def enabled(self) -> bool:
        return True

    async def execute(self, arguments: Dict[str, Any]) -> Any:
        query = arguments.get("query")
        if not query:
            return {"success": False, "error": "No query provided"}
            
        n_results = arguments.get("n_results", 3)
        
        try:
            # Search across all memory types (documents, conversation summaries, facts)
            results = await self.vector_store.query_memories_async(
                query=query,
                n_results=n_results
            )
            
            if not results:
                return {"success": True, "results": "No relevant documents found."}
                
            formatted = []
            for r in results:
                metadata = r.get("metadata", {})
                source = metadata.get("source", "Unknown")
                page = metadata.get("page", "N/A")
                chunk_index = metadata.get("chunk_index", "N/A")
                content = r.get("content", "")
                formatted.append(f"[Source: {source} | Page: {page} | Chunk: {chunk_index}]\n{content}\n")
                
            return {"success": True, "results": "\n---\n".join(formatted)}
        except Exception as e:
            return {"success": False, "error": str(e)}
