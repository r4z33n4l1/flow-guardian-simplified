"""Embedding generation module for Flow Guardian.

Supports multiple embedding providers:
1. Gemini (default) - Fast, free tier, lightweight dependency
2. Local sentence-transformers - Works offline, no API needed

Provider selection:
- EMBEDDING_PROVIDER=gemini (default) - Uses Google Gemini API
- EMBEDDING_PROVIDER=local - Uses sentence-transformers locally
- EMBEDDING_PROVIDER=auto - Gemini if API key set, else local
"""
import os
from typing import Optional
from functools import lru_cache

# Provider configuration
PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "auto").lower()

# Gemini configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")  # Latest, best quality
GEMINI_OUTPUT_DIM = int(os.environ.get("GEMINI_EMBEDDING_DIM", "768"))  # Reduce from 3072 for efficiency

# Local model configuration
LOCAL_MODEL = os.environ.get("LOCAL_EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")

# Vector dimensions by model (native dimensions)
VECTOR_DIMS = {
    "text-embedding-004": 768,
    "gemini-embedding-001": 3072,  # Reduced to GEMINI_OUTPUT_DIM via MRL
    "BAAI/bge-large-en-v1.5": 768,
}

# Default/target dimension - we use 768 for storage efficiency
VECTOR_DIM = GEMINI_OUTPUT_DIM if "gemini-embedding" in GEMINI_MODEL else 768

# Lazy-loaded clients
_gemini_client = None
_local_model = None
_active_provider: Optional[str] = None


class EmbeddingError(Exception):
    """Base exception for embedding-related errors."""
    pass


class ProviderNotAvailableError(EmbeddingError):
    """No embedding provider is available."""
    pass


# ============ GEMINI PROVIDER ============

def _get_gemini_client():
    """Get or create Gemini client."""
    global _gemini_client
    if _gemini_client is None:
        if not GEMINI_API_KEY:
            raise EmbeddingError("GEMINI_API_KEY or GOOGLE_API_KEY not set")
        try:
            from google import genai
            _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        except ImportError:
            raise EmbeddingError("google-genai not installed. Install with: pip install google-genai")
    return _gemini_client


def _gemini_embed(text: str) -> list[float]:
    """Generate embedding using Gemini API."""
    client = _get_gemini_client()

    # Build config with output dimensionality if using gemini-embedding-001
    config = {}
    if "gemini-embedding" in GEMINI_MODEL and GEMINI_OUTPUT_DIM < 3072:
        config["output_dimensionality"] = GEMINI_OUTPUT_DIM

    result = client.models.embed_content(
        model=GEMINI_MODEL,
        contents=text,
        config=config if config else None,
    )
    # Result contains embeddings list, get first one
    if result.embeddings:
        return list(result.embeddings[0].values)
    return []


