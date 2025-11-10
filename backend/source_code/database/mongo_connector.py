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
    
    def ensure_connected(self) -> bool:
        """Ensure MongoDB connection is established"""
        if self.db is not None:
            return True
        if self.client is None and self.uri:
            try:
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
                self.db = self.client.get_database('fintech_forecasting')
                return True
            except Exception:
                self.client = None
                self.db = None
                return False
        return False

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
    
    def save_evaluation_result(self, evaluation_data: Dict[str, Any]) -> str:
        """Save evaluation result to MongoDB"""
        if self.client is None and self.uri:
            try:
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
                self.db = self.client.get_database('fintech_forecasting')
            except Exception:
                return ""
        if self.db is None:
            return ""
        col = self.db.get_collection('evaluations')
        doc = dict(evaluation_data)
        doc['created_at'] = datetime.utcnow()
        ins = col.insert_one(doc)
        return str(ins.inserted_id)
    
    def save_alert(self, alert_data: Dict[str, Any]) -> str:
        """Save alert to MongoDB"""
        if self.client is None and self.uri:
            try:
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
                self.db = self.client.get_database('fintech_forecasting')
            except Exception:
                return ""
        if self.db is None:
            return ""
        col = self.db.get_collection('alerts')
        doc = dict(alert_data)
        doc['created_at'] = datetime.utcnow()
        ins = col.insert_one(doc)
        return str(ins.inserted_id)
    
    def save_portfolio(self, portfolio_data: Dict[str, Any]) -> str:
        """Save portfolio to MongoDB"""
        try:
            # Ensure connection is established
            if not self.ensure_connected():
                print("Warning: MongoDB not connected, portfolio not saved")
                return ""
            
            if self.db is None:
                print("Warning: MongoDB database not available, portfolio not saved")
                return ""
            
            col = self.db.get_collection('portfolios')
            doc = dict(portfolio_data)
            
            # Ensure portfolio_id exists
            if 'portfolio_id' not in doc:
                print("Warning: Portfolio missing portfolio_id, cannot save")
                return ""
            
            # Set timestamps
            if 'created_at' not in doc:
                doc['created_at'] = datetime.utcnow()
            doc['updated_at'] = datetime.utcnow()
            
            # Remove _id if present (MongoDB will handle it)
            if '_id' in doc and isinstance(doc['_id'], str):
                # Try to convert string _id to ObjectId if needed, or remove it
                try:
                    from bson import ObjectId
                    doc['_id'] = ObjectId(doc['_id'])
                except:
                    # If conversion fails, remove _id and let MongoDB create new one
                    doc.pop('_id', None)
            
            # Upsert based on portfolio_id
            result = col.update_one(
                {'portfolio_id': doc['portfolio_id']},
                {'$set': doc},
                upsert=True
            )
            
            # Verify save was successful
            if result.upserted_id or result.modified_count > 0 or result.matched_count > 0:
                print(f"Portfolio saved successfully: {doc['portfolio_id']}, Holdings: {doc.get('holdings', {})}, Cash: ${doc.get('cash', 0):.2f}")
                return doc['portfolio_id']
            else:
                print(f"Warning: Portfolio save may have failed: {doc['portfolio_id']}")
                return doc['portfolio_id']
                
        except Exception as e:
            # Don't raise exception - just return empty string
            print(f"MongoDB save_portfolio error: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def save_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """Save transaction to MongoDB"""
        if self.client is None and self.uri:
            try:
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
                self.db = self.client.get_database('fintech_forecasting')
            except Exception:
                return ""
        if self.db is None:
            return ""
        col = self.db.get_collection('transactions')
        doc = dict(transaction_data)
        doc['created_at'] = datetime.utcnow()
        ins = col.insert_one(doc)
        return str(ins.inserted_id)
    
    def get_portfolio(self, portfolio_id: str) -> Dict[str, Any]:
        """Get portfolio by ID"""
        if self.client is None and self.uri:
            try:
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
                self.db = self.client.get_database('fintech_forecasting')
            except Exception:
                return {}
        if self.db is None:
            return {}
        col = self.db.get_collection('portfolios')
        doc = col.find_one({'portfolio_id': portfolio_id})
        if doc:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            # Ensure holdings is always a dict (not None or missing)
            if 'holdings' not in doc or doc['holdings'] is None:
                doc['holdings'] = {}
            # Log what we're retrieving
            print(f"Retrieved portfolio {portfolio_id} from MongoDB - Holdings: {doc.get('holdings', {})}, Cash: ${doc.get('cash', 0):.2f}")
        return doc or {}
    
    def get_transactions(self, portfolio_id: str, limit: int = 100) -> list:
        """Get transactions for a portfolio"""
        if self.client is None and self.uri:
            try:
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
                self.db = self.client.get_database('fintech_forecasting')
            except Exception:
                return []
        if self.db is None:
            return []
        col = self.db.get_collection('transactions')
        docs = list(col.find({'portfolio_id': portfolio_id}).sort('created_at', -1).limit(limit))
        for doc in docs:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        return docs
    
    def list_portfolios(self, limit: int = 100) -> list:
        """List all portfolios"""
        if self.client is None and self.uri:
            try:
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
                self.db = self.client.get_database('fintech_forecasting')
            except Exception:
                return []
        if self.db is None:
            return []
        col = self.db.get_collection('portfolios')
        docs = list(col.find({}).sort('created_at', -1).limit(limit))
        portfolios = []
        for doc in docs:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            # Only return essential fields for listing
            portfolios.append({
                'portfolio_id': doc.get('portfolio_id'),
                'cash': doc.get('cash', 0),
                'total_value': doc.get('total_value', 0),
                'initial_value': doc.get('initial_value', 0),
                'created_at': doc.get('created_at'),
                'updated_at': doc.get('updated_at'),
                'holdings_count': len(doc.get('holdings', {}))
            })
        return portfolios


