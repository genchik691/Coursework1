"""Утилиты для работы с данными транзакций."""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from dotenv import load_dotenv

from src.logger_config import setup_logger

load_dotenv()
logger = setup_logger(__name__, "utils.log", logging.DEBUG)


def convert_to_serializable(obj):
    """Конвертирует numpy/pandas типы в Python типы для JSON сериализации."""
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return str(obj)
    if pd.isna(obj):
        return None
    return obj


def load_transactions(file_path: str = "data/operations.xlsx") -> pd.DataFrame:
    """Загружает транзакции из Excel файла."""
    logger.debug(f"Загрузка транзакций из {file_path}")

    try:
        if not Path(file_path).exists():
            logger.warning(f"Файл {file_path} не найден, создаем тестовые данные")
            return generate_test_data()

        df = pd.read_excel(file_path, engine='openpyxl')
        logger.info(f"Загружено {len(df)} транзакций")
        return df

    except Exception as e:
        logger.error(f"Ошибка загрузки файла: {e}")
        return generate_test_data()


def generate_test_data() -> pd.DataFrame:
    """Генерирует тестовые данные для демонстрации."""
    data = []
    categories = [
        "Супермаркеты", "Кафе и рестораны", "Транспорт", "Аптеки",
        "Одежда и обувь", "Электроника", "Развлечения", "Переводы",
        "Наличные", "ЖКХ", "Связь", "Образование", "Здоровье"
    ]

    cards = ["1234", "5678", "9012", "3456"]

    for i in range(200):
        date = datetime.now() - timedelta(days=i)
        amount = -abs((i % 10 + 1) * 100) if i % 3 != 0 else abs((i % 5 + 1) * 500)

        data.append({
            "Дата операции": date.strftime("%Y-%m-%d %H:%M:%S"),
            "Дата платежа": date.strftime("%Y-%m-%d %H:%M:%S"),
            "Номер карты": cards[i % len(cards)],
            "Статус": "OK" if i % 10 != 0 else "FAILED",
            "Сумма операции": amount,
            "Валюта операции": "RUB",
            "Сумма платежа": amount,
            "Валюта платежа": "RUB",
            "Кешбэк": round(abs(amount) * 0.05, 2) if amount < 0 else 0,
            "Категория": categories[i % len(categories)],
            "MCC": 5000 + (i % 100),
            "Описание": f"Тестовая операция {i+1}",
            "Бонусы (включая кешбэк)": round(abs(amount) * 0.05, 2) if amount < 0 else 0,
            "Округление на 'Инвесткопилку'": 0,
            "Сумма операции с округлением": amount,
        })

    df = pd.DataFrame(data)
    logger.info(f"Сгенерировано {len(df)} тестовых транзакций")
    return df


def filter_by_date_range(
    df: pd.DataFrame,
    end_date: datetime,
    period: str = "month"
) -> pd.DataFrame:
    """Фильтрует транзакции по диапазону дат."""
    if df.empty or 'Дата операции' not in df.columns:
        return pd.DataFrame()

    df['Дата операции'] = pd.to_datetime(df['Дата операции'], errors='coerce')

    if period == "month":
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0)
    elif period == "week":
        start_date = end_date - timedelta(days=end_date.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0)
    elif period == "year":
        start_date = end_date.replace(month=1, day=1, hour=0, minute=0, second=0)
    else:  # all
        start_date = datetime(2000, 1, 1)

    mask = (df['Дата операции'] >= start_date) & (df['Дата операции'] <= end_date)
    result = df[mask].copy()

    logger.debug(f"Отфильтровано {len(result)} транзакций")
    return result


def get_greeting() -> str:
    """Возвращает приветствие в зависимости от времени суток."""
    hour = datetime.now().hour

    if 6 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 18:
        return "Добрый день"
    if 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def format_date(date_value: Any) -> str:
    """Форматирует дату в формат DD.MM.YYYY."""
    if pd.isna(date_value):
        return ""

    if isinstance(date_value, str):
        try:
            date_obj = datetime.strptime(date_value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                date_obj = datetime.strptime(date_value, "%d.%m.%Y")
            except ValueError:
                return ""
    else:
        date_obj = date_value

    return date_obj.strftime("%d.%m.%Y") if date_obj else ""
