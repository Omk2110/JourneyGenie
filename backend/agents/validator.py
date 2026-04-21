"""
Validator Agent -- LLM-based evaluation of itinerary.
Evaluates distribution, user preferences, and overall feasibility.
Can use tools to verify information.
"""

from __future__ import annotations
import logging
import json
from backend.agents.state import TravelPlannerState
from backend.llm.provider import get_llm
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from backend.tools.serpapi_search import web_search

logger = logging.getLogger(__name__)

MAX_RETRIES = 5  # Allow up to 5 iterations globally in graph

@tool
async def search_validation_info(query: str) -> str:
    """Search the web to verify travel times, realistic costs, or whether activities are open."""
    try:
        res = await web_search(query, 3)
        return json.dumps(res)
    except Exception as e:
        return f"Tool failed: {e}"

VALIDATOR_SYSTEM_PROMPT = """You are an expert itinerary validator. You are validating a multi-day travel itinerary.
Your job is to read carefully through the itinerary and determine if it is realistic and aligns with user preferences.

CRITICAL CHECKS:
1. EVEN DISTRIBUTION: Are activities evenly distributed across all days? If Day 1 is jammed fully but Day 2 is empty, you MUST reject the plan.
2. PREFERENCES COMPLIANCE: Have the user's specific preferences and group type been respected?
3. BUFFER & TIME: Is there enough buffer time for traveling? Are activities packed too heavily? Provide realistic feedback on travel times.
4. BUDGET LIMITS: Has the budget been extremely exceeded without cause?

If you suspect travel times or activity feasibilities are inaccurate, use the 'search_validation_info' tool to verify. 

Once you are done evaluating, you MUST return your final verdict securely inside a JSON payload (using no markdown code fences). Do not return anything except the JSON payload when returning the verdict. Your JSON must strictly be:
{
  "passed": boolean,
  "issues": ["list", "of", "issues", "found"],
  "validation_feedback": "A very detailed string (multiple sentences) providing actionable feedback explaining EXACTLY what the next agent must fix. For example: 'Move two activities from Day 1 to Day 2 to balance the schedule. Add a vegetarian restaurant on Day 2.'"
}
If there are no critical issues and the plan is evenly distributed and complies with preferences, set "passed" to true.
"""

async def validator_agent(state: TravelPlannerState) -> dict:
    """
    LLM-powered validation agent.
    Checks itinerary for feasibility, pacing, and preferences.
    """
    destination = state.get("destination", "Unknown")
    budget = state.get("budget", 1000)
    budget_breakdown = state.get("budget_breakdown", {})
    itinerary = state.get("itinerary", [])
    retry_count = state.get("retry_count", 0)
    preferences = state.get("preferences", [])
    group_type = state.get("group_type", "solo")

    logger.info(f"[VALID] Validator LLM Agent: Checking itinerary (attempt {retry_count + 1})")

    # If we hit max retries, force a pass to avoid infinite loop
    if retry_count >= MAX_RETRIES - 1:
        logger.warning("[VALID] Max retries reached. Forcing pass.")
        return {
            "validation_result": {"passed": True, "issues": [], "warnings": ["Max validation retries reached"]},
            "validation_passed": True,
            "validation_feedback": "Max retries reached. Forcing pass.",
            "retry_count": retry_count + 1,
            "agent_logs": state.get("agent_logs", []) + ["Validator: Forced PASSED (Max Retries)"],
        }

    # Prepare LLM Context
    total_estimated = budget_breakdown.get("total_estimated", 0)
    
    itinerary_str = json.dumps(itinerary, indent=2)
    
    human_prompt = f"""
Destination: {destination}
Budget limit: ${budget}
Total estimated cost so far: ${total_estimated}
Group Strategy: {group_type}
User Preferences: {preferences}

Daily Itinerary Proposal:
{itinerary_str}

Evaluate the plan. Output your final JSON structure indicating if it 'passed', any 'issues', and detailed 'validation_feedback' to fix it.
"""

    llm = get_llm(temperature=0.1).bind_tools([search_validation_info])
    
    messages = [
        SystemMessage(content=VALIDATOR_SYSTEM_PROMPT),
        HumanMessage(content=human_prompt)
    ]

    max_tool_iterations = 3
    final_json = None
    
    # Internal Agent execution loop to handle tool calls
    for _ in range(max_tool_iterations):
        response = await llm.ainvoke(messages)
        messages.append(response)

        # If LLM wants to use a tool
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                logger.info(f"[VALID] Validator executing tool: {tool_call['name']}")
                if tool_call["name"] == "search_validation_info":
                    result = await search_validation_info.ainvoke(tool_call["args"])
                else:
                    result = "Unknown tool."
                
                messages.append(ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=str(result)
                ))
            continue # Continue loop with tool responses

        # We assume the LLM output the json payload
        content = response.content
        if isinstance(content, list):
            content = "".join([p.get("text", "") for p in content if isinstance(p, dict)])
        content = str(content).strip()
        # Clean markdown
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        if content.startswith("json"):
            content = content[4:].strip()

        try:
            final_json = json.loads(content)
            break
        except json.JSONDecodeError as e:
            logger.error(f"[VALID] Validator returned invalid JSON: {content}. Retrying...")
            messages.append(HumanMessage(content="You did not return valid JSON. Respond ONLY with the requested JSON struct."))
            continue

    if not final_json:
        logger.error("[VALID] Validator completely failed to return valid JSON.")
        # Fail open
        final_json = {
            "passed": False,
            "issues": ["Validator encountered errors parsing response."],
            "validation_feedback": "Ensure activities are evenly spread and budget fits perfectly."
        }

    validation_passed = bool(final_json.get("passed", False))
    issues = final_json.get("issues", [])
    validation_feedback = final_json.get("validation_feedback", "")

    if not validation_passed:
        logger.warning(f"[VALID] Validator REJECTED the plan. Issues: {issues}")
        logger.info(f"[VALID] Validator Feedback: {validation_feedback}")
    else:
        logger.info("[VALID] Validator APPROVED the plan.")

    return {
        "validation_result": {
            "passed": validation_passed,
            "issues": issues,
            "warnings": [],
            "feedback": validation_feedback
        },
        "validation_passed": validation_passed,
        "validation_feedback": validation_feedback,
        "retry_count": retry_count + 1,
        "agent_logs": state.get("agent_logs", []) + [
            f"Validator: {'PASSED' if validation_passed else 'FAILED'} -> {validation_feedback[:100]}..."
        ],
    }
