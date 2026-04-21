# ✈️ Agentic Travel Planner

A production-ready, multi-agent AI travel planning system powered by **LangGraph**, **LangChain**, and **Google Gemini**. The system uses 9 specialized AI agents to generate optimized, budget-aware, group-aware travel itineraries with interactive map visualization.

This system is fully integrated with **free-tier APIs** (Serper, OpenTripMap, WeatherAPI, RapidAPI, Geoapify) and localized for the **Indian Audience (INR Currency)**. It also features **LangSmith tracing** for complete visibility into the AI's reasoning.

## 🏗️ Architecture

```
Frontend (Next.js)  ←→  Backend (FastAPI)  ←→  Agent Pipeline (LangGraph)
     ↑                        ↑                         ↑
  Leaflet Maps           REST API              9 Specialized Agents
  Chart.js              Pydantic Models        Tool Integrations (6 Free APIs)
  React Components      CORS + Auth            LLM Abstraction & LangSmith
```

### Agent Pipeline Flow

```
Planner → Group Optimizer → Search → Budget Optimizer → Itinerary Generator
    → Map Agent → Context Agent → Validator → Report Generator
```

| Agent | Responsibility |
|-------|---------------|
| **Planner** | Parses user intent, creates planning strategy (Budget tiers in INR) |
| **Group Optimizer** | Classifies group type (solo/couple/family/friends), adjusts preferences |
| **Search** | Parallel API calls for hotels, attractions, flights, weather |
| **Budget Optimizer** | Scores options, selects optimal combinations within budget (₹) |
| **Itinerary Generator** | Creates day-wise schedule with proximity clustering |
| **Map Agent** | Geocodes places, optimizes routes using nearest-neighbor |
| **Context** | Weather insights, cultural tips, best-time-to-visit |
| **Validator** | Checks budget compliance, travel time feasibility |
| **Report Generator** | Assembles structured JSON output for frontend |

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- At least one LLM API key (Google Gemini recommended)

### 1. Clone & Setup Environment

```bash
# Backend
cd "T5 Lets Travel"
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r backend/requirements.txt
```

### 2. Configure API Keys

```bash
# Copy the example env file
copy .env.example .env    # Windows
cp .env.example .env      # macOS/Linux
```

Edit `.env` and add your API keys:

```env
# Required (at least one LLM key):
GOOGLE_API_KEY=your_gemini_key_here

# External APIs (Optional, system uses simulated fallbacks if missing):
SERPER_API_KEY=your_serper_key
GEOAPIFY_API_KEY=your_geoapify_key
MAPTILER_API_KEY=your_maptiler_key
X_RAPIDAPI_KEY=your_rapidapi_key
WEATHERAPI_API_KEY=your_weatherapi_key
OPENTRIPMAP_API_KEY=your_opentripmap_key

# LangSmith Tracing
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key
```

### 3. Start Backend

```bash
.\venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Setup & Start Frontend

```bash
cd frontend

# Copy env
copy .env.local.example .env.local

# Install dependencies (already done during setup)
npm install

# Start dev server
npm run dev
```

### 5. Open the App

Navigate to **http://localhost:3000** in your browser.

## 🔑 API Keys Guide

| Key | Service | Required | Get it at |
|-----|---------|----------|-----------|
| `GOOGLE_API_KEY` | Google Gemini LLM | ✅ Yes | [ai.google.dev](https://ai.google.dev/) |
| `OPENAI_API_KEY` | OpenAI GPT | Alternative | [platform.openai.com](https://platform.openai.com/) |
| `CEREBRAS_API_KEY` | Cerebras LLM | Alternative | [cerebras.ai](https://cerebras.ai/) |
| `SERPER_API_KEY` | Web Search | Optional | [serper.dev](https://serper.dev/) |
| `GEOAPIFY_API_KEY`| Maps, Geocoding, Routing| Optional| [geoapify.com](https://geoapify.com/) |
| `OPENTRIPMAP_API_KEY`| Places & Attractions | Optional | [opentripmap.io](https://opentripmap.io/) |
| `WEATHERAPI_API_KEY`| Weather & Forecast | Optional | [weatherapi.com](https://weatherapi.com/) |
| `X_RAPIDAPI_KEY`| Hotel & Flight Search | Optional | [Booking.com v15 rapidapi.com](https://rapidapi.com/) |
| `LANGSMITH_API_KEY`| LangSmith Tracing | Optional | [smith.langchain.com](https://smith.langchain.com/) |

> **Note:** The system works with just an LLM API key. All other APIs have built-in, 3-tier fallbacks that provide realistic simulated data for major international and Indian cities.

## 📁 Project Structure

```
T5 Lets Travel/
├── backend/
│   ├── main.py                 # FastAPI server
│   ├── config.py               # Environment & settings (INR currency configured)
│   ├── llm/provider.py         # Multi-provider LLM abstraction
│   ├── agents/
│   │   ├── graph.py            # LangGraph graph definition
│   │   ├── planner.py          # Planner Agent
│   │   ├── ...                 # Other Agents
│   │   └── report.py           # Report Generator Agent
│   ├── tools/
│   │   ├── google_places.py    # OpenTripMap API implementation
│   │   ├── serpapi_search.py   # Serper API integration
│   │   ├── weather.py          # WeatherAPI info & forecasts
│   │   ├── flights.py          # RapidAPI Flights (Booking.com v15)
│   │   ├── hotels.py           # RapidAPI Hotels (Booking.com v15)
│   │   ├── geocoding.py        # Geoapify Geocoding
│   │   └── distance_matrix.py  # Geoapify Distance & Routing
│   ├── cache/memory_cache.py   # TTL-based in-memory cache
│   ├── models/schemas.py       # Pydantic data models
│   └── requirements.txt        # Backend dependencies (Includes LangChain & LangSmith)
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.js         # Main page
│   │   │   └── globals.css     # Design system
│   │   ├── components/
│   │   │   ├── PlannerForm.jsx       # Input form (INR values)
│   │   │   ├── ResultsDashboard.jsx  # Tabbed results view
│   │   │   ├── MapView.jsx           # Leaflet interactive map
│   │   │   ├── BudgetChart.jsx       # Chart.js doughnut chart
│   │   │   ├── ItineraryTimeline.jsx # Vertical timeline
│   │   │   ├── InsightCards.jsx      # AI reasoning cards
│   │   │   └── LoadingState.jsx      # Agent progress display
│   │   └── lib/api.js          # Backend API client
│   └── package.json
├── .env.example
├── .gitignore
└── README.md
```

## 🎨 Frontend Features

- **Dark glassmorphism design** with gradient accents
- **Localized for INR** (₹) with Indian number formatting natively supported
- **Interactive Leaflet map** with day-colored markers and route lines
- **Budget doughnut chart** with category breakdown
- **Vertical timeline** with activity cards and connectors
- **AI insight cards** showing reasoning for decisions
- **Agent progress visualization** during planning
- **Responsive design** for mobile and desktop

## ⚙️ Technical Features

- **Complete LangSmith Integration** out of the box for viewing agent traces
- **API Fallback Chain** - Falls back to web search and simulated datasets to ensure 100% uptime
- **Multi-agent LangGraph pipeline** with 9 nodes and conditional retry edges
- **Multi-provider LLM support** (Gemini, OpenAI, Cerebras)
- **Parallel API calls** via `asyncio.gather()` for performance
- **In-memory TTL cache** to avoid redundant API calls
- **Composite scoring function** for budget optimization
- **Nearest-neighbor TSP heuristic** for route optimization
- **Structured JSON output** matching a strict schema

## 📄 License

MIT
