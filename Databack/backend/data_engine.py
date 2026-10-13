import os
import duckdb
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

class DataEngine:
    def __init__(self):
        self.con = duckdb.connect(database=":memory:")
        self.tables: Dict[str, pd.DataFrame] = {}
        self.file_metadata: Dict[str, Dict[str, Any]] = {}

    def register_csv(self, table_name: str, file_path: str) -> Dict[str, Any]:
        clean_name = "".join(c if c.isalnum() or c == "_" else "_" for c in table_name.lower())
        df = pd.read_csv(file_path)
        self.tables[clean_name] = df
        self.con.register(clean_name, df)
        
        columns_info = []
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            null_count = int(df[col].isnull().sum())
            unique_count = int(df[col].nunique())
            sample_vals = [str(x) for x in df[col].dropna().head(3).tolist()]
            columns_info.append({
                "name": col,
                "type": dtype_str,
                "null_count": null_count,
                "unique_count": unique_count,
                "samples": sample_vals
            })

        meta = {
            "table_name": clean_name,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": columns_info,
            "numeric_columns": df.select_dtypes(include=[np.number]).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=["object", "category"]).columns.tolist(),
            "datetime_columns": [c for c in df.columns if "date" in c.lower() or "time" in c.lower()]
        }
        self.file_metadata[clean_name] = meta
        return meta

    def get_all_schemas(self) -> str:
        if not self.tables:
            return "No tables currently loaded."
        schema_text = []
        for name, meta in self.file_metadata.items():
            cols = ", ".join([f"{c['name']} ({c['type']})" for c in meta["columns"]])
            schema_text.append(f"Table: {name} (Rows: {meta['row_count']})\nColumns: {cols}")
        return "\n\n".join(schema_text)

    def execute_sql(self, query: str) -> Dict[str, Any]:
        try:
            rel = self.con.execute(query)
            df = rel.df()
            
            clean_records = []
            for row in df.head(100).to_dict(orient="records"):
                clean_row = {}
                for k, v in row.items():
                    if pd.isna(v):
                        clean_row[k] = None
                    elif isinstance(v, (np.integer, np.int64, np.int32)):
                        clean_row[k] = int(v)
                    elif isinstance(v, (np.floating, np.float64, np.float32)):
                        clean_row[k] = round(float(v), 4)
                    else:
                        clean_row[k] = str(v)
                clean_records.append(clean_row)

            return {
                "success": True,
                "columns": df.columns.tolist(),
                "data": clean_records,
                "total_rows": len(df),
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "columns": [],
                "data": [],
                "total_rows": 0,
                "error": str(e)
            }

    def execute_pandas(self, code: str) -> Dict[str, Any]:
        try:
            local_scope = {"pd": pd, "np": np, **self.tables}
            exec_globals = {"pd": pd, "np": np}
            
            lines = [line for line in code.strip().split("\n") if line.strip()]
            if not lines:
                return {"success": False, "error": "Empty code provided"}
            
            exec_code = "\n".join(lines[:-1]) if len(lines) > 1 else ""
            last_line = lines[-1].strip()
            
            if exec_code:
                exec(exec_code, exec_globals, local_scope)
            
            if last_line.startswith("result =") or last_line.startswith("res ="):
                exec(last_line, exec_globals, local_scope)
                result_df = local_scope.get("result", local_scope.get("res"))
            else:
                try:
                    result_df = eval(last_line, exec_globals, local_scope)
                except SyntaxError:
                    exec(last_line, exec_globals, local_scope)
                    result_df = local_scope.get("result", None)

            if isinstance(result_df, pd.Series):
                result_df = result_df.reset_index()
            elif isinstance(result_df, (list, dict)):
                result_df = pd.DataFrame(result_df)
            elif not isinstance(result_df, pd.DataFrame):
                return {
                    "success": True,
                    "columns": ["result"],
                    "data": [{"result": str(result_df)}],
                    "total_rows": 1,
                    "error": None
                }

            clean_records = []
            for row in result_df.head(100).to_dict(orient="records"):
                clean_row = {}
                for k, v in row.items():
                    if pd.isna(v):
                        clean_row[k] = None
                    elif isinstance(v, (np.integer, np.int64, np.int32)):
                        clean_row[k] = int(v)
                    elif isinstance(v, (np.floating, np.float64, np.float32)):
                        clean_row[k] = round(float(v), 4)
                    else:
                        clean_row[k] = str(v)
                clean_records.append(clean_row)

            return {
                "success": True,
                "columns": result_df.columns.tolist(),
                "data": clean_records,
                "total_rows": len(result_df),
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "columns": [],
                "data": [],
                "total_rows": 0,
                "error": str(e)
            }
