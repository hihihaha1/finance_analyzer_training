import pandas as pd
import numpy as np

data = {
    'date' : pd.date_range(start='2026-01-01', periods=100, freq='D'),
    'category': np.random.choice(['Food', 'Gym', 'Transport', 'Education', 'Subscriptions'], 100),
    'amount' : np.random.uniform(10, 100, 100).round(2)
}

df = pd.DataFrame(data)

def generate_data(df):
    return df

def preprocess_data(df):
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

    return df

def get_report(df):
    df['future_amount'] = (df['amount'] * 1.1).round(2)

    total_spend_df = df.groupby('category').agg(
        Total_spend = ('amount','sum'),
        Average_check = ('amount', 'mean'),
        Future_total = ('future_amount','sum')
    ).round(2).sort_values('Total_spend', ascending=False)

    total_spend_df['Budget_Share_Pct'] = ((total_spend_df['Total_spend'] / df['amount'].sum()) * 100).round(2)
    return total_spend_df

if __name__ == "__main__":
    raw_data = generate_data(df)
    processed_df = preprocess_data(raw_data)
    report = get_report(processed_df)

    print(report)
    print(processed_df[['date', 'category', 'cat_share_in_rolling', 'deviation_pct']].head(10))