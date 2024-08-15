from datetime import datetime
from typing import Optional


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
