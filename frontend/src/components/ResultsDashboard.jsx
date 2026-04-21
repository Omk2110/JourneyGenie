"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import BudgetChart from "./BudgetChart";
import ItineraryTimeline from "./ItineraryTimeline";
import InsightCards from "./InsightCards";
import styles from "./ResultsDashboard.module.css";

// Leaflet must be loaded client-side only (no SSR)
const MapView = dynamic(() => import("./MapView"), { ssr: false });

const TABS = [
  { id: "overview", label: "📋 Overview", icon: "📋" },
  { id: "map", label: "🗺️ Map", icon: "🗺️" },
  { id: "timeline", label: "📅 Timeline", icon: "📅" },
  { id: "budget", label: "💰 Budget", icon: "💰" },
  { id: "insights", label: "💡 Insights", icon: "💡" },
];

/**
 * Format number in Indian locale style (e.g., 1,50,000)
 */
function formatINR(num) {
  if (!num && num !== 0) return "0";
  return Number(num).toLocaleString("en-IN");
}

export default function ResultsDashboard({ data }) {
  const [activeTab, setActiveTab] = useState("overview");

  if (!data) return null;

  const { summary, budget_breakdown, itinerary, map_data, recommendations, insights, warnings } = data;

  return (
    <div className={styles.dashboard}>
      {/* Summary Banner */}
      <div className={styles.banner}>
        <div className={styles.bannerContent}>
          <h2 className={styles.bannerTitle}>
            <span className="gradient-text">{summary?.destination}</span>
          </h2>
          <div className={styles.bannerStats}>
            <div className={styles.stat}>
              <span className={styles.statValue}>{summary?.duration_days}</span>
              <span className={styles.statLabel}>Days</span>
            </div>
            <div className={styles.statDivider} />
            <div className={styles.stat}>
              <span className={styles.statValue}>{summary?.people}</span>
              <span className={styles.statLabel}>Travelers</span>
            </div>
            <div className={styles.statDivider} />
            <div className={styles.stat}>
              <span className={styles.statValue}>₹{formatINR(summary?.estimated_cost)}</span>
              <span className={styles.statLabel}>Estimated</span>
            </div>
            <div className={styles.statDivider} />
            <div className={styles.stat}>
              <span className={styles.statValue}>₹{formatINR(summary?.total_budget)}</span>
              <span className={styles.statLabel}>Budget</span>
            </div>
            <div className={styles.statDivider} />
            <div className={styles.stat}>
              <span className={styles.statValue} style={{ textTransform: "capitalize" }}>
                {summary?.group_type}
              </span>
              <span className={styles.statLabel}>Group</span>
            </div>
          </div>
        </div>
      </div>

      {/* Warnings */}
      {warnings?.length > 0 && (
        <div className={styles.warnings}>
          {warnings.map((w, i) => (
            <div key={i} className={styles.warning}>
              ⚠️ {w}
            </div>
          ))}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
            id={`tab-${tab.id}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className={styles.tabContent}>
        {activeTab === "overview" && (
          <div className="animate-fade-in stagger">
            <div className={styles.overviewGrid}>
              <div className={styles.overviewMain}>
                <ItineraryTimeline itinerary={itinerary} compact />
              </div>
              <div className={styles.overviewSide}>
                <BudgetChart breakdown={budget_breakdown} />
                <InsightCards insights={insights} compact />
                {recommendations?.length > 0 && (
                  <div className={styles.recsCard}>
                    <h3 className={styles.sectionTitle}>🎯 Recommendations</h3>
                    {recommendations.map((rec, i) => (
                      <div key={i} className={styles.recItem}>
                        <div className={styles.recHeader}>
                          <span className={`${styles.priority} ${styles[rec.priority]}`}>
                            {rec.priority}
                          </span>
                          <strong>{rec.title}</strong>
                        </div>
                        <p className={styles.recDesc}>{rec.description}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === "map" && (
          <div className="animate-fade-in">
            <MapView mapData={map_data} itinerary={itinerary} />
          </div>
        )}

        {activeTab === "timeline" && (
          <div className="animate-fade-in">
            <ItineraryTimeline itinerary={itinerary} />
          </div>
        )}

        {activeTab === "budget" && (
          <div className="animate-fade-in">
            <div className={styles.budgetPage}>
              <BudgetChart breakdown={budget_breakdown} large />
              <div className={styles.budgetDetails}>
                <h3 className={styles.sectionTitle}>💵 Budget Breakdown</h3>
                {Object.entries(budget_breakdown || {})
                  .filter(([k]) => !["total_estimated", "total_budget", "remaining"].includes(k))
                  .map(([key, value]) => (
                    <div key={key} className={styles.budgetRow}>
                      <span className={styles.budgetLabel}>{key.replace(/_/g, " ")}</span>
                      <span className={styles.budgetValue}>₹{formatINR(value)}</span>
                    </div>
                  ))}
                <div className={`${styles.budgetRow} ${styles.budgetTotal}`}>
                  <span>Total Estimated</span>
                  <span>
                    ₹{formatINR(budget_breakdown?.total_estimated)}
                  </span>
                </div>
                <div className={`${styles.budgetRow} ${styles.budgetRemaining}`}>
                  <span>Remaining</span>
                  <span
                    style={{
                      color:
                        budget_breakdown?.remaining >= 0
                          ? "var(--accent-green)"
                          : "var(--accent-red)",
                    }}
                  >
                    ₹{formatINR(budget_breakdown?.remaining)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "insights" && (
          <div className="animate-fade-in">
            <InsightCards insights={insights} />
            {summary?.best_time_reasoning && (
              <div className={`glass-card ${styles.bestTime}`}>
                <h3>🗓️ Best Time to Visit</h3>
                <p className={styles.bestTimeMonths}>
                  {summary?.best_time_months?.join(", ") || summary?.best_time_to_visit}
                </p>
                <p className={styles.bestTimeReason}>{summary.best_time_reasoning}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
