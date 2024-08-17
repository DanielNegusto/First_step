import json
from unittest.mock import patch

import pandas as pd

from src.services import analyze_cashback, get_info_from_excel


def test_get_info_from_excel():
    # Создаем тестовый DataFrame
    df = pd.DataFrame(
        {"Дата операции": ["01.01.2022 12:00:00"], "Категория": ["Еда"], "Бонусы (включая кэшбэк)": ["100"]}
    )
    with patch("pandas.read_excel") as mock_read_excel:
        mock_read_excel.return_value = df
        # Проверяем, что функция возвращает словарь
        assert isinstance(get_info_from_excel(), list)


def test_analyze_cashback():
    # Создаем тестовые данные
    data = [
        {"Дата операции": "01.01.2022 12:00:00", "Категория": "Еда", "Бонусы (включая кэшбэк)": "100"},
        {"Дата операции": "01.01.2022 12:00:00", "Категория": "Транспорт", "Бонусы (включая кэшбэк)": "200"},
        {"Дата операции": "01.02.2022 12:00:00", "Категория": "Развлечения", "Бонусы (включая кэшбэк)": "300"},
    ]
    year = 2022
    month = 1
    # Проверяем, что функция возвращает словарь
    assert isinstance(analyze_cashback(data, year, month), str)
    # Проверяем, что в результате анализа есть категория 'Еда' и 'Транспорт'
    assert "Еда" in json.loads(analyze_cashback(data, year, month))
    assert "Транспорт" in json.loads(analyze_cashback(data, year, month))
