import requests
from abc import ABC, abstractmethod
from typing import Dict
from .config import ParserConfig


class ApiRequestError(Exception):
    """Exception for API request errors"""
    pass


class BaseApiClient(ABC):
    """Abstract base class for API clients"""
    
    def __init__(self, config: ParserConfig):
        self.config = config
    
    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """Fetch currency rates from API"""
        pass


class CoinGeckoClient(BaseApiClient):
    """Client for working with CoinGecko API"""
    
    def fetch_rates(self) -> Dict[str, float]:
        """Get cryptocurrency rates from CoinGecko"""
        try:
            crypto_ids = [self.config.CRYPTO_ID_MAP[crypto] for crypto in self.config.CRYPTO_CURRENCIES]
            
            params = {
                "ids": ",".join(crypto_ids),
                "vs_currencies": self.config.BASE_CURRENCY.lower()
            }
            
            response = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 429:
                raise ApiRequestError("CoinGecko API rate limit exceeded. Please try again later.")
            elif response.status_code == 401:
                raise ApiRequestError("CoinGecko API authentication failed.")
            elif response.status_code == 403:
                raise ApiRequestError("CoinGecko API access forbidden.")
            elif response.status_code != 200:
                raise ApiRequestError(f"CoinGecko API returned status {response.status_code}: {response.text[:100]}")
            
            data = response.json()
            
            rates = {}
            for crypto_code in self.config.CRYPTO_CURRENCIES:
                crypto_id = self.config.CRYPTO_ID_MAP[crypto_code]
                if crypto_id in data and self.config.BASE_CURRENCY.lower() in data[crypto_id]:
                    rate = data[crypto_id][self.config.BASE_CURRENCY.lower()]
                    rates[f"{crypto_code}_{self.config.BASE_CURRENCY}"] = rate
            
            return rates
            
        except requests.exceptions.Timeout:
            raise ApiRequestError(f"CoinGecko API request timed out after {self.config.REQUEST_TIMEOUT} seconds")
        except requests.exceptions.ConnectionError:
            raise ApiRequestError("Connection error to CoinGecko API. Check your internet connection.")
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Network error when requesting CoinGecko: {str(e)}")
        except KeyError as e:
            raise ApiRequestError(f"Error parsing data from CoinGecko: missing key {str(e)}")
        except Exception as e:
            raise ApiRequestError(f"Unexpected error when requesting CoinGecko: {str(e)}")


class ExchangeRateApiClient(BaseApiClient):
    """Client for working with ExchangeRate-API"""
    
    def fetch_rates(self) -> Dict[str, float]:
        """Get fiat currency rates from ExchangeRate-API"""
        try:
            url = f"{self.config.EXCHANGERATE_API_URL}/{self.config.EXCHANGERATE_API_KEY}/latest/{self.config.BASE_CURRENCY}"
            
            response = requests.get(
                url,
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 429:
                raise ApiRequestError("ExchangeRate-API rate limit exceeded. Please try again later.")
            elif response.status_code == 401:
                raise ApiRequestError("ExchangeRate-API authentication failed. Check your API key.")
            elif response.status_code == 403:
                raise ApiRequestError("ExchangeRate-API access forbidden. Check your API permissions.")
            elif response.status_code != 200:
                raise ApiRequestError(f"ExchangeRate-API returned status {response.status_code}: {response.text[:100]}")
            
            data = response.json()
            
            if data.get("result") != "success":
                error_type = data.get("error-type", "unknown error")
                raise ApiRequestError(f"ExchangeRate-API returned error: {error_type}")
            
            rates = {}
            for currency in self.config.FIAT_CURRENCIES:
                if currency in data.get("conversion_rates", {}):
                    rate = data["conversion_rates"][currency]
                    rates[f"{self.config.BASE_CURRENCY}_{currency}"] = rate
            
            return rates
            
        except requests.exceptions.Timeout:
            raise ApiRequestError(f"ExchangeRate-API request timed out after {self.config.REQUEST_TIMEOUT} seconds")
        except requests.exceptions.ConnectionError:
            raise ApiRequestError("Connection error to ExchangeRate-API. Check your internet connection.")
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Network error when requesting ExchangeRate-API: {str(e)}")
        except KeyError as e:
            raise ApiRequestError(f"Error parsing data from ExchangeRate-API: missing key {str(e)}")
        except Exception as e:
            raise ApiRequestError(f"Unexpected error when requesting ExchangeRate-API: {str(e)}")