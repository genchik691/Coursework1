"""Тесты для модуля views."""

import json
from datetime import datetime
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from src.views import events_page, get_greeting, main_page


def test_get_greeting():
    """Тест приветствия."""
    greeting = get_greeting()
    assert isinstance(greeting, str)
    assert len(greeting) > 0


@patch('src.views.load_transactions')
@patch('src.views.get_currency_rates')
@patch('src.views.get_stock_prices')
def test_main_page(mock_stocks, mock_currencies, mock_load):
    """Тест главной страницы."""
    # Создаем тестовые данные с правильными типами
    test_df = pd.DataFrame({
        'Дата операции': ['2024-01-15 10:00:00'],
        'Номер карты': ['1234'],
        'Сумма операции': [-1000.0],
        'Категория': ['Тест'],
        'Описание': ['Тестовая операция']
    })

    mock_load.return_value = test_df
    mock_currencies.return_value = [{"currency": "USD", "rate": 90.0}]
    mock_stocks.return_value = [{"stock": "AAPL", "price": 150.0}]

    result = main_page("2024-01-15 12:00:00")

    # Проверяем, что результат - валидный JSON
    assert isinstance(result, str)
    data = json.loads(result)

    # Проверяем наличие основных полей
    assert "greeting" in data
    assert "cards" in data
    assert "top_transactions" in data
    assert "currency_rates" in data
    assert "stock_prices" in data


@patch('src.views.load_transactions')
@patch('src.views.get_currency_rates')
@patch('src.views.get_stock_prices')
def test_events_page(mock_stocks, mock_currencies, mock_load):
    """Тест страницы событий."""
    # Создаем тестовые данные с одинаковой длиной массивов
    test_df = pd.DataFrame({
        'Дата операции': ['2024-01-15 10:00:00', '2024-01-10 10:00:00', '2024-01-05 10:00:00'],
        'Сумма операции': [-1000.0, -500.0, 5000.0],
        'Категория': ['Супермаркеты', 'Переводы', 'Пополнение'],
        'Описание': ['Тест1', 'Тест2', 'Тест3']
    })

    mock_load.return_value = test_df
    mock_currencies.return_value = [{"currency": "USD", "rate": 90.0}]
    mock_stocks.return_value = [{"stock": "AAPL", "price": 150.0}]

    result = events_page("2024-01-15 12:00:00", "M")
    assert isinstance(result, str)
    data = json.loads(result)

    assert "expenses" in data
    assert "income" in data
    assert "currency_rates" in data
    assert "stock_prices" in data


@patch('src.views.load_transactions')
def test_main_page_empty_data(mock_load):
    """Тест главной страницы с пустыми данными."""
    test_df = pd.DataFrame()
    mock_load.return_value = test_df

    result = main_page("2024-01-15 12:00:00")
    assert isinstance(result, str)
    data = json.loads(result)

    # При пустых данных может быть ошибка или пустые поля
    assert isinstance(data, dict)


@patch('src.views.load_transactions')
def test_events_page_empty_data(mock_load):
    """Тест страницы событий с пустыми данными."""
    test_df = pd.DataFrame()
    mock_load.return_value = test_df

    result = events_page("2024-01-15 12:00:00", "M")
    assert isinstance(result, str)
    data = json.loads(result)

    assert isinstance(data, dict)
