from src.data_fetcher import fetch_stock_data
from src.analyzer import calculate_moving_averages, calculate_daily_returns

def main():
    # Example: Analyze Reliance Industries (NSE) and Tata Consultancy Services (NSE)
    tickers = ['RELIANCE.NS', 'TCS.NS']
    start = '2023-01-01'
    end = '2024-01-01'
    
    for ticker in tickers:
        print(f"\n{'='*40}")
        print(f"Analyzing {ticker}")
        print(f"{'='*40}")
        
        # 1. Fetch Data
        data = fetch_stock_data(ticker, start, end)
        
        if data.empty:
            print("No data fetched. Please check the ticker symbol and dates.")
            continue
            
        print("\nData fetched successfully. First few rows:")
        print(data.head())
        
        # 2. Analyze Data
        print("\nCalculating moving averages (50 and 200 days)...")
        data_with_ma = calculate_moving_averages(data)
        
        print("Calculating daily returns...")
        data_analyzed = calculate_daily_returns(data_with_ma)
        
        print("\nAnalysis complete. Latest data snapshot:")
        print(data_analyzed.tail())

if __name__ == "__main__":
    main()
