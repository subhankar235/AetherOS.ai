import logging
from typing import Optional, List, Union

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from core.config import settings

logger = logging.getLogger("integrations.qdrant_client")


def get_allowed_access_levels(user_access_level: str) -> List[str]:
    """
    Returns the list of allowed document access levels based on the user's access level.
    Hierarchical access levels: Owner > Admin > Member > Viewer.
    Normalizes input to handle casing variants.
    """
    lvl = user_access_level.strip().lower()

    if lvl == "owner":
        return ["Owner", "Admin", "Member", "Viewer", "owner", "admin", "member", "viewer"]
    elif lvl == "admin":
        return ["Admin", "Member", "Viewer", "admin", "member", "viewer"]
    elif lvl == "member":
        return ["Member", "Viewer", "member", "viewer"]
    else:  # viewer or lower/unknown
        return ["Viewer", "viewer"]


class QdrantClientWrapper:
    def __init__(self):
        self._client: Optional[AsyncQdrantClient] = None

    def get_client(self) -> AsyncQdrantClient:
        if self._client is None:
            self._client = AsyncQdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
            )
        return self._client

    async def init_collections(self):
        """
        Initializes the three Qdrant collections on startup or migration:
        company_memory, research_cache, support_kb.
        All collections are set to 3072 dimensions matching OpenAI text-embedding-3-large
        using Cosine distance.
        """
        client = self.get_client()
        collections_to_create = [
            settings.QDRANT_COLLECTION_COMPANY_MEMORY,
            settings.QDRANT_COLLECTION_RESEARCH_CACHE,
            settings.QDRANT_COLLECTION_SUPPORT_KB,
        ]

        vector_size = 3072

        for collection in collections_to_create:
            try:
                exists = await client.collection_exists(collection)
                if not exists:
                    logger.info(f"Creating Qdrant collection: {collection}")
                    await client.create_collection(
                        collection_name=collection,
                        vectors_config=models.VectorParams(
                            size=vector_size,
                            distance=models.Distance.COSINE
                        )
                    )

                    # Create payload indexes for company_memory
                    if collection == settings.QDRANT_COLLECTION_COMPANY_MEMORY:
                        await client.create_payload_index(
                            collection_name=collection,
                            field_name="org_id",
                            field_schema=models.PayloadSchemaType.KEYWORD
                        )
                        await client.create_payload_index(
                            collection_name=collection,
                            field_name="access_level",
                            field_schema=models.PayloadSchemaType.KEYWORD
                        )
                else:
                    logger.debug(f"Qdrant collection already exists: {collection}")
            except Exception as e:
                logger.exception(f"Failed to initialize Qdrant collection {collection}: {str(e)}")
                raise

    async def upsert(
        self,
        collection_name: str,
        points: List[models.PointStruct]
    ) -> models.UpdateResult:
        """
        Wrapper to upsert points into a Qdrant collection.
        """
        client = self.get_client()
        try:
            return await client.upsert(
                collection_name=collection_name,
                points=points
            )
        except Exception as e:
            logger.exception(f"Qdrant upsert failed for collection {collection_name}: {str(e)}")
            raise

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        org_id: str,
        access_level: str,
        filter_extra: Optional[Union[models.Filter, models.Condition]] = None,
        limit: int = 5
    ) -> List[models.ScoredPoint]:
        """
        Wrapper to search points in a Qdrant collection.
        Enforces tenant isolation and access control checks server-side for 'company_memory'.
        Requires org_id and access_level arguments to prevent callers from omitting filters.
        """
        client = self.get_client()
        must_conditions = []

        # Apply access control for company_memory
        if collection_name == settings.QDRANT_COLLECTION_COMPANY_MEMORY:
            must_conditions.append(
                models.FieldCondition(key="org_id", match=models.MatchValue(value=org_id))
            )
            allowed_levels = get_allowed_access_levels(access_level)
            must_conditions.append(
                models.FieldCondition(key="access_level", match=models.MatchAny(any=allowed_levels))
            )

        # Merge with custom filter_extra if provided
        if filter_extra is not None:
            if isinstance(filter_extra, models.Filter):
                if filter_extra.must:
                    if isinstance(filter_extra.must, list):
                        must_conditions.extend(filter_extra.must)
                    else:
                        must_conditions.append(filter_extra.must)
                query_filter = models.Filter(
                    must=must_conditions,
                    should=filter_extra.should,
                    must_not=filter_extra.must_not
                )
            else:
                must_conditions.append(filter_extra)
                query_filter = models.Filter(must=must_conditions)
        else:
            query_filter = models.Filter(must=must_conditions) if must_conditions else None

        try:
            result = await client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=limit
            )
            return result.points
        except Exception as e:
            logger.exception(f"Qdrant search failed for collection {collection_name}: {str(e)}")
            raise

    async def delete(
        self,
        collection_name: str,
        ids: List[Union[int, str]]
    ) -> models.UpdateResult:
        """
        Wrapper to delete points from a Qdrant collection.
        """
        client = self.get_client()
        try:
            return await client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(points=ids)  # type: ignore[arg-type]
            )
        except Exception as e:
            logger.exception(f"Qdrant delete failed for collection {collection_name}: {str(e)}")
            raise


# Export a singleton instance of the wrapper
qdrant_client = QdrantClientWrapper()
