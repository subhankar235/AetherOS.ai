import logging
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from db.session import get_db
from models.user import User
from agents.research_agent import run_research

logger = logging.getLogger("routers.research")

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/run")
async def trigger_research(
    company: str = Form(..., description="Company name to research"),
    context: Optional[str] = Form(None, description="Additional context for disambiguation"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await run_research(company=company, context=context)
        return result
    except Exception as e:
        logger.error(f"Research failed for company '{company}': {e}")
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@router.get("/result")
async def get_research_result(
    company: str = Query(..., description="Company name to look up"),
    context: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await run_research(company=company, context=context)
        return result
    except Exception as e:
        logger.error(f"Research lookup failed for '{company}': {e}")
        raise HTTPException(status_code=500, detail=f"Research lookup failed: {str(e)}")
