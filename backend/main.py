"""
FastAPI entry point for the Agentic Travel Planner.
Provides REST API endpoints for the frontend.
"""

from __future__ import annotations
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.config import settings
from backend.agents.graph import run_travel_planner
from backend.models.schemas import TravelInput

# ── Logging Setup ─────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("Agentic Travel Planner -- Starting Up")
    logger.info("=" * 60)

    # Check LLM availability
    providers = settings.get_available_llm_providers()
    if providers:
        logger.info(f"LLM Providers available: {', '.join(providers)}")
    else:
        logger.warning("No LLM API keys configured! Add keys to .env file.")

    # Report missing API keys
    missing = settings.get_missing_api_keys()
    if missing:
        logger.warning(f"Missing API keys: {', '.join(missing)}")
        logger.warning("System will use fallback data for missing integrations.")

    yield

    logger.info("Agentic Travel Planner -- Shutting Down")


# ── FastAPI App ───────────────────────────────────────────────
app = FastAPI(
    title="Agentic Travel Planner",
    description="Multi-agent AI travel planning system powered by LangGraph",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Response Models ───────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str = "ok"
    llm_providers: list[str] = []
    missing_api_keys: list[str] = []


class PlanResponse(BaseModel):
    success: bool
    data: dict = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


# ── Endpoints ─────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with system status."""
    return HealthResponse(
        status="ok",
        llm_providers=settings.get_available_llm_providers(),
        missing_api_keys=settings.get_missing_api_keys(),
    )


@app.post("/api/plan", response_model=PlanResponse)
async def create_plan(request: TravelInput):
    """
    Create a travel plan using the multi-agent pipeline.
    Accepts destination, budget, days, people, and preferences.
    """
    logger.info(
        f"📨 New plan request: {request.destination}, "
        f"{request.days} days, ₹{request.budget}, {request.people} people"
    )

    # ── Validate LLM availability ─────────────────────────────
    if not settings.has_any_llm():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "No LLM provider configured",
                "message": "Please add at least one LLM API key to your .env file: "
                           "GOOGLE_AI_API_KEY, OPENAI_API_KEY, or CEREBRAS_API_KEY",
                "missing_keys": settings.get_missing_api_keys(),
            },
        )

    # ── Human-in-the-loop: validate input completeness ────────
    warnings = []
    if request.budget < 5000:
        warnings.append("Budget seems very low. Results may be limited.")
    if not request.preferences:
        warnings.append("No preferences specified -- using general sightseeing defaults.")

    try:
        # Run the agent pipeline
        result = await run_travel_planner(
            destination=request.destination,
            days=request.days,
            budget=request.budget,
            people=request.people,
            preferences=request.preferences,
            start_date=request.start_date or "",
            origin=request.origin or "",
        )

        # Add any request-level warnings
        if warnings and isinstance(result, dict):
            existing_warnings = result.get("warnings", [])
            result["warnings"] = warnings + existing_warnings

        return PlanResponse(success=True, data=result)

    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        return PlanResponse(
            success=False,
            data={},
            errors=[f"Planning failed: {str(e)}"],
        )


@app.get("/api/providers")
async def get_providers():
    """Get available LLM providers and their status."""
    return {
        "available": settings.get_available_llm_providers(),
        "default": settings.get_best_llm_provider(),
        "models": {
            "gemini": settings.GEMINI_MODEL,
            "openai": settings.OPENAI_MODEL,
            "cerebras": settings.CEREBRAS_MODEL,
        },
    }


# ── Run ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
