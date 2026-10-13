import pytest
from backend.data_engine import DataEngine
from backend.anomaly_detector import AnomalyDetector
from backend.agent import AgentOrchestrator

def test_data_engine_csv_and_sql():
    engine = DataEngine()
    meta = engine.register_csv("sales_test", "sample_data/sales_data.csv")
    assert meta["row_count"] == 1000
    assert "sales_test" in engine.tables

    result = engine.execute_sql("SELECT region, SUM(revenue) as total_rev FROM sales_test GROUP BY region")
    assert result["success"] is True
    assert len(result["data"]) > 0

def test_data_engine_pandas():
    engine = DataEngine()
    engine.register_csv("sales_test", "sample_data/sales_data.csv")
    py_code = "sales_test.groupby('region')['revenue'].sum().reset_index()"
    result = engine.execute_pandas(py_code)
    assert result["success"] is True
    assert len(result["data"]) > 0

def test_anomaly_detector():
    engine = DataEngine()
    engine.register_csv("sales_test", "sample_data/sales_data.csv")
    df = engine.tables["sales_test"]
    anomalies = AnomalyDetector.detect_anomalies(df, ["revenue", "profit"])
    assert "anomalies" in anomalies
    assert anomalies["anomaly_count"] > 0
    assert len(anomalies["anomalies"]) > 0

def test_agent_orchestrator_fallback_region():
    engine = DataEngine()
    engine.register_csv("sales_data", "sample_data/sales_data.csv")
    agent = AgentOrchestrator(engine)
    res = agent.run("Which region generated the highest revenue?")
    assert res["action_type"] == "sql"
    assert "total_revenue" in res["code"]
    assert res["result"]["success"] is True

def test_agent_orchestrator_fallback_anomalies():
    engine = DataEngine()
    engine.register_csv("sales_data", "sample_data/sales_data.csv")
    agent = AgentOrchestrator(engine)
    res = agent.run("Detect anomalies in the dataset")
    assert res["action_type"] == "anomaly"
    assert res["result"]["success"] is True
    assert res["result"]["total_rows"] > 0
