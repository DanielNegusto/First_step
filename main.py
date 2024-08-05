import json
import logging
import pprint
from datetime import datetime

from src.views import events, save_result_to_file, home_page

if __name__ == "__main__":
    user_int = input("Введите 1/2: ")
    date = "2020-07-22 10:32:50"
    if user_int == "2":
        date_rang = 'M'  # Диапазон данных (может быть 'W', 'M', 'Y', 'ALL'), по умолчанию 'M'
        result = events(date, date_rang)
        pprint.pp(json.loads(result))
        save_result_to_file(result, 'result.json')
    if user_int == "1":
        result = home_page(date)
        pprint.pp(json.loads(result))
        save_result_to_file(result, 'result.json')
