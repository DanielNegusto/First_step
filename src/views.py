import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

API_KEY = os.getenv("API")
Alpha_KEY = os.getenv("AlPHA_API")


# Загрузка пользовательских настроек
def load_user_settings(filepath: str) -> Any:
    """
    Загружает настройки пользователя из указанного файла.

    Args:
        filepath (str): Путь к файлу с настройками пользователя.

    Returns:
        Any: Объект, представляющий собой данные, загруженные из JSON-файла.
    """
    with open(filepath, "r") as f:
        return json.load(f)


def get_greeting(current_time: datetime) -> str:
    """
    Возвращает приветствие в зависимости от текущего времени суток.

    Args:
        current_time (datetime): Текущее время.

    Returns:
        str: Приветствие на русском языке ("Доброе утро", "Добрый день", "Добрый вечер" или "Доброй ночи").
    """
    hour = current_time.hour
    if 6 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 24:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


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


def parse_date_range(date_str: str, date_range: Optional[str] = None) -> Tuple[datetime, datetime]:
    """
    Парсит дату и диапазон дат из строки.

    Args:
        date_str (str): Строка с датой и диапазоном дат.
        date_range (Optional[str]): Диапазон дат.

    Returns:
        Tuple[datetime, datetime]: Начальная и конечная даты.
    """
    current_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    if date_range == "W":
        start_date = current_time - timedelta(days=current_time.weekday())
    elif date_range == "M":
        start_date = current_time.replace(day=1)
    elif date_range == "Y":
        start_date = current_time.replace(month=1, day=1)
    elif date_range == "ALL":
        start_date = datetime.min  # Заменяем None на минимально возможное значение даты
    else:
        start_date = current_time.replace(day=1)

    end_date = current_time
    return start_date, end_date


# Получение данных по картам из Excel
def get_card_data_from_excel(
    filepath: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
) -> pd.DataFrame:
    """
    Загружает данные о транзакциях с карт из Excel-файла и фильтрует их по дате.

    Args:
        filepath (str): Путь к Excel-файлу.
        start_date (Optional[datetime]): Начальная дата фильтрации.
        end_date (Optional[datetime]): Конечная дата фильтрации.

    Returns:
        pd.DataFrame: DataFrame с данными о транзакциях, отфильтрованными по дате.
    """
    df = pd.read_excel(filepath)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")
    if start_date:
        df = df[df["Дата операции"] >= start_date]
    if end_date:
        df = df[df["Дата операции"] <= end_date]

    return df


