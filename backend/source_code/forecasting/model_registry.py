"""
Model Registry
Tracks model versions, metadata, and performance in MongoDB
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pymongo import MongoClient
import os


class ModelRegistry:
    """Manages model versioning and metadata in MongoDB"""
    
    def __init__(self, mongo_uri: Optional[str] = None):
        """
        Initialize model registry
        
        Args:
            mongo_uri: MongoDB connection URI (defaults to env var)
        """
        self.uri = mongo_uri or os.getenv('MONGODB_URI')
        self.client = None
        self.db = None
        self._init_connection()
    
    def _init_connection(self):
        """Initialize MongoDB connection"""
        if self.uri:
            try:
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=2000)
                self.db = self.client.get_database('fintech_forecasting')
            except Exception:
                self.client = None
                self.db = None
    
    def save_model_version(
        self,
        model_type: str,
        version: str,
        ticker: str,
        hyperparameters: Dict[str, Any],
        training_data_info: Dict[str, Any],
        is_production: bool = False
    ) -> Optional[str]:
        """
        Save model version metadata to MongoDB
        
        Args:
            model_type: Type of model (lstm, gru, transformer, arima, mlp, etc.)
            version: Version identifier
            ticker: Ticker symbol the model was trained on
            hyperparameters: Model hyperparameters
            training_data_info: Info about training data (days, date range, etc.)
            is_production: Whether this is the production version
            
        Returns:
            Document ID or None if failed
        """
        if self.db is None:
            return None
        
        col = self.db.get_collection('model_versions')
        
        # If setting as production, unset other production flags for this model_type and ticker
        if is_production:
            col.update_many(
                {
                    'model_type': model_type,
                    'ticker': ticker,
                    'is_production': True
                },
                {'$set': {'is_production': False}}
            )
        
        doc = {
            'model_type': model_type,
            'version': version,
            'ticker': ticker,
            'hyperparameters': hyperparameters,
            'training_data_info': training_data_info,
            'is_production': is_production,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Upsert based on model_type, version, and ticker
        result = col.update_one(
            {
                'model_type': model_type,
                'version': version,
                'ticker': ticker
            },
            {'$set': doc},
            upsert=True
        )
        
        return str(result.upserted_id) if result.upserted_id else None
    
    def save_model_performance(
        self,
        model_type: str,
        version: str,
        ticker: str,
        metrics: Dict[str, float],
        evaluation_date: Optional[datetime] = None
    ) -> Optional[str]:
        """
        Save model performance metrics
        
        Args:
            model_type: Type of model
            version: Version identifier
            ticker: Ticker symbol
            metrics: Dictionary of metrics (MAE, RMSE, MAPE, etc.)
            evaluation_date: Date of evaluation (defaults to now)
            
        Returns:
            Document ID or None if failed
        """
        if self.db is None:
            return None
        
        col = self.db.get_collection('model_performance')
        
        doc = {
            'model_type': model_type,
            'version': version,
            'ticker': ticker,
            'metrics': metrics,
            'evaluation_date': evaluation_date or datetime.utcnow(),
            'created_at': datetime.utcnow()
        }
        
        result = col.insert_one(doc)
        return str(result.inserted_id)
    
    def get_latest_model(
        self,
        model_type: str,
        ticker: str,
        production_only: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest model version for a model type and ticker
        
        Args:
            model_type: Type of model
            ticker: Ticker symbol
            production_only: Only return production models
            
        Returns:
            Model version document or None
        """
        if self.db is None:
            return None
        
        col = self.db.get_collection('model_versions')
        
        query = {
            'model_type': model_type,
            'ticker': ticker
        }
        
        if production_only:
            query['is_production'] = True
        
        doc = col.find_one(query, sort=[('created_at', -1)])
        
        if doc and '_id' in doc:
            doc['_id'] = str(doc['_id'])
        
        return doc
    
    def list_model_versions(
        self,
        model_type: Optional[str] = None,
        ticker: Optional[str] = None,
        production_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List all model versions
        
        Args:
            model_type: Filter by model type (optional)
            ticker: Filter by ticker (optional)
            production_only: Only return production models
            
        Returns:
            List of model version documents
        """
        if self.db is None:
            return []
        
        col = self.db.get_collection('model_versions')
        
        query = {}
        if model_type:
            query['model_type'] = model_type
        if ticker:
            query['ticker'] = ticker
        if production_only:
            query['is_production'] = True
        
        docs = list(col.find(query).sort('created_at', -1))
        
        for doc in docs:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        
        return docs
    
    def promote_model_version(
        self,
        model_type: str,
        version: str,
        ticker: str
    ) -> bool:
        """
        Promote a model version to production
        
        Args:
            model_type: Type of model
            version: Version identifier
            ticker: Ticker symbol
            
        Returns:
            True if successful, False otherwise
        """
        if self.db is None:
            return False
        
        col = self.db.get_collection('model_versions')
        
        # Unset other production flags
        col.update_many(
            {
                'model_type': model_type,
                'ticker': ticker,
                'is_production': True
            },
            {'$set': {'is_production': False}}
        )
        
        # Set this version as production
        result = col.update_one(
            {
                'model_type': model_type,
                'version': version,
                'ticker': ticker
            },
            {
                '$set': {
                    'is_production': True,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    def get_model_performance_history(
        self,
        model_type: str,
        version: str,
        ticker: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get performance history for a model version
        
        Args:
            model_type: Type of model
            version: Version identifier
            ticker: Ticker symbol
            limit: Maximum number of records to return
            
        Returns:
            List of performance records
        """
        if self.db is None:
            return []
        
        col = self.db.get_collection('model_performance')
        
        query = {
            'model_type': model_type,
            'version': version,
            'ticker': ticker
        }
        
        docs = list(col.find(query).sort('evaluation_date', -1).limit(limit))
        
        for doc in docs:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        
        return docs

