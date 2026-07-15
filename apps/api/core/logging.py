# Configures application logging. Records important events, errors, and requests with details like request_id, user_id, and agent_name for debugging and monitoring.


import contextvars
import json
import logging
import time
import uuid
from typing import Any, Dict, Optional
from contextlib import contextmanager
from starlette.types import ASGIApp, Receive, Scope, Send

# Context variables for request, user, and agent trace mapping
request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)
user_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("user_id", default=None)
agent_name_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("agent_name", default=None)

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Fetch values from async context vars
        request_id = request_id_var.get()
        user_id = user_id_var.get()
        agent_name = agent_name_var.get()

        # Build basic log payload
        log_data: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)) + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "request_id": request_id,
            "user_id": user_id,
            "agent_name": agent_name,
        }

        # Handle exception context
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include custom fields passed as extra
        standard_attrs = {
            "args", "asctime", "created", "exc_info", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs", "message",
            "msg", "name", "pathname", "process", "processName", "relativeCreated",
            "stack_info", "thread", "threadName"
        }
        extra = {k: v for k, v in record.__dict__.items() if k not in standard_attrs}
        if extra:
            log_data["extra"] = extra

        return json.dumps(log_data)

def setup_logging(log_level: str = "INFO") -> None:
    # Set up root logger handler
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clean existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create stdout console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)

    # Force uvicorn loggers to propagate to root so their logs are JSON-formatted as well
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.propagate = True

@contextmanager
def logging_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    agent_name: Optional[str] = None,
):
    """Context manager to set and revert contextvars for logging."""
    tokens = []
    if request_id is not None:
        tokens.append((request_id_var, request_id_var.set(request_id)))
    if user_id is not None:
        tokens.append((user_id_var, user_id_var.set(user_id)))
    if agent_name is not None:
        tokens.append((agent_name_var, agent_name_var.set(agent_name)))

    try:
        yield
    finally:
        for var, token in reversed(tokens):
            var.reset(token)

def set_user_id(user_id: Optional[str]) -> None:
    user_id_var.set(user_id)

def set_agent_name(agent_name: Optional[str]) -> None:
    agent_name_var.set(agent_name)

def get_request_id() -> Optional[str]:
    return request_id_var.get()

class LoggingASGIMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Extract X-Request-ID or generate
        headers = dict(scope.get("headers", []))
        req_id_bytes = headers.get(b"x-request-id", b"")
        request_id = req_id_bytes.decode("utf-8") if req_id_bytes else str(uuid.uuid4())

        # Extract X-User-ID or leave None
        user_id_bytes = headers.get(b"x-user-id", b"")
        user_id = user_id_bytes.decode("utf-8") if user_id_bytes else None

        req_token = request_id_var.set(request_id)
        user_token = user_id_var.set(user_id)
        agent_token = agent_name_var.set(None)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Ensure response headers include the X-Request-ID
                response_headers = list(message.get("headers", []))
                response_headers.append((b"x-request-id", request_id.encode("utf-8")))
                message["headers"] = response_headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            request_id_var.reset(req_token)
            user_id_var.reset(user_token)
            agent_name_var.reset(agent_token)
