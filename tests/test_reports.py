"""Тесты для модуля reports."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.reports import report_decorator, spending_by_category, spending_by_weekday, spending_by_workday


class TestReportDecorator:
    """Тесты для декоратора отчетов."""

    @patch('src.reports.json.dump')
    def test_report_decorator_saves_file(self, mock_json_dump):
        """Тест сохранения отчета в файл."""

        @report_decorator("test_report.json")
        def test_func():
            return {"test": "data"}

        result = test_func()
        assert result == {"test": "data"}

        # Проверяем, что файл был создан (через mock)
        reports_dir = Path("reports")
        assert reports_dir.exists()


class TestSpendingByCategory:
    """Тесты для отчета по категории."""

    @pytest.fixture
    def sample_df(self):
        """Фикстура с тестовыми данными."""
        today = datetime.now()
        return pd.DataFrame({
            'Дата операции': [
                (today - timedelta(days=30)).strftime("%Y-%m-%d"),
                (today - timedelta(days=60)).strftime("%Y-%m-%d"),
                (today - timedelta(days=100)).strftime("%Y-%m-%d"),
                (today - timedelta(days=10)).strftime("%Y-%m-%d")
            ],
            'Сумма операции': [-1000, -500, -200, 1000],
            'Категория': ['Супермаркеты', 'Супермаркеты', 'Супермаркеты', 'Доход']
        })

    def test_spending_by_category(self, sample_df):
        """Тест отчета по категории."""
        result = spending_by_category(sample_df, "Супермаркеты", datetime.now().strftime("%Y-%m-%d"))
        assert len(result) >= 2  # Транзакции за последние 90 дней
        assert all(result['Категория'] == 'Супермаркеты')
        assert all(result['Сумма операции'] > 0)

    def test_spending_by_category_no_transactions(self):
        """Тест при отсутствии транзакций."""
        empty_df = pd.DataFrame()
        result = spending_by_category(empty_df, "Категория")
        assert result.empty


class TestSpendingByWeekday:
    """Тесты для отчета по дням недели."""

    @pytest.fixture
    def sample_df(self):
        """Фикстура с тестовыми данными."""
        today = datetime.now()
        return pd.DataFrame({
            'Дата операции': [
                (today - timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range(30)
            ],
            'Сумма операции': [-100] * 30,
            'Категория': ['Тест'] * 30
        })

    def test_spending_by_weekday(self, sample_df):
        """Тест отчета по дням недели."""
        result = spending_by_weekday(sample_df, datetime.now().strftime("%Y-%m-%d"))
        assert len(result) == 7  # 7 дней недели
        assert 'day_of_week' in result.columns
        assert 'average_spending' in result.columns
        assert all(result['average_spending'] >= 0)

    def test_spending_by_weekday_empty_data(self):
        """Тест с пустыми данными."""
        empty_df = pd.DataFrame()
        result = spending_by_weekday(empty_df)
        assert result.empty


class TestSpendingByWorkday:
    """Тесты для отчета по рабочим/выходным дням."""

    @pytest.fixture
    def sample_df(self):
        """Фикстура с тестовыми данными."""
        today = datetime.now()
        return pd.DataFrame({
            'Дата операции': [
                (today - timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range(60)
            ],
            'Сумма операции': [-100] * 60,
            'Категория': ['Тест'] * 60
        })

    def test_spending_by_workday(self, sample_df):
        """Тест отчета по рабочим/выходным дням."""
        result = spending_by_workday(sample_df, datetime.now().strftime("%Y-%m-%d"))
        assert len(result) == 2
        assert 'day_type' in result.columns
        assert 'average_spending' in result.columns
        assert 'Рабочий день' in result['day_type'].values
        assert 'Выходной день' in result['day_type'].values

    def test_spending_by_workday_empty_data(self):
        """Тест с пустыми данными."""
        empty_df = pd.DataFrame()
        result = spending_by_workday(empty_df)
        assert result.empty
