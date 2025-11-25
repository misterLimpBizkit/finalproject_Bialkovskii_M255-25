import hashlib
import secrets
from datetime import datetime


class User:
    def __init__(self, user_id: int, username: str, password: str, registration_date: datetime):
        if len(password) < 4:
            raise ValueError("Пароль должен быть больше 4 символов")
        self._user_id = user_id
        self._username = username
        self._salt = secrets.token_hex(16)
        self._hashed_password = self._hash_password(password, self._salt)
        self._registration_date = registration_date or datetime.now() 
        
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password"""
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def get_user_info(self):
        '''Display user info'''
        return {
            'user_id': self._user_id,
            'username': self._username,
            'registration_date': self._registration_date.isoformat(' ')
            }
    
    def change_password(self, new_password: str):
        '''Change user password'''
        if len(new_password) < 4:
            raise ValueError('Пароль должен быть больше 4 символов')
        self._salt = secrets.token_hex(16)
        self._hashed_password = self._hash_password(new_password, self._salt)
    
    def verify_password(self, password: str) -> bool:
        '''Verify user password'''
        if len(password) < 4:
            return False
        return self._hashed_password == self._hash_password(password, self._salt)
    
    @property
    def user_id(self) -> int:
        '''Get user id'''
        return self._user_id
    
    @property
    def username(self) -> str:
        '''Get username'''
        return self._username
    
    @username.setter
    def username(self, new_username: str):
        '''Change username'''
        if not new_username:
            raise ValueError("Имя не может быть пустым")
        self._username = new_username
    
    @property
    def salt(self) -> str:
        '''Display salt'''
        return self._salt
    
    @property
    def hashed_password(self) -> str:
        '''Display hashed password'''
        return self._hashed_password
    
    @property
    def registration_date(self) -> datetime:
        '''Display registration date'''
        return self._registration_date


class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        self._currency_code = currency_code
        self._balance = 0.0
        self.balance = balance
    
    def deposit(self, amount: float):
        '''Add money'''
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError('Невозможно пополнить баланс на отрицательную сумму')
        self.balance += amount
        print(f"Успешно пополнено: {amount} {self.currency_code}")
    
    def withdraw(self, amount: float):
        '''Subtract money'''
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError('Невозможно снять такую сумму')
        if self.balance < amount:
            raise ValueError('Недостаточно средств')
        self.balance -= amount
        print(f"Успешно снято: {amount} {self.currency_code}")
    
    def get_balance_info(self):
        '''Display balance info'''
        return f"Баланс: {self.balance:.2f} {self.currency_code}"
    
    @property
    def currency_code(self) -> str:
        '''Get currency code'''
        return self._currency_code

    @property
    def balance(self) -> float:
        '''Balance getter'''
        return self._balance
    
    @balance.setter
    def balance(self, amount: float):
        '''Balance setter'''
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount < 0:
            raise ValueError('Невозможно установить отрицательный баланс')
        if abs(amount) == float('inf') or amount != amount:
            raise ValueError("Некорректное значение баланса")
        
        self._balance = float(amount)
    


class Portfolio:
    exchange_rates = {
        'USD': 1.0,
        'EUR': 1.18,
        'BTC': 0.000025,
        'ETH': 0.0003,
    }
    
    def __init__(self, user_id: int):
        self._user_id = user_id
        self._wallets = {}
        self.add_currency('USD')
        self.add_currency('BTC')
        self.add_currency('EUR')
    
    @property
    def user(self) -> int:
        return self._user_id
    
    @property
    def wallets(self) -> dict:
        return self._wallets.copy()
    
    def add_currency(self, currency_code: str):
        '''Add currency to portfolio'''
        if currency_code not in self._wallets:
            self._wallets[currency_code] = Wallet(currency_code)
    
    def get_wallet(self, currency_code: str):
        '''Get wallet by currency code'''
        return self._wallets.get(currency_code)
    
    def get_total_value(self, base_currency='USD') -> float:
        '''Get total value of portfolio'''
        total = 0.0
        base_rate = self.exchange_rates.get(base_currency, 1.0)
        
        for wallet in self._wallets.values():
            currency_rate = self.exchange_rates.get(wallet.currency_code, 1.0)
            if currency_rate > 0:
                converted_amount = wallet.balance * (currency_rate / base_rate)
                total += converted_amount
            else:
                raise ValueError(f"Неизвестный код валюты: {wallet.currency_code}")
        return total