def _gemini_embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts using Gemini API."""
    client = _get_gemini_client()

    # Build config with output dimensionality if using gemini-embedding-001
    config = {}
    if "gemini-embedding" in GEMINI_MODEL and GEMINI_OUTPUT_DIM < 3072:
        config["output_dimensionality"] = GEMINI_OUTPUT_DIM

    result = client.models.embed_content(
        model=GEMINI_MODEL,
        contents=texts,
        config=config if config else None,
    )
    return [list(emb.values) for emb in result.embeddings]


def _gemini_available() -> bool:
    """Check if Gemini is available."""
    if not GEMINI_API_KEY:
        return False
    try:
        from google import genai
        return True
    except ImportError:
        return False


# ============ LOCAL PROVIDER (sentence-transformers) ============

def _get_local_model():
    """Lazy-load the sentence-transformer model."""
    global _local_model
    if _local_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            device = os.environ.get("EMBEDDING_DEVICE", "cpu")
            _local_model = SentenceTransformer(LOCAL_MODEL, device=device)
        except ImportError:
            raise EmbeddingError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers torch"
            )
    return _local_model


def _local_embed(text: str) -> list[float]:
    """Generate embedding using local model."""
    model = _get_local_model()
    embedding = model.encode(text, normalize_embeddings=True, show_progress_bar=False)
    return embedding.tolist()


def _local_embed_batch(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """Generate embeddings for multiple texts using local model."""
    model = _get_local_model()
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=batch_size
    )
    return embeddings.tolist()


def _local_available() -> bool:
    """Check if local model is available."""
    try:
        from sentence_transformers import SentenceTransformer
        return True
    except ImportError:
        return False


# ============ PROVIDER SELECTION ============

def _select_provider() -> str:
    """Select the best available provider."""
    global _active_provider

    if _active_provider:
        return _active_provider

    if PROVIDER == "gemini":
        if _gemini_available():
            _active_provider = "gemini"
        else:
            raise ProviderNotAvailableError("Gemini requested but not available (check GEMINI_API_KEY)")

    elif PROVIDER == "local":
        if _local_available():
            _active_provider = "local"
        else:
            raise ProviderNotAvailableError("Local model requested but sentence-transformers not installed")

    else:  # auto
        if _gemini_available():
            _active_provider = "gemini"
        elif _local_available():
            _active_provider = "local"
        else:
            raise ProviderNotAvailableError(
                "No embedding provider available. Either:\n"
                "  1. Set GEMINI_API_KEY for Gemini embeddings, or\n"
                "  2. Install sentence-transformers for local embeddings"
            )

    return _active_provider


# ============ PUBLIC API ============

def get_embedding(text: str) -> list[float]:
    """
    Generate a normalized embedding vector for the given text.

    Args:
        text: The text to embed.

    Returns:
        List of floats representing the embedding vector.

    Raises:
        EmbeddingError: If embedding generation fails.
    """
    if not text or not text.strip():
        return [0.0] * VECTOR_DIM

    # Truncate very long text
    max_chars = 8000
    if len(text) > max_chars:
        text = text[:max_chars]

    provider = _select_provider()

    try:
        if provider == "gemini":
            return _gemini_embed(text)
        else:
            return _local_embed(text)
    except Exception as e:
        raise EmbeddingError(f"Failed to generate embedding: {e}") from e


def get_embeddings_batch(texts: list[str], batch_size: int = 32) -> list[list[float]]:
    """
    Generate embeddings for multiple texts efficiently.

    Args:
        texts: List of texts to embed.
        batch_size: Batch size for local model (ignored for Gemini).

    Returns:
        List of embedding vectors.
    """
    if not texts:
        return []

    # Handle empty strings
    processed = []
    empty_indices = set()
    for i, text in enumerate(texts):
        if not text or not text.strip():
            empty_indices.add(i)
            processed.append("placeholder")
        else:
            t = text[:8000] if len(text) > 8000 else text
            processed.append(t)

    provider = _select_provider()

    try:
        if provider == "gemini":
            results = _gemini_embed_batch(processed)
        else:
            results = _local_embed_batch(processed, batch_size)

        # Replace empty text embeddings with zero vectors
        dim = len(results[0]) if results else VECTOR_DIM
        zero_vector = [0.0] * dim
        for i in empty_indices:
            results[i] = zero_vector

        return results

    except Exception as e:
        raise EmbeddingError(f"Failed to generate batch embeddings: {e}") from e


def is_available() -> bool:
    """Check if any embedding provider is available."""
    try:
        _select_provider()
        return True
    except ProviderNotAvailableError:
        return False


def get_model_info() -> dict:
    """Get information about the active embedding configuration."""
    try:
        provider = _select_provider()
    except ProviderNotAvailableError:
        provider = None

    model_name = GEMINI_MODEL if provider == "gemini" else LOCAL_MODEL if provider == "local" else None

    # Determine actual output dimension
    if provider == "gemini" and "gemini-embedding" in GEMINI_MODEL:
        dimension = GEMINI_OUTPUT_DIM  # Reduced via MRL
    elif model_name:
        dimension = VECTOR_DIMS.get(model_name, VECTOR_DIM)
    else:
        dimension = None

    return {
        "provider": provider,
        "model_name": model_name,
        "dimension": dimension,
        "gemini_available": _gemini_available(),
        "local_available": _local_available(),
        "configured_provider": PROVIDER,
    }


@lru_cache(maxsize=100)
def _cached_query_embedding(query: str) -> tuple:
    """Cache embeddings for repeated queries."""
    return tuple(get_embedding(query))


def get_query_embedding(query: str) -> list[float]:
    """Get embedding for a search query with caching."""
    return list(_cached_query_embedding(query))


def clear_cache():
    """Clear the query embedding cache."""
    _cached_query_embedding.cache_clear()
