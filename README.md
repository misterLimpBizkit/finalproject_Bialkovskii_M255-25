# ValutaTrade Hub

Система управления валютным портфелем с поддержкой криптовалют и фиатных валют.

## Описание

ValutaTrade Hub - это система для управления портфелем криптовалют и фиатных валют с возможностью отслеживания курсов в реальном времени.

## Установка

```bash
poetry install
```

## Использование

### Запуск CLI интерфейса

```bash
poetry run valutetrade
```

### Доступные команды

#### Регистрация и вход
- `register --username USERNAME --password PASSWORD` - Регистрация нового пользователя
- `login --username USERNAME --password PASSWORD` - Вход в систему

#### Управление портфелем
- `show-portfolio [--base BASE]` - Показать портфель
- `buy --currency CURRENCY --amount AMOUNT` - Купить валюту
- `sell --currency CURRENCY --amount AMOUNT` - Продать валюту

#### Работа с курсами валют
- `get-rate --from FROM --to TO` - Получить курс валюты
- `update-rates [--source SOURCE]` - Обновить курсы валют
- `show-rates [--currency CURRENCY] [--top N] [--base BASE]` - Показать актуальные курсы

#### Служебные команды
- `help` - Показать справку
- `exit` - Выход из программы

### Команда update-rates

Обновляет курсы валют из внешних источников:

```bash
poetry run valutetrade update-rates
```

Опциональные параметры:
- `--source coingecko` - обновить только криптовалюты из CoinGecko
- `--source exchangerate` - обновить только фиатные валюты из ExchangeRate-API

### Команда show-rates

Показывает актуальные курсы из локального кэша:

```bash
poetry run valutetrade show-rates
```

Опциональные параметры:
- `--currency BTC` - показать курс только для указанной валюты
- `--top 5` - показать 5 самых дорогих криптовалют
- `--base EUR` - показать курсы относительно EUR вместо USD

## Структура проекта

```
valutetrade_hub/
├── cli/              # Командный интерфейс
├── core/             # Основная бизнес-логика
├── infra/            # Инфраструктурные компоненты
├── parser_service/   # Сервис парсинга курсов валют
└── data/             # Данные приложения
```

## Сервис парсинга курсов

Сервис парсинга (`parser_service`) отвечает за получение и обновление курсов валют из внешних источников:
- CoinGecko для криптовалют (BTC, ETH, SOL)
- ExchangeRate-API для фиатных валют (EUR, GBP, RUB)

Сервис сохраняет данные в двух файлах:
- `data/rates.json` - актуальные курсы для использования в основном приложении
- `data/exchange_rates.json` - история всех полученных курсов

## Лицензия

MIT