"""Модуль для генерации JSON-ответов для веб-страниц."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import requests

from src.logger_config import setup_logger
from src.utils import filter_by_date_range, format_date, get_greeting, load_transactions

logger = setup_logger(__name__, "views.log", logging.DEBUG)


def load_user_settings() -> Dict[str, Any]:
    """Загружает настройки пользователя из JSON файла."""
    settings_path = Path("user_settings.json")

    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки настроек: {e}")
        return {"user_currencies": ["USD", "EUR"], "user_stocks": []}


def get_currency_rates(currencies: List[str]) -> List[Dict[str, Any]]:
    """
    Получает курсы валют через API.

    Args:
        currencies: Список кодов валют

    Returns:
        Список словарей с курсами
    """
    rates = []

    for currency in currencies:
        try:
            # Используем бесплатное API (пример)
            url = f"https://api.exchangerate-api.com/v4/latest/{currency}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                rate = data.get('rates', {}).get('RUB', 0)
                rates.append({"currency": currency, "rate": round(rate, 2)})
            else:
                # Fallback курс
                fallback_rates = {"USD": 90.0, "EUR": 98.0, "GBP": 112.0, "CNY": 12.5}
                rates.append({"currency": currency, "rate": fallback_rates.get(currency, 90.0)})

        except Exception as e:
            logger.error(f"Ошибка получения курса {currency}: {e}")
            rates.append({"currency": currency, "rate": 90.0})

    return rates


def get_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    """
    Получает цены акций через API.

    Args:
        stocks: Список тикеров акций

    Returns:
        Список словарей с ценами
    """
    prices = []

    for stock in stocks:
        try:
            # Используем Alpha Vantage API (требуется ключ)
            # Для демонстрации используем mock данные
            mock_prices = {
                "AAPL": 175.50, "AMZN": 145.20, "GOOGL": 140.75,
                "MSFT": 380.50, "TSLA": 240.30, "META": 320.10, "NVDA": 890.50
            }
            prices.append({"stock": stock, "price": mock_prices.get(stock, 100.00)})

        except Exception as e:
            logger.error(f"Ошибка получения цены {stock}: {e}")
            prices.append({"stock": stock, "price": 100.00})

    return prices


def get_cards_info(df: pd.DataFrame, end_date: datetime) -> List[Dict[str, Any]]:
    """
    Получает информацию о картах.

    Args:
        df: DataFrame с транзакциями
        end_date: Конечная дата для анализа

    Returns:
        Список информации о картах
    """
    # Фильтруем данные с начала месяца
    filtered_df = filter_by_date_range(df, end_date, "month")

    if filtered_df.empty or 'Номер карты' not in filtered_df.columns:
        return []

    cards_info = []
    cards = filtered_df['Номер карты'].dropna().unique()

    for card in cards:
        if pd.isna(card) or card == 0:
            continue

        card_str = str(int(card)) if isinstance(card, float) else str(card)
        last_digits = card_str[-4:] if len(card_str) >= 4 else card_str

        # Расходы по карте
        card_expenses = filtered_df[
            (filtered_df['Номер карты'] == card)
            & (filtered_df['Сумма операции'] < 0)
            ]
        total_spent = abs(card_expenses['Сумма операции'].sum())
        cashback = total_spent / 100  # 1 рубль на каждые 100 рублей

        cards_info.append({
            "last_digits": last_digits,
            "total_spent": round(total_spent, 2),
            "cashback": round(cashback, 2)
        })

    return cards_info


def get_top_transactions(df: pd.DataFrame, end_date: datetime, n: int = 5) -> List[Dict[str, Any]]:
    """
    Получает топ-N транзакций по сумме.

    Args:
        df: DataFrame с транзакциями
        end_date: Конечная дата
        n: Количество транзакций

    Returns:
        Список топ транзакций
    """
    # Фильтруем данные с начала месяца
    filtered_df = filter_by_date_range(df, end_date, "month")

    if filtered_df.empty:
        return []

    # Сортируем по абсолютной сумме
    filtered_df['abs_amount'] = abs(filtered_df['Сумма операции'])
    top_df = filtered_df.nlargest(n, 'abs_amount')

    transactions = []
    for _, row in top_df.iterrows():
        transactions.append({
            "date": format_date(row.get('Дата операции')),
            "amount": round(abs(row.get('Сумма операции', 0)), 2),
            "category": row.get('Категория', ''),
            "description": row.get('Описание', '')[:50]
        })

    return transactions


def main_page(date_str: str) -> str:
    """
    Главная страница - возвращает JSON с данными для веб-страницы.

    Args:
        date_str: Дата в формате 'YYYY-MM-DD HH:MM:SS'

    Returns:
        JSON строка с данными
    """
    logger.info(f"Генерация главной страницы для даты: {date_str}")

    try:
        # Парсим дату
        current_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

        # Загружаем транзакции
        df = load_transactions()

        if df.empty:
            logger.warning("Нет данных для анализа")
            return json.dumps({"error": "Нет данных"}, ensure_ascii=False)

        # Загружаем настройки
        settings = load_user_settings()

        # Формируем JSON ответ
        response = {
            "greeting": get_greeting(),
            "cards": get_cards_info(df, current_date),
            "top_transactions": get_top_transactions(df, current_date, 5),
            "currency_rates": get_currency_rates(settings.get("user_currencies", [])),
            "stock_prices": get_stock_prices(settings.get("user_stocks", []))
        }

        logger.info("Главная страница успешно сгенерирована")
        return json.dumps(response, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Ошибка генерации главной страницы: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def events_page(date_str: str, period: str = "M") -> str:
    """
    Страница событий - аналитика расходов и поступлений.

    Args:
        date_str: Дата в формате 'YYYY-MM-DD HH:MM:SS'
        period: Период ('W' - неделя, 'M' - месяц, 'Y' - год, 'ALL' - все)

    Returns:
        JSON строка с аналитикой
    """
    logger.info(f"Генерация страницы событий для даты: {date_str}, период: {period}")

    try:
        current_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

        # Определяем период
        period_map = {"W": "week", "M": "month", "Y": "year", "ALL": "all"}
        filter_period = period_map.get(period, "month")

        # Загружаем и фильтруем данные
        df = load_transactions()
        filtered_df = filter_by_date_range(df, current_date, filter_period)

        if filtered_df.empty:
            return json.dumps({"error": "Нет данных"}, ensure_ascii=False)

        # Расходы (отрицательные суммы)
        expenses_df = filtered_df[filtered_df['Сумма операции'] < 0].copy()
        expenses_df['Сумма операции'] = abs(expenses_df['Сумма операции'])

        # Поступления (положительные суммы)
        income_df = filtered_df[filtered_df['Сумма операции'] > 0].copy()

        # Анализ расходов по категориям
        expenses_by_category = expenses_df.groupby('Категория')['Сумма операции'].sum().sort_values(ascending=False)

        # Топ-7 категорий
        top_categories = []
        other_total = 0

        for i, (category, amount) in enumerate(expenses_by_category.items()):
            if i < 7:
                top_categories.append({"category": str(category), "amount": int(round(amount))})
            else:
                other_total += amount

        if other_total > 0:
            top_categories.append({"category": "Остальное", "amount": int(round(other_total))})

        # Переводы и наличные
        transfers_cash = expenses_df[expenses_df['Категория'].isin(['Переводы', 'Наличные'])].copy()
        transfers_cash_by_category = transfers_cash.groupby('Категория')['Сумма операции'].sum().sort_values(
            ascending=False)

        transfers_cash_list = [
            {"category": str(cat), "amount": int(round(amount))}
            for cat, amount in transfers_cash_by_category.items()
        ]

        # Поступления по категориям
        income_by_category = income_df.groupby('Категория')['Сумма операции'].sum().sort_values(ascending=False)
        income_list = [
            {"category": str(cat), "amount": int(round(amount))}
            for cat, amount in income_by_category.head(10).items()
        ]

        # Загружаем настройки для валют и акций
        settings = load_user_settings()

        response = {
            "expenses": {
                "total_amount": int(round(expenses_df['Сумма операции'].sum())),
                "main": top_categories,
                "transfers_and_cash": transfers_cash_list
            },
            "income": {
                "total_amount": int(round(income_df['Сумма операции'].sum())),
                "main": income_list
            },
            "currency_rates": get_currency_rates(settings.get("user_currencies", [])),
            "stock_prices": get_stock_prices(settings.get("user_stocks", []))
        }

        logger.info("Страница событий успешно сгенерирована")
        return json.dumps(response, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Ошибка генерации страницы событий: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)
