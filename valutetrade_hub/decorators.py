"""
Decorators for the currency trading system.
This module implements logging and other decorators.
"""

import functools
from datetime import datetime
from typing import Callable, Any

from valutetrade_hub.logging_config import logger


def log_action(action_name: str):
    """
    Decorator for logging user actions.
    
    Args:
        action_name (str): Name of the action being performed
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            user_id = None
            if args and len(args) > 0:
                if hasattr(args[0], 'current_user_id'):
                    user_id = args[0].current_user_id
                elif hasattr(args[0], '_user_id'):
                    user_id = args[0]._user_id
                elif len(args) > 1:
                    user_id = args[1] if isinstance(args[1], int) else None
            
            start_time = datetime.now()
            logger.info(f"User {user_id}: Starting {action_name}")
            
            try:
                result = func(*args, **kwargs)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.info(f"User {user_id}: Completed {action_name} in {duration:.2f}s")
                return result
            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.error(f"User {user_id}: Error in {action_name} after {duration:.2f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator

