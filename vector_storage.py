"""Vector storage module for Flow Guardian.

Provides SQLite-based vector storage using sqlite-vec for similarity search.
This replaces Backboard's cloud-based vector storage with a fully local solution.

Features:
- SQLite + sqlite-vec for vector similarity search
- FTS5 for keyword search fallback
- Namespace support (personal/team)
- Content type filtering (learning/session/document)
"""
import json
import os
import sqlite3
import struct
from datetime import datetime
from pathlib import Path
from typing import Optional

from embeddings import VECTOR_DIM

# Default storage location
DEFAULT_DB_PATH = Path.home() / ".flow-guardian" / "vectors.db"


class VectorStorageError(Exception):
    """Base exception for vector storage errors."""
    pass


class VectorStore:
    """
    SQLite-based vector store with semantic search capabilities.

    Uses sqlite-vec for vector similarity search and FTS5 for keyword fallback.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the vector store.

        Args:
            db_path: Path to the SQLite database file. Defaults to
                     ~/.flow-guardian/vectors.db or FLOW_GUARDIAN_DB_PATH env var.
        """
        if db_path:
            self.db_path = Path(db_path).expanduser()
        else:
            env_path = os.environ.get("FLOW_GUARDIAN_DB_PATH")
            if env_path:
                self.db_path = Path(env_path).expanduser()
            else:
                self.db_path = DEFAULT_DB_PATH

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_conn()

        # Load sqlite-vec extension
        try:
            conn.enable_load_extension(True)
            import sqlite_vec
            sqlite_vec.load(conn)
            conn.enable_load_extension(False)
        except Exception as e:
            # sqlite-vec might not be available, fall back to keyword-only search
            print(f"Warning: sqlite-vec not available, using keyword search only: {e}")

        # Main content table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                namespace TEXT NOT NULL DEFAULT 'personal',
                content TEXT NOT NULL,
                content_type TEXT NOT NULL DEFAULT 'learning',
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for common queries
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_namespace
            ON memories(namespace)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_content_type
            ON memories(content_type)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_created_at
            ON memories(created_at DESC)
        """)

        # Try to create vector table (requires sqlite-vec)
        try:
            conn.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec USING vec0(
                    id TEXT PRIMARY KEY,
                    embedding float[{VECTOR_DIM}]
                )
            """)
            self._vector_available = True
        except sqlite3.OperationalError:
            # sqlite-vec not available
            self._vector_available = False

        # Full-text search table for keyword fallback
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                id,
                content,
                tags,
                content='memories',
                content_rowid='rowid'
            )
        """)

        # Triggers to keep FTS in sync
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, id, content, tags)
                VALUES (new.rowid, new.id, new.content,
                        COALESCE(json_extract(new.metadata, '$.tags'), ''));
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, id, content, tags)
                VALUES('delete', old.rowid, old.id, old.content,
                       COALESCE(json_extract(old.metadata, '$.tags'), ''));
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, id, content, tags)
                VALUES('delete', old.rowid, old.id, old.content,
                       COALESCE(json_extract(old.metadata, '$.tags'), ''));
                INSERT INTO memories_fts(rowid, id, content, tags)
                VALUES (new.rowid, new.id, new.content,
                        COALESCE(json_extract(new.metadata, '$.tags'), ''));
            END
        """)

        conn.commit()

    def _serialize_embedding(self, embedding: list[float]) -> bytes:
        """Serialize embedding to bytes for sqlite-vec."""
        return struct.pack(f'{len(embedding)}f', *embedding)

    def _deserialize_embedding(self, data: bytes) -> list[float]:
        """Deserialize embedding from bytes."""
        count = len(data) // 4  # 4 bytes per float
        return list(struct.unpack(f'{count}f', data))

    def store(
        self,
        content: str,
        embedding: list[float],
        namespace: str = "personal",
        content_type: str = "learning",
        metadata: Optional[dict] = None,
        memory_id: Optional[str] = None,
    ) -> str:
        """
        Store content with its embedding.

        Args:
            content: The text content to store.
            embedding: The embedding vector (768 dimensions).
            namespace: Storage namespace ('personal' or 'team').
            content_type: Type of content ('learning', 'session', 'document').
            metadata: Optional metadata dictionary.
            memory_id: Optional custom ID. Generated if not provided.

        Returns:
            The memory ID.

        Raises:
            VectorStorageError: If storage fails.
        """
        if memory_id is None:
            memory_id = f"{content_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        conn = self._get_conn()

        try:
            # Store in main table
            metadata_json = json.dumps(metadata or {})
            conn.execute("""
                INSERT OR REPLACE INTO memories (id, namespace, content, content_type, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (memory_id, namespace, content, content_type, metadata_json, datetime.now().isoformat()))

            # Store embedding if vector search is available
            if self._vector_available and embedding:
                embedding_bytes = self._serialize_embedding(embedding)
                conn.execute("""
                    INSERT OR REPLACE INTO memories_vec (id, embedding)
                    VALUES (?, ?)
                """, (memory_id, embedding_bytes))

            conn.commit()
            return memory_id

        except Exception as e:
            conn.rollback()
            raise VectorStorageError(f"Failed to store memory: {e}") from e

    def search(
        self,
        query_embedding: list[float],
        namespace: str = "personal",
        content_type: Optional[str] = None,
        limit: int = 10,
        distance_threshold: float = 2.0,
    ) -> list[dict]:
        """
        Semantic search using vector similarity.

        Args:
            query_embedding: The query embedding vector.
            namespace: Filter by namespace.
            content_type: Optional filter by content type.
            limit: Maximum results to return.
            distance_threshold: Maximum distance for results (lower = more similar).

        Returns:
            List of matching memories with distance scores.
        """
        if not self._vector_available:
            # Fall back to keyword search if no vector support
            return []

        conn = self._get_conn()

        try:
            # Build query with filters
            query_bytes = self._serialize_embedding(query_embedding)

            sql = """
                SELECT
                    m.id,
                    m.content,
                    m.content_type,
                    m.metadata,
                    m.created_at,
                    v.distance
                FROM memories_vec v
                JOIN memories m ON m.id = v.id
                WHERE m.namespace = ?
                  AND v.embedding MATCH ?
                  AND k = ?
            """
            params = [namespace, query_bytes, limit * 2]  # Get extra for filtering

            if content_type:
                sql += " AND m.content_type = ?"
                params.append(content_type)

            sql += " ORDER BY v.distance"

            results = conn.execute(sql, params).fetchall()

            # Filter by distance threshold and limit
            output = []
            for row in results:
                if row['distance'] <= distance_threshold:
                    output.append({
                        "id": row['id'],
                        "content": row['content'],
                        "content_type": row['content_type'],
                        "metadata": json.loads(row['metadata']) if row['metadata'] else {},
                        "created_at": row['created_at'],
                        "distance": row['distance'],
                        "score": 1.0 / (1.0 + row['distance']),  # Convert distance to similarity score
                    })
                    if len(output) >= limit:
                        break

            return output

        except Exception as e:
            # If vector search fails, return empty (caller should try keyword search)
            print(f"Vector search error: {e}")
            return []

    def keyword_search(
        self,
        query: str,
        namespace: str = "personal",
        content_type: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Keyword-based search using FTS5.

        Args:
            query: The search query (supports FTS5 syntax).
            namespace: Filter by namespace.
            content_type: Optional filter by content type.
            limit: Maximum results to return.

        Returns:
            List of matching memories with BM25 scores.
        """
        conn = self._get_conn()

        try:
            # Clean query for FTS5 (escape special characters)
            clean_query = query.replace('"', '""')

            # Build SQL with filters
            sql = """
                SELECT
                    m.id,
                    m.content,
                    m.content_type,
                    m.metadata,
                    m.created_at,
                    bm25(memories_fts) as score
                FROM memories_fts f
                JOIN memories m ON m.id = f.id
                WHERE memories_fts MATCH ?
                  AND m.namespace = ?
            """
            params = [f'"{clean_query}"', namespace]

            if content_type:
                sql += " AND m.content_type = ?"
                params.append(content_type)

            sql += " ORDER BY score LIMIT ?"
            params.append(limit)

            results = conn.execute(sql, params).fetchall()

            return [
                {
                    "id": row['id'],
                    "content": row['content'],
                    "content_type": row['content_type'],
                    "metadata": json.loads(row['metadata']) if row['metadata'] else {},
                    "created_at": row['created_at'],
                    "score": abs(row['score']),  # BM25 returns negative scores
                }
                for row in results
            ]

        except Exception as e:
            print(f"Keyword search error: {e}")
            return []

    def get_by_id(self, memory_id: str) -> Optional[dict]:
        """
        Get a specific memory by ID.

        Args:
            memory_id: The memory ID.

        Returns:
            Memory dictionary or None if not found.
        """
        conn = self._get_conn()

        row = conn.execute("""
            SELECT id, namespace, content, content_type, metadata, created_at
            FROM memories
            WHERE id = ?
        """, (memory_id,)).fetchone()

        if row:
            return {
                "id": row['id'],
                "namespace": row['namespace'],
                "content": row['content'],
                "content_type": row['content_type'],
                "metadata": json.loads(row['metadata']) if row['metadata'] else {},
                "created_at": row['created_at'],
            }
        return None

    def list_recent(
        self,
        namespace: str = "personal",
        content_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """
        List recent memories.

        Args:
            namespace: Filter by namespace.
            content_type: Optional filter by content type.
            limit: Maximum results to return.

        Returns:
            List of memories sorted by creation time (newest first).
        """
        conn = self._get_conn()

        sql = """
            SELECT id, content, content_type, metadata, created_at
            FROM memories
            WHERE namespace = ?
        """
        params = [namespace]

        if content_type:
            sql += " AND content_type = ?"
            params.append(content_type)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        results = conn.execute(sql, params).fetchall()

        return [
            {
                "id": row['id'],
                "content": row['content'],
                "content_type": row['content_type'],
                "metadata": json.loads(row['metadata']) if row['metadata'] else {},
                "created_at": row['created_at'],
            }
            for row in results
        ]

    def delete(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.

        Args:
            memory_id: The memory ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        conn = self._get_conn()

        try:
            cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))

            if self._vector_available:
                conn.execute("DELETE FROM memories_vec WHERE id = ?", (memory_id,))

            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            conn.rollback()
            raise VectorStorageError(f"Failed to delete memory: {e}") from e

    def get_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            Dictionary with counts by namespace and content type.
        """
        conn = self._get_conn()

        total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

        by_namespace = dict(conn.execute("""
            SELECT namespace, COUNT(*) FROM memories GROUP BY namespace
        """).fetchall())

        by_type = dict(conn.execute("""
            SELECT content_type, COUNT(*) FROM memories GROUP BY content_type
        """).fetchall())

        return {
            "total": total,
            "by_namespace": by_namespace,
            "by_content_type": by_type,
            "vector_search_available": self._vector_available,
            "db_path": str(self.db_path),
        }

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Module-level convenience functions
_default_store: Optional[VectorStore] = None


def get_store() -> VectorStore:
    """Get the default vector store instance."""
    global _default_store
    if _default_store is None:
        _default_store = VectorStore()
    return _default_store


def store_memory(
    content: str,
    embedding: list[float],
    namespace: str = "personal",
    content_type: str = "learning",
    metadata: Optional[dict] = None,
) -> str:
    """Store a memory in the default store."""
    return get_store().store(content, embedding, namespace, content_type, metadata)


def search_memories(
    query_embedding: list[float],
    namespace: str = "personal",
    limit: int = 10,
) -> list[dict]:
    """Search memories in the default store."""
    return get_store().search(query_embedding, namespace, limit=limit)
