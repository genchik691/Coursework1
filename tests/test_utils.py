"""Тесты для модуля utils."""

from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from src.utils import filter_by_date_range, format_date, generate_test_data, get_greeting, load_transactions


class TestLoadTransactions:
    """Тесты для загрузки транзакций."""

    def test_generate_test_data_returns_dataframe(self):
        """Тест генерации тестовых данных."""
        df = generate_test_data()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_generate_test_data_has_required_columns(self):
        """Тест наличия необходимых колонок."""
        df = generate_test_data()
        required_columns = ['Дата операции', 'Сумма операции', 'Категория', 'Описание']
        for col in required_columns:
            assert col in df.columns

    @patch('src.utils.Path.exists')
    @patch('src.utils.generate_test_data')
    def test_load_transactions_file_not_found(self, mock_generate, mock_exists):
        """Тест при отсутствии файла."""
        mock_exists.return_value = False
        mock_generate.return_value = pd.DataFrame({'test': [1, 2]})

        result = load_transactions("nonexistent.xlsx")
        assert len(result) == 2
        mock_generate.assert_called_once()


class TestFilterByDateRange:
    """Тесты для фильтрации по дате."""

    @pytest.fixture
    def sample_df(self):
        """Фикстура с тестовыми данными."""
        return pd.DataFrame({
            'Дата операции': [
                '2024-01-01 10:00:00',
                '2024-01-15 10:00:00',
                '2024-02-01 10:00:00',
                '2024-03-01 10:00:00'
            ],
            'Сумма операции': [-100, -200, -300, -400]
        })

    def test_filter_by_month(self, sample_df):
        """Тест фильтрации по месяцу."""
        end_date = datetime(2024, 1, 20)
        result = filter_by_date_range(sample_df, end_date, "month")
        assert len(result) == 2
        assert all(result['Дата операции'].dt.month == 1)

    def test_filter_empty_dataframe(self):
        """Тест с пустым DataFrame."""
        empty_df = pd.DataFrame()
        end_date = datetime(2024, 1, 15)
        result = filter_by_date_range(empty_df, end_date)
        assert result.empty

    def test_filter_all_period(self, sample_df):
        """Тест за все время."""
        end_date = datetime(2024, 3, 15)
        result = filter_by_date_range(sample_df, end_date, "all")
        assert len(result) == 4


class TestGetGreeting:
    """Тесты для приветствия."""

    def test_get_greeting_returns_string(self):
        """Тест возврата строки."""
        greeting = get_greeting()
        assert isinstance(greeting, str)
        assert len(greeting) > 0


class TestFormatDate:
    """Тесты для форматирования даты."""

    def test_format_date_with_datetime(self):
        """Тест форматирования datetime объекта."""
        date_obj = datetime(2024, 1, 15)
        result = format_date(date_obj)
        assert result == "15.01.2024"

    def test_format_date_with_string(self):
        """Тест форматирования строки даты."""
        date_str = "2024-01-15 10:30:00"
        result = format_date(date_str)
        assert result == "15.01.2024"

    def test_format_date_with_nan(self):
        """Тест с NaN значением."""
        result = format_date(pd.NA)
        assert result == ""
