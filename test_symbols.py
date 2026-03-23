import yfinance as yf

symbols = ['^NSEI', '^NSEBANK', '^NN50', '^NSEMDCP50', '^NSMIDCP', '^CNXSC', '^NSESCP', 'NIFTY_NEXT_50.NS']
for s in symbols:
    tkr = yf.Ticker(s)
    hist = tkr.history(period='5d')
    if not hist.empty:
        print(f"{s}: found {len(hist)} days of data")
    else:
        print(f"{s}: no data")
