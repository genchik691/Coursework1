"""Основной модуль приложения."""

from datetime import datetime

from src.reports import spending_by_category, spending_by_weekday, spending_by_workday
from src.services import (
    analyze_cashback_categories,
    investment_bank,
    search_by_phone_numbers,
    search_transfers_to_individuals,
    simple_search,
)
from src.utils import get_greeting, load_transactions
from src.views import events_page, main_page


def main():
    """Основная функция приложения."""
    print("=" * 60)
    print(get_greeting() + "! Добро пожаловать в систему анализа транзакций")
    print("=" * 60)

    df = load_transactions()
    transactions_list = df.to_dict('records') if not df.empty else []

    current_date = datetime.now()
    date_str = current_date.strftime("%Y-%m-%d %H:%M:%S")

    while True:
        print("\nВыберите действие:")
        print("1. Главная страница (JSON)")
        print("2. Страница событий (JSON)")
        print("3. Анализ кешбэка по категориям")
        print("4. Инвесткопилка")
        print("5. Поиск по описанию")
        print("6. Поиск по номерам телефонов")
        print("7. Поиск переводов физлицам")
        print("8. Отчет по категории")
        print("9. Отчет по дням недели")
        print("10. Отчет по рабочим/выходным дням")
        print("0. Выход")

        choice = input("\nВаш выбор: ").strip()

        if choice == "1":
            result = main_page(date_str)
            print("\n" + result[:1000] + "..." if len(result) > 1000 else result)

        elif choice == "2":
            result = events_page(date_str, "M")
            print("\n" + result[:1000] + "..." if len(result) > 1000 else result)

        elif choice == "3":
            year = int(input("Введите год: "))
            month = int(input("Введите месяц (1-12): "))
            result = analyze_cashback_categories(transactions_list, year, month)
            print("\n" + result)

        elif choice == "4":
            month = input("Введите месяц (YYYY-MM): ")
            limit = int(input("Введите лимит округления (10, 50, 100): "))
            result = investment_bank(month, transactions_list, limit)
            print(f"\nСумма в Инвесткопилке: {result} руб.")

        elif choice == "5":
            search_str = input("Введите строку для поиска: ")
            result = simple_search(transactions_list, search_str)
            print("\n" + result[:1000] + "..." if len(result) > 1000 else result)

        elif choice == "6":
            result = search_by_phone_numbers(transactions_list)
            print("\n" + result[:1000] + "..." if len(result) > 1000 else result)

        elif choice == "7":
            result = search_transfers_to_individuals(transactions_list)
            print("\n" + result[:1000] + "..." if len(result) > 1000 else result)

        elif choice == "8":
            category = input("Введите категорию: ")
            date_input = input("Введите дату (YYYY-MM-DD) или Enter для текущей: ")
            result = spending_by_category(df, category, date_input if date_input else None)
            print(f"\nНайдено {len(result)} транзакций")
            print(result.to_string())

        elif choice == "9":
            date_input = input("Введите дату (YYYY-MM-DD) или Enter для текущей: ")
            result = spending_by_weekday(df, date_input if date_input else None)
            print("\n" + result.to_string())

        elif choice == "10":
            date_input = input("Введите дату (YYYY-MM-DD) или Enter для текущей: ")
            result = spending_by_workday(df, date_input if date_input else None)
            print("\n" + result.to_string())

        elif choice == "0":
            print("До свидания!")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()
