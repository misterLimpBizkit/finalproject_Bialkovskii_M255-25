"""
Currency classes for the currency trading system.
This module defines the currency hierarchy with abstract base class and concrete implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class Currency(ABC):
    """Abstract base class for all currencies"""
    
    def __init__(self, code: str, name: str, is_crypto: bool = False):
        self._code = code
        self._name = name
        self._is_crypto = is_crypto
    
    @property
    def code(self) -> str:
        """Get currency code"""
        return self._code
    
    @property
    def name(self) -> str:
        """Get currency name"""
        return self._name
    
    @property
    def is_crypto(self) -> bool:
        """Check if currency is cryptocurrency"""
        return self._is_crypto
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get currency information"""
        return {
            'code' : self.code,
            'name' : self.name 
            }
        


class FiatCurrency(Currency):
    """Fiat currency implementation"""
    
    def __init__(self, code: str, name: str, country: str):
        super().__init__(code, name, is_crypto=False)
        self._country = country
    
    @property
    def country(self) -> str:
        """Get country of currency"""
        return self._country
    
    def get_info(self) -> Dict[str, Any]:
        """Get fiat currency information"""
        return {
            'code': self.code,
            'name': self.name,
            'type': 'fiat',
            'country': self.country
        }


class CryptoCurrency(Currency):
    """Cryptocurrency implementation"""
    
    def __init__(self, code: str, name: str, algorithm: str = "Unknown"):
        super().__init__(code, name, is_crypto=True)
        self._algorithm = algorithm
    
    @property
    def algorithm(self) -> str:
        """Get cryptocurrency algorithm"""
        return self._algorithm
    
    def get_info(self) -> Dict[str, Any]:
        """Get cryptocurrency information"""
        return {
            'code': self.code,
            'name': self.name,
            'type': 'crypto',
            'algorithm': self.algorithm
        }


USD = FiatCurrency("USD", "US Dollar", "United States")
EUR = FiatCurrency("EUR", "Euro", "European Union")
BTC = CryptoCurrency("BTC", "Bitcoin", "SHA-256")
ETH = CryptoCurrency("ETH", "Ethereum", "Ethash")

CURRENCY_REGISTRY = {
    "USD": USD,
    "EUR": EUR,
    "BTC": BTC,
    "ETH": ETH
}


def get_currency(code: str) -> Currency:
    """Get currency by code"""
    return CURRENCY_REGISTRY.get(code.upper())


def is_valid_currency(code: str) -> bool:
    """Check if currency code is valid"""
    return code.upper() in CURRENCY_REGISTRY