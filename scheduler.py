#!/usr/bin/env python3
"""
Scheduler for automatic currency rates updates
"""

import time
import threading
from valutetrade_hub.parser_service.scheduler import Scheduler
from valutetrade_hub.parser_service.config import ParserConfig

def start_scheduler():
    """Start the scheduler in a separate thread"""
    config = ParserConfig()
    scheduler = Scheduler(config)
    
    # Schedule updates every 60 minutes
    scheduler.schedule_updates(60)
    
    # Run scheduler in a separate thread
    scheduler_thread = threading.Thread(target=scheduler.run_scheduler, daemon=True)
    scheduler_thread.start()
    
    return scheduler

if __name__ == "__main__":
    print("Starting currency rates scheduler...")
    scheduler = start_scheduler()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping scheduler...")
        scheduler.stop_scheduler()