import logging
from typing import Any, List, Optional
from langchain_openai import ChatOpenAI
from core.config import settings

logger = logging.getLogger("core.llm_factory")


def get_provider_candidates(is_classifier: bool = True) -> List[dict[str, Any]]:
    order_str = getattr(settings, "LLM_FALLBACK_ORDER", "openrouter,groq,gemini")
    order = [p.strip().lower() for p in order_str.split(",") if p.strip()]
    candidates = []

    for provider in order:
        if provider in ("openrouter", "openai"):
            key = getattr(settings, "OPENAI_API_KEY", None)
            if key and not key.startswith("sk-xxxx") and key.strip():
                model = getattr(settings, "OPENAI_MODEL_CLASSIFIER" if is_classifier else "OPENAI_MODEL_PRIMARY", "openrouter/auto")
                candidates.append({
                    "name": "openrouter",
                    "api_key": key,
                    "base_url": settings.openai_base_url,
                    "model": model,
                })
        elif provider == "groq":
            key = getattr(settings, "GROQ_API_KEY", None)
            if key and not key.startswith("gsk_xxxx") and key.strip():
                candidates.append({
                    "name": "groq",
                    "api_key": key,
                    "base_url": "https://api.groq.com/openai/v1",
                    "model": getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile"),
                })
        elif provider == "gemini":
            key = getattr(settings, "GEMINI_API_KEY", None)
            if key and not key.startswith("AIza_xxxx") and key.strip():
                candidates.append({
                    "name": "gemini",
                    "api_key": key,
                    "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                    "model": getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash"),
                })

    return candidates


def invoke_llm_with_fallback(
    messages: List[Any],
    tools: Optional[List[dict[str, Any]]] = None,
    is_classifier: bool = True,
    temperature: float = 0.1,
) -> tuple[Any, str]:
    candidates = get_provider_candidates(is_classifier=is_classifier)

    if not candidates:
        raise RuntimeError("No valid LLM provider API keys configured.")

    last_exception = None

    for cand in candidates:
        provider_name = cand["name"]
        model_name = cand["model"]
        logger.info(f"Attempting LLM call via provider '{provider_name}' using model '{model_name}'...")

        try:
            kwargs = {
                "model": model_name,
                "temperature": temperature,
                "api_key": cand["api_key"],
            }
            if cand["base_url"]:
                kwargs["base_url"] = cand["base_url"]

            llm = ChatOpenAI(**kwargs)

            if tools:
                response = llm.bind_tools(tools).invoke(messages)
                tool_calls = getattr(response, "tool_calls", None) or []
                if not tool_calls:
                    # If this provider didn't produce tool calls when tools were requested, log and try next candidate if possible
                    content = getattr(response, "content", "") or ""
                    logger.warning(f"Provider '{provider_name}' returned no tool_calls. Content: {content[:100]}. Testing next candidate if available...")
                    # If there's another candidate, continue loop
                    if len(candidates) > 1 and cand != candidates[-1]:
                        last_exception = RuntimeError(f"Provider {provider_name} returned no tool calls")
                        continue
            else:
                response = llm.invoke(messages)

            logger.info(f"LLM call succeeded using provider '{provider_name}' ({model_name}).")
            return response, provider_name

        except Exception as exc:
            last_exception = exc
            logger.warning(f"LLM call failed for provider '{provider_name}' ({model_name}): {exc}. Trying next candidate...")

    raise RuntimeError(f"All configured LLM providers failed. Last error: {last_exception}")
