"""
Context Agent -- provides weather insights, cultural context, and best-time-to-visit reasoning.
"""

from __future__ import annotations
import json
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from backend.llm import get_llm
from backend.agents.state import TravelPlannerState

logger = logging.getLogger(__name__)

CONTEXT_SYSTEM_PROMPT = """You are a travel context expert. Given a destination and weather data, provide cultural insights and travel recommendations.

Return a JSON object:
{
    "cultural_insights": [
        "Insight about local customs, etiquette, or cultural tips"
    ],
    "best_time_to_visit": {
        "months": ["March", "April", "May"],
        "reasoning": "Why these months are ideal"
    },
    "practical_tips": [
        "Practical travel tip 1",
        "Practical travel tip 2"
    ],
    "local_cuisine": [
        "Must-try dish 1",
        "Must-try dish 2"
    ],
    "safety_notes": "Any safety considerations"
}

Return ONLY the JSON object."""


async def context_agent(state: TravelPlannerState) -> dict:
    """
    Provide weather context, cultural insights, and best-time-to-visit reasoning.
    """
    destination = state.get("destination", "")
    weather_data = state.get("weather_data", {})
    preferences = state.get("preferences", [])
    days = state.get("days", 3)

    logger.info(f"[CTX] Context Agent: Analyzing context for {destination}")

    weather_desc = (
        f"Temperature: {weather_data.get('temperature_celsius', 'N/A')}°C, "
        f"Conditions: {weather_data.get('description', 'N/A')}, "
        f"Humidity: {weather_data.get('humidity', 'N/A')}%"
    )

    user_prompt = f"""Destination: {destination}
Current Weather: {weather_desc}
Trip Duration: {days} days
Traveler Preferences: {', '.join(preferences) if preferences else 'general'}

Provide cultural insights, best time to visit, practical tips, and local cuisine recommendations."""

    try:
        llm = get_llm()
        messages = [
            SystemMessage(content=CONTEXT_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        response = await llm.ainvoke(messages)

        content = response.content
        if isinstance(content, list):
            content = "".join([p.get("text", "") for p in content if isinstance(p, dict)])
        content = str(content).strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        if content.startswith("json"):
            content = content[4:].strip()

        context_data = json.loads(content)

    except Exception as e:
        logger.warning(f"Context Agent LLM error: {e}, using defaults")
        context_data = _get_default_context(destination)

    cultural_insights = context_data.get("cultural_insights", [])
    best_time = context_data.get("best_time_to_visit", {"months": [], "reasoning": ""})
    practical_tips = context_data.get("practical_tips", [])
    local_cuisine = context_data.get("local_cuisine", [])

    # Combine all insights
    all_insights = cultural_insights + practical_tips
    if local_cuisine:
        all_insights.append(f"Must-try local food: {', '.join(local_cuisine[:3])}")

    return {
        "cultural_insights": all_insights,
        "best_time_to_visit": best_time,
        "agent_logs": state.get("agent_logs", []) + [
            f"Context: Generated {len(all_insights)} insights for {destination}"
        ],
    }


def _get_default_context(destination: str) -> dict:
    """Default context when LLM is unavailable."""
    return {
        "cultural_insights": [
            f"Research local customs and etiquette before visiting {destination}",
            "Learn a few basic phrases in the local language",
            "Respect local dress codes, especially at religious sites",
        ],
        "best_time_to_visit": {
            "months": ["March", "April", "May", "September", "October"],
            "reasoning": "Shoulder seasons typically offer pleasant weather and fewer crowds",
        },
        "practical_tips": [
            "Keep copies of important documents",
            "Download offline maps before departure",
            "Check visa requirements well in advance",
        ],
        "local_cuisine": [
            "Local street food",
            "Traditional regional dishes",
        ],
    }
