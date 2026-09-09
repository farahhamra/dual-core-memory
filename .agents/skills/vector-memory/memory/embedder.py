import requests
from typing import List
from .config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL, EMBEDDING_DIMENSION

class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
    pass

def get_embedding(text: str) -> List[float]:
    """
    Generate a 768-dimensional embedding vector for given text using local Ollama.
    """
    if not text or not isinstance(text, str) or not text.strip():
        raise ValueError("Text to embed must be a non-empty string.")

    endpoint = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {
        "model": OLLAMA_EMBED_MODEL,
        "prompt": text.strip(),
    }

    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )
    except requests.exceptions.ConnectionError as err:
        raise EmbeddingError(
            f"Failed to connect to Ollama at {OLLAMA_BASE_URL}. "
            f"Please ensure Ollama is running (`ollama serve`) and the model is pulled (`ollama pull {OLLAMA_EMBED_MODEL}`)."
        ) from err
    except requests.exceptions.Timeout as err:
        raise EmbeddingError(f"Ollama request timed out after 30s at {OLLAMA_BASE_URL}.") from err
    except Exception as err:
        raise EmbeddingError(f"Unexpected error communicating with Ollama: {err}") from err

    if response.status_code != 200:
        raise EmbeddingError(
            f"Ollama embedding request failed with status {response.status_code}: {response.text}"
        )

    try:
        data = response.json()
    except Exception as err:
        raise EmbeddingError(f"Invalid JSON returned from Ollama: {response.text}") from err

    embedding = data.get("embedding")
    if not isinstance(embedding, list) or len(embedding) == 0:
        raise EmbeddingError(f"Missing or invalid 'embedding' field in Ollama response: {data}")

    if len(embedding) != EMBEDDING_DIMENSION:
        import sys
        print(
            f"[Warning] Expected dimension {EMBEDDING_DIMENSION}, received {len(embedding)}",
            file=sys.stderr,
        )

    return [float(x) for x in embedding]

def get_batch_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a list of texts sequentially."""
    return [get_embedding(t) for t in texts if t and t.strip()]
