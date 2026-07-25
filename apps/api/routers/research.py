import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from db.session import get_db
from models.user import User
from agents.research_agent import run_research

logger = logging.getLogger("routers.research")

router = APIRouter(prefix="/research", tags=["research"])


class ResearchRequest(BaseModel):
    """JSON body for triggering a research run."""
    company: str = Field(..., min_length=1, max_length=200, description="Company name to research")
    context: Optional[str] = Field(None, max_length=500, description="Additional context for disambiguation")


@router.post("/run")
async def trigger_research(
    req: ResearchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run market research for a company. Returns structured report or disambiguation prompt."""
    try:
        result = await run_research(company=req.company.strip(), context=req.context)
        return result
    except Exception as e:
        logger.error(f"Research failed for company '{req.company}': {e}")
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@router.get("/result")
async def get_research_result(
    company: str = Query(..., min_length=1, description="Company name to look up"),
    context: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Look up or generate research for a company via query parameters."""
    try:
        result = await run_research(company=company.strip(), context=context)
        return result
    except Exception as e:
        logger.error(f"Research lookup failed for '{company}': {e}")
        raise HTTPException(status_code=500, detail=f"Research lookup failed: {str(e)}")
