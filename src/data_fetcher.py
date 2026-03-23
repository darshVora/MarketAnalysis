import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker_symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetches historical stock data from Yahoo Finance.
    For Indian stocks, append '.NS' for NSE or '.BO' for BSE.
    Example: Reliance on NSE is 'RELIANCE.NS'
    """
    print(f"Fetching data for {ticker_symbol} from {start_date} to {end_date}...")
    stock_data = yf.download(ticker_symbol, start=start_date, end=end_date)
    return stock_data
