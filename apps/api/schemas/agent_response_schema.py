from typing import Any, Literal
from pydantic import BaseModel


class AgentResponse(BaseModel):
    agent: str
    status: Literal["waiting_for_user", "completed", "error", "clarification_needed"]
    result: dict[str, Any]
    context_updates: dict[str, Any] = {}
    requires_approval: bool = False
