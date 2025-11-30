"""
Business logic layer for the currency trading system.
This module contains use cases that implement the business logic of the application.
"""

from datetime import datetime

from valutetrade_hub.core.models import User, Portfolio
from valutetrade_hub.core.currencies import is_valid_currency
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
            return False, "Username cannot be empty"
        
        if len(password) < 4:
            return False, "Password must be at least 4 characters long"
        
        users = self.db_manager.load_users()
        
        if username in users:
            return False, f"Username '{username}' is already taken"
        
        user_id = max([user.user_id for user in users.values()], default=0) + 1
        
        user = User(user_id, username, password, datetime.now())
        users[username] = user
        
        if not self.db_manager.save_users(users):
            return False, "Error saving user"
        
        portfolio = Portfolio(user_id)
        if not self.db_manager.save_portfolio(portfolio):
            return False, "Error creating portfolio"
        
        return True, f"User '{username}' registered (id={user_id}). Login: login --username {username} --password ****"
    
    @log_action("user_login")
    def login_user(self, username: str, password: str) -> tuple[bool, str]:
        """Authorizes the user"""
        users = self.db_manager.load_users()
        
        if username not in users:
            return False, f"User '{username}' not found"
        
        user = users[username]
        
        if not user.verify_password(password):
            return False, "Invalid password"
        
        return True, f"You are logged in as '{username}'"


