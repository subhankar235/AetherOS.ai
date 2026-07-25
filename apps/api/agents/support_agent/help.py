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

CLASSIFIER_PROMPT = """You are a support triage system for AetherOS.ai. Classify the user's question into one of:

- **identity_or_greeting**: Questions about identity ("Who are you?", "What can you do?", "How are you?", "How can you help me?", "What features do you have?"), greetings ("hello", "hi"), jokes, or general conversational chat
- **general_conversation**: Out-of-box questions, technical explanations ("Explain OAuth", "What's LangGraph"), general knowledge, advice, jokes, chitchat, or any question not requiring inbox/calendar actions.
- **genuine_question**: A real how-to or product question that could be answered from documentation
- **feature_request**: The user is asking for a new feature or capability that doesn't exist yet
  ("can it do X", "I wish it could", "add support for", "why doesn't it have")
- **bug_report**: The user is reporting something broken or not working correctly
  ("X is broken", "Y doesn't work", "error when", "bug")
- **feedback**: General feedback, praise, or suggestions
- **other**: Anything else

Respond with the classification only.

""" + INJECTION_GUARDRAIL

IDENTITY_PROMPT = """You are AetherOS.ai, an AI-powered executive assistant operating system designed for founders, executives, and professionals.
You operate conversationally by voice or text.
Your key features and capabilities include:
1. **Inbox Search & Triage**: Find, read, and summarize emails from Gmail/inbox in real time.
2. **AI Email Reply Drafting**: Draft context-aware, polished email replies grounded in your inbox and company knowledge base.
3. **Calendar & Meeting Scheduling**: Schedule meetings, check attendee availability, avoid double-booking, and create Google Meet links.
4. **Company Memory & Knowledge Base Query**: Retrieve answers from company documentation and policies.
5. **Market & Company Research**: Conduct comprehensive research on companies and industries.
6. **Voice Assistant**: Natural hands-free conversational voice interaction powered by ElevenLabs STT & TTS.

Rules:
- ALWAYS identify yourself as **AetherOS.ai** when introducing yourself or answering "Who are you?", "What can you do?", "How are you?", "How can you help me?", "What features do you have?".
- Generate dynamic, conversational, warm, and natural responses. NEVER use static or hardcoded template messages.
- Keep responses concise, clear, and direct (2-4 natural sentences).
""" + INJECTION_GUARDRAIL

GENERAL_CONVERSATION_PROMPT = """You are AetherOS.ai, an intelligent AI executive assistant.
You are having a natural, open-ended conversation with the user.
Answer the user's question, request, joke, or explanation clearly, accurately, and conversationally using your general knowledge.

Rules:
- Speak naturally, warmly, and intelligently.
- Provide direct, high-quality answers (e.g. explain technical concepts like OAuth or LangGraph clearly, tell witty jokes when asked, answer "How are you?" cordially).
- Do NOT use hardcoded template strings or generic canned responses.
- Keep answers engaging, structured, and easy to read or listen to aloud.
""" + INJECTION_GUARDRAIL

ANSWER_PROMPT = """You are AetherOS.ai, the AI executive assistant operating system. Answer the user's question based on the provided support documentation passages or general product knowledge.

Rules:
- Identify yourself as AetherOS.ai
- Be concise, helpful, and natural
- Cite source document titles if available

""" + INJECTION_GUARDRAIL


class QuestionClassification(BaseModel):
    type: str = Field(description="One of: identity_or_greeting, general_conversation, genuine_question, feature_request, bug_report, feedback, other")


class SupportAnswer(BaseModel):
    answer: str = Field(description="The answer to the user's question")
    source_titles: list[str] = Field(default_factory=list, description="Source document titles")


async def _generate_identity_answer(question: str, llm: Optional[ChatOpenAI] = None) -> str:
    try:
        from core.llm_factory import invoke_llm_with_fallback
        messages = [
            {"role": "system", "content": IDENTITY_PROMPT},
            {"role": "user", "content": f"User question: '{question}'"},
        ]
        response, _ = invoke_llm_with_fallback(messages=messages, is_classifier=False)
        content = getattr(response, "content", "") or str(response)
        if content and len(content.strip()) > 5:
            return content.strip()
    except Exception as exc:
        logger.warning(f"Identity response LLM generation failed: {exc}")

    return "Hello! I am AetherOS.ai, your AI executive assistant operating system. I can help you search your inbox, draft email replies, schedule calendar meetings with Google Meet, query company knowledge, and run market research. How can I help you today?"


