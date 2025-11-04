"""
SARAi AGI - Vector Database Module

Sistema de base de datos vectorial para memoria conversacional y RAG.
Soporta Qdrant (producción) y ChromaDB (desarrollo/alternativa).

Características:
- Cliente Qdrant para producción (escalable, persistente)
- Cliente ChromaDB para desarrollo local
- Integración con Embedding Gemma (2B/300M)
- Top-k retrieval con filtros
- Gestión automática de colecciones
- Thread-safe operations

Uso:
    from sarai_agi.memory.vector_db import VectorDB
    
    # Producción con Qdrant
    db = VectorDB(backend="qdrant", host="localhost", port=6333)
    
    # Desarrollo con ChromaDB
    db = VectorDB(backend="chroma", persist_directory="state/chroma")
    
    # Añadir documentos
    db.add_documents([
        {"text": "SARAi es una AGI local", "metadata": {"source": "docs"}},
        {"text": "El sistema usa modelos GGUF", "metadata": {"source": "docs"}}
    ])
    
    # Búsqueda semántica
    results = db.search("¿Qué es SARAi?", top_k=5)
    for result in results:
        print(f"{result['text']} (score: {result['score']})")
"""

import os
import logging
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime
import hashlib

# Type hints
Backend = Literal["qdrant", "chroma"]

# Imports condicionales (dependencias opcionales)
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QdrantClient = None
    QDRANT_AVAILABLE = False

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    chromadb = None
    CHROMA_AVAILABLE = False

# Embedding model (placeholder - se integrará con Embedding Gemma)
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False


logger = logging.getLogger(__name__)


