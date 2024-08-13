import json
import pprint
from typing import List, Optional

import pandas as pd

from src.reports import category_spending, spending_by_category
from src.services import analyze_cashback, investment_bank, get_info_from_excel
from src.utils import get_day_input, get_month_input, get_year_input, main_func, parse_user_date


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
    print("Выберите необходимый пункт меню:")
    print("1. Веб-Страницы")
    print("2. Сервисы")
    print("3. Отчёты")

    main_option = get_user_input("Введите номер: ", ["1", "2", "3"])
    if main_option == "1":
        print("Меню: Веб-Страницы:")
        date_option = get_user_input("Выбрать текущую дату? (Да/Нет): ", ["ДА", "НЕТ"])
        if date_option == "ДА":
            date_str = parse_user_date()
        else:
            year = get_year_input()
            month = get_month_input()
            day = get_day_input()
            date_str = parse_user_date(year, month, day)
        print("По какой странице вам нужна информация?")
        print("1. Главная")
        print("2. События")
        option = get_user_input("Введите номер: ", ["1", "2"])
        if option == "1":
            print("Получение информации по вашей дате...")
            result = main_func("home", date_str)
            print("Информация получена")
            file_option = get_user_input("Сохранить файл(Да/Нет): ", ["ДА", "НЕТ"])
            if file_option == "ДА":
                save_result_to_file(result, "data/result.json")
                print("Полученные данные сохранены в 'result.json'")
            print("Ваши данные по запросу -> ")
            pprint.pp(json.loads(result))
        elif option == "2":
            print("W — неделя, на которую приходится дата")
            print("M — месяц, на который приходится дата")
            print("Y — год, на который приходится дата")
            print("ALL — все данные до указанной даты")
            date_range = get_user_input("Выберете диапазон данных: ", ["W", "M", "Y", "ALL"])
            print("Получение информации по вашей дате и диапазону данных...")
            result = main_func("events", date_str, date_range)
            print("Информация получена")
            file_option = get_user_input("Сохранить файл(Да/Нет): ", ["ДА", "НЕТ"])
            if file_option == "ДА":
                save_result_to_file(result, "data/result.json")
                print("Полученные данные сохранены в 'result.json'")
            print("Ваши данные по запросу -> ")
            pprint.pp(json.loads(result))
    elif main_option == "2":
        print("Введите дату для анализа данных")
        year = get_year_input()
        month = get_month_input()
        df = get_info_from_excel()
        print("Какие сервисы вы хотите использовать?")
        print("1. Выгодные категории повышенного кешбэка")
        print("2. Инвесткопилка")
        option = get_user_input("Введите номер: ", ["1", "2"])
        if option == "1":
            print("Анализ выгодных категорий")
            result = analyze_cashback(df, int(year), int(month))
            print("Информация получена")
            file_option = get_user_input("Сохранить файл(Да/Нет): ", ["ДА", "НЕТ"])
            if file_option == "ДА":
                save_result_to_file(result, "data/result.json")
            print("Ваши данные по запросу -> ")
            print(result)
        elif option == "2":
            limit = get_user_input("Введите порог округления: ", ["10", "50", "100"])
            month = f"{year}-{month}"
            result = investment_bank(month, df, int(limit))
            print(round(result, 2))
    elif main_option == "3":
        print("Выбрано траты по категории")
        data = get_info_from_excel()
        df = pd.DataFrame(data)
        df['Дата операции'] = pd.to_datetime(df['Дата операции'], dayfirst=True)
        date_option = get_user_input("Выбрать текущую дату для анализа? (Да/Нет): ", ["ДА", "НЕТ"])
        if date_option == "ДА":
            found = category_spending(df)
            result = spending_by_category(df, found)
            print(result)
        if date_option == "НЕТ":
            print("Введите дату для анализа данных")
            year = get_year_input()
            month = get_month_input()
            day = get_day_input()
            date_str = f"{year}-{month}-{day}"
            found = category_spending(df)
            result = spending_by_category(df, found, date_str)
            print(result)


if __name__ == "__main__":
    main()
