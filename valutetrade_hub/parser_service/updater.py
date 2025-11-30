import logging
from typing import Dict, Any
from datetime import datetime
from .config import ParserConfig
from .api_clients import CoinGeckoClient, ExchangeRateApiClient, ApiRequestError
from .storage import StorageManager

class RatesUpdater:
    """Main class for updating currency rates"""
    
    def __init__(self, config: ParserConfig = None):
        self.config = config or ParserConfig()
        self.logger = logging.getLogger(__name__)
        self.storage = StorageManager(self.config)
        
        # Initialize API clients
        self.clients = {
            "coingecko": CoinGeckoClient(self.config),
            "exchangerate": ExchangeRateApiClient(self.config)
        }
    
    def run_update(self, source: str = None) -> Dict[str, Any]:
        """
        Run currency rates update
        
        Args:
            source (str, optional): Source for update (coingecko or exchangerate)
            
        Returns:
            Dict[str, Any]: Update result with rate information
        """
        self.logger.info("Starting rates update...")
        
        # Dictionary to store all rates
        all_rates = {}
        
        # Counters for statistics
        updated_count = 0
        errors = []
        
        # Determine which sources to update
        sources_to_update = []
        if source:
            if source in self.clients:
                sources_to_update = [source]
            else:
                self.logger.error(f"Unknown source: {source}")
                raise ValueError(f"Unknown source: {source}")
        else:
            sources_to_update = list(self.clients.keys())
        
        # Update data from each source
        for source_name in sources_to_update:
            try:
                self.logger.info(f"Fetching from {source_name}...")
                client = self.clients[source_name]
                rates = client.fetch_rates()
                
                # Add rates to the overall dictionary
                all_rates.update(rates)
                
                # Add records to history
                for pair, rate in rates.items():
                    from_currency, to_currency = pair.split("_")
                    self.storage.add_history_record(
                        from_currency=from_currency,
                        to_currency=to_currency,
                        rate=rate,
                        source=source_name
                    )
                
                self.logger.info(f"Fetching from {source_name}... OK ({len(rates)} rates)")
                updated_count += len(rates)
                
            except ApiRequestError as e:
                error_msg = f"Failed to fetch from {source_name}: {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
                # Continue with other sources
                continue
            except Exception as e:
                error_msg = f"Unexpected error from {source_name}: {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
                # Continue with other sources
                continue
        
        # Prepare data for cache
        cache_rates = {}
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        for pair, rate in all_rates.items():
            cache_rates[pair] = {
                "rate": rate,
                "updated_at": timestamp,
                # Determine source by pair prefix
                "source": "CoinGecko" if any(crypto in pair.split('_')[0] for crypto in self.config.CRYPTO_CURRENCIES) else "ExchangeRate-API"
            }
        
        # Save cache
        self.storage.save_cache(cache_rates)
        
        # Form result
        result = {
            "updated_count": updated_count,
            "last_refresh": timestamp,
            "errors": errors,
            "rates": cache_rates
        }
        
        if errors:
            self.logger.warning(f"Update completed with {len(errors)} errors. Check logs for details.")
        else:
            self.logger.info(f"Update successful. Total rates updated: {updated_count}. Last refresh: {timestamp}")
        
        return result
    
    def get_rates_summary(self) -> Dict[str, Any]:
        """
        Get summary of current rates from cache
        
        Returns:
            Dict[str, Any]: Rate summary
        """
        cache = self.storage.load_cache()
        return {
            "pairs": cache.get("pairs", {}),
            "last_refresh": cache.get("last_refresh"),
            "total_pairs": len(cache.get("pairs", {}))
        }

