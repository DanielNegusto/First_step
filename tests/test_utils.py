
from datetime import datetime
from typing import Dict, Generator, Optional
from unittest.mock import MagicMock, patch

import pytest

from src.utils import get_day_input, get_month_input, get_year_input, parse_user_date


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
