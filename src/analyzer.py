import pandas as pd

def calculate_moving_averages(df: pd.DataFrame, window_sizes: list = [50, 200]) -> pd.DataFrame:
    """
    Calculates Simple Moving Averages (SMA) for given window sizes.
    """
    df_copy = df.copy()
    for window in window_sizes:
        # Check if 'Close' column exists, yfinance might return MultiIndex columns
        close_col = 'Close'
        if isinstance(df_copy.columns, pd.MultiIndex):
            df_copy[f'SMA_{window}'] = df_copy['Close'].rolling(window=window).mean()
        else:
            df_copy[f'SMA_{window}'] = df_copy[close_col].rolling(window=window).mean()
    return df_copy

def calculate_daily_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates daily returns based on the closing price.
    """
    df_copy = df.copy()
    if isinstance(df_copy.columns, pd.MultiIndex):
        df_copy['Daily_Return'] = df_copy['Close'].pct_change()
    else:
        df_copy['Daily_Return'] = df_copy['Close'].pct_change()
    return df_copy
