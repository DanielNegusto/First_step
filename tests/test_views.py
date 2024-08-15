import json
from datetime import datetime
from typing import Any, Dict, List, Tuple
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from tqdm import tqdm

from src.views import (get_card_data_from_excel, get_card_from_main, get_common_data, get_currency_rates, get_expenses,
                       get_greeting, get_income, get_rates_and_prices, get_stock_prices, get_top_transactions,
                       get_user_settings_data, load_user_settings, main_func, parse_date_range, process_events_data,
                       process_home_data)


def test_get_common_data() -> None:
    start_date = datetime(2024, 8, 1)
    end_date = datetime(2024, 8, 10)

    mock_df: MagicMock = MagicMock()

    with patch("src.views.get_card_data_from_excel", return_value=mock_df) as mock_get_card_data:
        mock_progress_bar: MagicMock = MagicMock(spec=tqdm)

        # Вызов функции с моками
        result = get_common_data(start_date, end_date, mock_progress_bar)

        # Проверка вызова get_card_data_from_excel с правильными аргументами
        mock_get_card_data.assert_called_once_with("data/operations.xls", start_date=start_date, end_date=end_date)

        # Проверка, что прогресс-бар был обновлен на 20
        mock_progress_bar.update.assert_called_once_with(20)

        # Проверка, что функция вернула ожидаемый DataFrame (или его мок)
        assert result == mock_df


def test_load_user_settings() -> None:
    with pytest.raises(FileNotFoundError):
        load_user_settings("not_found.xlsx")


RatesAndPricesParams = Tuple[
    List[str],  # Список валют
    List[str],  # Список акций
    Dict[str, Any],  # Ожидаемые курсы валют
    Dict[str, Any],  # Ожидаемые цены на акции
    List[int],  # Обновления прогресс-бара
]


def test_get_rates_and_prices(rates_and_prices_params: RatesAndPricesParams) -> None:
    currencies, stocks, expected_currency_rates, expected_stock_prices, progress_updates = rates_and_prices_params
    with patch("src.views.get_currency_rates", return_value=expected_currency_rates) as mock_get_currency_rates, patch(
        "src.views.get_stock_prices", return_value=expected_stock_prices
    ) as mock_get_stock_prices:
        mock_progress_bar = MagicMock()

        currency_rates, stock_prices = get_rates_and_prices(currencies, stocks, mock_progress_bar)

        mock_get_currency_rates.assert_called_once_with(currencies)
        mock_get_stock_prices.assert_called_once_with(stocks)
        assert currency_rates == expected_currency_rates
        assert stock_prices == expected_stock_prices

        assert mock_progress_bar.update.call_count == len(progress_updates)
        for update in progress_updates:
            mock_progress_bar.update.assert_any_call(update)


def test_get_user_settings_data() -> None:
    mock_user_settings = {"user_currencies": ["USD", "EUR", "JPY"], "user_stocks": ["AAPL", "GOOGL", "TSLA"]}

    expected_currencies = ["USD", "EUR", "JPY"]
    expected_stocks = ["AAPL", "GOOGL", "TSLA"]

    # Мокаем функцию load_user_settings
    with patch("src.views.load_user_settings", return_value=mock_user_settings) as mock_load_user_settings:
        mock_progress_bar: MagicMock = MagicMock(spec=tqdm)

        # Вызов тестируемой функции
        currencies, stocks = get_user_settings_data(mock_progress_bar)

        # Проверка, что load_user_settings был вызван с правильным файлом
        mock_load_user_settings.assert_called_once_with("user_settings.json")

        # Проверка, что прогресс-бар был обновлен на 10
        mock_progress_bar.update.assert_called_once_with(10)

        # Проверка, что функция вернула правильные списки валют и акций
        assert currencies == expected_currencies
        assert stocks == expected_stocks


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


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "amount": [100, 200, 300],
            "type": ["income", "expense", "income"],
        }
    )


def test_main_func_home(sample_df):
    with patch("src.views.get_greeting", return_value="Hello"), patch(
        "src.views.process_home_data"
    ) as mock_process_home_data:
        mock_process_home_data.return_value = {
            "cards": ["Card1", "Card2"],
            "top_transactions": ["Transaction1", "Transaction2"],
            "currency_rates": {"USD": 1.0},
            "stock_prices": {"AAPL": 150.0},
        }

        result = main_func("home", "2023-01-01 00:00:00", sample_df)

        assert isinstance(result, str)
        data = json.loads(result)
        assert data["greeting"] == "Hello"
        assert "cards" in data
        assert "top_transactions" in data
        assert "currency_rates" in data
        assert "stock_prices" in data


def test_main_func_events(sample_df):
    with patch("src.views.get_greeting", return_value="Hello"), patch(
        "src.views.get_common_data", return_value=sample_df
    ), patch("src.views.process_events_data") as mock_process_events_data:
        mock_process_events_data.return_value = {
            "expenses": [100, 200],
            "income": [300],
            "currency_rates": {"USD": 1.0},
            "stock_prices": {"AAPL": 150.0},
        }

        result = main_func("events", "2023-01-01 00:00:00", sample_df)

        assert isinstance(result, str)
        data = json.loads(result)
        assert data["greeting"] == "Hello"
        assert "expenses" in data
        assert "income" in data
        assert "currency_rates" in data
        assert "stock_prices" in data


def test_main_func_no_data():
    result = main_func("home", "2023-01-01 00:00:00", None)
    assert isinstance(result, str)
    data = json.loads(result)
    assert data["error"] == "No data available."


def test_process_home_data(sample_df):
    with patch("src.views.get_card_from_main", return_value=["Card1", "Card2"]), patch(
        "src.views.get_top_transactions", return_value=["Transaction1", "Transaction2"]
    ), patch("src.views.get_user_settings_data", return_value=(["USD"], ["AAPL"])), patch(
        "src.views.get_rates_and_prices", return_value=({"USD": 1.0}, {"AAPL": 150.0})
    ):
        pbar = MagicMock()
        result = process_home_data(pbar, sample_df, pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-31"))

        assert "cards" in result
        assert "top_transactions" in result
        assert "currency_rates" in result
        assert "stock_prices" in result


def test_process_events_data(sample_df):
    with patch("src.views.get_expenses", return_value=[100, 200]), patch(
        "src.views.get_income", return_value=[300]
    ), patch("src.views.get_user_settings_data", return_value=(["USD"], ["AAPL"])), patch(
        "src.views.get_rates_and_prices", return_value=({"USD": 1.0}, {"AAPL": 150.0})
    ):
        pbar = MagicMock()
        result = process_events_data(pbar, sample_df)

        assert "expenses" in result
        assert "income" in result
        assert "currency_rates" in result
        assert "stock_prices" in result
