import "./globals.css";

export const metadata = {
  title: "Agentic Travel Planner — AI-Powered Trip Planning",
  description:
    "Plan your perfect trip with our multi-agent AI system. Get optimized itineraries, budget breakdowns, interactive maps, and cultural insights powered by real-time data.",
  keywords: ["travel planner", "AI travel", "itinerary generator", "trip planning"],
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="ambient-bg" />
        {children}
      </body>
    </html>
  );
}
