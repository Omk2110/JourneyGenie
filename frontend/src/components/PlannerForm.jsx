"use client";

import { useState } from "react";
import styles from "./PlannerForm.module.css";

const PREFERENCE_OPTIONS = [
  { id: "cultural", label: "🏛️ Cultural", icon: "🏛️" },
  { id: "adventure", label: "🧗 Adventure", icon: "🧗" },
  { id: "food", label: "🍜 Food & Cuisine", icon: "🍜" },
  { id: "relaxation", label: "🧘 Relaxation", icon: "🧘" },
  { id: "nightlife", label: "🌙 Nightlife", icon: "🌙" },
  { id: "nature", label: "🌿 Nature", icon: "🌿" },
  { id: "shopping", label: "🛍️ Shopping", icon: "🛍️" },
  { id: "family", label: "👨‍👩‍👧‍👦 Family", icon: "👨‍👩‍👧‍👦" },
];

/**
 * Format number in Indian locale style (e.g., 1,50,000)
 */
function formatINR(num) {
  if (!num && num !== 0) return "0";
  return num.toLocaleString("en-IN");
}

export default function PlannerForm({ onSubmit }) {
  const [destination, setDestination] = useState("");
  const [days, setDays] = useState(5);
  const [budget, setBudget] = useState(50000);
  const [people, setPeople] = useState(2);
  const [preferences, setPreferences] = useState([]);
  const [origin, setOrigin] = useState("");
  const [startDate, setStartDate] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);

  const togglePreference = (pref) => {
    setPreferences((prev) =>
      prev.includes(pref) ? prev.filter((p) => p !== pref) : [...prev, pref]
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!destination.trim()) return;

    onSubmit({
      destination: destination.trim(),
      days,
      budget,
      people,
      preferences,
      origin: origin.trim() || undefined,
      start_date: startDate || undefined,
    });
  };

  const perPersonPerDay = (budget / Math.max(people, 1) / Math.max(days, 1)).toFixed(0);

  return (
    <form className={styles.form} onSubmit={handleSubmit} id="planner-form">
      <div className={styles.formHeader}>
        <h2 className={styles.formTitle}>Plan Your Dream Trip</h2>
        <p className={styles.formDesc}>
          Our AI agents will craft the perfect itinerary for you
        </p>
      </div>

      {/* Main Fields */}
      <div className={styles.grid}>
        {/* Destination */}
        <div className={`${styles.field} ${styles.fieldFull}`}>
          <label className="label" htmlFor="destination">
            Where do you want to go?
          </label>
          <input
            id="destination"
            className={`input ${styles.inputLarge}`}
            type="text"
            placeholder="e.g., Goa, Jaipur, Paris, Tokyo, Bali..."
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            required
            autoFocus
          />
        </div>

        {/* Days */}
        <div className={styles.field}>
          <label className="label" htmlFor="days">
            Duration
          </label>
          <div className={styles.numberInput}>
            <button
              type="button"
              className={styles.numBtn}
              onClick={() => setDays(Math.max(1, days - 1))}
            >
              −
            </button>
            <input
              id="days"
              className="input"
              type="number"
              min="1"
              max="30"
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              style={{ textAlign: "center" }}
            />
            <span className={styles.numLabel}>days</span>
            <button
              type="button"
              className={styles.numBtn}
              onClick={() => setDays(Math.min(30, days + 1))}
            >
              +
            </button>
          </div>
        </div>

        {/* People */}
        <div className={styles.field}>
          <label className="label" htmlFor="people">
            Travelers
          </label>
          <div className={styles.numberInput}>
            <button
              type="button"
              className={styles.numBtn}
              onClick={() => setPeople(Math.max(1, people - 1))}
            >
              −
            </button>
            <input
              id="people"
              className="input"
              type="number"
              min="1"
              max="20"
              value={people}
              onChange={(e) => setPeople(Number(e.target.value))}
              style={{ textAlign: "center" }}
            />
            <span className={styles.numLabel}>people</span>
            <button
              type="button"
              className={styles.numBtn}
              onClick={() => setPeople(Math.min(20, people + 1))}
            >
              +
            </button>
          </div>
        </div>

        {/* Budget */}
        <div className={`${styles.field} ${styles.fieldFull}`}>
          <label className="label" htmlFor="budget">
            Total Budget (₹ INR)
          </label>
          <div className={styles.budgetWrap}>
            <input
              id="budget"
              className={`input ${styles.budgetInput}`}
              type="range"
              min="5000"
              max="500000"
              step="1000"
              value={budget}
              onChange={(e) => setBudget(Number(e.target.value))}
            />
            <div className={styles.budgetInfo}>
              <span className={styles.budgetAmount}>₹{formatINR(budget)}</span>
              <span className={styles.budgetPpd}>
                ~₹{formatINR(Number(perPersonPerDay))}/person/day
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Preferences */}
      <div className={styles.section}>
        <label className="label">Travel Style & Preferences</label>
        <div className={styles.tags}>
          {PREFERENCE_OPTIONS.map((pref) => (
            <button
              key={pref.id}
              type="button"
              className={`tag ${preferences.includes(pref.id) ? "active" : ""}`}
              onClick={() => togglePreference(pref.id)}
              id={`pref-${pref.id}`}
            >
              {pref.label}
            </button>
          ))}
        </div>
      </div>

      {/* Advanced Options */}
      <button
        type="button"
        className={styles.advancedToggle}
        onClick={() => setShowAdvanced(!showAdvanced)}
      >
        {showAdvanced ? "▾ Hide" : "▸ Show"} Advanced Options
      </button>

      {showAdvanced && (
        <div className={`${styles.advancedFields} animate-fade-in`}>
          <div className={styles.grid}>
            <div className={styles.field}>
              <label className="label" htmlFor="origin">
                Departing From
              </label>
              <input
                id="origin"
                className="input"
                type="text"
                placeholder="e.g., Mumbai, Delhi, Bangalore..."
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
              />
            </div>
            <div className={styles.field}>
              <label className="label" htmlFor="start-date">
                Start Date
              </label>
              <input
                id="start-date"
                className="input"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Submit */}
      <button
        type="submit"
        className={`btn btn-primary ${styles.submitBtn}`}
        disabled={!destination.trim()}
        id="submit-plan"
      >
        <span>🚀</span>
        Plan My Trip
      </button>
    </form>
  );
}
