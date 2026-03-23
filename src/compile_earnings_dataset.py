import polars as pl
import os
import glob
import time
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Month-index horizons (prices are monthly bhavcopy settlements, ~1 row/month)
MONTHS_3YR = 36   # 3 years
MONTHS_5YR = 60   # 5 years

# Paths relative to this script's location (src/Data/)
_DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")

def compile_dataset():
    price_path  = os.path.join(_DATA_DIR, "distilled_prices.parquet")
    res_dir     = os.path.join(_DATA_DIR, "desiquant_aux", "results", "nse", "*.parquet")
    output_path = os.path.join(_DATA_DIR, "earnings_valuation_data.parquet")

    print("Loading distilled price database...")
    prices_df = pl.read_parquet(price_path)

    # Standardize dates
    if prices_df['TIMESTAMP'].dtype == pl.String:
        prices_df = prices_df.with_columns(
            pl.coalesce([
                pl.col('TIMESTAMP').str.strptime(pl.Date, "%d-%b-%Y", strict=False),
                pl.col('TIMESTAMP').str.strptime(pl.Date, "%Y-%m-%d", strict=False)
            ]).alias('date')
        )
    else:
        prices_df = prices_df.with_columns(pl.col('TIMESTAMP').cast(pl.Date).alias('date'))

    prices_df = prices_df.drop_nulls('date').sort(['SYMBOL', 'date'])

    print("Finding corporate results files...")
    res_files = glob.glob(res_dir)

    dataset_rows = []

    print(f"Extracting features from {len(res_files)} stocks...")
    start = time.time()

    for count, f in enumerate(res_files):
        if count > 0 and count % 200 == 0:
            elapsed = time.time() - start
            print(f"  Parsed {count}/{len(res_files)} stocks... ({elapsed:.0f}s elapsed)")

        try:
            symbol = os.path.basename(f).replace('.parquet', '')
            res_df = pl.read_parquet(f)

            required_cols = ['filingDate', 'resultsData2.re_net_profit', 'resultsData2.re_net_sale']
            if not all(c in res_df.columns for c in required_cols):
                continue

            # Basic EPS column for TTM P/E computation
            eps_col = 'resultsData2.re_basic_eps_for_cont_dic_opr'
            has_eps = eps_col in res_df.columns

            select_cols = [
                pl.col('filingDate'),
                pl.col('resultsData2.re_net_profit').alias('net_profit'),
                pl.col('resultsData2.re_net_sale').alias('revenue'),
            ]
            if has_eps:
                select_cols.append(pl.col(eps_col).alias('eps_basic'))

            events = res_df.select(select_cols).drop_nulls('filingDate')

            # Parse filing date — format: '26-Oct-2023 12:07'
            events = events.with_columns(
                pl.col('filingDate').str.split(' ').list.get(0)
                    .str.strptime(pl.Date, "%d-%b-%Y", strict=False)
                    .alias('event_date')
            ).drop_nulls('event_date')

            # Cast numeric columns stored as comma-formatted strings
            cast_cols = [
                pl.col('net_profit').str.replace_all(',', '').cast(pl.Float64, strict=False),
                pl.col('revenue').str.replace_all(',', '').cast(pl.Float64, strict=False),
            ]
            if has_eps:
                cast_cols.append(
                    pl.col('eps_basic').str.replace_all(',', '').cast(pl.Float64, strict=False)
                )
            events = events.with_columns(cast_cols).sort('event_date')

            # YoY growth (shift 4 quarters — quarterly data)
            events = events.with_columns([
                ((pl.col('net_profit') - pl.col('net_profit').shift(4)) /
                 pl.col('net_profit').shift(4).abs()).alias('profit_yoy_growth'),
                ((pl.col('revenue') - pl.col('revenue').shift(4)) /
                 pl.col('revenue').shift(4).abs()).alias('rev_yoy_growth'),
            ])

            # TTM EPS = rolling sum of last 4 quarters of basic EPS
            if has_eps:
                events = events.with_columns(
                    pl.col('eps_basic').rolling_sum(window_size=4, min_samples=4).alias('ttm_eps')
                )

            # Filter prices for this symbol
            s_prices = prices_df.filter(pl.col('SYMBOL') == symbol)
            if s_prices.height < 60:
                continue

            price_dates = s_prices['date'].to_list()
            price_closes = s_prices['CLOSE'].to_list()
            date_array = np.array([d.toordinal() for d in price_dates])
            n = len(date_array)

            def fwd_return(entry_price, idx, fwd_days):
                """Return percentage gain from entry to T+fwd_days. None if data unavailable."""
                target_idx = idx + fwd_days
                if target_idx >= n:
                    return None
                fwd_price = price_closes[target_idx]
                if fwd_price == 0 or entry_price == 0:
                    return None
                ret = (fwd_price - entry_price) / entry_price * 100
                # Exclude extreme outliers likely caused by splits / corporate actions
                if ret > 10000 or ret < -99:
                    return None
                return float(ret)

            for row in events.iter_rows(named=True):
                evt_date = row['event_date']
                if evt_date is None or row['profit_yoy_growth'] is None:
                    continue

                e_ord = evt_date.toordinal()
                idx = np.searchsorted(date_array, e_ord)

                # Need at least 6 prior monthly price points for valuation price
                if idx < 6 or idx >= n:
                    continue

                # Entry price: closest monthly settlement on or after the filing date
                entry_price = price_closes[idx]
                # Pre-event price: 6 months before filing (for trailing P/E)
                price_t_pre = price_closes[idx - 6]

                if entry_price == 0 or price_t_pre == 0:
                    continue

                # Trailing P/E = pre-event price / TTM EPS
                # Uses T-20 price to avoid look-ahead on the reaction day itself
                trailing_pe = None
                if has_eps:
                    ttm_eps = row.get('ttm_eps')
                    if ttm_eps is not None and ttm_eps > 0:
                        trailing_pe = price_t_pre / ttm_eps
                        if trailing_pe <= 0 or trailing_pe > 500:  # sanity cap
                            trailing_pe = None

                # Long-term forward returns (conditional on data availability)
                fwd_3yr = fwd_return(entry_price, idx, MONTHS_3YR)
                fwd_5yr = fwd_return(entry_price, idx, MONTHS_5YR)

                # Skip events where neither long-term window has realised yet
                if fwd_3yr is None and fwd_5yr is None:
                    continue

                dataset_rows.append({
                    'symbol': symbol,
                    'event_date': evt_date,
                    'net_profit': float(row['net_profit']) if row['net_profit'] is not None else None,
                    'profit_yoy_growth': float(row['profit_yoy_growth']),
                    'rev_yoy_growth': float(row['rev_yoy_growth']) if row['rev_yoy_growth'] is not None else 0.0,
                    'trailing_pe': trailing_pe,
                    'entry_price': float(entry_price),
                    'forward_3yr_%': fwd_3yr,
                    'forward_5yr_%': fwd_5yr,
                })

        except Exception:
            continue

    if dataset_rows:
        final_df = pl.DataFrame(dataset_rows)
        # Remove rows with inf / nan in key growth columns
        final_df = final_df.filter(
            ~pl.col('profit_yoy_growth').is_nan() &
            ~pl.col('profit_yoy_growth').is_infinite()
        )

        n_events = len(final_df)
        n_with_3yr = final_df.filter(pl.col('forward_3yr_%').is_not_null()).height
        n_with_5yr = final_df.filter(pl.col('forward_5yr_%').is_not_null()).height

        print(f"\nSUCCESS! Built Long-Term Earnings-Valuation Dataset:")
        print(f"  Total earnings events matched to price data : {n_events}")
        print(f"  Events with 3-year forward return available : {n_with_3yr}")
        print(f"  Events with 5-year forward return available : {n_with_5yr}")
        final_df.write_parquet(output_path)
        print(f"\nSaved to {output_path}")
        print("\nDataset Snapshot:")
        print(final_df.head(10))
    else:
        print("Failed to map any overlap between earnings ranges and price dates.")

if __name__ == "__main__":
    compile_dataset()