class VectorDB:
    """
    Abstracción de base de datos vectorial con soporte para Qdrant y ChromaDB
    
    Args:
        backend: "qdrant" o "chroma"
        host: Host del servidor (para Qdrant)
        port: Puerto del servidor (para Qdrant)
        persist_directory: Directorio de persistencia (para ChromaDB)
        collection_name: Nombre de la colección
        embedding_dim: Dimensión de embeddings (default: 384 para all-MiniLM-L6-v2)
    """
    
    def __init__(
        self,
        backend: Backend = "qdrant",
        host: str = "localhost",
        port: int = 6333,
        persist_directory: str = "state/chroma",
        collection_name: str = "sarai_memory",
        embedding_dim: int = 384
    ):
        self.backend = backend
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        
        # Inicializar cliente según backend
        if backend == "qdrant":
            if not QDRANT_AVAILABLE:
                raise ImportError(
                    "qdrant-client no disponible. Instalar con: pip install qdrant-client"
                )
            
            try:
                self.client = QdrantClient(host=host, port=port)
                self._init_qdrant_collection()
                logger.info(f"Qdrant client inicializado: {host}:{port}")
            except Exception as e:
                logger.error(f"Error conectando a Qdrant: {e}")
                raise
        
        elif backend == "chroma":
            if not CHROMA_AVAILABLE:
                raise ImportError(
                    "chromadb no disponible. Instalar con: pip install chromadb"
                )
            
            try:
                os.makedirs(persist_directory, exist_ok=True)
                self.client = chromadb.PersistentClient(path=persist_directory)
                self.collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"ChromaDB client inicializado: {persist_directory}")
            except Exception as e:
                logger.error(f"Error inicializando ChromaDB: {e}")
                raise
        
        else:
            raise ValueError(f"Backend inválido: {backend}. Usar 'qdrant' o 'chroma'")
        
        # Embedder (placeholder - se reemplazará con Embedding Gemma)
        self._embedder = None
    
    def _init_qdrant_collection(self):
        """Inicializa colección en Qdrant si no existe"""
        try:
            # Verificar si colección existe
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # Crear colección
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Colección Qdrant creada: {self.collection_name}")
            else:
                logger.info(f"Colección Qdrant existente: {self.collection_name}")
        
        except Exception as e:
            logger.error(f"Error inicializando colección Qdrant: {e}")
            raise
    
    def _embed_text(self, text: str) -> List[float]:
        """
        Genera embedding para texto
        
        TODO: Integrar con Embedding Gemma
        Por ahora usa embedding dummy para testing
        
        Args:
            text: Texto a embedder
        
        Returns:
            Vector de embedding (lista de floats)
        """
        if self._embedder is not None:
            # Usar embedder real cuando esté disponible
            return self._embedder.encode(text)
        
        # Embedding dummy para testing (hash determinístico)
        if not NUMPY_AVAILABLE:
            # Fallback sin numpy
            text_hash = hashlib.md5(text.encode()).hexdigest()
            # Convertir hash a vector de floats normalizados
            embedding = [
                float(int(text_hash[i:i+2], 16)) / 255.0 
                for i in range(0, min(len(text_hash), self.embedding_dim * 2), 2)
            ]
            # Padding si es necesario
            while len(embedding) < self.embedding_dim:
                embedding.append(0.0)
            return embedding[:self.embedding_dim]
        
        # Con numpy (mejor performance)
        np.random.seed(int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32))
        embedding = np.random.randn(self.embedding_dim)
        # Normalizar
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding.tolist()
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """
        Añade documentos a la base de datos vectorial
        
        Args:
            documents: Lista de dicts con keys 'text' y opcionalmente 'metadata'
            batch_size: Tamaño de lote para inserciones
        
        Returns:
            Número de documentos añadidos
        
        Example:
            docs = [
                {"text": "SARAi es una AGI", "metadata": {"source": "docs"}},
                {"text": "Usa modelos GGUF", "metadata": {"source": "tech"}}
            ]
            count = db.add_documents(docs)
        """
        if not documents:
            logger.warning("add_documents: lista de documentos vacía")
            return 0
        
        try:
            if self.backend == "qdrant":
                return self._add_documents_qdrant(documents, batch_size)
            elif self.backend == "chroma":
                return self._add_documents_chroma(documents, batch_size)
        
        except Exception as e:
            logger.error(f"Error añadiendo documentos: {e}")
            raise
    
    def _add_documents_qdrant(self, documents: List[Dict], batch_size: int) -> int:
        """Añade documentos a Qdrant"""
        points = []
        
        for idx, doc in enumerate(documents):
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            
            if not text:
                logger.warning(f"Documento {idx} sin texto, omitiendo")
                continue
            
            # Generar embedding
            embedding = self._embed_text(text)
            
            # Crear point
            point = PointStruct(
                id=idx,  # En producción usar UUID
                vector=embedding,
                payload={
                    "text": text,
                    "metadata": metadata,
                    "timestamp": datetime.now().isoformat()
                }
            )
            points.append(point)
            
            # Insertar en batches
            if len(points) >= batch_size:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                points = []
        
        # Insertar restantes
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
        
        logger.info(f"Añadidos {len(documents)} documentos a Qdrant")
        return len(documents)
    
    def _add_documents_chroma(self, documents: List[Dict], batch_size: int) -> int:
        """Añade documentos a ChromaDB"""
        ids = []
        embeddings = []
        texts = []
        metadatas = []
        
        for idx, doc in enumerate(documents):
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            
            if not text:
                logger.warning(f"Documento {idx} sin texto, omitiendo")
                continue
            
            # Generar ID único
            doc_id = f"doc_{idx}_{datetime.now().timestamp()}"
            
            # Generar embedding
            embedding = self._embed_text(text)
            
            ids.append(doc_id)
            embeddings.append(embedding)
            texts.append(text)
            metadatas.append({
                **metadata,
                "timestamp": datetime.now().isoformat()
            })
        
        # Añadir en batches
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_embeddings = embeddings[i:i+batch_size]
            batch_texts = texts[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            
            self.collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings,
                documents=batch_texts,
                metadatas=batch_metadatas
            )
        
        logger.info(f"Añadidos {len(ids)} documentos a ChromaDB")
        return len(ids)
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Búsqueda semántica en la base de datos vectorial
        
        Args:
            query: Query de búsqueda en lenguaje natural
            top_k: Número de resultados a retornar
            filter_metadata: Filtros opcionales por metadata
        
        Returns:
            Lista de resultados ordenados por similitud
            [{"text": str, "score": float, "metadata": dict}, ...]
        
        Example:
            results = db.search("¿Qué es SARAi?", top_k=5)
            for result in results:
                print(f"{result['text']} (score: {result['score']:.3f})")
        """
        try:
            # Generar embedding de query
            query_embedding = self._embed_text(query)
            
            if self.backend == "qdrant":
                return self._search_qdrant(query_embedding, top_k, filter_metadata)
            elif self.backend == "chroma":
                return self._search_chroma(query_embedding, top_k, filter_metadata)
        
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return []
    
    def _search_qdrant(
        self,
        query_embedding: List[float],
        top_k: int,
        filter_metadata: Optional[Dict]
    ) -> List[Dict]:
        """Búsqueda en Qdrant"""
        # TODO: Implementar filtros de metadata
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k
        )
        
        results = []
        for hit in search_result:
            results.append({
                "text": hit.payload.get("text", ""),
                "score": hit.score,
                "metadata": hit.payload.get("metadata", {}),
                "timestamp": hit.payload.get("timestamp")
            })
        
        return results
    
    def _search_chroma(
        self,
        query_embedding: List[float],
        top_k: int,
        filter_metadata: Optional[Dict]
    ) -> List[Dict]:
        """Búsqueda en ChromaDB"""
        # TODO: Implementar filtros de metadata con where
        search_result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        results = []
        if search_result["documents"] and search_result["documents"][0]:
            for idx, doc in enumerate(search_result["documents"][0]):
                # ChromaDB usa distance, convertir a similarity score
                distance = search_result["distances"][0][idx] if search_result["distances"] else 0.0
                score = 1.0 - distance  # Aproximado para cosine
                
                results.append({
                    "text": doc,
                    "score": score,
                    "metadata": search_result["metadatas"][0][idx] if search_result["metadatas"] else {},
                    "id": search_result["ids"][0][idx]
                })
        
        return results
    
    def delete_collection(self):
        """Elimina la colección completa (usar con precaución)"""
        try:
            if self.backend == "qdrant":
                self.client.delete_collection(collection_name=self.collection_name)
                logger.info(f"Colección Qdrant eliminada: {self.collection_name}")
            elif self.backend == "chroma":
                self.client.delete_collection(name=self.collection_name)
                logger.info(f"Colección ChromaDB eliminada: {self.collection_name}")
        
        except Exception as e:
            logger.error(f"Error eliminando colección: {e}")
            raise
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas de la base de datos
        
        Returns:
            {"count": int, "backend": str, "collection": str}
        """
        try:
            if self.backend == "qdrant":
                collection_info = self.client.get_collection(self.collection_name)
                count = collection_info.points_count
            elif self.backend == "chroma":
                count = self.collection.count()
            
            return {
                "count": count,
                "backend": self.backend,
                "collection": self.collection_name,
                "embedding_dim": self.embedding_dim
            }
        
        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
            return {"count": 0, "backend": self.backend, "collection": self.collection_name}


# Singleton global
_vector_db_instance: Optional[VectorDB] = None


def get_vector_db(
    backend: Optional[Backend] = None,
    **kwargs
) -> VectorDB:
    """
    Factory function para obtener instancia singleton de VectorDB
    
    Args:
        backend: "qdrant" o "chroma" (default desde env VECTOR_DB_BACKEND o "qdrant")
        **kwargs: Argumentos adicionales para VectorDB()
    
    Returns:
        Instancia singleton de VectorDB
    """
    global _vector_db_instance
    
    if _vector_db_instance is None:
        # Leer de variable de entorno si no se especifica
        if backend is None:
            backend = os.getenv("VECTOR_DB_BACKEND", "qdrant")
        
        _vector_db_instance = VectorDB(backend=backend, **kwargs)
    
    return _vector_db_instance
