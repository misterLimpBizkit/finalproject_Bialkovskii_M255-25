import os

class ParserConfig:
    # API key loaded from environment variable
    EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY", "19b4ae2cbd9426591737db05")

    # Endpoints
    COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL = "https://v6.exchangerate-api.com/v6"

    # Currency lists
    BASE_CURRENCY = "USD"
    FIAT_CURRENCIES = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES = ("BTC", "ETH", "SOL")
    CRYPTO_ID_MAP = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
    }

    # Paths
    RATES_FILE_PATH = "data/rates.json"
    HISTORY_FILE_PATH = "data/exchange_rates.json"

    # Network parameters
    REQUEST_TIMEOUT = 10

