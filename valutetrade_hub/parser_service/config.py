import os

class ParserConfig:
    EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY", "19b4ae2cbd9426591737db05")

    COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL = "https://v6.exchangerate-api.com/v6"

    BASE_CURRENCY = "USD"
    FIAT_CURRENCIES = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES = ("BTC", "ETH", "SOL")
    CRYPTO_ID_MAP = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
    }

    RATES_FILE_PATH = "data/rates.json"
    HISTORY_FILE_PATH = "data/exchange_rates.json"

    REQUEST_TIMEOUT = 10

