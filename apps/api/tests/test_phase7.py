import asyncio
import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from qdrant_client.http import models as qdrant_models
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exceptions import ValidationError
from integrations.qdrant_client import qdrant_client, get_allowed_access_levels
from models.knowledge_document import KnowledgeDocument
from services.ingestion.chunker import chunk_text
from services.ingestion.parser import parse_document, parse_csv
from services.rag.embedder import embedder_service
from workers.kb_indexer import index_document_task
from core.deps import get_current_user
from db.session import get_db


# ==========================================
# 1. Access Level Hierarchy Helper Tests
# ==========================================
def test_allowed_access_levels():
    assert "Admin" in get_allowed_access_levels("owner")
    assert "Owner" in get_allowed_access_levels("owner")
    assert "Member" in get_allowed_access_levels("admin")
    assert "Owner" not in get_allowed_access_levels("admin")
    assert "Admin" not in get_allowed_access_levels("member")
    assert "Viewer" in get_allowed_access_levels("member")
    assert get_allowed_access_levels("viewer") == ["Viewer", "viewer"]


# ==========================================
# 2. Document Parser Tests
# ==========================================
def test_parse_txt_md():
    text_bytes = b"Hello world, this is raw text."
    result = parse_document(file_bytes=text_bytes, file_name="doc.txt")
    assert result == "Hello world, this is raw text."


def test_parse_csv():
    # CSV with headers
    csv_bytes = b"title,author,year\nBook A,Author X,2021\nBook B,Author Y,2022"
    result = parse_csv(csv_bytes)
    assert "Row 1: title: Book A, author: Author X, year: 2021" in result
    assert "Row 2: title: Book B, author: Author Y, year: 2022" in result

    # CSV without headers (empty values / invalid headers)
    csv_bytes_no_headers = b",Val A2,Val A3\nVal B1,Val B2,Val B3"
    result_no_headers = parse_csv(csv_bytes_no_headers)
    assert "Row 1: Val A2, Val A3" in result_no_headers
    assert "Row 2: Val B1, Val B2, Val B3" in result_no_headers


@patch("services.ingestion.parser.fitz.open")
def test_parse_pdf(mock_fitz_open):
    # Setup mock PDF document and pages
    mock_doc = MagicMock()
    mock_page_1 = MagicMock()
    mock_page_1.get_text.return_value = "Page 1 Content."
    mock_page_2 = MagicMock()
    mock_page_2.get_text.return_value = "Page 2 Content."
    mock_doc.__iter__.return_value = [mock_page_1, mock_page_2]
    mock_fitz_open.return_value = mock_doc

    result = parse_document(file_bytes=b"dummy_pdf_bytes", file_name="test.pdf")
    assert "Page 1 Content." in result
    assert "Page 2 Content." in result
    mock_fitz_open.assert_called_once()


@patch("services.ingestion.parser.Document")
def test_parse_docx(mock_docx_document):
    # Setup mock paragraphs and tables
    mock_doc = MagicMock()
    mock_p1 = MagicMock()
    mock_p1.text = "Paragraph 1 Content."
    mock_p2 = MagicMock()
    mock_p2.text = "Paragraph 2 Content."
    mock_doc.paragraphs = [mock_p1, mock_p2]
    
    mock_table = MagicMock()
    mock_cell_1 = MagicMock()
    mock_cell_1.text = "Cell A"
    mock_cell_2 = MagicMock()
    mock_cell_2.text = "Cell B"
    mock_row = MagicMock()
    mock_row.cells = [mock_cell_1, mock_cell_2]
    mock_table.rows = [mock_row]
    mock_doc.tables = [mock_table]

    mock_docx_document.return_value = mock_doc

    result = parse_document(file_bytes=b"dummy_docx_bytes", file_name="test.docx")
    assert "Paragraph 1 Content." in result
    assert "Paragraph 2 Content." in result
    assert "Cell A | Cell B" in result


