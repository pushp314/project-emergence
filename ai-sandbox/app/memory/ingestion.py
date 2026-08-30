import os
import uuid
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DocumentIngester:
    def __init__(self, vector_store):
        self.vector_store = vector_store
        
    async def ingest_file(self, file_path: str, source_name: str) -> int:
        """Extracts text, splits it semantically, and saves to VectorStore. Returns chunk count."""
        try:
            from langchain_community.document_loaders import PyMuPDFLoader, TextLoader, UnstructuredMarkdownLoader
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError as e:
            logger.error(f"LangChain dependencies missing: {e}")
            return 0
            
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            # 1. Load document
            if ext == ".pdf":
                loader = PyMuPDFLoader(file_path)
            elif ext == ".md":
                loader = UnstructuredMarkdownLoader(file_path)
            else:
                loader = TextLoader(file_path, encoding="utf-8")
                
            docs = loader.load()
            
            if not docs:
                return 0
                
            # 2. Split semantically
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", " ", ""]
            )
            splits = text_splitter.split_documents(docs)
            
            if not splits:
                return 0
                
            # 3. Add to vector store
            for i, split in enumerate(splits):
                memory_id = f"doc_{uuid.uuid4().hex[:8]}"
                
                # Merge base metadata with langchain's metadata
                metadata = {
                    "source": source_name,
                    "type": "document",
                    "chunk_index": i
                }
                
                # Add page numbers if they exist
                if "page" in split.metadata:
                    metadata["page"] = split.metadata["page"]
                
                await self.vector_store.add_memory_async(memory_id, split.page_content, metadata)
                
            logger.info(f"Ingested {len(splits)} semantic chunks from {source_name}")
            return len(splits)
            
        except Exception as e:
            logger.error(f"Error ingesting document {file_path}: {e}")
            return 0
