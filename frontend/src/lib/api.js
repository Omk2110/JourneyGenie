/**
 * API client for the Agentic Travel Planner backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Check backend health status.
 */
export async function checkHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error("Backend unavailable");
  return res.json();
}

/**
 * Create a travel plan via the multi-agent pipeline.
 * @param {Object} input - Travel planning input
 * @param {string} input.destination - Destination city
 * @param {number} input.days - Number of days
 * @param {number} input.budget - Total budget in USD
 * @param {number} input.people - Number of travelers
 * @param {string[]} input.preferences - Travel preferences
 * @param {string} [input.start_date] - Trip start date
 * @param {string} [input.origin] - Origin city
 */
export async function createPlan(input) {
  const res = await fetch(`${API_BASE}/api/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    throw new Error(error.detail?.message || error.detail || "Planning failed");
  }

  return res.json();
}

/**
 * Get available LLM providers.
 */
export async function getProviders() {
  const res = await fetch(`${API_BASE}/api/providers`);
  if (!res.ok) throw new Error("Failed to fetch providers");
  return res.json();
}
