import os
from typing import Any, Dict, Generator, List, Tuple, Union

import pandas as pd
import pytest


@pytest.fixture(scope="module")
def temp_excel_file() -> Generator[str, None, None]:
    data: Dict[str, List] = {
        "Дата операции": [
            "01.08.2023 12:00:00",
            "02.08.2023 14:00:00",
            "03.08.2023 10:00:00",
            "04.08.2023 16:00:00",
            "05.08.2023 18:00:00",
            "06.08.2023 20:00:00",
        ],
        "Сумма операции": [5000, 7000, 2000, 8000, 1000, 9000],
        "Категория": ["Продукты", "Развлечения", "Транспорт", "Рестораны", "Продукты", "Путешествия"],
        "Описание": [
            "Покупка в магазине",
            "Поход в кино",
            "Проезд",
            "Ужин в ресторане",
            "Покупка еды",
            "Билеты на самолет",
        ],
    }

    df: pd.DataFrame = pd.DataFrame(data)
    temp_file: str = "test_operations.xlsx"
    df.to_excel(temp_file, index=False)

    yield temp_file

    if os.path.exists(temp_file):
        os.remove(temp_file)


@pytest.fixture(
    params=[
        ("2024-01-01", "2024-01-31", {"start_date": "2024-01-01", "end_date": "2024-01-31"}, 20),
        ("2024-02-01", "2024-02-28", {"start_date": "2024-02-01", "end_date": "2024-02-28"}, 20),
    ]
)
def common_data_params(request: Any) -> Tuple[str, str, Dict[str, str], int]:
    param = request.param
    assert isinstance(param, tuple) and len(param) == 4
    assert isinstance(param[0], str) and isinstance(param[1], str)
    assert isinstance(param[2], dict) and isinstance(param[3], int)
    return param


@pytest.fixture(
    params=[
        ({"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "GOOGL"]}, ["USD", "EUR"], ["AAPL", "GOOGL"], 10),
        ({"user_currencies": ["JPY"], "user_stocks": ["MSFT"]}, ["JPY"], ["MSFT"], 10),
    ]
)
def user_settings_params(request: Any) -> Tuple[Dict[str, List[str]], List[str], List[str], int]:
    param = request.param
    assert isinstance(param, tuple) and len(param) == 4
    assert isinstance(param[0], dict) and isinstance(param[1], list)
    assert isinstance(param[2], list) and isinstance(param[3], int)
    return param


@pytest.fixture(
    params=[
        (
            ["USD", "EUR"],
            ["AAPL", "GOOGL"],
            {"USD": 1.0, "EUR": 0.85},
            [{"stock": "AAPL", "price": 150.00}, {"stock": "GOOGL", "price": 2800.00}],
            [10, 10],
        ),
        (["JPY"], ["MSFT"], {"JPY": 110.0}, [{"stock": "MSFT", "price": 300.00}], [10, 10]),
    ]
)
def rates_and_prices_params(
    request: Any,
) -> Tuple[List[str], List[str], Dict[str, float], List[Dict[str, float]], List[int]]:
    param = request.param
    assert isinstance(param, tuple) and len(param) == 5
    assert isinstance(param[0], list) and isinstance(param[1], list)
    assert isinstance(param[2], dict) and isinstance(param[3], list)
    assert isinstance(param[4], list)
    return param


@pytest.fixture(
    params=[
        ("home", "2024-08-10 12:00:00", None),
        ("events", "2024-08-10 12:00:00", "2024-07-01_2024-08-01"),
    ]
)
def main_func_params(request: Any) -> Tuple[str, str, Union[str, None]]:
    param = request.param
    assert isinstance(param, tuple) and len(param) == 3
    assert isinstance(param[0], str) and isinstance(param[1], str)
    assert isinstance(param[2], (str, type(None)))
    return param
