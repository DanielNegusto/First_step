from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.views import (get_card_data_from_excel, get_card_from_main, get_currency_rates, get_expenses, get_greeting,
                       get_income, get_stock_prices, get_top_transactions, load_user_settings, parse_date_range)


def test_load_user_settings() -> None:
    with pytest.raises(FileNotFoundError):
        load_user_settings("not_found.xlsx")


def test_get_greeting() -> None:
    assert get_greeting(datetime(2022, 1, 1, 7, 0, 0)) == "Доброе утро"
    assert get_greeting(datetime(2022, 1, 1, 11, 0, 0)) == "Доброе утро"
    assert get_greeting(datetime(2022, 1, 1, 17, 0, 0)) == "Добрый день"
    assert get_greeting(datetime(2022, 1, 1, 23, 59, 59)) == "Добрый вечер"


def test_parse_date_range() -> None:
    assert parse_date_range("2022-01-01 00:00:00", "W") == (datetime(2021, 12, 27), datetime(2022, 1, 1))
    assert parse_date_range("2022-01-01 00:00:00", "M") == (datetime(2022, 1, 1), datetime(2022, 1, 1))
    assert parse_date_range("2022-01-01 00:00:00", "Y") == (datetime(2022, 1, 1), datetime(2022, 1, 1))
    assert parse_date_range("2022-01-01 00:00:00", "ALL") == (datetime(1, 1, 1, 0, 0), datetime(2022, 1, 1))
    assert parse_date_range("2022-01-01 00:00:00", "D") == (datetime(2022, 1, 1), datetime(2022, 1, 1))


def test_get_card_data_from_excel() -> None:
    with pytest.raises(FileNotFoundError):
        get_card_data_from_excel("not_found.xlsx")


def test_get_card_from_main() -> None:
    df = pd.DataFrame({"Номер карты": [5555555555555555], "Сумма операции": [100]})
    assert get_card_from_main(df) == [{"last_digits": "5555", "total_spent": 100, "cashback": 1}]


def test_get_expenses() -> None:
    df = pd.DataFrame({"Сумма операции": [-100, -50, 50, 100], "Категория": ["Food", "Transfers", "Cash", "Other"]})
    assert get_expenses(df) == {
        "total_amount": 150,
        "main": [{"category": "Food", "amount": 100}, {"category": "Transfers", "amount": 50}],
        "transfers_and_cash": [],
    }


def test_get_income() -> None:
    df = pd.DataFrame({"Сумма операции": [-100, -50, 50, 100], "Категория": ["Food", "Transfers", "Cash", "Other"]})
    assert get_income(df) == {
        "total_amount": 150,
        "main": [{"category": "Other", "amount": 100}, {"category": "Cash", "amount": 50}],
    }


def test_get_top_transactions_all(temp_excel_file: Any) -> None:
    # Тест без указания дат (все транзакции)
    result = get_top_transactions(filepath=str(temp_excel_file))

    assert len(result) == 5
    assert result[0]["amount"] == 9000  # Самая большая сумма
    assert result[1]["amount"] == 8000  # Вторая по величине сумма
    assert result[4]["amount"] == 2000  # Пятая по величине сумма


def test_get_top_transactions_with_date_range(temp_excel_file: Any) -> None:
    # Тест с указанием диапазона дат
    start_date = datetime(2023, 8, 2)
    end_date = datetime(2023, 8, 5)
    result = get_top_transactions(filepath=str(temp_excel_file), start_date=start_date, end_date=end_date)

    assert len(result) == 3
    assert result[0]["amount"] == 8000  # Самая большая сумма в указанном диапазоне
    assert result[1]["amount"] == 7000
    assert result[2]["amount"] == 2000


def test_get_top_transactions_no_transactions_in_range(temp_excel_file: Any) -> None:
    # Тест с диапазоном дат, в который не попадает ни одна транзакция
    start_date = datetime(2023, 7, 1)
    end_date = datetime(2023, 7, 31)
    result = get_top_transactions(filepath=str(temp_excel_file), start_date=start_date, end_date=end_date)

    assert len(result) == 0  # Нет транзакций в указанном диапазоне


@patch("src.views.API_KEY", "fake_api_key")  # Подмена API_KEY на фиктивный
def test_get_currency_rates() -> None:
    # Определяем данные, которые будет возвращать подмененный запрос
    mock_response_data = {"rates": {"RUB": 74.0}}

    # Создаем mock-объект для ответа
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data

    # Используем patch для подмены requests.get
    with patch("src.views.requests.get", return_value=mock_response) as mock_get:
        # Вызов тестируемой функции
        currencies = ["USD", "EUR"]
        result = get_currency_rates(currencies)

        # Проверка результатов
        expected_result = [{"currency": "USD", "rate": 74.0}, {"currency": "EUR", "rate": 74.0}]
        assert result == expected_result

        # Проверка, что requests.get был вызван дважды (по одному разу на каждую валюту)
        assert mock_get.call_count == 2

        # Проверка аргументов вызова requests.get
        mock_get.assert_any_call(
            "https://api.apilayer.com/fixer/latest", headers={"apikey": "fake_api_key"}, params={"base": "USD"}
        )
        mock_get.assert_any_call(
            "https://api.apilayer.com/fixer/latest", headers={"apikey": "fake_api_key"}, params={"base": "EUR"}
        )


@patch("src.views.Alpha_KEY", "fake_alpha_key")  # Подмена Alpha_KEY на фиктивный
def test_get_stock_prices() -> None:
    # Определяем фиктивные данные для ответа
    mock_response_data = {
        "Meta Data": {"3. Last Refreshed": "2024-08-08"},
        "Time Series (Daily)": {"2024-08-08": {"4. close": "150.00"}},
    }

    # Создаем mock-объект для ответа
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data

    # Используем patch для подмены requests.get
    with patch("src.views.requests.get", return_value=mock_response) as mock_get:
        # Вызов тестируемой функции
        stocks = ["AAPL", "GOOGL"]
        result = get_stock_prices(stocks)

        # Проверка результатов
        expected_result = [{"stock": "AAPL", "price": 150.00}, {"stock": "GOOGL", "price": 150.00}]
        assert result == expected_result

        # Проверка, что requests.get был вызван дважды (по одному разу для каждой акции)
        assert mock_get.call_count == 2

        # Проверка аргументов вызова requests.get
        mock_get.assert_any_call(
            "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=AAPL&apikey=fake_alpha_key"
        )
        mock_get.assert_any_call(
            "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=GOOGL&apikey=fake_alpha_key"
        )
