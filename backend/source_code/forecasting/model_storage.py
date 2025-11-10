"""
Model Storage Utilities
Handles serialization and deserialization of different model types
"""

import os
import pickle
import json
from typing import Any, Dict, Optional
from pathlib import Path
import numpy as np

try:
    import torch
    import torch.nn as nn
except ImportError:
    torch = None
    nn = None


class ModelStorage:
    """Handles storage and retrieval of model artifacts"""
    
    def __init__(self, storage_dir: str = "models"):
        """
        Initialize model storage
        
        Args:
            storage_dir: Directory to store model files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def save_model(self, model: Any, model_type: str, version: str, metadata: Optional[Dict] = None) -> str:
        """
        Save a model to disk
        
        Args:
            model: The model object to save
            model_type: Type of model (e.g., 'lstm', 'gru', 'transformer', 'arima', 'mlp')
            version: Version identifier (e.g., 'v1.0.0' or timestamp)
            metadata: Additional metadata to store
            
        Returns:
            Path to saved model file
        """
        version_dir = self.storage_dir / model_type / version
        version_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = version_dir / "model.pkl"
        metadata_path = version_dir / "metadata.json"
        
        # Save model based on type
        if model_type in ['lstm', 'gru', 'transformer'] and torch is not None:
            # PyTorch models
            if isinstance(model, nn.Module):
                torch.save(model.state_dict(), version_dir / "model.pt")
                # Also save as pickle for compatibility
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
            else:
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
        else:
            # Sklearn, statsmodels, or other pickleable models
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
        
        # Save metadata
        if metadata:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
        
        return str(model_path)
    
    def load_model(self, model_type: str, version: str) -> Optional[Any]:
        """
        Load a model from disk
        
        Args:
            model_type: Type of model
            version: Version identifier
            
        Returns:
            Loaded model or None if not found
        """
        version_dir = self.storage_dir / model_type / version
        model_path = version_dir / "model.pkl"
        pt_path = version_dir / "model.pt"
        
        if not model_path.exists() and not pt_path.exists():
            return None
        
        try:
            if pt_path.exists() and torch is not None and model_type in ['lstm', 'gru', 'transformer']:
                # Load PyTorch model
                # Note: We need the model class to reconstruct
                # For now, load from pickle
                if model_path.exists():
                    with open(model_path, 'rb') as f:
                        return pickle.load(f)
            else:
                with open(model_path, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Error loading model: {e}")
            return None
    
    def load_metadata(self, model_type: str, version: str) -> Optional[Dict]:
        """Load metadata for a model version"""
        version_dir = self.storage_dir / model_type / version
        metadata_path = version_dir / "metadata.json"
        
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    def list_versions(self, model_type: str) -> list:
        """List all versions for a model type"""
        model_type_dir = self.storage_dir / model_type
        if not model_type_dir.exists():
            return []
        
        return [d.name for d in model_type_dir.iterdir() if d.is_dir()]
    
    def delete_version(self, model_type: str, version: str) -> bool:
        """Delete a model version"""
        version_dir = self.storage_dir / model_type / version
        if version_dir.exists():
            import shutil
            shutil.rmtree(version_dir)
            return True
        return False

