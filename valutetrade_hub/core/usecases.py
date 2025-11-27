"""
Business logic layer for the currency trading system.
This module contains use cases that implement the business logic of the application.
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional

from valutetrade_hub.core.models import User, Portfolio, Wallet
from valutetrade_hub.core.currencies import get_currency, is_valid_currency, CURRENCY_REGISTRY
from valutetrade_hub.core.exceptions import InsufficientFundsError, CurrencyNotFoundError
from valutetrade_hub.infra.settings import settings
from valutetrade_hub.infra.database import db_manager
from valutetrade_hub.decorators import log_action


class UserUseCase:
    """Business logic for user management"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    @log_action("user_registration")
    def register_user(self, username: str, password: str) -> tuple[bool, str]:
        """Registration of a new user"""
        if not username or not username.strip():
            return False, "Имя пользователя не может быть пустым"
        
        if len(password) < 4:
            return False, "Пароль должен быть не короче 4 символов"
        
        users = self.db_manager.load_users()
        
        if username in users:
            return False, f"Имя пользователя '{username}' уже занято"
        
        user_id = max([user.user_id for user in users.values()], default=0) + 1
        
        user = User(user_id, username, password, datetime.now())
        users[username] = user
        
        if not self.db_manager.save_users(users):
            return False, "Ошибка сохранения пользователя"
        
        portfolio = Portfolio(user_id)
        if not self.db_manager.save_portfolio(portfolio):
            return False, "Ошибка создания портфеля"
        
        return True, f"Пользователь '{username}' зарегистрирован (id={user_id}). Войдите: login --username {username} --password ****"
    
    @log_action("user_login")
    def login_user(self, username: str, password: str) -> tuple[bool, str]:
        """Authorizes the user"""
        users = self.db_manager.load_users()
        
        if username not in users:
            return False, f"Пользователь '{username}' не найден"
        
        user = users[username]
        
        if not user.verify_password(password):
            return False, "Неверный пароль"
        
        return True, f"Вы вошли как '{username}'"


