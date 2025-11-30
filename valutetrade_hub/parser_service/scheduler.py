import schedule
import time
import logging
from .config import ParserConfig
from .updater import RatesUpdater

class Scheduler:
    """Scheduler for periodic exchange rate updates"""
    
    def __init__(self, config: ParserConfig = None):
        self.config = config or ParserConfig()
        self.updater = RatesUpdater(self.config)
        self.logger = logging.getLogger(__name__)
        self.is_running = False
    
    def schedule_updates(self, interval_minutes: int = 60) -> None:
        """
        Schedule regular exchange rate updates
        
        Args:
            interval_minutes (int): Update interval in minutes (default 60)
        """
        # Schedule rate updates every interval_minutes minutes
        schedule.every(interval_minutes).minutes.do(self._run_update)
        
        self.logger.info(f"Scheduled rates updates every {interval_minutes} minutes")
    
    def schedule_daily_updates(self, time_str: str = "00:00") -> None:
        """
        Schedule daily exchange rate updates
        
        Args:
            time_str (str): Update time in "HH:MM" format (default "00:00")
        """
        # Schedule daily rate updates
        schedule.every().day.at(time_str).do(self._run_update)
        
        self.logger.info(f"Scheduled daily rates updates at {time_str}")
    
    def _run_update(self) -> None:
        """Run exchange rate update"""
        try:
            self.logger.info("Scheduled update started")
            result = self.updater.run_update()
            self.logger.info(f"Scheduled update completed: {result['updated_count']} rates updated")
        except Exception as e:
            self.logger.error(f"Scheduled update failed: {str(e)}")
    
    def run_scheduler(self) -> None:
        """Run scheduler"""
        self.is_running = True
        self.logger.info("Scheduler started")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"Scheduler error: {str(e)}")
        finally:
            self.is_running = False
            self.logger.info("Scheduler finished")
    
    def stop_scheduler(self) -> None:
        """Stop scheduler"""
        self.is_running = False
        self.logger.info("Scheduler stop requested")

