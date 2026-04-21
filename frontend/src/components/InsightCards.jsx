"use client";

import styles from "./InsightCards.module.css";

const CATEGORY_STYLES = {
  weather: { icon: "🌤️", color: "#06b6d4" },
  cultural: { icon: "🏛️", color: "#8b5cf6" },
  budget: { icon: "💰", color: "#10b981" },
  timing: { icon: "⏰", color: "#f59e0b" },
  general: { icon: "💡", color: "#3b82f6" },
};

export default function InsightCards({ insights, compact = false }) {
  if (!insights || insights.length === 0) return null;

  const displayInsights = compact ? insights.slice(0, 3) : insights;

  return (
    <div className={`${styles.container} ${compact ? styles.compact : ""}`}>
      <h3 className={styles.title}>💡 AI Insights</h3>
      <div className={styles.grid}>
        {displayInsights.map((insight, i) => {
          const cat = insight.category?.toLowerCase() || "general";
          const style = CATEGORY_STYLES[cat] || CATEGORY_STYLES.general;

          return (
            <div
              key={i}
              className={styles.card}
              style={{ borderLeftColor: style.color }}
            >
              <div className={styles.cardHeader}>
                <span className={styles.cardIcon}>{style.icon}</span>
                <span className={styles.cardTitle}>{insight.title}</span>
              </div>
              <p className={styles.cardDesc}>{insight.description}</p>
              <span
                className={styles.cardCategory}
                style={{ color: style.color }}
              >
                {cat}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
