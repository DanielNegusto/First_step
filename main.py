import json
import pprint
from datetime import datetime
from typing import List, Optional

import pandas as pd

from src.reports import category_spending, spending_by_category
from src.services import analyze_cashback, get_info_from_excel, investment_bank
from src.utils import get_day_input, get_month_input, get_year_input, parse_user_date
from src.views import get_card_data_from_excel, main_func


def get_user_input(prompt: str, valid_options: Optional[List[str]] = None) -> str:
    while True:
        user_input = input(prompt).strip().upper()
        if valid_options and user_input not in valid_options:
            print(f"Неверный ввод. Доступные опции: {', '.join(valid_options)}")
        else:
            return user_input


def save_result_to_file(result: str, filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        f.write(result)


def main() -> None:
    print("Привет! Добро пожаловать в программу работы с банковскими данными.")
    main_option = get_user_input(
        "Выберите необходимый пункт меню:\n1. Веб-Страницы\n2. Сервисы\n3. Отчёты\nВведите номер: ", ["1", "2", "3"]
    )

    if main_option == "1":
        handle_web_pages()
    elif main_option == "2":
        handle_services()
    elif main_option == "3":
        handle_reports()


def handle_web_pages() -> None:
    date_option = get_user_input("Выбрать текущую дату? (Да/Нет): ", ["ДА", "НЕТ"])
    date_str = get_date_input(date_option)

    current_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    start_date = current_time.replace(day=1)
    end_date = current_time

    df = get_card_data_from_excel("data/operations.xls", start_date, end_date)
    option = get_user_input(
        "По какой странице вам нужна информация?\n1. Главная\n2. События\nВведите номер: ", ["1", "2"]
    )

    if option == "1":
        handle_home_page(df, date_str)
    elif option == "2":
        handle_events_page(df, date_str)


def get_date_input(date_option: str) -> str:
    if date_option == "ДА":
        return parse_user_date()
    else:
        year = get_year_input()
        month = get_month_input()
        day = get_day_input()
        return parse_user_date(year, month, day)


def handle_home_page(df: pd.DataFrame, date_str: str) -> None:
    print("Получение информации по вашей дате...")
    result = main_func("home", date_str, df)
    process_result(result)


def handle_events_page(df: pd.DataFrame, date_str: str) -> None:
    print(
        "W — неделя, на которую приходится дата\nM — месяц, на который приходится дата\n"
        "Y — год, на который приходится дата\nALL — все данные до указанной даты"
    )
    date_range = get_user_input("Выберите диапазон данных: ", ["W", "M", "Y", "ALL"])
    print("Получение информации по вашей дате и диапазону данных...")
    result = main_func("events", date_str, df, date_range)
    process_result(result)


def handle_services() -> None:
    print("Введите дату для анализа данных")
    year = get_year_input()
    month = get_month_input()
    print("Получение данных карт")
    option = get_user_input(
        "Какие сервисы вы хотите использовать?\n1. Выгодные категории повышенного кешбэка\n"
        "2. Инвесткопилка\nВведите номер: ",
        ["1", "2"],
    )

    if option == "1":
        analyze_cashback_service(year, month)
    elif option == "2":
        investment_service(year, month)


def analyze_cashback_service(year: str, month: str) -> None:
    print("Анализ выгодных категорий")
    data = get_info_from_excel()
    result = analyze_cashback(data, int(year), int(month))
    process_result(result)


def investment_service(year: str, month: str) -> None:
    data = get_info_from_excel()
    limit = get_user_input("Введите порог округления: ", ["10", "50", "100"])
    month_str = f"{year}-{month}"
    result = investment_bank(month_str, data, int(limit))
    print(round(result, 2))


def handle_reports() -> None:
    print("Выбрано траты по категории")
    data = get_info_from_excel()
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    date_option = get_user_input("Выбрать текущую дату для анализа? (Да/Нет): ", ["ДА", "НЕТ"])

    if date_option == "ДА":
        found = category_spending(df)
        result = spending_by_category(df, found)
        print(result)
    else:
        print("Введите дату для анализа данных")
        year = get_year_input()
        month = get_month_input()
        day = get_day_input()
        date_str = f"{year}-{month}-{day}"
        found = category_spending(df)
        result = spending_by_category(df, found, date_str)
        print(result)


def process_result(result: str) -> None:
    print("Информация получена")
    file_option = get_user_input("Сохранить файл(Да/Нет): ", ["ДА", "НЕТ"])
    if file_option == "ДА":
        save_result_to_file(result, "data/result.json")
        print("Полученные данные сохранены в 'result.json'")
    print("Ваши данные по запросу -> ")
    pprint.pp(json.loads(result))


if __name__ == "__main__":
    main()
