import requests
from abc import ABC, abstractmethod
from typing import Dict
from .config import ParserConfig


class ApiRequestError(Exception):
    """Exception for API request errors"""
    pass


class ApiRateLimitError(ApiRequestError):
    """API rate limit exceeded"""
    pass


class ApiAuthError(ApiRequestError):
    """API authentication failed"""
    pass


class BaseApiClient(ABC):
    """Abstract base class for API clients"""
    
    def __init__(self, config: ParserConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CurrencyParser/1.0'
        })
    
    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """Fetch currency rates from API"""
        pass
    
    def _handle_http_error(self, response: requests.Response) -> None:
        """Handle HTTP error responses with specific messages"""
        if response.status_code == 429:
            raise ApiRateLimitError(
                f"Rate limit exceeded for {response.url}. "
                f"Please try again later."
            )
        elif response.status_code == 401:
            raise ApiAuthError(
                f"Authentication failed for {response.url}. "
                f"Check your API key."
            )
        elif response.status_code == 403:
            raise ApiAuthError(
                f"Access forbidden for {response.url}. "
                f"Check your API permissions."
            )
        elif 400 <= response.status_code < 500:
            raise ApiRequestError(
                f"Client error {response.status_code} for {response.url}: "
                f"{response.text[:100]}"
            )
        elif 500 <= response.status_code < 600:
            raise ApiRequestError(
                f"Server error {response.status_code} for {response.url}. "
                f"Please try again later."
            )
        else:
            raise ApiRequestError(
                f"HTTP error {response.status_code} for {response.url}"
            )


class CoinGeckoClient(BaseApiClient):
    """Client for working with CoinGecko API"""
    
    def fetch_rates(self) -> Dict[str, float]:
        """Get cryptocurrency rates from CoinGecko"""
        try:
            crypto_ids = [
                self.config.CRYPTO_ID_MAP[crypto] 
                for crypto in self.config.CRYPTO_CURRENCIES 
                if crypto in self.config.CRYPTO_ID_MAP
            ]
            
            if not crypto_ids:
                return {} 
            
            params = {
                "ids": ",".join(crypto_ids),
                "vs_currencies": self.config.BASE_CURRENCY.lower()
            }
            
            response = self.session.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if response.status_code != 200:
                self._handle_http_error(response)
            
            data = response.json()
            
            rates = {}
            for crypto_code in self.config.CRYPTO_CURRENCIES:
                if crypto_code not in self.config.CRYPTO_ID_MAP:
                    continue 
                    
                crypto_id = self.config.CRYPTO_ID_MAP[crypto_code]
                if (crypto_id in data and 
                    self.config.BASE_CURRENCY.lower() in data[crypto_id]):
                    
                    rate = data[crypto_id][self.config.BASE_CURRENCY.lower()]
                    rates[f"{crypto_code}_{self.config.BASE_CURRENCY}"] = rate
            
            return rates
            
        except requests.exceptions.Timeout:
            raise ApiRequestError(
                f"Request to CoinGecko timed out after {self.config.REQUEST_TIMEOUT}s"
            )
        except requests.exceptions.ConnectionError:
            raise ApiRequestError(
                "Connection error to CoinGecko. Check your internet connection."
            )
        except (ApiRateLimitError, ApiAuthError):
            raise  
        except KeyError as e:
            raise ApiRequestError(
                f"Data parsing error from CoinGecko: missing key '{e}'"
            )
        except ValueError as e:
            raise ApiRequestError(
                f"Invalid JSON response from CoinGecko: {e}"
            )
        except Exception as e:
            raise ApiRequestError(
                f"Unexpected error when requesting CoinGecko: {str(e)}"
            )


class ExchangeRateApiClient(BaseApiClient):
    """Client for working with ExchangeRate-API"""
    
    def fetch_rates(self) -> Dict[str, float]:
        """Get fiat currency rates from ExchangeRate-API"""
        try:
            if not self.config.EXCHANGERATE_API_KEY or self.config.EXCHANGERATE_API_KEY == "demo_key":
                raise ApiAuthError("Invalid or missing ExchangeRate-API key")
            
            url = f"{self.config.EXCHANGERATE_API_URL}/{self.config.EXCHANGERATE_API_KEY}/latest/{self.config.BASE_CURRENCY}"
            
            response = self.session.get(
                url,
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if response.status_code != 200:
                self._handle_http_error(response)
            
            data = response.json()
            
            if data.get("result") != "success":
                error_type = data.get("error-type", "unknown error")
                raise ApiRequestError(f"ExchangeRate-API error: {error_type}")
            
            rates = {}
            conversion_rates = data.get("conversion_rates", {})
            
            for currency in self.config.FIAT_CURRENCIES:
                if currency in conversion_rates:
                    rate = conversion_rates[currency]
                    rates[f"{self.config.BASE_CURRENCY}_{currency}"] = rate
            
            return rates
            
        except requests.exceptions.Timeout:
            raise ApiRequestError(
                f"Request to ExchangeRate-API timed out after {self.config.REQUEST_TIMEOUT}s"
            )
        except requests.exceptions.ConnectionError:
            raise ApiRequestError(
                "Connection error to ExchangeRate-API. Check your internet connection."
            )
        except (ApiRateLimitError, ApiAuthError):
            raise  # Re-raise specific errors
        except KeyError as e:
            raise ApiRequestError(
                f"Data parsing error from ExchangeRate-API: missing key '{e}'"
            )
        except ValueError as e:
            raise ApiRequestError(
                f"Invalid JSON response from ExchangeRate-API: {e}"
            )
        except Exception as e:
            raise ApiRequestError(
                f"Unexpected error when requesting ExchangeRate-API: {str(e)}"
            )