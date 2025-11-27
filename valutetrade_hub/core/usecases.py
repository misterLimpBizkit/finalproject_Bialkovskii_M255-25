import json
import os
from datetime import datetime
from typing import Dict, Optional
from valutetrade_hub.core.models import User, Portfolio, Wallet


class UserStorage:
    def __init__(self, users_file: str = "data/users.json"):
        self.users_file = users_file
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Creates the directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
    
    def load_users(self) -> Dict[str, User]:
        """Loads users from the file"""
        if not os.path.exists(self.users_file):
            return {}
        
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

        except json.JSONDecodeError:
            print('Ошибка чтения файла')
            return {}
        except FileNotFoundError:
            print('Файл не найден')
            return {}
        
        users = {}
        for username, user_data in data.items():
            user = User.from_saved_data(
                user_id=user_data['user_id'],
                username=username,
                hashed_password=user_data['hashed_password'],
                salt=user_data['salt'],
                registration_date=datetime.fromisoformat(user_data['registration_date'])
            )
            
            users[username] = user
        
        return users
    
    def save_users(self, users: Dict[str, User]):
        """Saves users into the file"""
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
            print(f"Пользователи успешно сохранены в {self.users_file}")
        except PermissionError:
            print(f"Ошибка: Нет прав на запись в файл {self.users_file}")
        except IOError as e:
            print(f"Ошибка ввода-вывода при сохранении пользователей: {e}")
        except Exception as e:
            print(f"Неизвестная ошибка при сохранении пользователей: {e}")


class PortfolioStorage:
    def __init__(self, portfolios_file: str = "data/portfolios.json"):
        self.portfolios_file = portfolios_file
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Creates data directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.portfolios_file), exist_ok=True)
    
    def load_portfolio(self, user_id: int) -> Portfolio:
        """Loads user's portfolio"""
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
    
    def save_portfolio(self, portfolio: Portfolio):
        """Save user portfolio using Portfolio's built-in method"""
        try:
            try:
                with open(self.portfolios_file, 'r', encoding='utf-8') as f:
                    all_portfolios = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                all_portfolios = {}
            
            all_portfolios[str(portfolio.user_id)] = portfolio.get_portfolio_info()
            
            with open(self.portfolios_file, 'w', encoding='utf-8') as f:
                json.dump(all_portfolios, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Ошибка сохранения портфеля: {e}")


class RateStorage:
    def __init__(self, rates_file: str = "data/rates.json"):
        self.rates_file = rates_file
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Creates data directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.rates_file), exist_ok=True)
    
    def get_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get exchange rate"""
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
    
    def update_rate(self, from_currency: str, to_currency: str, rate: float):
        """Update exchange rate"""
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
        
        with open(self.rates_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class UserUseCase:
    def __init__(self):
        self.user_storage = UserStorage()
        self.portfolio_storage = PortfolioStorage()
    
    def register_user(self, username: str, password: str) -> tuple[bool, str]:
        """Registration of a new user"""
        if not username or not username.strip():
            return False, "Имя пользователя не может быть пустым"
        
        if len(password) < 4:
            return False, "Пароль должен быть не короче 4 символов"
        
        users = self.user_storage.load_users()
        
        if username in users:
            return False, f"Имя пользователя '{username}' уже занято"
        
        user_id = max([user.user_id for user in users.values()], default=0) + 1
        
        user = User(user_id, username, password, datetime.now())
        users[username] = user
        
        self.user_storage.save_users(users)
        
        portfolio = Portfolio(user_id)
        self.portfolio_storage.save_portfolio(portfolio)
        
        return True, f"Пользователь '{username}' зарегистрирован (id={user_id}). Войдите: login --username {username} --password ****"
    
    def login_user(self, username: str, password: str) -> tuple[bool, str]:
        """Authorizes the user"""
        users = self.user_storage.load_users()
        
        if username not in users:
            return False, f"Пользователь '{username}' не найден"
        
        user = users[username]
        
        if not user.verify_password(password):
            return False, "Неверный пароль"
        
        return True, f"Вы вошли как '{username}'"


class RateUseCase:
    """Business logic for exchange rates"""
    
    def __init__(self):
        self.rate_storage = RateStorage()
    
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
        
        fixed_rates = {
            'USD': 1.0,
            'EUR': 1.18,
            'BTC': 0.000025,
            'ETH': 0.0003,
        }
        
        rate = self.rate_storage.get_rate(from_currency, to_currency)
        
        if rate is None:
            from_rate_to_usd = self.rate_storage.get_rate(from_currency, 'USD')
            to_rate_to_usd = self.rate_storage.get_rate(to_currency, 'USD')
            
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
        self.rate_storage.update_rate(from_currency, to_currency, rate)
        
        return True, rate


class PortfolioUseCase:
    """Business logic for portfolio management"""
    
    def __init__(self, rate_usecase: RateUseCase = None):
        self.portfolio_storage = PortfolioStorage()
        self.rate_usecase = rate_usecase or RateUseCase()
    
    def get_portfolio_info(self, user_id: int, base_currency: str = "USD") -> tuple[bool, str]:
        """Display user's portfolio info"""
        portfolio = self.portfolio_storage.load_portfolio(user_id)
        
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
    
    def buy_currency(self, user_id: int, currency_code: str, amount: float) -> tuple[bool, str]:
        """Buy currency using USD from the USD wallet"""
        if amount <= 0:
            return False, "'amount' должен быть положительным числом"
        
        portfolio = self.portfolio_storage.load_portfolio(user_id)
        
        if currency_code == "USD":
            if currency_code not in portfolio.wallets:
                portfolio.add_currency(currency_code)
            
            wallet = portfolio.get_wallet(currency_code)
            if not wallet:
                return False, f"Не удалось создать кошелек для {currency_code}"
            
            old_balance = wallet.balance
            wallet.deposit(amount)
            
            self.portfolio_storage.save_portfolio(portfolio)
            
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
        
        self.portfolio_storage.save_portfolio(portfolio)
        
        lines = [f"Покупка произведена: {amount:.4f} {currency_code} по курсу {rate:.8f} USD/{currency_code}"]
        lines.append("Изменения в кошельках:")
        lines.append(f"- {currency_code}: было {old_target_balance:.4f} → стало {target_wallet.balance:.4f}")
        lines.append(f"- USD: было {old_usd_balance:.4f} → стало {usd_wallet.balance:.4f}")
        lines.append(f"Стоимость покупки: {cost_in_usd:.2f} USD")
        
        return True, "\n".join(lines)
    
    def sell_currency(self, user_id: int, currency_code: str, amount: float) -> tuple[bool, str]:
        """Sell currency and deposit equivalent USD to the USD wallet"""
        if amount <= 0:
            return False, "'amount' должен быть положительным числом"
        
        portfolio = self.portfolio_storage.load_portfolio(user_id)
        
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
        
        self.portfolio_storage.save_portfolio(portfolio)
        
        lines = [f"Продажа произведена: {amount:.4f} {currency_code} по курсу {rate:.8f} USD/{currency_code}"]
        lines.append("Изменения в кошельках:")
        lines.append(f"- {currency_code}: было {old_target_balance:.4f} → стало {target_wallet.balance:.4f}")
        lines.append(f"- USD: было {old_usd_balance:.4f} → стало {usd_wallet.balance:.4f}")
        lines.append(f"Выручка: {revenue_in_usd:.2f} USD")
        
        return True, "\n".join(lines)