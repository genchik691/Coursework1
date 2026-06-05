"""Модуль с отчетами по транзакциям."""

import functools
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd

from src.logger_config import setup_logger

logger = setup_logger(__name__, "reports.log", logging.DEBUG)


def report_decorator(filename: Optional[str] = None) -> Callable:
    """Декоратор для сохранения отчетов в файл."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            result = func(*args, **kwargs)

            output_filename = filename or f"report_{func.__name__}.json"
            report_dir = Path("reports")
            report_dir.mkdir(exist_ok=True)

            filepath = report_dir / output_filename

            if isinstance(result, pd.DataFrame):
                result.to_json(filepath, orient='records', force_ascii=False, indent=2, default_handler=str)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"Отчет сохранен в {filepath}")
            return result

        return wrapper
    return decorator


@report_decorator()
def spending_by_category(
    transactions: pd.DataFrame,
    category: str,
    date: Optional[str] = None
) -> pd.DataFrame:
    """Возвращает траты по заданной категории за последние 3 месяца."""
    logger.info(f"Отчет по категории: {category}, дата: {date}")

    if transactions.empty:
        return pd.DataFrame()

    end_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()
    start_date = end_date - timedelta(days=90)

    transactions['Дата операции'] = pd.to_datetime(transactions['Дата операции'], errors='coerce')

    mask = ((transactions['Дата операции'] >= start_date)
            & (transactions['Дата операции'] <= end_date)
            & (transactions['Категория'] == category)
            & (transactions['Сумма операции'] < 0))

    result = transactions[mask].copy()
    result['Сумма операции'] = abs(result['Сумма операции'])

    return result


@report_decorator()
def spending_by_weekday(
    transactions: pd.DataFrame,
    date: Optional[str] = None
) -> pd.DataFrame:
    """Возвращает средние траты по дням недели."""
    logger.info(f"Отчет по дням недели, дата: {date}")

    if transactions.empty:
        return pd.DataFrame()

    end_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()
    start_date = end_date - timedelta(days=90)

    transactions['Дата операции'] = pd.to_datetime(transactions['Дата операции'], errors='coerce')

    mask = ((transactions['Дата операции'] >= start_date)
            & (transactions['Дата операции'] <= end_date)
            & (transactions['Сумма операции'] < 0))

    filtered = transactions[mask].copy()
    filtered['Сумма операции'] = abs(filtered['Сумма операции'])
    filtered['День недели'] = filtered['Дата операции'].dt.day_name(locale='ru_RU.UTF-8')

    result = filtered.groupby('День недели')['Сумма операции'].mean().reset_index()
    result.columns = ['day_of_week', 'average_spending']
    result['average_spending'] = result['average_spending'].round(2)

    weekday_order = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    result['order'] = result['day_of_week'].apply(lambda x: weekday_order.index(x) if x in weekday_order else 999)
    result = result.sort_values('order').drop('order', axis=1)

    return result


def spending_by_workday(
    transactions: pd.DataFrame,
    date: Optional[str] = None
) -> pd.DataFrame:
    """Возвращает средние траты в рабочие и выходные дни."""
    logger.info(f"Отчет по рабочим/выходным дням, дата: {date}")

    if transactions.empty:
        return pd.DataFrame()

    end_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()
    start_date = end_date - timedelta(days=90)

    transactions['Дата операции'] = pd.to_datetime(transactions['Дата операции'], errors='coerce')

    mask = ((transactions['Дата операции'] >= start_date)
            & (transactions['Дата операции'] <= end_date)
            & (transactions['Сумма операции'] < 0))

    filtered = transactions[mask].copy()
    filtered['Сумма операции'] = abs(filtered['Сумма операции'])
    filtered['День недели'] = filtered['Дата операции'].dt.dayofweek
    filtered['Тип дня'] = filtered['День недели'].apply(lambda x: 'Рабочий день' if x < 5 else 'Выходной день')

    result = filtered.groupby('Тип дня')['Сумма операции'].mean().reset_index()
    result.columns = ['day_type', 'average_spending']
    result['average_spending'] = result['average_spending'].round(2)

    return result
