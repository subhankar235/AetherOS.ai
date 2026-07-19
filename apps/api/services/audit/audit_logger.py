import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.agent_log import AgentLog

logger = logging.getLogger("services.audit.audit_logger")

SECRET_FIELD_NAMES = frozenset({
    "api_key", "api_secret", "secret", "password", "passwd",
    "access_token", "refresh_token", "token",
    "authorization", "x-api-key", "client_secret",
    "openai_api_key", "elevenlabs_api_key",
    "clerk_secret_key", "google_client_secret",
})


def _redact_value(value: Any, depth: int = 0) -> Any:
    if depth > 10:
        return value
    if isinstance(value, dict):
        return _redact_payload(value, depth + 1)
    if isinstance(value, list):
        return [_redact_value(item, depth + 1) for item in value]
    if isinstance(value, str) and len(value) > 12:
        for field in SECRET_FIELD_NAMES:
            if field in value.lower():
                return "***REDACTED***"
        if value.startswith("sk-") or value.startswith("pk_") or value.startswith("whsec_"):
            return "***REDACTED***"
    return value


def _redact_payload(payload: Optional[dict[str, Any]], depth: int = 0) -> Optional[dict[str, Any]]:
    if payload is None:
        return None
    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(key, str) and key.lower() in SECRET_FIELD_NAMES:
            redacted[key] = "***REDACTED***"
        else:
            redacted[key] = _redact_value(value, depth)
    return redacted


async def log_agent_action(
    db: AsyncSession,
    user_id: uuid.UUID,
    agent_name: str,
    action_type: str,
    input_payload: Optional[dict[str, Any]] = None,
    output_payload: Optional[dict[str, Any]] = None,
    requires_approval: bool = False,
    status: str = "completed",
) -> uuid.UUID:
    safe_input = _redact_payload(input_payload)
    safe_output = _redact_payload(output_payload)

    log = AgentLog(
        id=uuid.uuid4(),
        user_id=user_id,
        agent_name=agent_name,
        action_type=action_type,
        input_payload=safe_input,
        output_payload=safe_output,
        requires_approval=requires_approval,
        status=status,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    logger.info(
        f"Logged agent action: agent={agent_name} action={action_type} "
        f"user={user_id} status={status}"
    )
    return log.id


async def mark_executed(
    db: AsyncSession,
    log_id: uuid.UUID,
    output_payload: Optional[dict[str, Any]] = None,
) -> None:
    result = await db.execute(
        select(AgentLog).where(AgentLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    if log is None:
        logger.warning(f"Agent log {log_id} not found for mark_executed")
        return
    log.executed_at = datetime.now(timezone.utc)
    if output_payload is not None:
        log.output_payload = _redact_payload(output_payload)
    await db.commit()
