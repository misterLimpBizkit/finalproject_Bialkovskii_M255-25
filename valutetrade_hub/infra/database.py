"""
Database manager for the currency trading system.
This module implements a Singleton DatabaseManager that abstracts the JSON storage.
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

from valutetrade_hub.infra.settings import settings
from valutetrade_hub.core.models import User, Portfolio
from valutetrade_hub.logging_config import logger


class DatabaseManager:
    """Singleton database manager for JSON storage"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.data_dir = settings.data_dir
            self.users_file = os.path.join(self.data_dir, "users.json")
            self.portfolios_file = os.path.join(self.data_dir, "portfolios.json")
            self.rates_file = os.path.join(self.data_dir, "rates.json")
            self._ensure_data_dir()
            self._initialized = True
    
    def _ensure_data_dir(self):
        """Creates data directory if it doesn't exist"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    # User operations
    def load_users(self) -> Dict[str, User]:
        """Load all users from the database"""
        if not os.path.exists(self.users_file):
            return {}
        
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning("Failed to load users from file")
            return {}
        
        users = {}
        for username, user_data in data.items():
            try:
                user = User.from_saved_data(
                    user_id=user_data['user_id'],
                    username=username,
                    hashed_password=user_data['hashed_password'],
                    salt=user_data['salt'],
                    registration_date=datetime.fromisoformat(user_data['registration_date'])
                )
                users[username] = user
            except Exception as e:
                logger.error(f"Failed to load user {username}: {e}")
        
        return users
    
    def save_users(self, users: Dict[str, User]) -> bool:
        """Save all users to the database"""
        data = {}
        for username, user in users.items():
            data[username] = {
                'user_id': user.user_id,
                'hashed_password': user.hashed_password,
                'salt': user.salt,
                'registration_date': user.registration_date.isoformat()
            }
        
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save users: {e}")
            return False
    
    # Portfolio operations
    def load_portfolio(self, user_id: int) -> Portfolio:
        """Load a user's portfolio from the database"""
        if not os.path.exists(self.portfolios_file):
            return Portfolio(user_id)
        
        try:
            with open(self.portfolios_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return Portfolio(user_id)
        
        portfolio_data = data.get(str(user_id), {})
        portfolio = Portfolio(user_id)
        
        for currency_code, balance in portfolio_data.get('wallets', {}).items():
            portfolio.add_currency(currency_code)
            wallet = portfolio.get_wallet(currency_code)
            if wallet:
                wallet.balance = balance
        
        return portfolio
    
    def save_portfolio(self, portfolio: Portfolio) -> bool:
        """Save a user's portfolio to the database"""
        try:
            if os.path.exists(self.portfolios_file):
                try:
                    with open(self.portfolios_file, 'r', encoding='utf-8') as f:
                        all_portfolios = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    all_portfolios = {}
            else:
                all_portfolios = {}
            
            all_portfolios[str(portfolio.user_id)] = portfolio.get_portfolio_info()
            
            with open(self.portfolios_file, 'w', encoding='utf-8') as f:
                json.dump(all_portfolios, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save portfolio for user {portfolio.user_id}: {e}")
            return False
    
    # Rate operations
    def get_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get exchange rate from the database"""
        if from_currency == to_currency:
            return 1.0
        
        pair_key = f"{from_currency}_{to_currency}"
        
        if not os.path.exists(self.rates_file):
            return None
        
        try:
            with open(self.rates_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None
        
        rate_data = data.get(pair_key)
        if rate_data:
            return rate_data.get('rate')
        
        return None
    
    def update_rate(self, from_currency: str, to_currency: str, rate: float) -> bool:
        """Update exchange rate in the database"""
        pair_key = f"{from_currency}_{to_currency}"
        
        if os.path.exists(self.rates_file):
            try:
                with open(self.rates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                data = {}
        else:
            data = {}
        
        data[pair_key] = {
            'rate': rate,
            'updated_at': datetime.now().isoformat()
        }
        
        data['source'] = 'LocalCache'
        data['last_refresh'] = datetime.now().isoformat()
        
        try:
            with open(self.rates_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to update rate {from_currency}->{to_currency}: {e}")
            return False

db_manager = DatabaseManager()