class RateUseCase:
    """Business logic for exchange rates"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    @log_action("get_exchange_rate")
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> tuple[bool, str]:
        """Get formatted exchange rate information"""
        success, rate = self.calculate_rate(from_currency, to_currency)
        if not success:
            return False, f"Курс {from_currency}→{to_currency} недоступен. Повторите попытку позже."
        
        if from_currency.upper() == to_currency.upper():
            lines = [f"Курс {from_currency}→{to_currency}: 1.00000000"]
            lines.append(f"Обратный курс {to_currency}→{from_currency}: 1.00")
            return True, "\n".join(lines)
        
        reverse_rate = 1.0 / rate if rate != 0 else 0.0
        
        updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        lines = [f"Курс {from_currency}→{to_currency}: {rate:.8f} (обновлено: {updated_at})"]
        lines.append(f"Обратный курс {to_currency}→{from_currency}: {reverse_rate:.8f}")
        
        return True, "\n".join(lines)
    
    def calculate_rate(self, from_currency: str, to_currency: str) -> tuple[bool, float]:
        """Calculate exchange rate without formatting"""
        if not from_currency or not to_currency:
            return False, 0.0
        
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        if from_currency == to_currency:
            return True, 1.0
        
        if not is_valid_currency(from_currency):
            return False, 0.0
        
        if not is_valid_currency(to_currency):
            return False, 0.0
        
        fixed_rates = {
            'USD': 1.0,
            'EUR': 1.18,
            'BTC': 0.000025,
            'ETH': 0.0003,
        }
        
        rate = self.db_manager.get_rate(from_currency, to_currency)
        
        if rate is None:
            from_rate_to_usd = self.db_manager.get_rate(from_currency, 'USD')
            to_rate_to_usd = self.db_manager.get_rate(to_currency, 'USD')
            
            if from_rate_to_usd is None:
                from_rate_to_usd = fixed_rates.get(from_currency, 1.0)
            if to_rate_to_usd is None:
                to_rate_to_usd = fixed_rates.get(to_currency, 1.0)
            
            if to_rate_to_usd > 0:
                rate = from_rate_to_usd / to_rate_to_usd
            else:
                rate = None
        
        if rate is None:
            return False, 0.0
        
        # Сохраняем рассчитанный курс в хранилище для будущего использования
        self.db_manager.update_rate(from_currency, to_currency, rate)
        
        return True, rate


class PortfolioUseCase:
    """Business logic for portfolio management"""
    
    def __init__(self, rate_usecase: RateUseCase = None):
        self.db_manager = db_manager
        self.rate_usecase = rate_usecase or RateUseCase()
    
    @log_action("get_portfolio_info")
    def get_portfolio_info(self, user_id: int, base_currency: str = "USD") -> tuple[bool, str]:
        """Display user's portfolio info"""
        if not is_valid_currency(base_currency):
            return False, f"Неподдерживаемая валюта: {base_currency}"
        
        portfolio = self.db_manager.load_portfolio(user_id)
        
        wallets = portfolio.wallets
        
        if not wallets:
            return True, f"Портфель пользователя (id={user_id}) пуст"
        
        lines = [f"Портфель пользователя (база: {base_currency}):"]
        total_value = 0.0
        
        for currency_code, wallet in wallets.items():
            success, rate = self.rate_usecase.calculate_rate(currency_code, base_currency)
            if not success:
                # Фиксированные курсы относительно USD
                fixed_rates = {
                    'USD': 1.0,
                    'EUR': 1.18,
                    'BTC': 0.000025,
                    'ETH': 0.0003,
                }
                
                # Получаем курсы относительно USD
                from_rate_to_usd = fixed_rates.get(currency_code, 1.0)
                to_rate_to_usd = fixed_rates.get(base_currency, 1.0)
                
                # Рассчитываем курс через USD
                if to_rate_to_usd > 0:
                    rate = from_rate_to_usd / to_rate_to_usd
                else:
                    rate = 1.0 if currency_code == base_currency else 0.0
            
            value = wallet.balance * rate
            total_value += value
            lines.append(f"- {currency_code}: {wallet.balance:.4f} → {value:.2f} {base_currency}")
        
        lines.append("-" * 30)
        lines.append(f"ИТОГО: {total_value:.2f} {base_currency}")
        
        return True, "\n".join(lines)
    
    @log_action("buy_currency")
    def buy_currency(self, user_id: int, currency_code: str, amount: float) -> tuple[bool, str]:
        """Buy currency using USD from the USD wallet"""
        if amount <= 0:
            return False, "Сумма должна быть положительным числом"
        
        if not is_valid_currency(currency_code):
            return False, f"Неподдерживаемая валюта: {currency_code}"
        
        portfolio = self.db_manager.load_portfolio(user_id)
        
        if currency_code == "USD":
            if currency_code not in portfolio.wallets:
                portfolio.add_currency(currency_code)
            
            wallet = portfolio.get_wallet(currency_code)
            if not wallet:
                return False, f"Не удалось создать кошелек для {currency_code}"
            
            old_balance = wallet.balance
            wallet.deposit(amount)
            
            if not self.db_manager.save_portfolio(portfolio):
                return False, "Ошибка сохранения портфеля"
            
            lines = [f"Внесены средства: {amount:.4f} {currency_code}"]
            lines.append("Изменения в кошельке:")
            lines.append(f"- {currency_code}: было {old_balance:.4f} → стало {wallet.balance:.4f}")
            
            return True, "\n".join(lines)
        
        if currency_code not in portfolio.wallets:
            portfolio.add_currency(currency_code)
        
        target_wallet = portfolio.get_wallet(currency_code)
        usd_wallet = portfolio.get_wallet("USD")
        
        if not target_wallet:
            return False, f"Не удалось создать кошелек для {currency_code}"
        
        if not usd_wallet:
            return False, "USD кошелек не найден. Пожалуйста, внесите средства в USD кошелек."
        
        success, rate = self.rate_usecase.calculate_rate(currency_code, "USD")
        if not success:
            fixed_rates = {
                'USD': 1.0,
                'EUR': 1.18,
                'BTC': 0.000025,
                'ETH': 0.0003,
            }
            rate = fixed_rates.get(currency_code, 1.0)
        
        cost_in_usd = amount * rate
        if usd_wallet.balance < cost_in_usd:
            return False, f"Недостаточно средств в USD кошельке: доступно {usd_wallet.balance:.4f} USD, необходимо {cost_in_usd:.4f} USD"
        
        old_target_balance = target_wallet.balance
        old_usd_balance = usd_wallet.balance
        
        target_wallet.deposit(amount)
        usd_wallet.withdraw(cost_in_usd)
        
        if not self.db_manager.save_portfolio(portfolio):
            return False, "Ошибка сохранения портфеля"
        
        lines = [f"Покупка произведена: {amount:.4f} {currency_code} по курсу {rate:.8f} USD/{currency_code}"]
        lines.append("Изменения в кошельках:")
        lines.append(f"- {currency_code}: было {old_target_balance:.4f} → стало {target_wallet.balance:.4f}")
        lines.append(f"- USD: было {old_usd_balance:.4f} → стало {usd_wallet.balance:.4f}")
        lines.append(f"Стоимость покупки: {cost_in_usd:.2f} USD")
        
        return True, "\n".join(lines)
    
    @log_action("sell_currency")
    def sell_currency(self, user_id: int, currency_code: str, amount: float) -> tuple[bool, str]:
        """Sell currency and deposit equivalent USD to the USD wallet"""
        if amount <= 0:
            return False, "Сумма должна быть положительным числом"
        
        if not is_valid_currency(currency_code):
            return False, f"Неподдерживаемая валюта: {currency_code}"
        
        portfolio = self.db_manager.load_portfolio(user_id)
        
        if currency_code not in portfolio.wallets:
            return False, f"У вас нет кошелька '{currency_code}'. Добавьте валюту: она создается автоматически при первой покупке."
        
        target_wallet = portfolio.get_wallet(currency_code)
        usd_wallet = portfolio.get_wallet("USD")
        
        if not target_wallet:
            return False, f"Кошелек {currency_code} не найден"
        
        if not usd_wallet:
            portfolio.add_currency("USD")
            usd_wallet = portfolio.get_wallet("USD")
            if not usd_wallet:
                return False, "Не удалось создать USD кошелек"
        
        if target_wallet.balance < amount:
            return False, f"Недостаточно средств: доступно {target_wallet.balance:.4f} {currency_code}, необходимо {amount:.4f} {currency_code}"
        
        success, rate = self.rate_usecase.calculate_rate(currency_code, "USD")
        if not success:
            fixed_rates = {
                'USD': 1.0,
                'EUR': 1.18,
                'BTC': 0.000025,
                'ETH': 0.0003,
            }
            rate = fixed_rates.get(currency_code, 1.0)
        
        revenue_in_usd = amount * rate
        
        old_target_balance = target_wallet.balance
        old_usd_balance = usd_wallet.balance
        
        target_wallet.withdraw(amount)
        usd_wallet.deposit(revenue_in_usd)
        
        if not self.db_manager.save_portfolio(portfolio):
            return False, "Ошибка сохранения портфеля"
        
        lines = [f"Продажа произведена: {amount:.4f} {currency_code} по курсу {rate:.8f} USD/{currency_code}"]
        lines.append("Изменения в кошельках:")
        lines.append(f"- {currency_code}: было {old_target_balance:.4f} → стало {target_wallet.balance:.4f}")
        lines.append(f"- USD: было {old_usd_balance:.4f} → стало {usd_wallet.balance:.4f}")
        lines.append(f"Выручка: {revenue_in_usd:.2f} USD")
        
        return True, "\n".join(lines)