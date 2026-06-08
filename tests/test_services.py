"""Тесты для модуля services."""

import json
from datetime import datetime
from unittest.mock import patch

import pytest

from src.services import (
    analyze_cashback_categories,
    investment_bank,
    search_by_phone_numbers,
    search_transfers_to_individuals,
    simple_search,
)


class TestAnalyzeCashbackCategories:
    """Тесты для анализа кешбэка."""

    @pytest.fixture
    def sample_transactions(self):
        """Фикстура с тестовыми транзакциями."""
        return [
            {'Дата операции': '2024-01-15 10:00:00', 'Сумма операции': -1000, 'Категория': 'Супермаркеты'},
            {'Дата операции': '2024-01-20 10:00:00', 'Сумма операции': -500, 'Категория': 'Супермаркеты'},
            {'Дата операции': '2024-01-10 10:00:00', 'Сумма операции': -200, 'Категория': 'Кафе'},
            {'Дата операции': '2024-02-01 10:00:00', 'Сумма операции': -300, 'Категория': 'Супермаркеты'},
        ]

    def test_analyze_cashback_categories(self, sample_transactions):
        """Тест анализа кешбэка."""
        result = analyze_cashback_categories(sample_transactions, 2024, 1)
        data = json.loads(result)

        assert "Супермаркеты" in data
        assert "Кафе" in data
        # Кешбэк 5%: 1500 * 0.05 = 75
        assert data["Супермаркеты"] == 75.0
        # Кешбэк 5%: 200 * 0.05 = 10
        assert data["Кафе"] == 10.0

    def test_analyze_cashback_no_transactions(self):
        """Тест при отсутствии транзакций."""
        result = analyze_cashback_categories([], 2024, 1)
        data = json.loads(result)
        assert data == {}


class TestInvestmentBank:
    """Тесты для инвесткопилки."""

    @pytest.fixture
    def sample_transactions(self):
        """Фикстура с тестовыми транзакциями."""
        return [
            {'Дата операции': '2024-01-15', 'Сумма операции': -1712},
            {'Дата операции': '2024-01-20', 'Сумма операции': -100},
            {'Дата операции': '2024-02-01', 'Сумма операции': -500},
            {'Дата операции': '2024-01-10', 'Сумма операции': 1000},  # Поступление
        ]

    def test_investment_bank_limit_50(self, sample_transactions):
        """Тест с лимитом 50."""
        result = investment_bank("2024-01", sample_transactions, 50)
        # 1712 округляется до 1750, разница 38
        # 100 округляется до 100, разница 0
        assert result == 38.0

    def test_investment_bank_limit_100(self, sample_transactions):
        """Тест с лимитом 100."""
        result = investment_bank("2024-01", sample_transactions, 100)
        # 1712 округляется до 1800, разница 88
        # 100 округляется до 100, разница 0
        assert result == 88.0

    def test_investment_bank_empty_month(self, sample_transactions):
        """Тест с месяцем без транзакций."""
        result = investment_bank("2024-03", sample_transactions, 50)
        assert result == 0.0


class TestSimpleSearch:
    """Тесты для поиска транзакций."""

    @pytest.fixture
    def sample_transactions(self):
        """Фикстура с тестовыми транзакциями."""
        return [
            {'Описание': 'Перевод организации', 'Категория': 'Переводы'},
            {'Описание': 'Покупка в магазине', 'Категория': 'Супермаркеты'},
            {'Описание': 'Оплата услуг', 'Категория': 'Услуги'},
            {'Описание': 'ПЕРЕВОД другу', 'Категория': 'Переводы'},
        ]

    def test_simple_search_case_insensitive(self, sample_transactions):
        """Тест регистронезависимого поиска."""
        result = simple_search(sample_transactions, "перевод")
        data = json.loads(result)
        assert len(data) == 2

    def test_simple_search_not_found(self, sample_transactions):
        """Тест при отсутствии результатов."""
        result = simple_search(sample_transactions, "несуществующее")
        data = json.loads(result)
        assert len(data) == 0

    def test_simple_search_empty_string(self, sample_transactions):
        """Тест с пустой строкой."""
        result = simple_search(sample_transactions, "")
        data = json.loads(result)
        assert len(data) == 0

    def test_simple_search_whitespace_string(self, sample_transactions):
        """Тест со строкой из пробелов."""
        result = simple_search(sample_transactions, "   ")
        data = json.loads(result)
        assert len(data) == 0


class TestSearchByPhoneNumbers:
    """Тесты для поиска по телефонным номерам."""

    @pytest.fixture
    def sample_transactions(self):
        """Фикстура с тестовыми транзакциями."""
        return [
            {'Описание': 'Я МТС +7 921 11-22-33'},
            {'Описание': 'Тинькофф Мобайл +7 995 555-55-55'},
            {'Описание': 'Простой перевод без телефона'},
            {'Описание': '8 921 333-44-55'},
            {'Описание': 'Номер +79211223344'},
            {'Описание': '8-921-123-45-67'},
        ]

    def test_search_by_phone_numbers(self, sample_transactions):
        """Тест поиска телефонных номеров."""
        result = search_by_phone_numbers(sample_transactions)
        data = json.loads(result)
        # Должно найти 5 из 6 транзакций (все кроме "Простой перевод без телефона")
        assert len(data) == 5

    def test_search_by_phone_numbers_no_results(self):
        """Тест при отсутствии номеров."""
        transactions = [{'Описание': 'Обычная операция'}]
        result = search_by_phone_numbers(transactions)
        data = json.loads(result)
        assert len(data) == 0


class TestSearchTransfersToIndividuals:
    """Тесты для поиска переводов физлицам."""

    @pytest.fixture
    def sample_transactions(self):
        """Фикстура с тестовыми транзакциями."""
        return [
            {'Категория': 'Переводы', 'Описание': 'Валерий А.'},
            {'Категория': 'Переводы', 'Описание': 'Сергей З.'},
            {'Категория': 'Переводы', 'Описание': 'Перевод организации'},
            {'Категория': 'Супермаркеты', 'Описание': 'Валерий А.'},
            {'Категория': 'Переводы', 'Описание': 'Анна К.'},
        ]

    def test_search_transfers_to_individuals(self, sample_transactions):
        """Тест поиска переводов физлицам."""
        result = search_transfers_to_individuals(sample_transactions)
        data = json.loads(result)
        assert len(data) == 3
        assert data[0]['Описание'] == 'Валерий А.'
        assert data[1]['Описание'] == 'Сергей З.'
        assert data[2]['Описание'] == 'Анна К.'
