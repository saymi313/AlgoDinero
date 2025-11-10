"""
Retraining Scheduler
Automatically schedules and triggers model retraining based on configured intervals
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import threading
import atexit

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    # Create dummy classes if APScheduler is not available
    class BackgroundScheduler:
        def __init__(self): pass
        def add_job(self, *args, **kwargs): pass
        def start(self): pass
        def shutdown(self, *args, **kwargs): pass
        def get_jobs(self): return []
    class CronTrigger:
        def __init__(self, *args, **kwargs): pass
    class IntervalTrigger:
        def __init__(self, *args, **kwargs): pass

logger = logging.getLogger(__name__)


class RetrainingScheduler:
    """Manages automatic scheduled retraining of models"""
    
    def __init__(self, retraining_service):
        """
        Initialize retraining scheduler
        
        Args:
            retraining_service: Instance of RetrainingService to use for retraining
        """
        self.retraining_service = retraining_service
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self._lock = threading.Lock()
        
        # Register cleanup on exit
        atexit.register(self.shutdown)
    
    def start(self, check_interval_hours: int = 24, check_time: str = "00:00"):
        """
        Start the scheduler
        
        Args:
            check_interval_hours: Hours between retraining checks (default: 24, i.e., daily)
            check_time: Time of day to run checks in HH:MM format (default: "00:00" for midnight)
        """
        if not HAS_APSCHEDULER:
            logger.warning("APScheduler not available. Install with: pip install APScheduler")
            return
        
        with self._lock:
            if self.is_running:
                logger.warning("Scheduler is already running")
                return
            
            try:
                # Schedule daily retraining check
                hour, minute = map(int, check_time.split(':'))
                self.scheduler.add_job(
                    self._check_and_retrain_all,
                    trigger=CronTrigger(hour=hour, minute=minute),
                    id='daily_retrain_check',
                    name='Daily Retraining Check',
                    replace_existing=True
                )
                
                # Also add an interval-based check as backup
                self.scheduler.add_job(
                    self._check_and_retrain_all,
                    trigger=IntervalTrigger(hours=check_interval_hours),
                    id='interval_retrain_check',
                    name='Interval Retraining Check',
                    replace_existing=True
                )
                
                self.scheduler.start()
                self.is_running = True
                logger.info(f"Retraining scheduler started. Checks scheduled daily at {check_time} and every {check_interval_hours} hours")
                
            except Exception as e:
                logger.error(f"Failed to start scheduler: {str(e)}")
                self.is_running = False
                raise
    
    def stop(self):
        """Stop the scheduler"""
        with self._lock:
            if not self.is_running:
                return
            
            try:
                self.scheduler.shutdown(wait=False)
                self.is_running = False
                logger.info("Retraining scheduler stopped")
            except Exception as e:
                logger.error(f"Error stopping scheduler: {str(e)}")
    
    def shutdown(self):
        """Shutdown scheduler (called on exit)"""
        self.stop()
    
    def _check_and_retrain_all(self):
        """
        Check all active tickers and retrain models if needed
        This is called by the scheduler at regular intervals
        """
        logger.info("Starting scheduled retraining check...")
        
        try:
            # Get list of active tickers from recent forecasts
            active_tickers = self._get_active_tickers()
            
            if not active_tickers:
                logger.info("No active tickers found for retraining")
                return
            
            logger.info(f"Found {len(active_tickers)} active ticker(s): {', '.join(active_tickers)}")
            
            # Model types to check for retraining
            model_types = ['lstm', 'gru', 'transformer', 'mlp', 'arima']
            
            retrained_count = 0
            skipped_count = 0
            
            for ticker in active_tickers:
                for model_type in model_types:
                    try:
                        # Check if retraining is needed
                        schedule_check = self.retraining_service.check_retrain_schedule(
                            ticker=ticker,
                            model_type=model_type,
                            retrain_interval_days=7  # Default: retrain every 7 days
                        )
                        
                        if schedule_check.get('should_retrain', False):
                            logger.info(
                                f"Retraining {model_type} for {ticker} "
                                f"(last retrain: {schedule_check.get('days_since_retrain', 0)} days ago)"
                            )
                            
                            # Trigger retraining
                            result = self.retraining_service.retrain_model(
                                ticker=ticker,
                                model_type=model_type,
                                window_days=60,
                                retrain_every_days=7
                            )
                            
                            if result.get('success', False):
                                retrained_count += 1
                                logger.info(f"Successfully retrained {model_type} for {ticker}")
                            else:
                                logger.warning(f"Failed to retrain {model_type} for {ticker}: {result.get('message', 'Unknown error')}")
                        else:
                            skipped_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error checking/retraining {model_type} for {ticker}: {str(e)}")
                        continue
            
            logger.info(
                f"Scheduled retraining check completed. "
                f"Retrained: {retrained_count}, Skipped: {skipped_count}"
            )
            
        except Exception as e:
            logger.error(f"Error in scheduled retraining check: {str(e)}")
    
    def _get_active_tickers(self, days_back: int = 30) -> List[str]:
        """
        Get list of tickers that have been forecasted recently
        
        Args:
            days_back: Number of days to look back for active tickers
            
        Returns:
            List of ticker symbols
        """
        try:
            # Try to get active tickers from MongoDB if available
            from pymongo import MongoClient
            import os
            
            mongo_uri = os.getenv('MONGODB_URI')
            if not mongo_uri:
                # Fallback: return empty list if MongoDB not configured
                return []
            
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            db = client.get_database('fintech_forecasting')
            forecasts_col = db.get_collection('forecasts')
            
            # Get unique tickers from recent forecasts
            start_date = datetime.utcnow() - timedelta(days=days_back)
            recent_forecasts = forecasts_col.find({
                'created_at': {'$gte': start_date.isoformat()}
            })
            
            tickers = set()
            for forecast in recent_forecasts:
                ticker = forecast.get('ticker')
                if ticker:
                    tickers.add(ticker)
            
            client.close()
            return list(tickers)
            
        except Exception as e:
            logger.warning(f"Could not fetch active tickers from MongoDB: {str(e)}")
            # Return empty list on error - scheduler will skip retraining
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status
        
        Returns:
            Dictionary with scheduler status information
        """
        with self._lock:
            jobs = []
            if self.is_running:
                for job in self.scheduler.get_jobs():
                    jobs.append({
                        'id': job.id,
                        'name': job.name,
                        'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
                    })
            
            return {
                'is_running': self.is_running,
                'jobs': jobs,
                'job_count': len(jobs)
            }

