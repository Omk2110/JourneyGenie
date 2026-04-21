"use client";

import styles from "./ItineraryTimeline.module.css";

const CATEGORY_ICONS = {
  attraction: "🏛️",
  restaurant: "🍽️",
  meal: "🍽️",
  transport: "🚗",
  hotel: "🏨",
  nature: "🌿",
  shopping: "🛍️",
  activity: "🎯",
  entertainment: "🎭",
};

const CATEGORY_COLORS = {
  attraction: "#3b82f6",
  restaurant: "#f59e0b",
  meal: "#f59e0b",
  transport: "#8b5cf6",
  hotel: "#06b6d4",
  nature: "#10b981",
  shopping: "#ec4899",
  activity: "#14b8a6",
  entertainment: "#f97316",
};

export default function ItineraryTimeline({ itinerary, compact = false }) {
  if (!itinerary || itinerary.length === 0) {
    return (
      <div className={styles.empty}>
        <p>No itinerary data available</p>
      </div>
    );
  }

  return (
    <div className={`${styles.timeline} ${compact ? styles.compact : ""}`}>
      {itinerary.map((day) => (
        <div key={day.day} className={styles.dayBlock}>
          {/* Day Header */}
          <div className={styles.dayHeader}>
            <div className={styles.dayBadge}>Day {day.day}</div>
            <div className={styles.dayMeta}>
              <h3 className={styles.dayTheme}>{day.theme || `Day ${day.day}`}</h3>
              <div className={styles.dayStats}>
                <span>{day.activities?.length || 0} activities</span>
                {day.total_cost > 0 && <span>~${day.total_cost.toFixed(0)}</span>}
                {day.travel_time_minutes > 0 && (
                  <span>{day.travel_time_minutes} min travel</span>
                )}
              </div>
            </div>
          </div>

          {/* Activities */}
          <div className={styles.activities}>
            {(day.activities || []).map((activity, idx) => {
              const cat = activity.category?.toLowerCase() || "activity";
              const icon = CATEGORY_ICONS[cat] || "📍";
              const color = CATEGORY_COLORS[cat] || "#64748b";

              return (
                <div key={idx} className={styles.activity}>
                  <div className={styles.activityLine}>
                    <div
                      className={styles.activityDot}
                      style={{ background: color, boxShadow: `0 0 8px ${color}66` }}
                    />
                    {idx < (day.activities?.length || 0) - 1 && (
                      <div className={styles.connector} />
                    )}
                  </div>

                  <div className={styles.activityContent}>
                    <div className={styles.activityHeader}>
                      <span className={styles.activityIcon}>{icon}</span>
                      <span className={styles.activityName}>{activity.name}</span>
                      {activity.time && (
                        <span className={styles.activityTime}>{activity.time}</span>
                      )}
                    </div>

                    {!compact && (
                      <div className={styles.activityDetails}>
                        {activity.description && (
                          <p className={styles.activityDesc}>{activity.description}</p>
                        )}
                        <div className={styles.activityMeta}>
                          {activity.duration_minutes > 0 && (
                            <span>⏱ {activity.duration_minutes}min</span>
                          )}
                          {activity.estimated_cost > 0 && (
                            <span>💵 ${activity.estimated_cost}</span>
                          )}
                          {activity.rating > 0 && <span>⭐ {activity.rating}</span>}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
