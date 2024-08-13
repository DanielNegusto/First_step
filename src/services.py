import json
import logging
from datetime import datetime
from typing import Any, Dict, Hashable, List

import pandas as pd


def get_info_from_excel() -> list[dict[Hashable, Any]]:
    # Читаем данные из Excel-таблицы
    df = pd.read_excel("data/operations.xls")
    # Преобразуем данные в словарь
    data = df.to_dict("records")
    return data


def analyze_cashback(data: List[Dict[Hashable, Any]], year: int, month: int) -> str:
    """
    Анализирует категории повышенного кешбэка.

    Args:
        data (List[Dict[Hashable, Any]]): Данные с транзакциями.
        year (int): Год, за который проводится анализ.
        month (int): Месяц, за который проводится анализ.

    Returns:
        str: JSON с анализом, сколько на каждой категории можно заработать кешбэка.
    """

    # Инициализируем словарь для хранения результатов анализа
    analysis: Dict[str, float] = {}

    # Итерируем по транзакциям
    for transaction in data:
        # Преобразуем строку даты в объект datetime
        transaction_date = datetime.strptime(transaction.get("Дата операции", ""), "%d.%m.%Y %H:%M:%S")

        # Проверяем, соответствует ли транзакция указанному году и месяцу
        if transaction_date.year == year and transaction_date.month == month:
            # Получаем категорию транзакции
            category: str = transaction.get("Категория", "")

            # Проверяем, есть ли кэшбэк для этой транзакции
            if float(transaction.get("Бонусы (включая кэшбэк)", "0")) > 0:
                # Если категория не существует в анализе, добавляем ее
                if category not in analysis:
                    analysis[category] = 0.0

                # Добавляем сумму кэшбэка к категории
                analysis[category] += float(transaction.get("Бонусы (включая кэшбэк)", "0"))

    # Сортируем словарь по значениям в порядке убывания
    sorted_analysis: Dict[str, float] = dict(sorted(analysis.items(), key=lambda item: item[1], reverse=True))

    # Возвращаем результаты анализа в формате JSON
    return json.dumps(sorted_analysis, indent=4, ensure_ascii=False)


def round_up_amount(amount: float, limit: int) -> float:
    """
    Округляет сумму операции до заданного предела.

    Args:
        amount: Сумма операции.
        limit: Предел округления.

    Returns:
        Округленная сумма.
    """

    return -(-amount // limit) * limit - amount


def investment_bank(month: str, transactions: List[Dict[Hashable, Any]], limit: int) -> float:
    """
    Рассчитывает сумму, которую удалось бы отложить в «Инвесткопилку» за заданный месяц.

    Args:
        month: Месяц, для которого рассчитывается отложенная сумма (строка в формате 'YYYY-MM').
        transactions: Список словарей, содержащий информацию о транзакциях.
        limit: Предел, до которого нужно округлять суммы операций (целое число).

    Returns:
        Сумма, которую удалось бы отложить в «Инвесткопилку».
    """

    total_savings = 0.0
    for transaction in transactions:
        # Предполагаем, что в Excel-файле столбец с датой называется "Дата операции"
        transaction_date_str = transaction.get("Дата операции")
        if transaction_date_str:
            try:
                # Преобразование строки в datetime объект
                transaction_date = pd.to_datetime(transaction_date_str, format="%d.%m.%Y %H:%M:%S").date()
            except ValueError as e:
                logging.error(f"Ошибка при парсинге даты транзакции: {e}, transaction: {transaction}")
                continue

            if transaction_date.strftime("%Y-%m") == month:
                transaction_amount = transaction.get("Сумма операции")
                if isinstance(transaction_amount, (int, float)):
                    savings = round_up_amount(transaction_amount, limit)
                    total_savings += savings
                else:
                    logging.warning(f"Пропущена транзакция с некорректной суммой: {transaction}")
        else:
            logging.warning(f"Пропущена транзакция без даты: {transaction}")

    return total_savings
