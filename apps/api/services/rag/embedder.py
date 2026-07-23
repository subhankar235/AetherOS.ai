import logging
from typing import List, Optional

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings

logger = logging.getLogger("services.rag.embedder")

embed_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)


class EmbedderService:
    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None

    def get_client(self) -> AsyncOpenAI:
        if self._client is None:
            kwargs = {"api_key": settings.OPENAI_API_KEY}
            if getattr(settings, "openai_base_url", None):
                kwargs["base_url"] = settings.openai_base_url
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    @embed_retry
    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        client = self.get_client()
        try:
            response = await client.embeddings.create(
                input=texts,
                model=settings.OPENAI_EMBEDDING_MODEL
            )
            return [item.embedding for item in response.data]
        except Exception as exc:
            logger.warning(f"OpenAI embedding batch failed: {exc}. Returning zero vectors...")
            # Fallback to zero vectors of dimension 1536 so vector search safely falls back
            return [[0.0] * 1536 for _ in texts]

    async def embed_chunks(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generates embeddings for a list of texts by batching calls to the OpenAI Embedding API.
        Default batch size is 100 texts per API call.
        """
        if not texts:
            return []

        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                batch_embeddings = await self._embed_batch(batch)
                embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch starting at index {i}: {str(e)}")
                raise

        return embeddings


# Export a singleton instance of the service
embedder_service = EmbedderService()
