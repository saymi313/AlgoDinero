from typing import Dict, Any
import os
from datetime import datetime
from pymongo import MongoClient


class MongoConnector:
    def __init__(self):
        # Lazy init: avoid DNS resolution at import/startup
        self.uri = os.getenv('MONGODB_URI')
        self.client = None
        self.db = None
        self.col = None

    def save_forecast_result(self, result: Dict[str, Any]) -> str:
        if self.col is None and self.uri:
            try:
                # Don't block long on selection; resolve only when saving
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
                self.db = self.client.get_database('fintech_forecasting')
                self.col = self.db.get_collection('forecasts')
            except Exception:
                self.client = None
                self.db = None
                self.col = None
        if self.col is None:
            return ""
        doc = dict(result)
        doc['created_at'] = datetime.utcnow()
        ins = self.col.insert_one(doc)
        return str(ins.inserted_id)

    def save_curated_data(self, ticker: str, merged_rows: list) -> str:
        if self.client is None and self.uri:
            try:
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
                self.db = self.client.get_database('fintech_forecasting')
            except Exception:
                return ""
        if self.db is None:
            return ""
        col = self.db.get_collection('curated')
        # Coerce any non-serializable types (e.g., datetime.date) to strings
        safe_rows = []
        for row in merged_rows:
            safe_row = {}
            for k, v in row.items():
                if hasattr(v, 'isoformat'):
                    try:
                        safe_row[k] = v.isoformat()
                        continue
                    except Exception:
                        pass
                safe_row[k] = v
            safe_rows.append(safe_row)

        doc = {
            'ticker': ticker,
            'rows': safe_rows,
            'created_at': datetime.utcnow(),
        }
        ins = col.insert_one(doc)
        return str(ins.inserted_id)

    def save_visualize_snapshot(self, payload: Dict[str, Any]) -> str:
        if self.client is None and self.uri:
            try:
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
                self.db = self.client.get_database('fintech_forecasting')
            except Exception:
                return ""
        if self.db is None:
            return ""
        col = self.db.get_collection('visualize_snapshots')
        doc = dict(payload)
        doc['created_at'] = datetime.utcnow()
        ins = col.insert_one(doc)
        return str(ins.inserted_id)


