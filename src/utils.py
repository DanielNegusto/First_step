import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from tqdm import tqdm

from src.views import (get_card_data_from_excel, get_card_from_main, get_currency_rates, get_expenses, get_greeting,
                       get_income, get_stock_prices, get_top_transactions, load_user_settings, parse_date_range)


def get_common_data(start_date: datetime, end_date: datetime, progress_bar: tqdm) -> Any:
    """
    Загружает данные о картах из Excel-файла в указанный диапазон дат.

    Args:
        start_date (datetime): Начальная дата для фильтрации данных.
        end_date (datetime): Конечная дата для фильтрации данных.
        progress_bar (tqdm): Прогресс-бар для обновления хода выполнения операции.

    Returns:
        Any: DataFrame, содержащий отфильтрованные данные о картах.
    """
    df = get_card_data_from_excel("data/operations.xls", start_date=start_date, end_date=end_date)
    progress_bar.update(20)
    return df


def get_user_settings_data(progress_bar: tqdm) -> Tuple[List[str], List[str]]:
    """
    Загружает настройки пользователя и получает список валют и акций.

    Args:
        progress_bar (tqdm): Прогресс-бар для обновления хода выполнения операции.

    Returns:
        Tuple[List[str], List[str]]: Кортеж, содержащий два списка - пользовательские валюты и акции.
    """
    user_settings = load_user_settings("user_settings.json")
    currencies = user_settings.get("user_currencies", [])
    stocks = user_settings.get("user_stocks", [])
    progress_bar.update(10)
    return currencies, stocks


def get_rates_and_prices(currencies: List[str], stocks: List[str], progress_bar: tqdm) -> Tuple[List[Any], List[Any]]:
    """
    Получает текущие курсы для указанных валют и цены на указанные акции.

    Args:
        currencies (List[str]): Список кодов валют.
        stocks (List[str]): Список тикеров акций.
        progress_bar (tqdm): Прогресс-бар для обновления хода выполнения операции.

    Returns:
        Tuple[List[Any], List[Any]]: Кортеж, содержащий два списка - курсы валют и цены акций.
    """
    currency_rates = get_currency_rates(currencies)
    progress_bar.update(10)
    stock_prices = get_stock_prices(stocks)
    progress_bar.update(10)
    return currency_rates, stock_prices


def main_func(data_type: str, date_str: str, date_range: Optional[str] = None) -> str:
    """
    Основная функция для обработки и возврата финансовых данных на основе указанного типа данных и даты.

    Args:
        data_type (str): Тип данных для получения ('home' или 'events').
        date_str (str): Дата для обработки данных.
        date_range (Optional[str]): Необязательный диапазон дат для фильтрации данных.

    Returns:
        str: Строка в формате JSON, содержащая обработанные данные или сообщение об ошибке.
    """
    try:
        current_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        greeting = get_greeting(current_time)

        dic_lst: Dict[str, Any] = {}

        with tqdm(total=100, desc="Processing") as pbar:
            if data_type == "home":
                pbar.set_description("Получение данных карт")
                start_date = current_time.replace(day=1)
                end_date = current_time
                df = get_common_data(start_date, end_date, pbar)

                pbar.set_description("Получение информации о картах")
                card_data = get_card_from_main(df)
                pbar.update(20)

                pbar.set_description("Получение топовых транзакций")
                top_transactions = get_top_transactions(start_date=start_date, end_date=end_date)
                pbar.update(20)

                currencies, stocks = get_user_settings_data(pbar)

                pbar.set_description("Получение курсов валют и цен на акции")
                currency_rates, stock_prices = get_rates_and_prices(currencies, stocks, pbar)
                pbar.update(10)

                dic_lst = {
                    "greeting": greeting,
                    "cards": card_data,
                    "top_transactions": top_transactions,
                    "currency_rates": currency_rates,
                    "stock_prices": stock_prices,
                }

            elif data_type == "events":
                pbar.set_description("Разбор диапазона дат")
                start_date, end_date = parse_date_range(date_str, date_range)
                pbar.update(20)

                pbar.set_description("Получение данных карт")
                df = get_common_data(start_date, end_date, pbar)

                pbar.set_description("Получение расходов")
                expenses = get_expenses(df)
                pbar.update(15)

                pbar.set_description("Получение доходов")
                income = get_income(df)
                pbar.update(15)

                currencies, stocks = get_user_settings_data(pbar)

                pbar.set_description("Получение курсов валют и цен на акции")
                currency_rates, stock_prices = get_rates_and_prices(currencies, stocks, pbar)
                pbar.update(10)

                dic_lst = {
                    "greeting": greeting,
                    "expenses": expenses,
                    "income": income,
                    "currency_rates": currency_rates,
                    "stock_prices": stock_prices,
                }

            else:
                raise ValueError("Invalid data type. Must be 'home' or 'events'.")

        return json.dumps(dic_lst, ensure_ascii=False, indent=4)

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return json.dumps({"error": "An error occurred while processing the request."}, ensure_ascii=False, indent=4)


def parse_user_date(year: Optional[str] = None, month: Optional[str] = None, day: Optional[str] = None) -> str:
    """
    Формирует строку даты и времени из предоставленных пользователем года, месяца и дня.

    Args:
        year (Optional[str]): Год в виде строки.
        month (Optional[str]): Месяц в виде строки.
        day (Optional[str]): День в виде строки.

    Returns:
        str: Строка даты и времени в формате 'YYYY-MM-DD HH:MM:SS'.
    """
    if year and month and day:
        date_part = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
        time_part = datetime.now().time()
        return datetime.combine(date_part, time_part).strftime("%Y-%m-%d %H:%M:%S")
    else:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_year_input() -> str:
    """
    Запрашивает у пользователя ввод года в формате 'xxxx' и проверяет корректность ввода.

    Returns:
        str: Введенный пользователем и проверенный год.
    """
    while True:
        user_input = input("Введите год в формате xxxx: ")
        if user_input.isdigit() and len(user_input) == 4:
            return user_input
        else:
            print("Некорректный ввод. Пожалуйста, введите год в формате xxxx (например, 2023).")


def get_month_input() -> str:
    """
    Запрашивает у пользователя ввод месяца в формате 'xx' и проверяет корректность ввода.

    Returns:
        str: Введенный пользователем и проверенный месяц.
    """
    while True:
        month = input("Введите месяц в формате xx: ")
        if month.isdigit() and 1 <= int(month) <= 12:
            return month.zfill(2)
        else:
            print("Некорректный ввод. Пожалуйста, введите месяц в формате xx (например, 1 для января).")


def get_day_input() -> str:
    """
    Запрашивает у пользователя ввод дня в формате 'xx' и проверяет корректность ввода.

    Returns:
        str: Введенный пользователем и проверенный день.
    """
    while True:
        day = input("Введите день в формате xx: ")
        if day.isdigit() and 1 <= int(day) <= 31:
            return day.zfill(2)
        else:
            print("Некорректный ввод. Пожалуйста, введите день в формате xx (например, 1).")
