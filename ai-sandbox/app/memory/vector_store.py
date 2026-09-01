import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import asyncio

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

class VectorMemoryStore:
    """
    Semantic Memory Store for agents using ChromaDB.
    """
    def __init__(self, db_path: str):
        self.db_path = Path(db_path) / "vector_db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.db_path), settings=Settings(anonymized_telemetry=False))
        
        # Setup high-quality embedding function
        try:
            self.embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        except Exception as e:
            logger.warning(f"Failed to load sentence-transformers, falling back to default: {e}")
            self.embedding_func = None
            
        self.collection = self.client.get_or_create_collection(
            name="memories", 
            embedding_function=self.embedding_func
        )
    
    def add_memory(self, memory_id: str, content: str, metadata: Dict[str, Any]) -> None:
        """
        Adds a memory to the vector store.
        """
        # Ensure metadata values are strings, ints, floats, or bools as required by ChromaDB
        sanitized_metadata = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                sanitized_metadata[k] = v
            else:
                sanitized_metadata[k] = json.dumps(v)
                
        try:
            self.collection.add(
                documents=[content],
                metadatas=[sanitized_metadata],
                ids=[memory_id]
            )
            logger.debug(f"Added memory to vector store: {memory_id}")
        except Exception as e:
            logger.error(f"Failed to add memory to vector store: {e}")

    def query_memories(self, query: str, n_results: int = 5, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Query memories by semantic similarity.
        """
        if self.collection.count() == 0:
            return []
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results, self.collection.count()),
                where=where
            )
            
            memories = []
            if results and 'documents' in results and results['documents']:
                for i in range(len(results['documents'][0])):
                    memories.append({
                        "id": results['ids'][0][i],
                        "content": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if 'distances' in results and results['distances'] else None
                    })
            return memories
        except Exception as e:
            logger.error(f"Failed to query vector store: {e}")
            return []

    async def add_memory_async(self, memory_id: str, content: str, metadata: Dict[str, Any]) -> None:
        """Async wrapper for add_memory."""
        await asyncio.to_thread(self.add_memory, memory_id, content, metadata)

    def search(self, query: str, limit: int = 5, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Alias for query_memories."""
        return self.query_memories(query, n_results=limit, where=where)

    async def search_async(self, query: str, limit: int = 5, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Async alias for query_memories_async."""
        return await self.query_memories_async(query, n_results=limit, where=where)

    async def query_memories_async(self, query: str, n_results: int = 5, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Async wrapper for query_memories."""
        return await asyncio.to_thread(self.query_memories, query, n_results, where)
