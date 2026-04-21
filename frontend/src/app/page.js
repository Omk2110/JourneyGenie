"use client";

import { useState } from "react";
import PlannerForm from "@/components/PlannerForm";
import ResultsDashboard from "@/components/ResultsDashboard";
import LoadingState from "@/components/LoadingState";
import { createPlan } from "@/lib/api";
import styles from "./page.module.css";

export default function Home() {
  const [planData, setPlanData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentAgent, setCurrentAgent] = useState("");

  const handleSubmit = async (input) => {
    setLoading(true);
    setError(null);
    setPlanData(null);

    // Simulate agent progress
    const agents = [
      "Planner Agent — analyzing your request...",
      "Group Optimizer — tailoring for your group...",
      "Search Agent — finding hotels, attractions, flights...",
      "Budget Optimizer — maximizing value...",
      "Itinerary Generator — crafting your schedule...",
      "Map Agent — optimizing routes...",
      "Context Agent — gathering weather & cultural insights...",
      "Validator — checking feasibility...",
      "Report Generator — assembling your plan...",
    ];

    let agentIdx = 0;
    const agentInterval = setInterval(() => {
      if (agentIdx < agents.length) {
        setCurrentAgent(agents[agentIdx]);
        agentIdx++;
      }
    }, 2500);

    try {
      const result = await createPlan(input);
      clearInterval(agentInterval);

      if (result.success) {
        setPlanData(result.data);
      } else {
        setError(result.errors?.join(", ") || "Planning failed. Please try again.");
      }
    } catch (err) {
      clearInterval(agentInterval);
      setError(err.message || "Failed to connect to the backend. Is the server running?");
    } finally {
      setLoading(false);
      setCurrentAgent("");
    }
  };

  const handleReset = () => {
    setPlanData(null);
    setError(null);
  };

  return (
    <main className={styles.main}>
      <div className="page-container">
        {/* Header */}
        <header className={styles.header}>
          <div className={styles.logo}>
            <span className={styles.logoIcon}>✈️</span>
            <h1 className={styles.logoText}>
              <span className="gradient-text">Agentic</span> Travel Planner
            </h1>
          </div>
          <p className={styles.subtitle}>
            AI-powered multi-agent system that plans your perfect trip
          </p>
        </header>

        {/* Content */}
        {!planData && !loading && (
          <div className="animate-fade-in-up">
            <PlannerForm onSubmit={handleSubmit} />
          </div>
        )}

        {loading && (
          <div className="animate-fade-in">
            <LoadingState currentAgent={currentAgent} />
          </div>
        )}

        {error && (
          <div className={styles.error}>
            <div className={styles.errorContent}>
              <span className={styles.errorIcon}>⚠️</span>
              <div>
                <h3>Something went wrong</h3>
                <p>{error}</p>
              </div>
            </div>
            <button className="btn btn-secondary" onClick={handleReset}>
              Try Again
            </button>
          </div>
        )}

        {planData && (
          <div className="animate-fade-in-up">
            <div className={styles.resultHeader}>
              <button className="btn btn-secondary" onClick={handleReset}>
                ← Plan Another Trip
              </button>
            </div>
            <ResultsDashboard data={planData} />
          </div>
        )}
      </div>
    </main>
  );
}
