import os
import shutil
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

import pandas as pd
import numpy as np
from backend.data_engine import DataEngine
from backend.agent import AgentOrchestrator
from backend.anomaly_detector import AnomalyDetector

load_dotenv()

app = FastAPI(title="Digital Back Office - AI Data Analyst API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if not os.path.exists(frontend_dist):
    frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend_dist")

data_engine = DataEngine()
agent = AgentOrchestrator(data_engine)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploaded_files")
os.makedirs(UPLOAD_DIR, exist_ok=True)

sample_sales = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sales_data.csv")
sample_cust = os.path.join(os.path.dirname(__file__), "..", "sample_data", "customers.csv")
if os.path.exists(sample_sales):
    data_engine.register_csv("sales_data", sample_sales)
if os.path.exists(sample_cust):
    data_engine.register_csv("customers", sample_cust)

class QueryRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, Any]]] = []

class CustomSQLRequest(BaseModel):
    query: str

class CustomPandasRequest(BaseModel):
    code: str

class AnomalyRequest(BaseModel):
    table_name: str
    target_columns: Optional[List[str]] = None
    contamination: Optional[float] = 0.03

@app.get("/api/health")
def health_check():
    return {"status": "ok", "tables": list(data_engine.tables.keys())}

@app.get("/api/tables")
def get_tables():
    return {
        "tables": data_engine.file_metadata,
        "table_names": list(data_engine.tables.keys())
    }

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        if not file.filename.endswith(".csv"):
            continue
        table_name = os.path.splitext(file.filename)[0]
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        meta = data_engine.register_csv(table_name, file_path)
        results.append(meta)
    
    return {"uploaded": len(results), "metadata": results}

@app.post("/api/query")
def run_query(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return agent.run(request.query, request.history)

@app.post("/api/sql")
def execute_sql(request: CustomSQLRequest):
    return data_engine.execute_sql(request.query)

@app.post("/api/pandas")
def execute_pandas(request: CustomPandasRequest):
    return data_engine.execute_pandas(request.code)

@app.post("/api/anomalies")
def detect_anomalies(request: AnomalyRequest):
    if request.table_name not in data_engine.tables:
        raise HTTPException(status_code=404, detail=f"Table {request.table_name} not found")
    df = data_engine.tables[request.table_name]
    return AnomalyDetector.detect_anomalies(df, request.target_columns, request.contamination or 0.03)

@app.get("/api/quality/{table_name}")
def data_quality_check(table_name: str):
    if table_name not in data_engine.tables:
        raise HTTPException(status_code=404, detail=f"Table {table_name} not found")
    df = data_engine.tables[table_name]
    
    stats = []
    for col in df.columns:
        col_type = str(df[col].dtype)
        null_count = int(df[col].isnull().sum())
        null_pct = round((null_count / len(df)) * 100, 2)
        unique_cnt = int(df[col].nunique())
        
        stat = {
            "column": col,
            "type": col_type,
            "null_count": null_count,
            "null_percentage": null_pct,
            "unique_count": unique_cnt
        }
        if pd.api.types.is_numeric_dtype(df[col]):
            stat["mean"] = round(float(df[col].mean()), 2) if not df[col].dropna().empty else None
            stat["min"] = round(float(df[col].min()), 2) if not df[col].dropna().empty else None
            stat["max"] = round(float(df[col].max()), 2) if not df[col].dropna().empty else None
            stat["std"] = round(float(df[col].std()), 2) if not df[col].dropna().empty else None
        stats.append(stat)

    return {
        "table_name": table_name,
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "quality_metrics": stats
    }

if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
