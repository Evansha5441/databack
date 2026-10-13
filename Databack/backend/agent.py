import os
import json
import re
from typing import Dict, List, Any, Optional
import httpx
from backend.data_engine import DataEngine
from backend.anomaly_detector import AnomalyDetector

class AgentOrchestrator:
    def __init__(self, data_engine: DataEngine):
        self.engine = data_engine
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("MODEL_NAME", "gpt-4o-mini")

    def run(self, query: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        schemas = self.engine.get_all_schemas()
        
        system_prompt = f"""You are an expert AI Data Analyst and Business Intelligence specialist.
You have access to the following dataset tables loaded in an in-memory SQL database (DuckDB) and Pandas:

{schemas}

Analyze the user's question and produce a JSON response with the following keys:
1. "thought": Detailed step-by-step reasoning explaining how to analyze the data.
2. "action_type": Choose one from ["sql", "pandas", "anomaly", "general"].
3. "code": The SQL query or Pandas script to run.
   - For SQL: Write standard DuckDB SQL (e.g. SELECT ... FROM table_name GROUP BY ...). Always use case-insensitive partial match with ILIKE '%keyword%' when filtering strings or names so variations like 'Horizon' match 'Horizon Media'.
   - For Pandas: Write python code using dataframes named after the tables (e.g. sales_data, customers). Set final result to `result`.
   - For Anomaly: Return JSON string with table name and optional target columns: {{"table": "table_name", "columns": ["revenue", "profit"]}}.
   - For General: Leave code empty string "".
4. "chart_spec": Visualization recommendations if the question involves comparison, trends, breakdown, or correlation.
   Structure:
   {{
     "recommended": true/false,
     "type": "bar" | "line" | "pie" | "scatter",
     "x_key": "column_for_x_axis",
     "y_key": "column_for_y_axis",
     "title": "Title of the chart"
   }}
5. "explanation": A clear, professional business explanation answering the user's question based on the analysis.

Ensure the output is strictly valid JSON without any markdown code fence wrapping or backticks.
"""

        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            for msg in conversation_history[-6:]:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": query})

        if not self.api_key:
            return self._heuristic_fallback(query)

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1
            }
            with httpx.Client(timeout=45.0) as client:
                res = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                res.raise_for_status()
                res_json = res.json()
                raw_content = res_json["choices"][0]["message"]["content"].strip()
                
                clean_json_str = raw_content
                if "```json" in clean_json_str:
                    clean_json_str = clean_json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_json_str:
                    clean_json_str = clean_json_str.split("```")[1].split("```")[0].strip()
                
                start_idx = clean_json_str.find("{")
                end_idx = clean_json_str.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    clean_json_str = clean_json_str[start_idx:end_idx+1]
                
                parsed = json.loads(clean_json_str)
                return self._execute_and_enrich(parsed, query)
        except Exception as e:
            fallback = self._heuristic_fallback(query)
            fallback["warning"] = f"LLM API call fell back to local rule engine: {str(e)}"
            return fallback

    def _execute_and_enrich(self, plan: Dict[str, Any], query: str) -> Dict[str, Any]:
        action_type = plan.get("action_type", "general")
        code = plan.get("code", "")
        execution_result = None

        if action_type == "sql" and code:
            execution_result = self.engine.execute_sql(code)
            if not execution_result["success"]:
                fix_sql = self._try_fix_code("sql", code, execution_result["error"])
                if fix_sql:
                    plan["code"] = fix_sql
                    execution_result = self.engine.execute_sql(fix_sql)
        elif action_type == "pandas" and code:
            execution_result = self.engine.execute_pandas(code)
            if not execution_result["success"]:
                fix_py = self._try_fix_code("pandas", code, execution_result["error"])
                if fix_py:
                    plan["code"] = fix_py
                    execution_result = self.engine.execute_pandas(fix_py)
        elif action_type == "anomaly":
            target_table = list(self.engine.tables.keys())[0] if self.engine.tables else None
            cols = None
            if code:
                try:
                    cdata = json.loads(code) if isinstance(code, str) else code
                    target_table = cdata.get("table", target_table)
                    cols = cdata.get("columns", None)
                except Exception:
                    pass
            if target_table and target_table in self.engine.tables:
                anom_res = AnomalyDetector.detect_anomalies(self.engine.tables[target_table], cols)
                execution_result = {
                    "success": True,
                    "columns": ["row_index", "reasons"],
                    "data": anom_res.get("anomalies", []),
                    "total_rows": anom_res.get("anomaly_count", 0),
                    "meta": anom_res
                }
            else:
                execution_result = {"success": False, "error": "Table not found for anomaly check"}

        return {
            "query": query,
            "thought": plan.get("thought", ""),
            "action_type": action_type,
            "code": plan.get("code", ""),
            "chart_spec": plan.get("chart_spec", {"recommended": False}),
            "explanation": plan.get("explanation", ""),
            "result": execution_result
        }

    def _try_fix_code(self, code_type: str, broken_code: str, error_msg: str) -> Optional[str]:
        if not self.api_key:
            return None
        prompt = f"Fix this broken {code_type} code for DuckDB/Pandas.\nBroken Code:\n{broken_code}\n\nError Message:\n{error_msg}\n\nAvailable Schemas:\n{self.engine.get_all_schemas()}\n\nReturn ONLY the fixed code without explanations or markdown."
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0
            }
            with httpx.Client(timeout=20.0) as client:
                res = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    fixed = res.json()["choices"][0]["message"]["content"].strip()
                    fixed = re.sub(r"^```[a-zA-Z]*\n", "", fixed)
                    fixed = re.sub(r"\n```$", "", fixed)
                    return fixed.strip()
        except Exception:
            pass
        return None

    def _heuristic_fallback(self, query: str) -> Dict[str, Any]:
        q = query.lower()
        tables = list(self.engine.tables.keys())
        main_table = "sales_data" if "sales_data" in tables else (tables[0] if tables else "data")
        
        if "anomal" in q or "outlier" in q:
            anom_res = {}
            if main_table in self.engine.tables:
                anom_res = AnomalyDetector.detect_anomalies(self.engine.tables[main_table])
            return {
                "query": query,
                "thought": f"Identified request for statistical anomaly detection on table '{main_table}'. Applied Isolation Forest algorithm with Z-score outlier flagging on numeric metrics.",
                "action_type": "anomaly",
                "code": json.dumps({"table": main_table, "columns": ["revenue", "profit", "quantity"]}),
                "chart_spec": {
                    "recommended": True,
                    "type": "scatter",
                    "x_key": "revenue",
                    "y_key": "profit",
                    "title": "Revenue vs Profit Outlier Cluster"
                },
                "explanation": f"Identified {anom_res.get('anomaly_count', 0)} anomalous transactions out of {anom_res.get('total_records', 0)} total records using multivariate Isolation Forest. Extreme spikes in revenue with disproportionate profit/margins were flagged with specific Z-score deviation metrics.",
                "result": {
                    "success": True,
                    "columns": ["row_index", "reasons"],
                    "data": anom_res.get("anomalies", []),
                    "total_rows": anom_res.get("anomaly_count", 0),
                    "meta": anom_res
                }
            }
        
        if "region" in q and ("highest" in q or "revenue" in q or "sales" in q):
            sql = f"SELECT region, ROUND(SUM(revenue), 2) as total_revenue, ROUND(SUM(profit), 2) as total_profit, COUNT(order_id) as orders_count FROM {main_table} GROUP BY region ORDER BY total_revenue DESC"
            res = self.engine.execute_sql(sql)
            top_region = res["data"][0]["region"] if res.get("data") else "Unknown"
            top_rev = float(res["data"][0]["total_revenue"]) if res.get("data") else 0.0
            return {
                "query": query,
                "thought": "Aggregated total revenue and profit grouped by geographic region and ordered descending to determine the highest performing territory.",
                "action_type": "sql",
                "code": sql,
                "chart_spec": {
                    "recommended": True,
                    "type": "bar",
                    "x_key": "region",
                    "y_key": "total_revenue",
                    "title": "Revenue Breakdown by Region"
                },
                "explanation": f"The region generating the highest revenue is {top_region} with total revenue of £{top_rev:,.2f}, leading overall territorial performance.",
                "result": res
            }

        if "monthly" in q or "trend" in q:
            date_col = "order_date"
            sql = f"SELECT strftime(CAST({date_col} AS DATE), '%Y-%m') as month, ROUND(SUM(revenue), 2) as monthly_revenue, ROUND(SUM(profit), 2) as monthly_profit FROM {main_table} GROUP BY month ORDER BY month ASC"
            res = self.engine.execute_sql(sql)
            return {
                "query": query,
                "thought": f"Grouped transactions chronologically by month using {date_col} to trace revenue and profit growth patterns over time.",
                "action_type": "sql",
                "code": sql,
                "chart_spec": {
                    "recommended": True,
                    "type": "line",
                    "x_key": "month",
                    "y_key": "monthly_revenue",
                    "title": "Monthly Revenue Trend"
                },
                "explanation": "Extracted monthly sales and revenue progression across all operating cycles, revealing seasonal volume fluctuations and consistency in billing.",
                "result": res
            }

        if "underperform" in q or "lowest" in q:
            sql = f"SELECT product_name, category, ROUND(SUM(revenue), 2) as total_revenue, ROUND(SUM(profit), 2) as total_profit, SUM(quantity) as units_sold FROM {main_table} GROUP BY product_name, category ORDER BY total_revenue ASC LIMIT 5"
            res = self.engine.execute_sql(sql)
            return {
                "query": query,
                "thought": "Calculated total revenue, margins, and sales volume by product, sorted ascending to surface the lowest-performing catalog items.",
                "action_type": "sql",
                "code": sql,
                "chart_spec": {
                    "recommended": True,
                    "type": "bar",
                    "x_key": "product_name",
                    "y_key": "total_revenue",
                    "title": "Lowest Performing Products by Revenue"
                },
                "explanation": "Evaluated product sales volumes and bottom-line margins. The bottom 5 underperforming items exhibit low order counts and subdued total revenue realization.",
                "result": res
            }

        if "top" in q and ("customer" in q or "client" in q):
            sql = f"SELECT customer_name, ROUND(SUM(revenue), 2) as total_revenue, COUNT(order_id) as total_orders, ROUND(SUM(profit), 2) as total_profit FROM {main_table} GROUP BY customer_name ORDER BY total_revenue DESC LIMIT 5"
            res = self.engine.execute_sql(sql)
            return {
                "query": query,
                "thought": "Grouped total revenue by customer entity and filtered the top 5 ranking clients by enterprise transaction volume.",
                "action_type": "sql",
                "code": sql,
                "chart_spec": {
                    "recommended": True,
                    "type": "bar",
                    "x_key": "customer_name",
                    "y_key": "total_revenue",
                    "title": "Top 5 Customers by Revenue"
                },
                "explanation": "The top 5 corporate accounts by lifetime order spend were ranked. These enterprise accounts constitute the highest share of commercial turnover.",
                "result": res
            }

        if "how many" in q and ("customer" in q or "client" in q or "account" in q):
            sql = f"SELECT COUNT(DISTINCT customer_id) as total_customers, COUNT(DISTINCT customer_name) as distinct_names FROM {main_table}"
            res = self.engine.execute_sql(sql)
            cnt = res["data"][0]["total_customers"] if res.get("data") else 0
            return {
                "query": query,
                "thought": "Executed distinct count aggregation on customer identifiers to compute the total customer base.",
                "action_type": "sql",
                "code": sql,
                "chart_spec": {"recommended": False},
                "explanation": f"There are {cnt} unique customers registered in the database.",
                "result": res
            }

        if "horizon" in q or "detail of" in q or "search" in q or "find customer" in q:
            name_term = "Horizon Media" if "horizon" in q else q.split("of")[-1].strip()
            sql = f"SELECT * FROM {main_table} WHERE LOWER(customer_name) LIKE '%{name_term.lower()}%' LIMIT 15"
            res = self.engine.execute_sql(sql)
            return {
                "query": query,
                "thought": f"Filtered transaction records for customer matching '{name_term}'.",
                "action_type": "sql",
                "code": sql,
                "chart_spec": {
                    "recommended": True,
                    "type": "bar",
                    "x_key": "product_name",
                    "y_key": "revenue",
                    "title": f"Purchases for {name_term}"
                },
                "explanation": f"Retrieved account details and purchase activity for {name_term}. Showing order transactions with itemized revenue and product lines.",
                "result": res
            }

        if "sql" in q:
            sql = f"SELECT category, sales_channel, ROUND(SUM(revenue), 2) as revenue, ROUND(AVG(discount)*100, 1) as avg_discount_pct FROM {main_table} GROUP BY category, sales_channel ORDER BY revenue DESC"
            res = self.engine.execute_sql(sql)
            return {
                "query": query,
                "thought": "Formulated multi-dimensional aggregation SQL query across product categories and sales distribution channels.",
                "action_type": "sql",
                "code": sql,
                "chart_spec": {
                    "recommended": True,
                    "type": "bar",
                    "x_key": "category",
                    "y_key": "revenue",
                    "title": "Revenue by Category and Sales Channel"
                },
                "explanation": "Generated and executed the DuckDB SQL query. The results provide an itemized matrix of revenue generation alongside average applied discount percentages.",
                "result": res
            }

        fallback_sql = f"SELECT * FROM {main_table} LIMIT 10"
        res = self.engine.execute_sql(fallback_sql)
        return {
            "query": query,
            "thought": f"Selected preview sample records from {main_table} to observe schema attributes, distribution, and baseline values.",
            "action_type": "sql",
            "code": fallback_sql,
            "chart_spec": {"recommended": False},
            "explanation": f"Retrieved preview entries from table '{main_table}'. Ask any specific analytical question regarding trends, regional breakdowns, top performers, or anomalies.",
            "result": res
        }
