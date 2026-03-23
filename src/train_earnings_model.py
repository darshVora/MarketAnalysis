import polars as pl
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score
import pandas as pd
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")

def train_earnings_model():
    data_path = os.path.join(_DATA_DIR, "earnings_valuation_data.parquet")

    print("1. Loading Long-Term Earnings-Valuation Dataset...")
    df = pl.read_parquet(data_path).to_pandas()

    # Sort chronologically to prevent lookahead bias in training
    df.sort_values('event_date', inplace=True)

    # Clip extreme growth values (e.g. turnarounds from near-zero base)
    df = df[(df['profit_yoy_growth'] < 100) & (df['profit_yoy_growth'] > -100)]
    df = df[(df['rev_yoy_growth'] < 100) & (df['rev_yoy_growth'] > -100)]

    # Cap trailing P/E to a sensible range; drop loss-making (negative P/E)
    df = df[(df['trailing_pe'].isna()) | ((df['trailing_pe'] > 0) & (df['trailing_pe'] < 150))]

    print(f"Total earnings events in dataset: {len(df)}")
    print(f"  Events with 3-year forward return: {df['forward_3yr_%'].notna().sum()}")
    print(f"  Events with 5-year forward return: {df['forward_5yr_%'].notna().sum()}")

    # ── Train on 3-year horizon (primary) ──────────────────────────────────────
    print("\n2. Primary Model: 3-Year Forward Return")
    _train_model(df, target='forward_3yr_%', label='3-Year')

    # ── Train on 5-year horizon (secondary) ────────────────────────────────────
    print("\n3. Secondary Model: 5-Year Forward Return")
    _train_model(df, target='forward_5yr_%', label='5-Year')


def _train_model(df: pd.DataFrame, target: str, label: str):
    """Train and evaluate an XGBoost regressor for a given return horizon."""
    df_h = df.dropna(subset=['profit_yoy_growth', 'rev_yoy_growth', target])

    # Include trailing_pe only for rows where it is available
    has_pe = df_h['trailing_pe'].notna().sum() > 100
    features = ['profit_yoy_growth', 'rev_yoy_growth']
    if has_pe:
        features.append('trailing_pe')
        df_h = df_h.copy()
        df_h['trailing_pe'] = df_h['trailing_pe'].fillna(df_h['trailing_pe'].median())

    print(f"   Usable events for {label}: {len(df_h)}")
    print(f"   Features: {features}")
    print(f"   Target  : {target}")

    X = df_h[features]
    y = df_h[target]

    # Strict chronological split — first 80% train, last 20% test
    split_idx = int(len(df_h) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    print(f"   Train: {len(X_train)} events up to {df_h['event_date'].iloc[split_idx - 1].date()}")
    print(f"   Test : {len(X_test)} events from  {df_h['event_date'].iloc[split_idx].date()}")

    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    print(f"\n   ── {label} Out-of-Sample Performance ──")
    print(f"   Mean Absolute Error : {mae:.1f}%")
    print(f"   R²                  : {r2:.4f}")

    importance = pd.DataFrame({
        'Feature': features,
        'Importance': model.feature_importances_
    }).sort_values('Importance', ascending=False)
    print(f"\n   Factor Importances ({label}):")
    print(importance.to_string(index=False))

if __name__ == "__main__":
    train_earnings_model()
