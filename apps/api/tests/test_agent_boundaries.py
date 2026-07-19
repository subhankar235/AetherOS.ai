import ast
import os
from pathlib import Path

import pytest

AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"

AGENT_ALLOWED_IMPORTS: dict[str, set[str]] = {
    "inbox_agent": {
        "integrations.gmail_client",
        "integrations.google_auth",
        "core.config",
        "core.exceptions",
        "core.logging",
        "models.email_metadata",
        "models.thread",
        "schemas.email_schema",
        "schemas.agent_response_schema",
        "services.approval.approval_gate",
        "services.audit.audit_logger",
        "db.session",
    },
    "reply_agent": {
        "integrations.gmail_client",
        "integrations.google_auth",
        "integrations.qdrant_client",
        "core.config",
        "core.exceptions",
        "core.logging",
        "models.draft",
        "models.email_metadata",
        "models.thread",
        "schemas.draft_schema",
        "schemas.agent_response_schema",
        "services.approval.approval_gate",
        "services.audit.audit_logger",
        "services.rag.embedder",
        "db.session",
    },
    "calendar_agent": {
        "integrations.calendar_client",
        "integrations.meet_client",
        "integrations.google_auth",
        "core.config",
        "core.exceptions",
        "core.logging",
        "models.meeting",
        "schemas.agent_response_schema",
        "services.approval.approval_gate",
        "services.audit.audit_logger",
        "db.session",
    },
    "knowledge_agent": {
        "integrations.qdrant_client",
        "core.config",
        "core.exceptions",
        "core.logging",
        "models.knowledge_document",
        "schemas.agent_response_schema",
        "services.rag.embedder",
        "services.ingestion.chunker",
        "services.ingestion.parser",
        "db.session",
    },
    "research_agent": {
        "integrations.qdrant_client",
        "core.config",
        "core.exceptions",
        "core.logging",
        "schemas.agent_response_schema",
        "services.audit.audit_logger",
        "db.session",
    },
    "support_agent": {
        "integrations.qdrant_client",
        "core.config",
        "core.exceptions",
        "core.logging",
        "schemas.agent_response_schema",
        "services.audit.audit_logger",
        "db.session",
    },
    "payment_agent": {
        "core.config",
        "core.exceptions",
        "core.logging",
        "schemas.agent_response_schema",
        "services.audit.audit_logger",
        "db.session",
    },
}

FORBIDDEN_IMPORTS: dict[str, set[str]] = {
    "inbox_agent": {
        "integrations.calendar_client",
        "integrations.meet_client",
    },
    "reply_agent": {
        "integrations.calendar_client",
        "integrations.meet_client",
    },
    "calendar_agent": {
        "integrations.gmail_client",
    },
    "knowledge_agent": {
        "integrations.gmail_client",
        "integrations.calendar_client",
        "integrations.meet_client",
    },
}


def _get_top_level_imports(filepath: Path) -> list[str]:
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(filepath))

    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                imports.append(top)
    return imports


def test_agent_import_boundaries():
    if not AGENTS_DIR.exists():
        pytest.skip("Agents directory does not exist yet — nothing to check")

    agent_dirs = [d for d in AGENTS_DIR.iterdir() if d.is_dir() and not d.name.startswith("__")]

    for agent_dir in agent_dirs:
        agent_name = agent_dir.name
        py_files = list(agent_dir.rglob("*.py"))
        if not py_files:
            continue

        forbidden = FORBIDDEN_IMPORTS.get(agent_name, set())
        if not forbidden:
            continue

        for py_file in py_files:
            if py_file.name.startswith("__"):
                continue
            imports = _get_top_level_imports(py_file)
            for forbid in forbidden:
                top = forbid.split(".")[0]
                if top in imports:
                    pytest.fail(
                        f"Agent '{agent_name}' in {py_file.relative_to(AGENTS_DIR.parent)} "
                        f"imports forbidden module '{forbid}'. "
                        f"Agent '{agent_name}' must not import {forbidden}"
                    )


def describe_agent_allowed_imports():
    for agent_name, allowed in sorted(AGENT_ALLOWED_IMPORTS.items()):
        print(f"\n  {agent_name}:")
        for mod in sorted(allowed):
            print(f"    - {mod}")
