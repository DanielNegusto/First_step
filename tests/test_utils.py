import json
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional, Tuple
from unittest.mock import MagicMock, patch

import pytest
from tqdm import tqdm

from src.utils import (get_common_data, get_day_input, get_month_input, get_rates_and_prices, get_user_settings_data,
                       get_year_input, main_func, parse_user_date)


def test_get_common_data() -> None:
    start_date = datetime(2024, 8, 1)
    end_date = datetime(2024, 8, 10)

    mock_df: MagicMock = MagicMock()

    with patch("src.utils.get_card_data_from_excel", return_value=mock_df) as mock_get_card_data:
        mock_progress_bar: MagicMock = MagicMock(spec=tqdm)

        # Вызов функции с моками
        result = get_common_data(start_date, end_date, mock_progress_bar)

        # Проверка вызова get_card_data_from_excel с правильными аргументами
        mock_get_card_data.assert_called_once_with("data/operations.xls", start_date=start_date, end_date=end_date)

        # Проверка, что прогресс-бар был обновлен на 20
        mock_progress_bar.update.assert_called_once_with(20)

        # Проверка, что функция вернула ожидаемый DataFrame (или его мок)
        assert result == mock_df


def test_get_user_settings_data() -> None:
    mock_user_settings = {"user_currencies": ["USD", "EUR", "JPY"], "user_stocks": ["AAPL", "GOOGL", "TSLA"]}

    expected_currencies = ["USD", "EUR", "JPY"]
    expected_stocks = ["AAPL", "GOOGL", "TSLA"]

    # Мокаем функцию load_user_settings
    with patch("src.utils.load_user_settings", return_value=mock_user_settings) as mock_load_user_settings:
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


RatesAndPricesParams = Tuple[
    List[str],  # Список валют
    List[str],  # Список акций
    Dict[str, Any],  # Ожидаемые курсы валют
    Dict[str, Any],  # Ожидаемые цены на акции
    List[int],  # Обновления прогресс-бара
]


def test_get_rates_and_prices(rates_and_prices_params: RatesAndPricesParams) -> None:
    currencies, stocks, expected_currency_rates, expected_stock_prices, progress_updates = rates_and_prices_params
    with patch("src.utils.get_currency_rates", return_value=expected_currency_rates) as mock_get_currency_rates, patch(
        "src.utils.get_stock_prices", return_value=expected_stock_prices
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


@pytest.mark.parametrize(
    "year, month, day, expected_date_format",
    [
        (2024, 8, 10, "%Y-%m-%d %H:%M:%S"),  # Текущая дата с указанными годом, месяцем и днем
        (None, None, None, "%Y-%m-%d %H:%M:%S"),  # Текущая дата и время
    ],
)
def test_parse_user_date(
    year: Optional[str], month: Optional[str], day: Optional[str], expected_date_format: str
) -> None:
    result = parse_user_date(year, month, day)

    # Проверка, что дата возвращена в правильном формате
    try:
        datetime.strptime(result, expected_date_format)
    except ValueError:
        pytest.fail(f"Returned date '{result}' does not match expected format '{expected_date_format}'")


@patch("builtins.input", side_effect=["abcd", "123", "2023"])
def test_get_year_input(_: MagicMock) -> None:
    result = get_year_input()
    assert result == "2023"


@patch("builtins.input", side_effect=["13", "0", "8"])
def test_get_month_input(_: MagicMock) -> None:
    result = get_month_input()
    assert result == "08"


@patch("builtins.input", side_effect=["32", "0", "10"])
def test_get_day_input(_: MagicMock) -> None:
    result = get_day_input()
    assert result == "10"


@pytest.fixture
def mock_dependencies() -> Generator[Dict[str, MagicMock], None, None]:
    with patch("src.utils.get_greeting") as mock_get_greeting, patch(
        "src.utils.get_common_data"
    ) as mock_get_common_data, patch("src.utils.get_card_from_main") as mock_get_card_from_main, patch(
        "src.utils.get_top_transactions"
    ) as mock_get_top_transactions, patch(
        "src.utils.get_user_settings_data"
    ) as mock_get_user_settings_data, patch(
        "src.utils.get_rates_and_prices"
    ) as mock_get_rates_and_prices:

        # Задаем возвращаемые значения для моков
        mock_get_greeting.return_value = "Hello"
        mock_get_common_data.return_value = MagicMock()  # Можно использовать пустой MagicMock для df
        mock_get_card_from_main.return_value = ["card_data"]
        mock_get_top_transactions.return_value = ["top_transaction"]
        mock_get_user_settings_data.return_value = (["currency"], ["stock"])
        mock_get_rates_and_prices.return_value = (["currency_rates"], ["stock_prices"])

        yield {
            "mock_get_greeting": mock_get_greeting,
            "mock_get_common_data": mock_get_common_data,
            "mock_get_card_from_main": mock_get_card_from_main,
            "mock_get_top_transactions": mock_get_top_transactions,
            "mock_get_user_settings_data": mock_get_user_settings_data,
            "mock_get_rates_and_prices": mock_get_rates_and_prices,
        }


def test_main_func_home(mock_dependencies: Dict[str, MagicMock]) -> None:
    # Тестируемая дата
    date_str = "2024-08-10 12:00:00"

    # Ожидаемый результат
    expected_output = {
        "greeting": "Hello",
        "cards": ["card_data"],
        "top_transactions": ["top_transaction"],
        "currency_rates": ["currency_rates"],
        "stock_prices": ["stock_prices"],
    }

    # Вызов функции
    result = main_func(data_type="home", date_str=date_str)

    # Преобразуем результат в словарь для сравнения
    result_dict = json.loads(result)

    # Проверяем соответствие ожидаемого результата и реального
    assert expected_output == result_dict
