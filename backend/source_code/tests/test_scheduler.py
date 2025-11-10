"""
Tests for retraining scheduler functionality
"""

import unittest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from forecasting.scheduler import RetrainingScheduler
    from forecasting.retraining_service import RetrainingService
    HAS_SCHEDULER = True
except ImportError:
    HAS_SCHEDULER = False


@unittest.skipIf(not HAS_SCHEDULER, "Scheduler module not available")
class TestScheduler(unittest.TestCase):
    """Test retraining scheduler"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_retraining_service = Mock(spec=RetrainingService)
        self.scheduler = RetrainingScheduler(self.mock_retraining_service)
    
    def tearDown(self):
        """Clean up after tests"""
        if self.scheduler.is_running:
            self.scheduler.stop()
    
    def test_scheduler_initialization(self):
        """Test scheduler initialization"""
        self.assertFalse(self.scheduler.is_running)
        self.assertIsNotNone(self.scheduler.scheduler)
        self.assertEqual(self.scheduler.retraining_service, self.mock_retraining_service)
    
    def test_scheduler_start_stop(self):
        """Test starting and stopping scheduler"""
        # Start scheduler
        self.scheduler.start(check_interval_hours=24, check_time="00:00")
        self.assertTrue(self.scheduler.is_running)
        
        # Stop scheduler
        self.scheduler.stop()
        self.assertFalse(self.scheduler.is_running)
    
    def test_scheduler_status(self):
        """Test getting scheduler status"""
        status = self.scheduler.get_status()
        
        self.assertIn('is_running', status)
        self.assertIn('jobs', status)
        self.assertIn('job_count', status)
        self.assertFalse(status['is_running'])
        self.assertEqual(status['job_count'], 0)
        
        # Start scheduler and check status again
        self.scheduler.start(check_interval_hours=24, check_time="00:00")
        status = self.scheduler.get_status()
        self.assertTrue(status['is_running'])
        self.assertGreater(status['job_count'], 0)
        self.scheduler.stop()
    
    def test_get_active_tickers(self):
        """Test getting active tickers from MongoDB"""
        # Mock MongoDB connection
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        
        # Mock recent forecasts
        mock_forecasts = [
            {'ticker': 'AAPL', 'created_at': datetime.utcnow().isoformat()},
            {'ticker': 'TSLA', 'created_at': datetime.utcnow().isoformat()},
            {'ticker': 'AAPL', 'created_at': datetime.utcnow().isoformat()},  # Duplicate
        ]
        
        mock_collection.find.return_value = mock_forecasts
        mock_db.get_collection.return_value = mock_collection
        mock_client.get_database.return_value = mock_db
        
        with patch('forecasting.scheduler.MongoClient', return_value=mock_client):
            with patch.dict('os.environ', {'MONGODB_URI': 'mongodb://test'}):
                tickers = self.scheduler._get_active_tickers()
                
                # Should return unique tickers
                self.assertIn('AAPL', tickers)
                self.assertIn('TSLA', tickers)
                self.assertEqual(len(tickers), 2)
    
    def test_get_active_tickers_no_mongodb(self):
        """Test getting active tickers when MongoDB is not configured"""
        with patch.dict('os.environ', {}, clear=True):
            tickers = self.scheduler._get_active_tickers()
            self.assertEqual(tickers, [])
    
    def test_get_active_tickers_error_handling(self):
        """Test error handling when fetching active tickers"""
        # Mock MongoDB to raise exception
        with patch('forecasting.scheduler.MongoClient', side_effect=Exception("Connection error")):
            with patch.dict('os.environ', {'MONGODB_URI': 'mongodb://test'}):
                tickers = self.scheduler._get_active_tickers()
                # Should return empty list on error
                self.assertEqual(tickers, [])
    
    def test_check_and_retrain_all_no_tickers(self):
        """Test retraining check with no active tickers"""
        # Mock _get_active_tickers to return empty list
        self.scheduler._get_active_tickers = Mock(return_value=[])
        
        # Should not raise exception
        self.scheduler._check_and_retrain_all()
        
        # Retraining service should not be called
        self.mock_retraining_service.check_retrain_schedule.assert_not_called()
    
    def test_check_and_retrain_all_with_tickers(self):
        """Test retraining check with active tickers"""
        # Mock active tickers
        self.scheduler._get_active_tickers = Mock(return_value=['AAPL', 'TSLA'])
        
        # Mock schedule check to indicate retraining needed
        self.mock_retraining_service.check_retrain_schedule.return_value = {
            'should_retrain': True,
            'days_since_retrain': 8
        }
        
        # Mock retrain_model to return success
        self.mock_retraining_service.retrain_model.return_value = {
            'success': True,
            'message': 'Retrained successfully'
        }
        
        # Run check
        self.scheduler._check_and_retrain_all()
        
        # Should have called check_retrain_schedule for each ticker/model combination
        self.assertGreater(self.mock_retraining_service.check_retrain_schedule.call_count, 0)
    
    def test_check_and_retrain_all_error_handling(self):
        """Test error handling in retraining check"""
        # Mock active tickers
        self.scheduler._get_active_tickers = Mock(return_value=['AAPL'])
        
        # Mock schedule check to raise exception
        self.mock_retraining_service.check_retrain_schedule.side_effect = Exception("Service error")
        
        # Should not raise exception, should handle gracefully
        try:
            self.scheduler._check_and_retrain_all()
        except Exception:
            self.fail("_check_and_retrain_all should handle exceptions gracefully")
    
    def test_scheduler_double_start(self):
        """Test that starting scheduler twice doesn't cause issues"""
        self.scheduler.start(check_interval_hours=24, check_time="00:00")
        self.assertTrue(self.scheduler.is_running)
        
        # Try to start again
        self.scheduler.start(check_interval_hours=24, check_time="00:00")
        self.assertTrue(self.scheduler.is_running)
        
        self.scheduler.stop()
    
    def test_scheduler_double_stop(self):
        """Test that stopping scheduler twice doesn't cause issues"""
        self.scheduler.start(check_interval_hours=24, check_time="00:00")
        self.scheduler.stop()
        self.assertFalse(self.scheduler.is_running)
        
        # Try to stop again
        self.scheduler.stop()
        self.assertFalse(self.scheduler.is_running)


if __name__ == '__main__':
    unittest.main()

