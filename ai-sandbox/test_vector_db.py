from app.memory.vector_store import VectorMemoryStore

def test_vector_db():
    print("Initializing Vector DB...")
    store = VectorMemoryStore(db_path=".")
    
    print("Adding a test memory...")
    store.add_memory(
        memory_id="test_mem_1",
        content="The user prefers using FastAPI and React for the dashboard.",
        metadata={"conversation_id": "test_conv", "type": "fact"}
    )
    
    print("Querying the vector store for 'dashboard'...")
    results = store.query_memories(
        query="What does the user prefer for the dashboard?",
        n_results=1,
        where={"conversation_id": "test_conv"}
    )
    
    print("Results:")
    for r in results:
        print(f"- {r['content']} (Distance: {r.get('distance')})")
        
    print("Vector DB works successfully!")

if __name__ == "__main__":
    test_vector_db()
