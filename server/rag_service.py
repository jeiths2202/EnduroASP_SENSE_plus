#!/usr/bin/env python3
"""
RAG (Retrieval-Augmented Generation) Service
Efficient document-based chat system for resource-constrained environments
"""

import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader, 
    PyPDFLoader, 
    DirectoryLoader,
    UnstructuredMarkdownLoader
)
import time

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, 
                 persist_directory: str = "./chromadb",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 use_onnx: bool = True,
                 chunk_size: int = 512,
                 chunk_overlap: int = 50):
        """
        Initialize RAG Service with optimized settings for local deployment
        
        Args:
            persist_directory: ChromaDB storage path
            embedding_model: Sentence transformer model name
            use_onnx: Use ONNX backend for faster inference
            chunk_size: Maximum chunk size in characters
            chunk_overlap: Overlap between chunks
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize embedding model with ONNX backend for efficiency
        logger.info(f"Loading embedding model: {embedding_model}")
        try:
            if use_onnx:
                # Try ONNX backend first for better performance
                # Use optimized ONNX model for faster inference
                self.embedding_model = SentenceTransformer(
                    embedding_model, 
                    backend='onnx',
                    model_kwargs={"file_name": "model_O2.onnx"},  # Use O2 optimized model
                    trust_remote_code=True
                )
                logger.info("ONNX backend loaded successfully (O2 optimized)")
            else:
                self.embedding_model = SentenceTransformer(embedding_model)
                logger.info("Standard backend loaded")
        except Exception as e:
            logger.warning(f"ONNX backend failed, falling back to standard: {e}")
            self.embedding_model = SentenceTransformer(embedding_model)
        
        # Initialize ChromaDB with persistent storage
        logger.info(f"Initializing ChromaDB at: {self.persist_directory}")
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize text splitter for smart chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info("RAG Service initialized successfully")
        self._log_collection_stats()
    
    def _log_collection_stats(self):
        """Log current collection statistics"""
        try:
            count = self.collection.count()
            logger.info(f"Collection contains {count} documents")
        except Exception as e:
            logger.warning(f"Could not get collection stats: {e}")
    
    def _generate_doc_id(self, content: str, source: str) -> str:
        """Generate unique document ID based on content and source"""
        combined = f"{source}:{content}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def load_documents_from_directory(self, directory_path: str, 
                                    file_types: List[str] = None) -> Dict[str, Any]:
        """
        Load and process documents from a directory
        
        Args:
            directory_path: Path to document directory
            file_types: List of file extensions to process
            
        Returns:
            Processing results with statistics
        """
        if file_types is None:
            file_types = ['.txt', '.md', '.pdf', '.json']
        
        directory_path = Path(directory_path)
        if not directory_path.exists():
            raise ValueError(f"Directory not found: {directory_path}")
        
        results = {
            'processed_files': [],
            'failed_files': [],
            'total_chunks': 0,
            'processing_time': 0
        }
        
        start_time = time.time()
        
        # Process each supported file type
        for file_type in file_types:
            pattern = f"**/*{file_type}"
            files = list(directory_path.glob(pattern))
            
            for file_path in files:
                try:
                    logger.info(f"Processing: {file_path}")
                    
                    # Load document based on file type
                    if file_type == '.pdf':
                        loader = PyPDFLoader(str(file_path))
                    elif file_type == '.md':
                        loader = UnstructuredMarkdownLoader(str(file_path))
                    else:  # .txt, .json and others
                        loader = TextLoader(str(file_path), encoding='utf-8')
                    
                    documents = loader.load()
                    
                    # Process each document
                    for doc in documents:
                        chunks_added = self.add_document(
                            content=doc.page_content,
                            source=str(file_path),
                            metadata=doc.metadata
                        )
                        results['total_chunks'] += chunks_added
                    
                    results['processed_files'].append(str(file_path))
                    
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")
                    results['failed_files'].append({
                        'file': str(file_path),
                        'error': str(e)
                    })
        
        results['processing_time'] = time.time() - start_time
        logger.info(f"Directory processing completed: {results}")
        
        return results
    
    def add_document(self, content: str, source: str, 
                    metadata: Dict[str, Any] = None) -> int:
        """
        Add a document to the vector database
        
        Args:
            content: Document content
            source: Source identifier (file path, URL, etc.)
            metadata: Additional metadata
            
        Returns:
            Number of chunks created
        """
        if not content.strip():
            logger.warning(f"Empty content for source: {source}")
            return 0
        
        # Split content into chunks
        chunks = self.text_splitter.split_text(content)
        
        if not chunks:
            logger.warning(f"No chunks created for source: {source}")
            return 0
        
        # Prepare metadata
        base_metadata = metadata or {}
        base_metadata.update({
            'source': source,
            'chunk_count': len(chunks),
            'added_at': time.time()
        })
        
        # Generate embeddings for all chunks at once (batch processing)
        try:
            embeddings = self.embedding_model.encode(
                chunks, 
                batch_size=32, 
                show_progress_bar=False,
                convert_to_numpy=True
            ).tolist()
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return 0
        
        # Prepare data for ChromaDB
        ids = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            doc_id = self._generate_doc_id(chunk, f"{source}:chunk_{i}")
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                'chunk_index': i,
                'chunk_text': chunk[:200] + "..." if len(chunk) > 200 else chunk
            })
            
            ids.append(doc_id)
            metadatas.append(chunk_metadata)
        
        # Add to ChromaDB
        try:
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(chunks)} chunks from {source}")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Failed to add chunks to database: {e}")
            return 0
    
    def search_documents(self, query: str, n_results: int = 5,
                        min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search for relevant documents
        
        Args:
            query: Search query
            n_results: Maximum number of results
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of relevant documents with metadata
        """
        if not query.strip():
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(
                [query], 
                show_progress_bar=False,
                convert_to_numpy=True
            ).tolist()[0]
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, 100),  # ChromaDB limit
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            documents = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    # Convert distance to similarity score (ChromaDB uses cosine distance)
                    similarity = 1 - distance
                    
                    if similarity >= min_score:
                        documents.append({
                            'content': doc,
                            'metadata': metadata,
                            'similarity': similarity,
                            'rank': i + 1
                        })
            
            logger.info(f"Found {len(documents)} relevant documents for query")
            return documents
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the document collection"""
        try:
            count = self.collection.count()
            
            # Get some sample documents to analyze
            sample_results = self.collection.peek(limit=10)
            
            info = {
                'total_documents': count,
                'collection_name': self.collection.name,
                'persist_directory': str(self.persist_directory),
                'embedding_model': getattr(self.embedding_model, 'model_name', 'all-MiniLM-L6-v2'),
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap
            }
            
            if sample_results and sample_results.get('metadatas'):
                # Analyze sources
                sources = set()
                for metadata in sample_results['metadatas']:
                    if metadata and 'source' in metadata:
                        sources.add(metadata['source'])
                
                info['sample_sources'] = list(sources)[:5]
                info['estimated_sources'] = len(sources)
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {
                'error': str(e),
                'total_documents': 0,
                'collection_name': 'unknown'
            }
    
    def clear_collection(self) -> bool:
        """Clear all documents from the collection"""
        try:
            # Delete the collection and recreate it
            self.chroma_client.delete_collection(name="documents")
            self.collection = self.chroma_client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Collection cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on RAG service"""
        health = {
            'status': 'healthy',
            'embedding_model_loaded': False,
            'chromadb_accessible': False,
            'collection_accessible': False,
            'issues': []
        }
        
        try:
            # Test embedding model
            test_embedding = self.embedding_model.encode(["test"], show_progress_bar=False)
            health['embedding_model_loaded'] = True
        except Exception as e:
            health['issues'].append(f"Embedding model error: {e}")
            health['status'] = 'degraded'
        
        try:
            # Test ChromaDB connection
            self.chroma_client.heartbeat()
            health['chromadb_accessible'] = True
        except Exception as e:
            health['issues'].append(f"ChromaDB error: {e}")
            health['status'] = 'unhealthy'
        
        try:
            # Test collection access
            self.collection.count()
            health['collection_accessible'] = True
        except Exception as e:
            health['issues'].append(f"Collection error: {e}")
            health['status'] = 'degraded'
        
        return health

# Global RAG service instance
rag_service = None

def get_rag_service() -> RAGService:
    """Get or create global RAG service instance"""
    global rag_service
    if rag_service is None:
        # Initialize with optimized settings for local deployment
        persist_dir = os.getenv('RAG_PERSIST_DIR', './chromadb')
        embedding_model = os.getenv('RAG_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        use_onnx = os.getenv('RAG_USE_ONNX', 'true').lower() == 'true'
        
        rag_service = RAGService(
            persist_directory=persist_dir,
            embedding_model=embedding_model,
            use_onnx=use_onnx
        )
    return rag_service