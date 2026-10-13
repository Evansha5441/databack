# AI-Powered Data Analyst

A full-stack, production-ready AI Data Analyst application that enables users to upload multiple CSV datasets and interact with their data using natural language. Built for the **Digital Back Office Ltd. AI Engineer Assignment**.

---

## Architecture Overview

```
+-------------------------------------------------------------------------+
|                               React Frontend                            |
|     (Vite + Lucide Icons + Chart.js / Bar, Line, Pie, Scatter Plots)    |
+------------------------------------+------------------------------------+
                                     | HTTP / JSON API
+------------------------------------v------------------------------------+
|                               FastAPI Engine                            |
|   - Session & Table Ingestion Registry                                  |
|   - Multi-File Context Manager                                          |
|   - Data Quality Auditor                                                |
+-------------------+--------------------------------+--------------------+
                    |                                |
+-------------------v------------+   +---------------v--------------------+
|       Agent Orchestrator       |   |       Analytical Core Engines      |
|  - Chain-of-Thought Reasoning  |   |  - DuckDB In-Memory OLAP SQL       |
|  - Dynamic SQL / Pandas Gen    |   |  - Pandas Vectorized Execution     |
|  - Code Self-Correction Loop   |   |  - Isolation Forest Outlier Engine |
+--------------------------------+   +------------------------------------+
```

---

## Features

- **Multi-CSV Ingestion & Auto-Registration**: Upload multiple CSV files simultaneously into an in-memory DuckDB analytical engine with inferred schemas and relationship context.
- **Natural Language Interaction**: Ask complex business questions in natural language.
- **Explainable Reasoning (Chain-of-Thought)**: Every answer outlines the plan, generated code, and business insight.
- **Automated Visualization Spec**: Generates Bar, Line, Pie, and Scatter charts based on analytical requirements.
- **Code Execution & Self-Correction**: Executes DuckDB SQL and Pandas code directly on virtual tables, automatically repairing execution errors.
- **Statistical & ML Anomaly Detection**: Uses scikit-learn's `IsolationForest` alongside parametric Z-scores to isolate anomalies and explain standard deviations.
- **Data Quality Auditing**: Real-time auditing of null counts, percentages, cardinality, and numerical distributions.

---

## Example Queries Supported

1. `Which region generated the highest revenue?`
2. `Show monthly sales trends.`
3. `Which products are underperforming?`
4. `What are the top five customers?`
5. `Generate SQL for this analysis.`
6. `Detect anomalies in the dataset.`

---

## Tech Stack

- **Backend**: FastAPI, Uvicorn, DuckDB, Pandas, Scikit-learn, Pydantic, HTTPX
- **Frontend**: React (Vite), Chart.js, react-chartjs-2, Lucide Icons
- **Containerization**: Docker, Docker Compose
- **Testing**: Pytest

---

## Quickstart Guide

### 1. Local Run

#### Prerequisites
- Python 3.10+
- Node.js 18+ (optional if using prebuilt frontend in `frontend/dist`)

#### Backend Setup
```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key"   # Optional: built-in heuristic agent runs if unset
python3 -m uvicorn backend.main:app --port 8888 --host 0.0.0.0
```
Open `http://localhost:8888` in your browser.

#### Frontend Development (Optional)
```bash
cd frontend
npm install
npm run dev
```

---

### 2. Docker Deployment

```bash
docker compose up --build
```
Access the application at `http://localhost:8000`.

---

## Running Test Suite

```bash
PYTHONPATH=. pytest tests/
```

---

## Project Structure

```
├── backend/
│   ├── agent.py              # Orchestrator & self-correction loop
│   ├── anomaly_detector.py   # Isolation Forest & Z-Score detector
│   ├── data_engine.py        # DuckDB in-memory OLAP & Pandas runner
│   └── main.py               # FastAPI REST endpoints
├── frontend/
│   ├── src/
│   │   ├── components/       # ChartViewer & UI components
│   │   ├── App.jsx           # Main chat & data quality interface
│   │   └── index.css         # Modern dark theme styles
├── sample_data/
│   ├── sales_data.csv        # 1,000 transaction records with injected anomalies
│   ├── customers.csv         # Enterprise account profiles
│   └── generate_samples.py   # Dataset generator script
├── tests/
│   └── test_backend.py       # Pytest unit & integration tests
├── Dockerfile                # Multi-stage Docker build
├── docker-compose.yml        # Orchestration file
└── requirements.txt          # Python dependencies
```
