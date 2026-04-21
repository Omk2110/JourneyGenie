"use client";

import { useEffect, useRef } from "react";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";
import { Doughnut } from "react-chartjs-2";
import styles from "./BudgetChart.module.css";

ChartJS.register(ArcElement, Tooltip, Legend);

const CATEGORY_COLORS = {
  accommodation: "#3b82f6",
  transport: "#8b5cf6",
  food: "#f59e0b",
  activities: "#10b981",
  miscellaneous: "#64748b",
};

const CATEGORY_ICONS = {
  accommodation: "🏨",
  transport: "🚗",
  food: "🍽️",
  activities: "🎯",
  miscellaneous: "📦",
};

/**
 * Format number in Indian locale style (e.g., 1,50,000)
 */
function formatINR(num) {
  if (!num && num !== 0) return "0";
  return Number(num).toLocaleString("en-IN");
}

export default function BudgetChart({ breakdown, large = false }) {
  if (!breakdown) return null;

  const categories = ["accommodation", "transport", "food", "activities", "miscellaneous"];
  const values = categories.map((c) => breakdown[c] || 0);
  const total = breakdown.total_estimated || values.reduce((a, b) => a + b, 0);

  const data = {
    labels: categories.map((c) => c.charAt(0).toUpperCase() + c.slice(1)),
    datasets: [
      {
        data: values,
        backgroundColor: categories.map((c) => CATEGORY_COLORS[c]),
        borderColor: "transparent",
        borderWidth: 0,
        hoverOffset: 8,
        cutout: "65%",
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "rgba(17, 24, 39, 0.95)",
        titleFont: { family: "'Inter', sans-serif", size: 13 },
        bodyFont: { family: "'Inter', sans-serif", size: 12 },
        padding: 12,
        cornerRadius: 8,
        callbacks: {
          label: (ctx) => {
            const val = ctx.parsed;
            const pct = total > 0 ? ((val / total) * 100).toFixed(0) : 0;
            return ` ₹${formatINR(val)} (${pct}%)`;
          },
        },
      },
    },
  };

  return (
    <div className={`${styles.container} ${large ? styles.large : ""}`}>
      <h3 className={styles.title}>💰 Budget Allocation</h3>

      <div className={styles.chartWrap}>
        <Doughnut data={data} options={options} />
        <div className={styles.chartCenter}>
          <span className={styles.chartTotal}>₹{formatINR(total)}</span>
          <span className={styles.chartLabel}>Total</span>
        </div>
      </div>

      {/* Legend */}
      <div className={styles.legend}>
        {categories.map((cat, i) => {
          const pct = total > 0 ? ((values[i] / total) * 100).toFixed(0) : 0;
          return (
            <div key={cat} className={styles.legendItem}>
              <span
                className={styles.legendDot}
                style={{ background: CATEGORY_COLORS[cat] }}
              />
              <span className={styles.legendLabel}>
                {CATEGORY_ICONS[cat]} {cat}
              </span>
              <span className={styles.legendValue}>
                ₹{formatINR(values[i])}
              </span>
              <span className={styles.legendPct}>{pct}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
