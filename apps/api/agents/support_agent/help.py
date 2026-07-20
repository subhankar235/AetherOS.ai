import logging
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from core.config import settings
from core.exceptions import ExternalServiceError
from integrations.qdrant_client import qdrant_client
from services.rag.embedder import embedder_service
from agents.supervisor.prompts import INJECTION_GUARDRAIL

logger = logging.getLogger("agents.support_agent.help")

CLASSIFIER_PROMPT = """You are a support triage system. Classify the user's question into one of:

- **genuine_question**: A real how-to or product question that could be answered from documentation
- **feature_request**: The user is asking for a new feature or capability that doesn't exist yet
  ("can it do X", "I wish it could", "add support for", "why doesn't it have")
- **bug_report**: The user is reporting something broken or not working correctly
  ("X is broken", "Y doesn't work", "error when", "bug")
- **feedback**: General feedback, praise, or suggestions
- **other**: Anything else

Respond with the classification only.

""" + INJECTION_GUARDRAIL

ANSWER_PROMPT = """You are a product support agent. Answer the user's question based ONLY on the
provided support documentation passages. If the passages don't contain the answer, say so clearly
— do not fabricate functionality or guess.

Rules:
- Only use information present in the provided passages
- If no passage is relevant, say "I couldn't find documentation on that. Let me log this so our team can help."
- Be concise and helpful
- Cite the source document title for each claim

""" + INJECTION_GUARDRAIL


class QuestionClassification(BaseModel):
    type: str = Field(description="One of: genuine_question, feature_request, bug_report, feedback, other")


class SupportAnswer(BaseModel):
    answer: str = Field(description="The answer to the user's question")
    source_titles: list[str] = Field(default_factory=list, description="Source document titles")


async def answer_question(
    question: str,
    llm: Optional[ChatOpenAI] = None,
) -> dict[str, Any]:
    if llm is None:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY,
        )

    classification = await _classify_question(question, llm)
    logger.info(f"Support question classified as: {classification.type}")

    if classification.type == "feature_request":
        return _feedback_result(
            question,
            "feature_request",
            "That sounds like a great feature idea! I've logged your request for our product team to review. "
            "We'll consider it for a future update.",
        )

    if classification.type == "bug_report":
        return _feedback_result(
            question,
            "bug_report",
            "Thanks for reporting this! I've logged the details so our engineering team can investigate and fix it.",
        )

    if classification.type == "feedback":
        return _feedback_result(
            question,
            "feedback",
            "Thanks for your feedback! I've logged it and our team will take it into consideration.",
        )

    answer = await _retrieve_and_answer(question, llm)
    return {
        "agent": "support_agent",
        "status": "completed",
        "result": {
            "answer": answer.answer,
            "sources": answer.source_titles,
            "classification": classification.type,
        },
        "context_updates": {"last_support_query": question},
        "requires_approval": False,
    }


async def _classify_question(
    question: str,
    llm: ChatOpenAI,
) -> QuestionClassification:
    structured = llm.with_structured_output(QuestionClassification)
    try:
        return await structured.ainvoke([
            {"role": "system", "content": CLASSIFIER_PROMPT},
            {"role": "user", "content": f"Question: {question}"},
        ])
    except Exception as exc:
        logger.warning(f"Question classification failed, defaulting to genuine_question: {exc}")
        return QuestionClassification(type="genuine_question")


async def _retrieve_and_answer(
    question: str,
    llm: ChatOpenAI,
) -> SupportAnswer:
    try:
        embeddings = await embedder_service.embed_chunks([question])
        query_vector = embeddings[0]
    except Exception as exc:
        logger.exception(f"Failed to embed support question: {exc}")
        return SupportAnswer(answer="I'm having trouble searching the knowledge base right now. Please try again.")

    try:
        scored_points = await qdrant_client.search(
            collection_name=settings.QDRANT_COLLECTION_SUPPORT_KB,
            query_vector=query_vector,
            org_id="",
            access_level="",
            limit=5,
        )
    except Exception as exc:
        logger.exception(f"Support KB search failed: {exc}")
        return SupportAnswer(answer="I couldn't search the support documentation right now. Please try again.")

    if not scored_points:
        return SupportAnswer(
            answer="I couldn't find documentation on that. Let me log this so our team can help.",
        )

    passages = []
    source_titles = []
    seen_docs: set[str] = set()
    for pt in scored_points:
        payload = pt.payload or {}
        chunk_text = payload.get("chunk_text", "")
        title = payload.get("title", payload.get("source", "Support Doc"))
        passages.append(f"[Passage from '{title}']\n{chunk_text[:2000]}")
        if title not in seen_docs:
            seen_docs.add(title)
            source_titles.append(title)

    combined = "\n\n---\n\n".join(passages)
    answer = await _synthesize(question, combined, llm)
    return SupportAnswer(answer=answer, source_titles=source_titles)


async def _synthesize(
    question: str,
    context: str,
    llm: ChatOpenAI,
) -> str:
    try:
        response = await llm.ainvoke([
            {"role": "system", "content": ANSWER_PROMPT},
            {"role": "user", "content": f"Question: {question}\n\nSupport documentation:\n{context}"},
        ])
        return response.content
    except Exception as exc:
        logger.exception(f"Support answer synthesis failed: {exc}")
        chunks_count = context.count("[Passage from") if context else 0
        return f"Found {chunks_count} relevant articles but couldn't synthesize an answer."


def _feedback_result(
    question: str,
    feedback_type: str,
    message: str,
) -> dict[str, Any]:
    return {
        "agent": "support_agent",
        "status": "completed",
        "result": {
            "answer": message,
            "sources": [],
            "classification": feedback_type,
            "feedback_logged": True,
        },
        "context_updates": {"last_support_query": question},
        "requires_approval": False,
    }
