import logging
import os
import json

import requests
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv


load_dotenv()


API_KEY = os.getenv('API')
Alpha_KEY = os.getenv('AlPHA_API')


# Загрузка пользовательских настроек
def load_user_settings(filepath='user_settings.json'):
    with open(filepath, 'r') as f:
        return json.load(f)


def get_greeting(current_time):
    hour = current_time.hour
    if 6 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 24:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def parse_date_range(date_str, date_range='M'):
    current_time = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    if date_range == 'W':
        start_date = current_time - timedelta(days=current_time.weekday())
    elif date_range == 'M':
        start_date = current_time.replace(day=1)
    elif date_range == 'Y':
        start_date = current_time.replace(month=1, day=1)
    elif date_range == 'ALL':
        start_date = None
    else:
        start_date = current_time.replace(day=1)
    end_date = current_time
    return start_date, end_date


# Получение данных по картам из Excel
def get_card_data_from_excel(filepath='data/operations.xls', start_date=None, end_date=None):
    df = pd.read_excel(filepath)
    df['Дата операции'] = pd.to_datetime(df['Дата операции'], format='%d.%m.%Y %H:%M:%S', errors='coerce')
    if start_date:
        df = df[df['Дата операции'] >= start_date]
    if end_date:
        df = df[df['Дата операции'] <= end_date]

    return df


def get_card_from_main(df):
    card_summary = df.groupby('Номер карты')['Сумма операции'].sum().reset_index()

    card_info = []
    for index, row in card_summary.iterrows():
        last_digits = str(row['Номер карты'])[-4:]
        total_spent = row['Сумма операции']
        cashback = round(total_spent * 0.01, 2)
        card_info.append({
            "last_digits": last_digits,
            "total_spent": total_spent,
            "cashback": cashback
        })

    return card_info


def get_expenses(df):
    expenses = df[df['Сумма операции'] < 0]
    total_amount = round(abs(expenses['Сумма операции'].sum()))
    main_categories = expenses.groupby('Категория')['Сумма операции'].sum().abs().nlargest(7).reset_index()
    other_amount = abs(expenses[~expenses['Категория'].isin(main_categories['Категория'])]['Сумма операции'].sum())
    main_expenses = main_categories.to_dict('records')
    if other_amount > 0:
        main_expenses.append({"Категория": "Остальное", "Сумма операции": round(other_amount)})
    transfers_and_cash = expenses[expenses['Категория'].isin(['Наличные', 'Переводы'])].groupby('Категория')['Сумма операции'].sum().abs().reset_index().to_dict('records')
    return {
        "total_amount": total_amount,
        "main": [{"category": row['Категория'], "amount": round(row['Сумма операции'])} for row in main_expenses],
        "transfers_and_cash": [{"category": row['Категория'], "amount": round(row['Сумма операции'])} for row in transfers_and_cash]
    }


def get_income(df):
    income = df[df['Сумма операции'] > 0]
    total_amount = round(income['Сумма операции'].sum())
    main_categories = income.groupby('Категория')['Сумма операции'].sum().nlargest(7).reset_index()
    main_income = main_categories.to_dict('records')
    return {
        "total_amount": total_amount,
        "main": [{"category": row['Категория'], "amount": round(row['Сумма операции'])} for row in main_income]
    }


# Получение топ-5 транзакций из Excel
def get_top_transactions(filepath='data/operations.xls', start_date=None, end_date=None):
    df = pd.read_excel(filepath)
    df['Дата операции'] = pd.to_datetime(df['Дата операции'], format='%d.%m.%Y %H:%M:%S', errors='coerce')
    if start_date and end_date:
        mask = (df['Дата операции'] >= start_date) & (df['Дата операции'] <= end_date)
        df = df.loc[mask]

    df = df.dropna(subset=['Дата операции'])
    top_transactions = df.nlargest(5, 'Сумма операции').to_dict('records')

    formatted_transactions = []
    for transaction in top_transactions:
        formatted_transactions.append({
            "date": transaction['Дата операции'].strftime('%d.%m.%Y'),
            "amount": transaction['Сумма операции'],
            "category": transaction['Категория'],
            "description": transaction['Описание']
        })

    return formatted_transactions


# Получение курсов валют
def get_currency_rates(currencies):
    currency_rates = []
    for currency in currencies:
        url = 'https://api.apilayer.com/fixer/latest'
        params = {
            'base': currency
        }
        headers = {
            'apikey': API_KEY
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            currency_rates.append({
                "currency": currency,
                "rate": data['rates'].get("RUB", "N/A")
            })
    return currency_rates


# Получение стоимости акций
def get_stock_prices(stocks):
    stock_prices = []
    for stock in stocks:
        api_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={stock}&apikey={API_KEY}"
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            last_refreshed = data['Meta Data']['3. Last Refreshed']
            stock_price = data['Time Series (Daily)'][last_refreshed]['4. close']
            stock_prices.append({
                "stock": stock,
                "price": float(stock_price)
            })
    return stock_prices


def save_result_to_file(result, filename='result.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(result)


# Главные функции
def home_page(date_str):
    try:
        current_time = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        greeting = get_greeting(current_time)

        start_date = current_time.replace(day=1)
        end_date = current_time

        df = get_card_data_from_excel(start_date=start_date, end_date=end_date)
        card_data = get_card_from_main(df)
        top_transactions = get_top_transactions(start_date=start_date, end_date=end_date)

        user_settings = load_user_settings()
        currencies = user_settings.get("user_currencies", [])
        stocks = user_settings.get("user_stocks", [])

        currency_rates = get_currency_rates(currencies)
        stock_prices = get_stock_prices(stocks)

        dic_lst = {
            "greeting": greeting,
            "cards": card_data,
            "top_transactions": top_transactions,
            "currency_rates": currency_rates,
            "stock_prices": stock_prices
        }

        return json.dumps(dic_lst, ensure_ascii=False, indent=4)

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return json.dumps({"error": "An error occurred while processing the request."}, ensure_ascii=False, indent=4)


def events(date_str, date_range):
    try:
        current_time = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        greeting = get_greeting(current_time)

        start_date, end_date = parse_date_range(date_str, date_range)

        df = get_card_data_from_excel(start_date=start_date, end_date=end_date)
        expenses = get_expenses(df)
        income = get_income(df)
        user_settings = load_user_settings()
        currencies = user_settings.get("user_currencies", [])
        stocks = user_settings.get("user_stocks", [])

        currency_rates = get_currency_rates(currencies)
        stock_prices = get_stock_prices(stocks)

        dic_lst = {
            "greeting": greeting,
            "expenses": expenses,
            "income": income,
            "currency_rates": currency_rates,
            "stock_prices": stock_prices
        }

        return json.dumps(dic_lst, ensure_ascii=False, indent=4)

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return json.dumps({"error": "An error occurred while processing the request."}, ensure_ascii=False)