def test_parse_validation_error():
    with pytest.raises(ValidationError):
        parse_document()


# ==========================================
# 3. Chunker Tests
# ==========================================
def test_chunker_splitting():
    text = (
        "Sentence one. Sentence two? Sentence three! "
        "Another sentence here to make the test realistic and fill some token space. "
        "And another one here."
    )
    # Perform chunking with low limits to trigger splitting
    chunks = chunk_text(text, min_chunk_size=10, max_chunk_size=20, overlap_size=5)
    assert len(chunks) >= 1
    # Check that sentences are reconstructed
    assert any("Sentence one." in chunk for chunk in chunks)


def test_chunker_empty_input():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


# ==========================================
# 4. Embedder Service Tests
# ==========================================
@pytest.mark.asyncio
@patch("services.rag.embedder.AsyncOpenAI")
async def test_embedder_service(mock_openai_class):
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    # Mock embeddings.create response
    mock_response = MagicMock()
    mock_item_1 = MagicMock()
    mock_item_1.embedding = [0.1] * 3072
    mock_item_2 = MagicMock()
    mock_item_2.embedding = [0.2] * 3072
    mock_response.data = [mock_item_1, mock_item_2]

    # Setup the async call
    mock_client.embeddings.create = AsyncMock(return_value=mock_response)

    texts = ["Chunk 1 text content", "Chunk 2 text content"]
    embeddings = await embedder_service.embed_chunks(texts, batch_size=100)

    assert len(embeddings) == 2
    assert embeddings[0] == [0.1] * 3072
    assert embeddings[1] == [0.2] * 3072
    mock_client.embeddings.create.assert_called_once_with(
        input=texts,
        model=settings.OPENAI_EMBEDDING_MODEL
    )


# ==========================================
# 5. Qdrant Client Wrapper Tests
# ==========================================
@pytest.mark.asyncio
@patch("integrations.qdrant_client.AsyncQdrantClient")
async def test_qdrant_client_init_collections(mock_qdrant_class):
    mock_client = AsyncMock()
    mock_qdrant_class.return_value = mock_client
    
    # Force collections to not exist
    mock_client.collection_exists.return_value = False

    wrapper = qdrant_client
    # Reset wrapper internal client
    wrapper._client = None

    await wrapper.init_collections()

    assert mock_client.collection_exists.call_count == 3
    assert mock_client.create_collection.call_count == 3
    
    # Assert company_memory creates payload indexes
    mock_client.create_payload_index.assert_any_call(
        collection_name=settings.QDRANT_COLLECTION_COMPANY_MEMORY,
        field_name="org_id",
        field_schema=qdrant_models.PayloadSchemaType.KEYWORD
    )
    mock_client.create_payload_index.assert_any_call(
        collection_name=settings.QDRANT_COLLECTION_COMPANY_MEMORY,
        field_name="access_level",
        field_schema=qdrant_models.PayloadSchemaType.KEYWORD
    )


@pytest.mark.asyncio
@patch("integrations.qdrant_client.AsyncQdrantClient")
async def test_qdrant_client_search_security_filter(mock_qdrant_class):
    mock_client = AsyncMock()
    mock_qdrant_class.return_value = mock_client
    
    wrapper = qdrant_client
    wrapper._client = mock_client

    query_vector = [0.1] * 3072
    org_id = "org_test_123"
    access_level = "member"

    # Search on company_memory should inject org_id and access_level must conditions
    await wrapper.search(
        collection_name=settings.QDRANT_COLLECTION_COMPANY_MEMORY,
        query_vector=query_vector,
        org_id=org_id,
        access_level=access_level,
        limit=5
    )

    print("MOCK CLIENT CALLS:", mock_client.mock_calls)
    print("MOCK QUERY_POINTS CALLS:", mock_client.query_points.mock_calls)

    mock_client.query_points.assert_called_once()
    _, kwargs = mock_client.query_points.call_args
    query_filter = kwargs.get("query_filter")

    assert query_filter is not None
    assert isinstance(query_filter, qdrant_models.Filter)
    
    # Check that must conditions contains org_id and access_level MatchAny
    must_conditions = query_filter.must
    assert len(must_conditions) == 2
    
    org_condition = must_conditions[0]
    assert org_condition.key == "org_id"
    assert org_condition.match.value == org_id

    access_condition = must_conditions[1]
    assert access_condition.key == "access_level"
    assert "Member" in access_condition.match.any
    assert "Viewer" in access_condition.match.any


@pytest.mark.asyncio
@patch("integrations.qdrant_client.AsyncQdrantClient")
async def test_qdrant_client_search_other_collection(mock_qdrant_class):
    mock_client = AsyncMock()
    mock_qdrant_class.return_value = mock_client
    
    wrapper = qdrant_client
    wrapper._client = mock_client

    query_vector = [0.1] * 3072

    # Search on support_kb should NOT inject security filters because it is a global collection
    await wrapper.search(
        collection_name=settings.QDRANT_COLLECTION_SUPPORT_KB,
        query_vector=query_vector,
        org_id="some_org",
        access_level="member",
        limit=5
    )

    mock_client.query_points.assert_called_once()
    _, kwargs = mock_client.query_points.call_args
    query_filter = kwargs.get("query_filter")
    # No filter should be passed since no extra filter was provided and it's not company_memory
    assert query_filter is None


# ==========================================
# 6. Celery Task Status Transition Tests
# ==========================================
@patch("workers.kb_indexer.AsyncSessionLocal")
@patch("services.ingestion.parser.parse_document")
@patch("services.ingestion.chunker.chunk_text")
@patch("services.rag.embedder.embedder_service.embed_chunks")
@patch("integrations.qdrant_client.qdrant_client.upsert")
def test_kb_indexer_celery_task_success(
    mock_qdrant_upsert,
    mock_embed_chunks,
    mock_chunk_text,
    mock_parse_document,
    mock_session_class
):
    # Setup mock database session
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session_class.return_value = mock_session

    doc_id = uuid.uuid4()
    mock_doc = KnowledgeDocument(
        id=doc_id,
        org_id="org_abc",
        access_level="Member",
        file_path_or_url="C:/path/to/test.txt",
        indexing_status="queued"
    )

    # Database query mock returning our document
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_doc
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Ingestion steps mocks
    mock_parse_document.return_value = "Extracted text content."
    mock_chunk_text.return_value = ["Extracted text content."]
    mock_embed_chunks.return_value = [[0.1] * 3072]
    mock_qdrant_upsert.return_value = MagicMock()

    # Trigger task synchronously
    index_document_task(str(doc_id))

    # Assertions
    # Status should transition to processing, then ready
    assert mock_doc.indexing_status == "ready"
    assert mock_session.commit.call_count == 2
    mock_qdrant_upsert.assert_called_once()


@patch("workers.kb_indexer.AsyncSessionLocal")
@patch("services.ingestion.parser.parse_document")
def test_kb_indexer_celery_task_failure(
    mock_parse_document,
    mock_session_class
):
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session_class.return_value = mock_session

    doc_id = uuid.uuid4()
    mock_doc = KnowledgeDocument(
        id=doc_id,
        org_id="org_abc",
        access_level="Member",
        file_path_or_url="C:/path/to/test.txt",
        indexing_status="queued"
    )

    # Database query mock returning our document
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_doc
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Force parser to fail
    mock_parse_document.side_effect = RuntimeError("Parser crashed")

    index_document_task(str(doc_id))

    # Status should transition to processing, then failed
    assert mock_doc.indexing_status == "failed"
    assert mock_session.commit.call_count == 2


# ==========================================
# 7. Knowledge Base Router API Tests
# ==========================================
from fastapi.testclient import TestClient
from main import app
from models.user import User, UserRole

client = TestClient(app)


