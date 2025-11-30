import json
import os
from typing import Dict, Any, List
from datetime import datetime
from .config import ParserConfig

class StorageManager:
    """Manager for working with data files"""
    
    def __init__(self, config: ParserConfig):
        self.config = config
    
    def load_history(self) -> List[Dict[str, Any]]:
        """Load exchange rate history from file"""
        if not os.path.exists(self.config.HISTORY_FILE_PATH):
            return []
        
        try:
            with open(self.config.HISTORY_FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, IOError):
            return []
    
    def save_history(self, records: List[Dict[str, Any]]) -> None:
        """Save exchange rate history to file"""
        os.makedirs(os.path.dirname(self.config.HISTORY_FILE_PATH), exist_ok=True)
        
        temp_path = self.config.HISTORY_FILE_PATH + '.tmp'
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, self.config.HISTORY_FILE_PATH)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
    
    def load_cache(self) -> Dict[str, Any]:
        """Load exchange rate cache from file"""
        if not os.path.exists(self.config.RATES_FILE_PATH):
            return {"pairs": {}, "last_refresh": None}
        
        try:
            with open(self.config.RATES_FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {"pairs": {}, "last_refresh": None}
        except (json.JSONDecodeError, IOError):
            return {"pairs": {}, "last_refresh": None}
    
    def save_cache(self, rates: Dict[str, Dict[str, Any]]) -> None:
        """Save exchange rate cache to file"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config.RATES_FILE_PATH), exist_ok=True)
        
        # Prepare data for saving
        cache_data = {
            "pairs": rates,
            "last_refresh": datetime.utcnow().isoformat() + "Z"
        }
        
        # Write data atomically (through temporary file)
        temp_path = self.config.RATES_FILE_PATH + '.tmp'
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, self.config.RATES_FILE_PATH)
        except Exception as e:
            # Remove temporary file if it was created
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
    
    def add_history_record(self, from_currency: str, to_currency: str, rate: float, source: str, meta: Dict[str, Any] = None) -> None:
        """Add record to exchange rate history"""
        # Create unique ID for record
        timestamp = datetime.utcnow().isoformat() + "Z"
        record_id = f"{from_currency}_{to_currency}_{timestamp}"
        
        # Create record
        record = {
            "id": record_id,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": rate,
            "timestamp": timestamp,
            "source": source,
            "meta": meta or {}
        }
        
        # Load existing history
        history = self.load_history()
        
        # Add new record
        history.append(record)
        
        # Save updated history
        self.save_history(history)