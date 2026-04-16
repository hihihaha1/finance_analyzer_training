import os
from datetime import datetime
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
import logging

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    DB_USER = 'dimasartakov'
    DB_PASSWORD = 'secretpassword'
    DB_HOST = '127.0.0.1'
    DB_PORT = '5433'
    DB_NAME = 'finance_db'
    DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(DATABASE_URL)


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
def generate_data(periods=100):
    data = {
        'date' : pd.date_range(start='2026-01-01', periods=periods, freq='D'),
        'category': np.random.choice(['Food', 'Gym', 'Transport', 'Education', 'Subscriptions'], 100),
        'amount' : np.random.uniform(10, periods, periods).round(2),
        'currency': 'USD'
    }
    return pd.DataFrame(data)

def save_csv(df, filename):
    df.to_csv(filename, index=False)
    logging.info(f"Данные сохранены в: {filename}")

def load_from_csv(filename):
    if os.path.exists(filename):
        logging.info(f"Считываем файл: {filename}")
        return pd.read_csv(filename)
    else:
        logging.info(f"Файл не найден")
        return None

def save_to_sql(df, table_name):
    try:
        logging.info(f"Попытка загрузить данные в SQL таблицу")
        df_to_save = df.reset_index() if df.index.name else df
        df_to_save.to_sql(table_name, engine, if_exists='append', index=False)
        logging.info(f"Успешно.")
    except Exception as e:
        logging.error(f"Не удалось загрузить данные: {e}")


def preprocess_data(df):
    logging.info(f"Начало Transform")

    initial_size = len(df)

    df = df.drop_duplicates(keep='first').copy()
    df['amount'] = df['amount'].fillna(value=0)
    df = df[df['amount'] > 0]

    cleaned_size = len(df)
    if cleaned_size < initial_size:
        logging.warning(f"Чистка от аномалий завершена. Удалено {initial_size - cleaned_size} аномалий")

    df = df.sort_values(['date', 'category'])

    # Какой процент составляет конкретная категория от общего за последние 7 дней
    df['rolling_amount_7d'] = df.groupby('category')['amount'].transform(lambda x: x.rolling(window=7).mean())
    df['rolling_7d'] = df['amount'].rolling(window=7).mean()
    df['cat_share_in_rolling'] = ((df['rolling_amount_7d'] / df['rolling_7d']) * 100).round(2)

    # Накопительная сумма общая и по категориям
    df['total_accumulated'] = df['amount'].cumsum()
    df['category_cumsum'] = df.groupby('category')['amount'].cumsum()

    # Темп роста расходов внутри каждой категории
    df['mean_amount'] = df.groupby('category')['amount'].transform('mean')
    df['deviation_pct'] = ((df['amount'] - df['mean_amount']) / df['mean_amount']) * 100

    logging.info("Transform завершен")
    return df

def get_report(df):
    df['future_amount'] = (df['amount'] * 1.1).round(2)

    report = df.groupby('category').agg(
        Total_spend = ('amount','sum'),
        Average_check = ('amount', 'mean'),
        Future_total = ('future_amount','sum'),
        Currency = ('currency', 'first')
    ).round(2).sort_values('Total_spend', ascending=False)

    report['created_at'] = datetime.now()

    report['Budget_Share_Pct'] = ((report['Total_spend'] / df['amount'].sum()) * 100).round(2)
    return report

if __name__ == "__main__":
    raw_file = 'raw_transactions.csv'
    raw_data = generate_data()
    save_csv(raw_data, raw_file)

    loaded_df = load_from_csv(raw_file)

    if loaded_df is not None:
        final_df = preprocess_data(loaded_df)
        report = get_report(final_df)

        save_to_sql(final_df, 'processed_transactions')
        save_to_sql(report, 'category_analysis')

        logging.info("Процесс завершен")