async def _generate_general_conversation(question: str, llm: Optional[ChatOpenAI] = None) -> str:
    try:
        from core.llm_factory import invoke_llm_with_fallback
        messages = [
            {"role": "system", "content": GENERAL_CONVERSATION_PROMPT},
            {"role": "user", "content": f"User prompt: '{question}'"},
        ]
        response, _ = invoke_llm_with_fallback(messages=messages, is_classifier=False)
        content = getattr(response, "content", "") or str(response)
        if content and len(content.strip()) > 5:
            return content.strip()
    except Exception as exc:
        logger.warning(f"General conversation response LLM generation failed: {exc}")

    return f"I'd be happy to help with that! Regarding '{question}': I'm AetherOS.ai, your executive assistant, and I'm ready to assist you."


async def answer_question(
    question: str,
    llm: Optional[ChatOpenAI] = None,
) -> dict[str, Any]:
    lowered = question.lower().strip()
    neg_ack_kws = ["don't read", "dont read", "no need to read", "don't read it", "dont read it", "skip that", "never mind", "no thanks", "no problem", "that's fine", "its fine", "it's fine"]
    if any(kw in lowered for kw in neg_ack_kws):
        return {
            "agent": "support_agent",
            "status": "completed",
            "result": {
                "answer": "No problem.",
                "message": "No problem.",
                "sources": [],
                "classification": "acknowledgment",
            },
            "context_updates": {"last_support_query": question},
            "requires_approval": False,
        }

    identity_kws = [
        "who are you", "what is your name", "what's your name", "what is ur name", "what can you do", "how are you", "how can you help",
        "what features", "what can i do", "who made you", "what is aetheros",
        "who is aetheros", "tell me about yourself", "who built you", "introduce yourself"
    ]
    if any(kw in lowered for kw in identity_kws) or lowered in ("hi", "hello", "hey", "greetings"):
        answer_text = await _generate_identity_answer(question, llm)
        return {
            "agent": "support_agent",
            "status": "completed",
            "result": {
                "answer": answer_text,
                "message": answer_text,
                "sources": [],
                "classification": "identity_or_greeting",
            },
            "context_updates": {"last_support_query": question},
            "requires_approval": False,
        }

    # Fast-path for common out-of-box conversational queries (jokes, explanations, tech questions)
    general_kws = ["joke", "oauth", "langgraph", "explain", "tell me a", "how does", "what is a ", "what is an ", "what are ", "why is ", "tell me about "]
    if any(kw in lowered for kw in general_kws):
        answer_text = await _generate_general_conversation(question, llm)
        return {
            "agent": "support_agent",
            "status": "completed",
            "result": {
                "answer": answer_text,
                "message": answer_text,
                "sources": [],
                "classification": "general_conversation",
            },
            "context_updates": {"last_support_query": question},
            "requires_approval": False,
        }

    if llm is None:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY,
        )

    classification = await _classify_question(question, llm)
    logger.info(f"Support question classified as: {classification.type}")

    if classification.type in ("identity_or_greeting", "general_conversation"):
        if classification.type == "identity_or_greeting":
            answer_text = await _generate_identity_answer(question, llm)
        else:
            answer_text = await _generate_general_conversation(question, llm)
        return {
            "agent": "support_agent",
            "status": "completed",
            "result": {
                "answer": answer_text,
                "message": answer_text,
                "sources": [],
                "classification": classification.type,
            },
            "context_updates": {"last_support_query": question},
            "requires_approval": False,
        }

    if classification.type == "feature_request":
        return _feedback_result(
            question,
            "feature_request",
            "That sounds like a great feature idea! I'm AetherOS.ai, and I've logged your request for our product team to review. "
            "We'll consider it for a future update.",
        )

    if classification.type == "bug_report":
        return _feedback_result(
            question,
            "bug_report",
            "Thanks for reporting this! I'm AetherOS.ai and I've logged the details so our engineering team can investigate and fix it.",
        )

    if classification.type == "feedback":
        return _feedback_result(
            question,
            "feedback",
            "Thanks for your feedback! I'm AetherOS.ai and I've logged it for our product team.",
        )

    answer = await _retrieve_and_answer(question, llm)
    return {
        "agent": "support_agent",
        "status": "completed",
        "result": {
            "answer": answer.answer,
            "message": answer.answer,
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
