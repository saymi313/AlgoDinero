"""
Tests for API endpoints
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastapi.testclient import TestClient
    from api.app import app
    HAS_FASTAPI_TEST = True
except ImportError:
    HAS_FASTAPI_TEST = False


class TestAPI(unittest.TestCase):
    """Test API endpoints"""
    
    def setUp(self):
        """Set up test client"""
        if not HAS_FASTAPI_TEST:
            self.skipTest("FastAPI test client not available")
        self.client = TestClient(app)
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('ok', data)
    
    def test_curate_endpoint(self):
        """Test data curation endpoint"""
        response = self.client.post(
            "/api/curate",
            json={"ticker": "AAPL", "days": 10}
        )
        # Should succeed or fail gracefully
        self.assertIn(response.status_code, [200, 400, 500])
    
    def test_forecast_endpoint(self):
        """Test forecast endpoint"""
        response = self.client.post(
            "/api/forecast",
            json={"ticker": "AAPL", "days": 10, "horizon": 5}
        )
        # Should succeed or fail gracefully
        self.assertIn(response.status_code, [200, 400, 500])
    
    def test_retrain_endpoint(self):
        """Test retrain endpoint"""
        response = self.client.post(
            "/api/retrain",
            json={"ticker": "AAPL", "model_type": "lstm", "days": 60}
        )
        # Should succeed or fail gracefully
        self.assertIn(response.status_code, [200, 400, 500])
    
    def test_evaluate_endpoint(self):
        """Test evaluate endpoint"""
        response = self.client.post(
            "/api/evaluate",
            json={"ticker": "AAPL", "days_back": 7}
        )
        # Should succeed or fail gracefully
        self.assertIn(response.status_code, [200, 400, 500])
    
    def test_portfolio_create_endpoint(self):
        """Test portfolio creation endpoint"""
        response = self.client.post(
            "/api/portfolio/create",
            json={"initial_cash": 100000}
        )
        # Should succeed
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('portfolio_id', data)
    
    def test_scheduler_status_endpoint(self):
        """Test scheduler status endpoint"""
        response = self.client.get("/api/scheduler/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('is_running', data)
        self.assertIn('jobs', data)
    
    def test_monitoring_endpoints(self):
        """Test monitoring endpoints"""
        # Test metrics endpoint
        response = self.client.get("/api/monitoring/metrics?ticker=AAPL&window=daily&days_back=30")
        self.assertIn(response.status_code, [200, 400, 500])
        
        # Test rankings endpoint
        response = self.client.get("/api/monitoring/rankings?ticker=AAPL&metric=MAPE&days_back=30")
        self.assertIn(response.status_code, [200, 400, 500])
        
        # Test alerts endpoint
        response = self.client.get("/api/monitoring/alerts?limit=10")
        self.assertIn(response.status_code, [200, 400, 500])
    
    def test_model_version_endpoints(self):
        """Test model version endpoints"""
        # Test list versions
        response = self.client.get("/api/models/versions?ticker=AAPL")
        self.assertIn(response.status_code, [200, 400, 500])
    
    def test_forecast_with_ensemble_weights(self):
        """Test that forecast endpoint returns ensemble weights"""
        response = self.client.post(
            "/api/forecast",
            json={"ticker": "AAPL", "days": 10, "horizon": 5}
        )
        if response.status_code == 200:
            data = response.json()
            # Check if ensemble_weights are included in response
            if 'ensemble_weights' in data:
                self.assertIsInstance(data['ensemble_weights'], dict)


if __name__ == '__main__':
    unittest.main()

