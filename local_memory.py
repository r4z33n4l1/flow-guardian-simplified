"""Local Memory Service for Flow Guardian.

Replaces Backboard.io with a fully self-hosted solution using:
- SQLite + sqlite-vec for vector storage
- sentence-transformers for local embedding generation
- Cerebras for LLM synthesis (already integrated)

This provides complete offline capability while maintaining the same API
surface as the Backboard client.
"""
import asyncio
import os
from datetime import datetime
from typing import Optional

import embeddings
import vector_storage
import cerebras_client


class LocalMemoryError(Exception):
    """Base exception for local memory errors."""
    pass


class LocalMemoryService:
    """
    Local memory service that replaces Backboard.io.

    Provides semantic search and LLM synthesis using local embeddings
    and the vector store, with Cerebras for response generation.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the local memory service.

        Args:
            db_path: Optional path to the SQLite database.
        """
        self._store: Optional[vector_storage.VectorStore] = None
        self._db_path = db_path
        self._embedding_available: Optional[bool] = None

    @property
    def store(self) -> vector_storage.VectorStore:
        """Lazy-load the vector store."""
        if self._store is None:
            self._store = vector_storage.VectorStore(self._db_path)
        return self._store

    def is_available(self) -> bool:
        """Check if the local memory service is available."""
        if self._embedding_available is None:
            self._embedding_available = embeddings.is_available()
        return self._embedding_available

    async def store_message(
        self,
        content: str,
        namespace: str = "personal",
        content_type: str = "learning",
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Store content with automatic embedding generation.

        This is the primary storage method, replacing Backboard's store_message.

        Args:
            content: The text content to store.
            namespace: Storage namespace ('personal' or 'team').
            content_type: Type of content ('learning', 'session', 'document').
            metadata: Optional metadata dictionary.

        Returns:
            Memory ID.
        """
        # Generate embedding
        try:
            embedding = await asyncio.get_event_loop().run_in_executor(
                None, embeddings.get_embedding, content
            )
        except embeddings.EmbeddingError as e:
            # Store without embedding if generation fails
            print(f"Warning: Embedding generation failed, storing without vector: {e}")
            embedding = []

        # Store in vector database
        memory_id = self.store.store(
            content=content,
            embedding=embedding,
            namespace=namespace,
            content_type=content_type,
            metadata=metadata,
        )

        return memory_id

    async def recall(
        self,
        query: str,
        namespace: str = "personal",
        limit: int = 5,
        synthesize: bool = True,
    ) -> str:
        """
        Semantic recall with LLM synthesis.

        This replaces Backboard's recall function. Searches the vector store
        for relevant content and uses Cerebras to synthesize a response.

        Args:
            query: Natural language query.
            namespace: Namespace to search in.
            limit: Maximum number of results to retrieve.
            synthesize: If True, use LLM to synthesize response. If False, return raw results.

        Returns:
            Synthesized response string (or formatted raw results if synthesize=False).
        """
        results = []

        # Try vector search first
        if self.is_available():
            try:
                query_embedding = await asyncio.get_event_loop().run_in_executor(
                    None, embeddings.get_query_embedding, query
                )
                results = self.store.search(
                    query_embedding=query_embedding,
                    namespace=namespace,
                    limit=limit,
                )
            except Exception as e:
                print(f"Vector search failed: {e}")

        # Fall back to keyword search if vector search returns nothing
        if not results:
            results = self.store.keyword_search(
                query=query,
                namespace=namespace,
                limit=limit,
            )

        if not results:
            return "No relevant context found in memory."

        # Format results
        context_parts = []
        for r in results:
            meta = r.get("metadata", {})
            tags = meta.get("tags", [])
            tag_str = f" (tags: {', '.join(tags)})" if tags else ""

            content_type = r.get("content_type", "unknown")
            content = r.get("content", "")

            context_parts.append(f"[{content_type}] {content}{tag_str}")

        context = "\n\n".join(context_parts)

        if not synthesize:
            return context

        # Synthesize response using Cerebras
        prompt = f"""Based on the following stored context, answer this query:

Query: {query}

Relevant Context:
{context}

Provide a helpful, synthesized response based on the context above.
If the context doesn't fully answer the query, say so.
Be concise and actionable."""

        system = """You are a helpful assistant with access to stored memories and learnings.
Synthesize relevant information to answer queries accurately.
Focus on the most relevant parts of the context."""

        try:
            response = await cerebras_client.quick_answer(prompt, system=system)
            return response
        except Exception as e:
            # Return raw context if synthesis fails
            print(f"Synthesis failed: {e}")
            return f"Found relevant context (synthesis failed):\n\n{context}"

    async def query_team(self, query: str, limit: int = 5) -> str:
        """
        Query team memory.

        Equivalent to Backboard's query_team_memory.

        Args:
            query: Search query.
            limit: Maximum results.

        Returns:
            Synthesized response from team knowledge.
        """
        return await self.recall(query, namespace="team", limit=limit)

    # ============ Convenience methods matching Backboard API ============

    async def store_learning(
        self,
        text: str,
        tags: Optional[list[str]] = None,
        author: Optional[str] = None,
    ) -> str:
        """
        Store a learning/insight.

        Args:
            text: The learning text.
            tags: Optional tags.
            author: Optional author name.

        Returns:
            Memory ID.
        """
        metadata = {
            "tags": tags or [],
            "timestamp": datetime.now().isoformat(),
        }
        if author:
            metadata["author"] = author

        content = f"**Learning:** {text}"
        return await self.store_message(
            content=content,
            namespace="personal",
            content_type="learning",
            metadata=metadata,
        )

    async def store_team_learning(
        self,
        text: str,
        author: str,
        tags: Optional[list[str]] = None,
    ) -> str:
        """
        Store a team learning.

        Args:
            text: The learning text.
            author: Who shared the learning.
            tags: Optional tags.

        Returns:
            Memory ID.
        """
        metadata = {
            "tags": tags or [],
            "author": author,
            "timestamp": datetime.now().isoformat(),
        }

        content = f"**Team Learning** (from {author}): {text}"
        return await self.store_message(
            content=content,
            namespace="team",
            content_type="learning",
            metadata=metadata,
        )

    async def store_session(self, session: dict) -> str:
        """
        Store a session checkpoint.

        Args:
            session: Session data dictionary with context, git state, etc.

        Returns:
            Memory ID.
        """
        context = session.get("context", {})
        git = session.get("git", {})

        # Build content string
        content_parts = [f"**Session:** {context.get('summary', 'unknown')}"]
        content_parts.append(f"Branch: {git.get('branch', 'unknown')}")

        if context.get("decisions"):
            content_parts.append(f"Decisions: {', '.join(context['decisions'])}")
        if context.get("next_steps"):
            content_parts.append(f"Next steps: {', '.join(context['next_steps'])}")
        if context.get("blockers"):
            content_parts.append(f"Blockers: {', '.join(context['blockers'])}")

        content = "\n".join(content_parts)

        metadata = {
            "session_id": session.get("id"),
            "branch": git.get("branch"),
            "files": context.get("files", []),
            "tags": session.get("metadata", {}).get("tags", []),
            "timestamp": session.get("timestamp") or datetime.now().isoformat(),
        }

        return await self.store_message(
            content=content,
            namespace="personal",
            content_type="session",
            metadata=metadata,
        )

    async def get_restoration_context(self, changes_summary: str) -> str:
        """
        Generate a welcome-back message using stored context.

        Args:
            changes_summary: Summary of what changed while away.

        Returns:
            Natural language restoration message.
        """
        query = f"""Based on my most recent context snapshot, generate a concise "welcome back" summary.

Also consider these changes that happened while I was away:
{changes_summary}

Format:
1. What I was working on (1 sentence)
2. My hypothesis (if any)
3. What changed while away (highlight if it affects my work!)
4. Suggested next action

Keep it under 10 lines. Be direct."""

        return await self.recall(query, synthesize=True)

    # ============ Search without synthesis ============

    async def search_raw(
        self,
        query: str,
        namespace: str = "personal",
        content_type: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Search for memories without LLM synthesis.

        Useful for getting raw results to process further.

        Args:
            query: Search query.
            namespace: Namespace to search.
            content_type: Optional filter by type.
            limit: Maximum results.

        Returns:
            List of matching memories.
        """
        results = []

        # Try vector search
        if self.is_available():
            try:
                query_embedding = await asyncio.get_event_loop().run_in_executor(
                    None, embeddings.get_query_embedding, query
                )
                results = self.store.search(
                    query_embedding=query_embedding,
                    namespace=namespace,
                    content_type=content_type,
                    limit=limit,
                )
            except Exception as e:
                print(f"Vector search failed: {e}")

        # Fall back to keyword search
        if not results:
            results = self.store.keyword_search(
                query=query,
                namespace=namespace,
                content_type=content_type,
                limit=limit,
            )

        return results

    def get_recent(
        self,
        namespace: str = "personal",
        content_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """
        Get recent memories without search.

        Args:
            namespace: Namespace to list from.
            content_type: Optional filter by type.
            limit: Maximum results.

        Returns:
            List of recent memories.
        """
        return self.store.list_recent(
            namespace=namespace,
            content_type=content_type,
            limit=limit,
        )

    def get_stats(self) -> dict:
        """Get storage statistics."""
        return self.store.get_stats()

    def close(self):
        """Close the service and release resources."""
        if self._store:
            self._store.close()
            self._store = None


# ============ Module-level singleton ============

_service: Optional[LocalMemoryService] = None


def get_service() -> LocalMemoryService:
    """Get the singleton LocalMemoryService instance."""
    global _service
    if _service is None:
        _service = LocalMemoryService()
    return _service


# ============ Health check ============

async def health_check() -> dict:
    """
    Check the health of the local memory service.

    Returns:
        Dictionary with health status information.
    """
    service = get_service()

    return {
        "available": True,
        "embedding_available": service.is_available(),
        "vector_search_available": service.store._vector_available,
        "embedding_info": embeddings.get_model_info(),
        "storage_stats": service.get_stats(),
    }


# ============ Async convenience wrappers ============

async def store_learning(text: str, tags: list[str] = None) -> str:
    """Store a learning."""
    return await get_service().store_learning(text, tags)


async def recall(query: str, namespace: str = "personal") -> str:
    """Recall from memory."""
    return await get_service().recall(query, namespace)


async def query_team(query: str) -> str:
    """Query team memory."""
    return await get_service().query_team(query)
