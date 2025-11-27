"""
Custom exceptions for the currency trading system.
This module defines custom exceptions used throughout the application.
"""

class InsufficientFundsError(Exception):
    """Raised when there are insufficient funds for a transaction"""
    
    def __init__(self, currency: str, available: float, required: float):
        self.currency = currency
        self.available = available
        self.required = required
        super().__init__(f"Недостаточно средств в {currency}: доступно {available:.4f}, необходимо {required:.4f}")


class CurrencyNotFoundError(Exception):
    """Raised when a currency is not found"""
    
    def __init__(self, currency_code: str):
        self.currency_code = currency_code
        super().__init__(f"Валюта '{currency_code}' не найдена")


class ApiRequestError(Exception):
    """Raised when there is an error with an API request"""
    
    def __init__(self, message: str):
        super().__init__(f"Ошибка API запроса: {message}")