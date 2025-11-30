"""
Settings module for the currency trading system.
This module implements the Singleton pattern for application settings.
"""

import json
import os
from typing import Any


class SettingsLoader:
    """Singleton class for loading and managing application settings"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_file: str = "config.json"):
        if not self._initialized:
            self.config_file = config_file
            self._settings = {}
            self._load_settings()
            self._initialized = True
    
    def _load_settings(self):
        """Load settings from configuration file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading settings: {e}")
                self._settings = {}
        else:
            self._settings = {
                "data_dir": "data",
                "default_base_currency": "USD",
                "supported_currencies": ["USD", "EUR", "BTC", "ETH"]
            }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value by key"""
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set setting value"""
        self._settings[key] = value
    
    def save(self):
        """Save settings to configuration file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error saving settings: {e}")
    
    @property
    def data_dir(self) -> str:
        """Get data directory path"""
        return self.get("data_dir", "data")
    
    @property
    def default_base_currency(self) -> str:
        """Get default base currency"""
        return self.get("default_base_currency", "USD")
    
    @property
    def supported_currencies(self) -> list:
        """Get list of supported currencies"""
        return self.get("supported_currencies", ["USD", "EUR", "BTC", "ETH"])


# Global settings instance
settings = SettingsLoader()