def get_card_from_main(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Получает информацию о картах из основного DataFrame.

    Args:
        df (pd.DataFrame): Основной DataFrame с данными о транзакциях.

    Returns:
        List[Dict[str, Any]]: Список словарей, содержащих информацию о картах.
    """
    card_summary = df.groupby("Номер карты")["Сумма операции"].sum().reset_index()
    card_info = []
    for index, row in card_summary.iterrows():
        last_digits = str(row["Номер карты"])[-4:]
        total_spent = row["Сумма операции"]
        cashback = round(total_spent * 0.01, 2)
        card_info.append({"last_digits": last_digits, "total_spent": total_spent, "cashback": cashback})

    return card_info


def get_expenses(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Получает информацию о расходах из DataFrame.

    Args:
        df (pd.DataFrame): DataFrame с данными о транзакциях.

    Returns:
        Dict[str, Any]: Словарь с информацией о расходах.
    """

    expenses = df[df["Сумма операции"] < 0]
    total_amount = round(abs(expenses["Сумма операции"].sum()))
    main_categories = expenses.groupby("Категория")["Сумма операции"].sum().abs().nlargest(7).reset_index()
    other_amount = abs(expenses[~expenses["Категория"].isin(main_categories["Категория"])]["Сумма операции"].sum())
    main_expenses = main_categories.to_dict("records")
    if other_amount > 0:
        main_expenses.append({"Категория": "Остальное", "Сумма операции": round(other_amount)})
    transfers_and_cash = (
        expenses[expenses["Категория"].isin(["Наличные", "Переводы"])]
        .groupby("Категория")["Сумма операции"]
        .sum()
        .abs()
        .reset_index()
        .to_dict("records")
    )
    return {
        "total_amount": total_amount,
        "main": [{"category": row["Категория"], "amount": round(row["Сумма операции"])} for row in main_expenses],
        "transfers_and_cash": [
            {"category": row["Категория"], "amount": round(row["Сумма операции"])} for row in transfers_and_cash
        ],
    }


def get_income(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Получает информацию о доходах из DataFrame.

    Args:
        df (pd.DataFrame): DataFrame с данными о транзакциях.

    Returns:
        Dict[str, Any]: Словарь с информацией о доходах.
    """
    income = df[df["Сумма операции"] > 0]
    total_amount = round(income["Сумма операции"].sum())
    main_categories = income.groupby("Категория")["Сумма операции"].sum().nlargest(7).reset_index()
    main_income = main_categories.to_dict("records")
    return {
        "total_amount": total_amount,
        "main": [{"category": row["Категория"], "amount": round(row["Сумма операции"])} for row in main_income],
    }


# Получение топ-5 транзакций из Excel
def get_top_transactions(
    filepath: str = "data/operations.xls", start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Получает топ-5 транзакций за указанный период.

    Args:
        filepath (str): Путь к Excel-файлу с данными.
        start_date (Optional[datetime]): Начальная дата фильтрации.
        end_date (Optional[datetime]): Конечная дата фильтрации.

    Returns:
        List[Dict[str, Any]]: Список словарей с информацией о топ-5 транзакциях (дата, сумма, категория, описание).
    """
    df = pd.read_excel(filepath)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")
    if start_date and end_date:
        mask = (df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)
        df = df.loc[mask]

    df = df.dropna(subset=["Дата операции"])
    top_transactions = df.nlargest(5, "Сумма операции").to_dict("records")

    formatted_transactions = []
    for transaction in top_transactions:
        formatted_transactions.append(
            {
                "date": transaction["Дата операции"].strftime("%d.%m.%Y"),
                "amount": transaction["Сумма операции"],
                "category": transaction["Категория"],
                "description": transaction["Описание"],
            }
        )

    return formatted_transactions


# Получение курсов валют
def get_currency_rates(currencies: List[str]) -> List[Dict[str, Any]]:
    """
    Получает курсы валют для указанных валют.

    Args:
        currencies (List[str]): Список валют.

    Returns:
        List[Dict[str, Any]]: Список словарей с информацией о курсах валют.
    """
    currency_rates = []
    for currency in currencies:
        url = "https://api.apilayer.com/fixer/latest"
        params = {"base": currency}
        headers = {"apikey": API_KEY}

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            currency_rates.append({"currency": currency, "rate": data["rates"].get("RUB", "N/A")})
    return currency_rates


# Получение стоимости акций
def get_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    """
    Получает стоимость акций для указанных акций.

    Args:
        stocks (List[str]): Список акций.

    Returns:
        List[Dict[str, Any]]: Список словарей с информацией о стоимости акций.
    """
    stock_prices = []
    for stock in stocks:
        api_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={stock}&apikey={Alpha_KEY}"
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            last_refreshed = data["Meta Data"]["3. Last Refreshed"]
            stock_price = data["Time Series (Daily)"][last_refreshed]["4. close"]
            stock_prices.append({"stock": stock, "price": float(stock_price)})
    return stock_prices


def main_func(
    data_type: str, date_str: str, df: Optional[pd.DataFrame] = None, date_range: Optional[str] = None
) -> dict[Any, Any] | str:
    """
    Основная функция для обработки и возврата финансовых данных на основе указанного типа данных и даты.

    Args:
        data_type (str): Тип данных для получения ('home' или 'events').
        date_str (str): Дата для обработки данных.
        date_range (Optional[str]): Необязательный диапазон дат для фильтрации данных.
        df (Optional[pd.DataFrame]): Необязательный DataFrame с данными.

    Returns:
        str: Строка в формате JSON, содержащая обработанные данные или сообщение об ошибке.
    """
    try:
        current_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        greeting = get_greeting(current_time)


        if df is None:
            return json.dumps({"error": "No data available."}, ensure_ascii=False, indent=4)

        dic_lst: Dict[str, Any] = {}

        with tqdm(total=100, desc="Processing") as pbar:
            if data_type == "home":
                start_date = current_time.replace(day=1)
                end_date = current_time

                # Обработка данных для "home"
                dic_lst["greeting"] = greeting
                dic_lst.update(process_home_data(pbar, df, start_date, end_date))

            elif data_type == "events":
                start_date, end_date = parse_date_range(date_str, date_range)
                df = get_common_data(start_date, end_date, pbar)
                if df is None:
                    return json.dumps({"error": "No data available."}, ensure_ascii=False, indent=4)

                # Обработка данных для "events"
                dic_lst["greeting"] = greeting
                dic_lst.update(process_events_data(pbar, df))

            else:
                raise ValueError("Invalid data type. Must be 'home' or 'events'.")

        return json.dumps(dic_lst, ensure_ascii=False, indent=4)

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return json.dumps({"error": "An error occurred while processing the request."}, ensure_ascii=False, indent=4)


def process_home_data(pbar: tqdm, df: pd.DataFrame, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Обрабатывает данные для типа 'home'."""
    pbar.set_description("Получение информации о картах")
    card_data = get_card_from_main(df)
    pbar.update(30)

    pbar.set_description("Получение топовых транзакций")
    top_transactions = get_top_transactions(start_date=start_date, end_date=end_date)
    pbar.update(20)

    currencies, stocks = get_user_settings_data(pbar)

    pbar.set_description("Получение курсов валют и цен на акции")
    currency_rates, stock_prices = get_rates_and_prices(currencies, stocks, pbar)
    pbar.update(20)

    return {
        "cards": card_data,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }


def process_events_data(pbar: tqdm, df: pd.DataFrame) -> Dict[str, Any]:
    """Обрабатывает данные для типа 'events'."""
    pbar.set_description("Получение расходов")
    expenses = get_expenses(df)
    pbar.update(10)

    pbar.set_description("Получение доходов")
    income = get_income(df)
    pbar.update(10)

    currencies, stocks = get_user_settings_data(pbar)

    pbar.set_description("Получение курсов валют и цен на акции")
    currency_rates, stock_prices = get_rates_and_prices(currencies, stocks, pbar)
    pbar.update(10)

    return {
        "expenses": expenses,
        "income": income,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }
