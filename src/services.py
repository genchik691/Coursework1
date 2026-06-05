"""Модуль с сервисами для анализа транзакций."""

import json
import logging
import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from src.logger_config import setup_logger
from src.utils import convert_to_serializable

logger = setup_logger(__name__, "services.log", logging.DEBUG)


def analyze_cashback_categories(
    transactions: List[Dict[str, Any]],
    year: int,
    month: int
) -> str:
    """Анализирует выгодность категорий для повышенного кешбэка."""
    logger.info(f"Анализ кешбэка за {year}-{month}")

    filtered = []
    for t in transactions:
        date_str = t.get('Дата операции', '')
        if date_str:
            try:
                t_date = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
                if t_date.year == year and t_date.month == month and t.get('Сумма операции', 0) < 0:
                    filtered.append(t)
            except (ValueError, TypeError):
                pass

    category_spending = defaultdict(float)
    for t in filtered:
        category = t.get('Категория', 'Без категории')
        amount = abs(t.get('Сумма операции', 0))
        category_spending[category] += amount

    cashback = {category: round(amount * 0.05, 2) for category, amount in category_spending.items()}
    sorted_cashback = dict(sorted(cashback.items(), key=lambda x: x[1], reverse=True)[:10])

    return json.dumps(sorted_cashback, ensure_ascii=False, indent=2, default=convert_to_serializable)


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int = 50) -> float:
    """Рассчитывает сумму для Инвесткопилки."""
    logger.info(f"Расчет Инвесткопилки за {month} с лимитом {limit}")

    total_saved = 0.0

    for t in transactions:
        date_str = t.get('Дата операции', '')
        amount = t.get('Сумма операции', 0)

        if amount >= 0:
            continue

        if date_str and date_str.startswith(month):
            amount_abs = abs(amount)
            rounded = ((amount_abs + limit - 1) // limit) * limit
            saved = rounded - amount_abs
            total_saved += saved

    return round(total_saved, 2)


def simple_search(transactions: List[Dict[str, Any]], search_string: str) -> str:
    """Поиск транзакций по строке."""
    logger.info(f"Поиск транзакций по строке: {search_string}")

    if not search_string or not search_string.strip():
        return json.dumps([], ensure_ascii=False, indent=2)

    search_lower = search_string.lower()
    results = []

    for t in transactions:
        description = str(t.get('Описание', '')).lower()
        category = str(t.get('Категория', '')).lower()

        if search_lower in description or search_lower in category:
            results.append(t)

    return json.dumps(results, ensure_ascii=False, indent=2, default=convert_to_serializable)


def search_by_phone_numbers(transactions: List[Dict[str, Any]]) -> str:
    """Поиск транзакций с номерами телефонов."""
    logger.info("Поиск транзакций с номерами телефонов")

    import re

    # Более гибкий паттерн для поиска телефонов
    # Находит:
    # +7 921 11-22-33 (3, 2, 2 цифры)
    # +7 995 555-55-55 (3, 3, 2, 2 цифры)
    # +79211223344 (11 цифр)
    # 8 921 333-44-55 (3, 3, 2, 2)
    # 8-921-123-45-67 (3, 3, 2, 2)
    patterns = [
        # Формат: +7 XXX XX-XX-XX (3,2,2 цифры)
        re.compile(r'\+7\s\d{3}\s\d{2}-\d{2}-\d{2}'),
        # Формат: +7 XXX XXX-XX-XX (3,3,2,2 цифры)
        re.compile(r'\+7\s\d{3}\s\d{3}-\d{2}-\d{2}'),
        # Формат: +7-XXX-XXX-XX-XX
        re.compile(r'\+7-\d{3}-\d{3}-\d{2}-\d{2}'),
        # Формат: +7XXXXXXXXXX
        re.compile(r'\+7\d{10}'),
        # Формат: 8 XXX XX-XX-XX (3,2,2)
        re.compile(r'8\s\d{3}\s\d{2}-\d{2}-\d{2}'),
        # Формат: 8 XXX XXX-XX-XX (3,3,2,2)
        re.compile(r'8\s\d{3}\s\d{3}-\d{2}-\d{2}'),
        # Формат: 8-XXX-XXX-XX-XX
        re.compile(r'8-\d{3}-\d{3}-\d{2}-\d{2}'),
        # Формат: 8XXXXXXXXXX
        re.compile(r'8\d{10}'),
        # Формат: +7 XXX XXX XX XX
        re.compile(r'\+7\s\d{3}\s\d{3}\s\d{2}\s\d{2}'),
        # Формат: 8 XXX XXX XX XX
        re.compile(r'8\s\d{3}\s\d{3}\s\d{2}\s\d{2}'),
    ]

    results = []
    for t in transactions:
        description = str(t.get('Описание', ''))
        found = False
        for pattern in patterns:
            if pattern.search(description):
                found = True
                break
        if found:
            results.append(t)
            logger.debug(f"Найден телефон в: {description[:50]}")

    logger.info(f"Найдено {len(results)} транзакций с телефонами")
    return json.dumps(results, ensure_ascii=False, indent=2, default=convert_to_serializable)


def search_transfers_to_individuals(transactions: List[Dict[str, Any]]) -> str:
    """Поиск переводов физическим лицам."""
    logger.info("Поиск переводов физическим лицам")

    name_pattern = re.compile(r'[А-Я][а-я]+\s+[А-Я]\.')

    results = [
        t for t in transactions
        if t.get('Категория') == 'Переводы' and name_pattern.search(str(t.get('Описание', '')))
    ]

    logger.info(f"Найдено {len(results)} переводов физлицам")
    return json.dumps(results, ensure_ascii=False, indent=2, default=convert_to_serializable)
