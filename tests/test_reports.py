from datetime import datetime

import pandas as pd
import pytest

from src.reports import category_spending, save_to_file, spending_by_category


def test_save_to_file():
    # Создаем тестовую функцию-отчет
    @save_to_file()
    def test_func():
        return "Test result"

    # Вызываем функцию-отчет
    test_func()
    # Проверяем, что результат был сохранен в файл
    with open("reports.log", "r") as file:
        assert file.read() == "Test result"


@pytest.fixture
def transactions():
    data = {
        "Категория": ["Еда", "Еда", "Транспорт", "Транспорт", "Еда"],
        "Дата операции": [
            datetime(2022, 1, 1),
            datetime(2022, 1, 15),
            datetime(2022, 2, 1),
            datetime(2022, 3, 1),
            datetime(2022, 4, 1),
        ],
        "Сумма операции": [-100, -200, -50, -150, -250],
    }
    return pd.DataFrame(data)


def test_spending_by_category_with_date(transactions):
    # Тестирование функции с указанием даты
    result = spending_by_category(transactions, "Еда", "2022-02-01")
    assert len(result) == 1  # Должна быть 1 строка, поскольку операция была в январе
    assert result["Сумма операции"].sum() == 300  # Сумма операций должна быть 300


def test_spending_by_category_with_invalid_date():
    # Тестирование функции с неверной датой
    transactions = pd.DataFrame(columns=["Категория", "Дата операции", "Сумма операции"])
    with pytest.raises(ValueError):
        spending_by_category(transactions, "Еда", "invalid_date")


def test_spending_by_category_with_no_transactions_in_last_90_days():
    # Тестирование функции, когда нет транзакций за последние 90 дней
    transactions = pd.DataFrame(
        {"Категория": ["Еда"], "Дата операции": [datetime(2022, 1, 1)], "Сумма операции": [-100]}
    )
    result = spending_by_category(transactions, "Еда", "2023-04-01")
    assert len(result) == 0  # Должно быть 0 строк


@pytest.fixture
def df():
    data = {"Категория": ["Еда", "Транспорт", "Еда", "Товары", None], "Расходы": [100, 200, 50, 150, 0]}
    return pd.DataFrame(data)


def test_category_spending_found(df, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda x: "еда")
    result = category_spending(df)
    assert result == "Еда"


def test_category_spending_not_found(df, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda x: "не существующая категория")
    result = category_spending(df)
    assert result is None


def test_category_spending_empty_input(df, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda x: "")
    result = category_spending(df)
    assert result is None


def test_category_spending_null_category(df, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda x: "none")
    result = category_spending(df)
    assert result is None
