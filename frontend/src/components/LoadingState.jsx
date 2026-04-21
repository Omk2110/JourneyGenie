"use client";

import styles from "./LoadingState.module.css";

const AGENT_ICONS = {
  Planner: "🗺️",
  Group: "👥",
  Search: "🔍",
  Budget: "💰",
  Itinerary: "📋",
  Map: "🗺️",
  Context: "🌍",
  Validator: "✅",
  Report: "📊",
};

export default function LoadingState({ currentAgent }) {
  const agentKey = currentAgent ? currentAgent.split(" ")[0] : "";
  const icon = AGENT_ICONS[agentKey] || "⚙️";

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        {/* Spinner */}
        <div className={styles.spinnerWrap}>
          <div className={styles.spinner}></div>
          <span className={styles.spinnerIcon}>{icon}</span>
        </div>

        <h3 className={styles.title}>Planning Your Trip</h3>

        {currentAgent && (
          <p className={styles.agent}>{currentAgent}</p>
        )}

        {/* Agent Pipeline Visualization */}
        <div className={styles.pipeline}>
          {Object.entries(AGENT_ICONS).map(([name, ic], idx) => {
            const isActive = currentAgent?.includes(name);
            const isPast =
              currentAgent &&
              Object.keys(AGENT_ICONS).indexOf(name) <
                Object.keys(AGENT_ICONS).findIndex((k) => currentAgent?.includes(k));

            return (
              <div
                key={name}
                className={`${styles.pipelineNode} ${isActive ? styles.active : ""} ${
                  isPast ? styles.past : ""
                }`}
              >
                <span className={styles.nodeIcon}>{ic}</span>
                <span className={styles.nodeName}>{name}</span>
              </div>
            );
          })}
        </div>

        <p className={styles.hint}>
          Our 9 AI agents are working together to find the best options for you...
        </p>
      </div>
    </div>
  );
}