class RateUseCase:
    """Business logic for exchange rates"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    @log_action("get_exchange_rate")
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> tuple[bool, str]:
        """Get formatted exchange rate information"""
        success, rate = self.calculate_rate(from_currency, to_currency)
        if not success:
            return False, f"Rate {from_currency}→{to_currency} is unavailable. Please try again later."
        
        if from_currency.upper() == to_currency.upper():
            lines = [f"Rate {from_currency}→{to_currency}: 1.00000000"]
            lines.append(f"Reverse rate {to_currency}→{from_currency}: 1.00")
            return True, "\n".join(lines)
        
        reverse_rate = 1.0 / rate if rate != 0 else 0.0
        
        updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        lines = [f"Rate {from_currency}→{to_currency}: {rate:.8f} (updated: {updated_at})"]
        lines.append(f"Reverse rate {to_currency}→{from_currency}: {reverse_rate:.8f}")
        
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
            'BTC': 91000.0,
            'ETH': 2000.0,
        }
        
        rate = self.db_manager.get_rate(from_currency, to_currency)
        
        if rate is None:
            # Try to get rates through USD
            from_rate_to_usd = self.db_manager.get_rate(from_currency, 'USD')
            to_rate_to_usd = self.db_manager.get_rate(to_currency, 'USD')
            
            # If we can't get through USD, try through reverse rates
            if from_rate_to_usd is None:
                usd_rate_to_from = self.db_manager.get_rate('USD', from_currency)
                if usd_rate_to_from and usd_rate_to_from != 0:
                    from_rate_to_usd = 1.0 / usd_rate_to_from
            
            if to_rate_to_usd is None:
                usd_rate_to_to = self.db_manager.get_rate('USD', to_currency)
                if usd_rate_to_to and usd_rate_to_to != 0:
                    to_rate_to_usd = 1.0 / usd_rate_to_to
            
            # If we have rates to USD, calculate through them
            if from_rate_to_usd is not None and to_rate_to_usd is not None and to_rate_to_usd != 0:
                rate = from_rate_to_usd / to_rate_to_usd
            else:
                # Use fixed rates as a fallback
                from_rate_to_usd = fixed_rates.get(from_currency, 1.0)
                to_rate_to_usd = fixed_rates.get(to_currency, 1.0)
                
                if to_rate_to_usd > 0:
                    rate = from_rate_to_usd / to_rate_to_usd
                else:
                    rate = None
        
        if rate is None:
            return False, 0.0
        
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
            return False, f"Unsupported currency: {base_currency}"
        
        portfolio = self.db_manager.load_portfolio(user_id)
        
        wallets = portfolio.wallets
        
        if not wallets:
            return True, f"User portfolio (id={user_id}) is empty"
        
        lines = [f"User portfolio (base: {base_currency}):"]
        total_value = 0.0
        
        for currency_code, wallet in wallets.items():
            success, rate = self.rate_usecase.calculate_rate(currency_code, base_currency)
            if not success:
                # Fixed rates relative to USD
                fixed_rates = {
                    'USD': 1.0,
                    'EUR': 1.18,
                    'BTC': 91000.0,
                    'ETH': 2000.0,
                }
                
                # Get rates relative to USD
                from_rate_to_usd = fixed_rates.get(currency_code, 1.0)
                to_rate_to_usd = fixed_rates.get(base_currency, 1.0)
                
                # Calculate rate through USD
                if to_rate_to_usd > 0:
                    rate = from_rate_to_usd / to_rate_to_usd
                else:
                    rate = 1.0 if currency_code == base_currency else 0.0
            else:
                # Save the calculated rate in storage for future use
                self.db_manager.update_rate(currency_code, base_currency, rate)
            
            value = wallet.balance * rate
            total_value += value
            lines.append(f"- {currency_code}: {wallet.balance:.4f} → {value:.2f} {base_currency}")
        
        lines.append("-" * 30)
        lines.append(f"TOTAL: {total_value:.2f} {base_currency}")
        
        return True, "\n".join(lines)
    
    @log_action("buy_currency")
    def buy_currency(self, user_id: int, currency_code: str, amount: float) -> tuple[bool, str]:
        """Buy currency using USD from the USD wallet"""
        
        if amount <= 0:
            return False, "Amount must be a positive number"
        
        if not is_valid_currency(currency_code):
            return False, f"Unsupported currency: {currency_code}"
        
        portfolio = self.db_manager.load_portfolio(user_id)
        
        if currency_code == "USD":
            if currency_code not in portfolio.wallets:
                portfolio.add_currency(currency_code)
            
            wallet = portfolio.get_wallet(currency_code)
            if not wallet:
                return False, f"Failed to create wallet for {currency_code}"
            
            old_balance = wallet.balance
            wallet.deposit(amount)
            
            if not self.db_manager.save_portfolio(portfolio):
                return False, "Error saving portfolio"
            
            lines = [f"Funds deposited: {amount:.4f} {currency_code}"]
            lines.append("Wallet changes:")
            lines.append(f"- {currency_code}: was {old_balance:.4f} → became {wallet.balance:.4f}")
            
            return True, "\n".join(lines)
        
        if currency_code not in portfolio.wallets:
            portfolio.add_currency(currency_code)
        
        target_wallet = portfolio.get_wallet(currency_code)
        usd_wallet = portfolio.get_wallet("USD")
        
        if not target_wallet:
            return False, f"Failed to create wallet for {currency_code}"
        
        if not usd_wallet:
            return False, "USD wallet not found. Please deposit funds to USD wallet."
        
        success, rate = self.rate_usecase.calculate_rate(currency_code, "USD")
        if not success:
            fixed_rates = {
                'USD': 1.0,
                'EUR': 1.18,
                'BTC': 91000.0,
                'ETH': 2000.0,
            }
            rate = fixed_rates.get(currency_code, 1.0)
        else:
            # Save the calculated rate in storage for future use
            self.db_manager.update_rate(currency_code, "USD", rate)
        
        cost_in_usd = amount * rate
        if usd_wallet.balance < cost_in_usd:
            return False, f"Insufficient funds in USD wallet: available {usd_wallet.balance:.4f} USD, required {cost_in_usd:.4f} USD"
        
        old_target_balance = target_wallet.balance
        old_usd_balance = usd_wallet.balance
        
        target_wallet.deposit(amount)
        usd_wallet.withdraw(cost_in_usd)
        
        if not self.db_manager.save_portfolio(portfolio):
            return False, "Error saving portfolio"
        
        lines = [f"Purchase made: {amount:.4f} {currency_code} at rate {rate:.8f} USD/{currency_code}"]
        lines.append("Wallet changes:")
        lines.append(f"- {currency_code}: was {old_target_balance:.4f} → became {target_wallet.balance:.4f}")
        lines.append(f"- USD: was {old_usd_balance:.4f} → became {usd_wallet.balance:.4f}")
        lines.append(f"Purchase cost: {cost_in_usd:.4f} USD")
        
        return True, "\n".join(lines)
    
    @log_action("sell_currency")
    def sell_currency(self, user_id: int, currency_code: str, amount: float) -> tuple[bool, str]:
        """Sell currency and deposit equivalent USD to the USD wallet"""
        
        if amount <= 0:
            return False, "Amount must be a positive number"
        
        if not is_valid_currency(currency_code):
            return False, f"Unsupported currency: {currency_code}"
        
        portfolio = self.db_manager.load_portfolio(user_id)
        
        if currency_code not in portfolio.wallets:
            return False, f"You don't have a '{currency_code}' wallet. Add currency: it is created automatically on first purchase."
        
        target_wallet = portfolio.get_wallet(currency_code)
        usd_wallet = portfolio.get_wallet("USD")
        
        if not target_wallet:
            return False, f"Wallet {currency_code} not found"
        
        if not usd_wallet:
            portfolio.add_currency("USD")
            usd_wallet = portfolio.get_wallet("USD")
            if not usd_wallet:
                return False, "Failed to create USD wallet"
        
        if target_wallet.balance < amount:
            return False, f"Insufficient funds: available {target_wallet.balance:.4f} {currency_code}, required {amount:.4f} {currency_code}"
        
        success, rate = self.rate_usecase.calculate_rate(currency_code, "USD")
        if not success:
            fixed_rates = {
                'USD': 1.0,
                'EUR': 1.18,
                'BTC': 91000.0,
                'ETH': 2000.0,
            }
            rate = fixed_rates.get(currency_code, 1.0)
        else:
            # Save the calculated rate in storage for future use
            self.db_manager.update_rate(currency_code, "USD", rate)
        
        revenue_in_usd = amount * rate
        
        old_target_balance = target_wallet.balance
        old_usd_balance = usd_wallet.balance
        
        target_wallet.withdraw(amount)
        usd_wallet.deposit(revenue_in_usd)
        
        if not self.db_manager.save_portfolio(portfolio):
            return False, "Error saving portfolio"
        
        lines = [f"Sale made: {amount:.4f} {currency_code} at rate {rate:.8f} USD/{currency_code}"]
        lines.append("Wallet changes:")
        lines.append(f"- {currency_code}: was {old_target_balance:.4f} → became {target_wallet.balance:.4f}")
        lines.append(f"- USD: was {old_usd_balance:.4f} → became {usd_wallet.balance:.4f}")
        lines.append(f"Revenue: {revenue_in_usd:.4f} USD")
        
        return True, "\n".join(lines)

