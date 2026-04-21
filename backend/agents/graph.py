"""
LangGraph -- Stateful multi-agent graph for travel planning.

Flow: Planner -> Group Opt -> Search -> Budget Opt -> Itinerary -> Map -> Context -> Validator -> Report
With conditional retry: Validator failure -> Budget Opt (up to 2 retries)
"""

from __future__ import annotations
import logging
from langgraph.graph import StateGraph, END

from backend.agents.state import TravelPlannerState
from backend.agents.planner import planner_agent
from backend.agents.group_optimizer import group_optimization_agent
from backend.agents.search import search_agent
from backend.agents.budget_optimizer import budget_optimization_agent
from backend.agents.itinerary import itinerary_generator_agent
from backend.agents.map_agent import map_agent
from backend.agents.context import context_agent
from backend.agents.validator import validator_agent
from backend.agents.report import report_generator_agent

logger = logging.getLogger(__name__)


def _should_retry(state: TravelPlannerState) -> str:
    """
    Conditional edge after Validator:
    - If validation passed -> continue to report
    - If validation failed and retries left -> go back to budget_optimizer
    """
    if state.get("validation_passed", False):
        return "report_generator"
    elif state.get("retry_count", 0) < 5:
        logger.info("[RETRY] Validator failed -- retrying budget optimization")
        return "budget_optimizer"
    else:
        logger.warning("[RETRY] Max retries reached -- proceeding to report with warnings")
        return "report_generator"


def build_travel_planner_graph() -> StateGraph:
    """
    Build and compile the LangGraph state graph.

    Graph topology:
    ┌──────────┐    ┌────────────────┐    ┌────────┐    ┌──────────────────┐
    │ Planner  │───►│ Group Optimizer │───►│ Search │───►│ Budget Optimizer │◄─┐
    └──────────┘    └────────────────┘    └────────┘    └──────────┬───────┘  │
                                                                   ▼          │
    ┌──────────────┐    ┌─────────┐    ┌─────────┐    ┌───────────┴──┐       │
    │ Report Gen   │◄───│ Context │◄───│   Map   │◄───│  Itinerary   │       │
    └──────┬───────┘    └─────────┘    └─────────┘    └──────────────┘       │
           │                                                                  │
           ▼                                                                  │
    ┌──────────────┐                                                         │
    │  Validator   │─── (retry if failed) ───────────────────────────────────┘
    └──────┬───────┘
           ▼
         [END]
    """
    graph = StateGraph(TravelPlannerState)

    # ── Add all agent nodes ───────────────────────────────────
    graph.add_node("planner", planner_agent)
    graph.add_node("group_optimizer", group_optimization_agent)
    graph.add_node("search", search_agent)
    graph.add_node("budget_optimizer", budget_optimization_agent)
    graph.add_node("itinerary", itinerary_generator_agent)
    graph.add_node("map_agent", map_agent)
    graph.add_node("context", context_agent)
    graph.add_node("validator", validator_agent)
    graph.add_node("report_generator", report_generator_agent)

    # ── Define edges (mandatory flow) ─────────────────────────
    graph.set_entry_point("planner")

    graph.add_edge("planner", "group_optimizer")
    graph.add_edge("group_optimizer", "search")
    graph.add_edge("search", "budget_optimizer")
    graph.add_edge("budget_optimizer", "itinerary")
    graph.add_edge("itinerary", "map_agent")
    graph.add_edge("map_agent", "context")
    graph.add_edge("context", "validator")

    # Conditional edge: validator -> report_generator OR -> budget_optimizer (retry)
    graph.add_conditional_edges(
        "validator",
        _should_retry,
        {
            "report_generator": "report_generator",
            "budget_optimizer": "budget_optimizer",
        },
    )

    graph.add_edge("report_generator", END)

    return graph.compile()


# Pre-build the graph (singleton)
travel_planner_graph = build_travel_planner_graph()


async def run_travel_planner(
    destination: str,
    days: int,
    budget: int,
    people: int,
    preferences: list[str] | None = None,
    start_date: str = "",
    origin: str = "",
) -> dict:
    """
    Execute the full travel planning pipeline.
    Returns the final structured output.
    """
    logger.info(f"[START] Starting travel planner for {destination}")

    initial_state: TravelPlannerState = {
        "destination": destination,
        "days": days,
        "budget": budget,
        "people": people,
        "preferences": preferences or [],
        "start_date": start_date,
        "origin": origin,
        "errors": [],
        "warnings": [],
        "agent_logs": [],
        "retry_count": 0,
    }

    # Execute the graph
    result = await travel_planner_graph.ainvoke(initial_state)

    logger.info("[VALID] Travel planner completed")

    # Log agent activity
    for log in result.get("agent_logs", []):
        logger.info(f"  -> {log}")

    return result.get("final_output", {})
