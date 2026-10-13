import numpy as np
import pandas as pd
from typing import Dict, List, Any
from sklearn.ensemble import IsolationForest

class AnomalyDetector:
    @staticmethod
    def detect_anomalies(df: pd.DataFrame, target_columns: List[str] = None, contamination: float = 0.03) -> Dict[str, Any]:
        if df.empty:
            return {"error": "Dataset is empty"}

        numeric_df = df.select_dtypes(include=[np.number]).dropna()
        if numeric_df.empty or numeric_df.shape[1] == 0:
            return {"error": "No numeric columns found for anomaly detection"}

        if target_columns:
            valid_targets = [c for c in target_columns if c in numeric_df.columns]
            if valid_targets:
                numeric_df = numeric_df[valid_targets]

        if len(numeric_df) < 5:
            return {"error": "Not enough rows for statistical anomaly detection"}

        features = numeric_df.copy()
        
        iso = IsolationForest(contamination=contamination, random_state=42)
        preds = iso.fit_predict(features)
        anomaly_mask = preds == -1

        anomalous_rows = df.loc[numeric_df.index[anomaly_mask]].copy()
        
        flagged_explanations = []
        for idx, row in anomalous_rows.iterrows():
            reasons = []
            for col in numeric_df.columns:
                mean = numeric_df[col].mean()
                std = numeric_df[col].std()
                val = row[col]
                if std > 0:
                    z_score = (val - mean) / std
                    if abs(z_score) >= 2.0:
                        reasons.append(f"{col} = {val} (z-score: {z_score:.2f}, {abs(z_score):.1f} std devs away from mean {mean:.2f})")
            
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

            flagged_explanations.append({
                "row_index": int(idx),
                "data": clean_row,
                "reasons": reasons if reasons else ["Multivariate outlier identified by Isolation Forest"]
            })

        return {
            "total_records": len(df),
            "anomaly_count": len(flagged_explanations),
            "contamination_rate": contamination,
            "evaluated_columns": numeric_df.columns.tolist(),
            "anomalies": flagged_explanations[:25]
        }