@pytest.fixture
def override_router_deps():
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.__aenter__.return_value = mock_session

    mock_user = User(
        id=uuid.uuid4(),
        clerk_user_id="clerk_test_123",
        email="test_user@example.com",
        role=UserRole.MEMBER
    )

    async def _get_db():
        yield mock_session

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = _get_db

    yield mock_session, mock_user

    app.dependency_overrides.clear()


def test_route_upload_document_success(override_router_deps):
    mock_session, mock_user = override_router_deps

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch("workers.kb_indexer.index_document_task.delay") as mock_celery_task:
        response = client.post(
            "/knowledge/upload",
            data={
                "title": "API Upload Test",
                "access_level": "Member",
                "org_id": "org_test"
            },
            files={"file": ("test_upload.txt", b"API upload content bytes")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "API Upload Test"
        assert data["org_id"] == "org_test"
        assert data["indexing_status"] == "queued"
        
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_celery_task.assert_called_once()


def test_route_list_documents(override_router_deps):
    mock_session, mock_user = override_router_deps

    doc_id_1 = uuid.uuid4()
    doc_id_2 = uuid.uuid4()
    mock_docs = [
        KnowledgeDocument(
            id=doc_id_1,
            org_id="org_test",
            title="Doc A",
            source_type="upload",
            file_path_or_url="path/A.txt",
            doc_type="txt",
            access_level="Member",
            indexing_status="ready",
            created_at=datetime.now(timezone.utc)
        ),
        KnowledgeDocument(
            id=doc_id_2,
            org_id="org_test",
            title="Doc B",
            source_type="upload",
            file_path_or_url="path/B.txt",
            doc_type="txt",
            access_level="Viewer",
            indexing_status="ready",
            created_at=datetime.now(timezone.utc)
        )
    ]

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_docs
    mock_session.execute = AsyncMock(return_value=mock_result)

    response = client.get("/knowledge/documents?org_id=org_test")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Doc A"
    assert data[1]["title"] == "Doc B"


def test_route_delete_document_success(override_router_deps):
    mock_session, mock_user = override_router_deps

    doc_id = uuid.uuid4()
    mock_doc = KnowledgeDocument(
        id=doc_id,
        org_id="org_test",
        title="Doc to Delete",
        source_type="upload",
        file_path_or_url="path/delete.txt",
        doc_type="txt",
        access_level="Member",
        indexing_status="ready"
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_doc
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch("os.path.exists", return_value=False), \
         patch("integrations.qdrant_client.AsyncQdrantClient") as mock_qdrant_class:
         
        mock_client = AsyncMock()
        mock_qdrant_class.return_value = mock_client
        qdrant_client._client = mock_client

        response = client.delete(f"/knowledge/documents/{doc_id}?org_id=org_test")

        assert response.status_code == 200
        assert response.json()["detail"] == "Document successfully deleted"
        
        mock_session.delete.assert_called_once_with(mock_doc)
        mock_session.commit.assert_called_once()
        mock_client.delete.assert_called_once()


def test_route_query_knowledge_success(override_router_deps):
    mock_session, mock_user = override_router_deps

    mock_scored_point = MagicMock()
    mock_scored_point.score = 0.95
    mock_scored_point.payload = {"chunk_text": "Answer snippet", "source": "A.txt"}

    with patch("services.rag.embedder.embedder_service.embed_chunks") as mock_embed_chunks, \
         patch("integrations.qdrant_client.qdrant_client.search") as mock_qdrant_search:
         
        mock_embed_chunks.return_value = [[0.1] * 3072]
        mock_qdrant_search.return_value = [mock_scored_point]

        response = client.post(
            "/knowledge/query",
            data={
                "query": "What is the return policy?",
                "limit": 5,
                "org_id": "org_test"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["score"] == 0.95
        assert data[0]["payload"]["chunk_text"] == "Answer snippet"
        
        mock_embed_chunks.assert_called_once_with(["What is the return policy?"])
        mock_qdrant_search.assert_called_once()

