import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import xgboost as xgb
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")

def build_and_train_model():
    nifty_path = os.path.join(_DATA_DIR, "NIFTY 50_day.csv")
    macro_path = os.path.join(_DATA_DIR, "macro_data.csv")
    
    print("1. Loading datasets...")
    df_nifty = pd.read_csv(nifty_path)
    df_macro = pd.read_csv(macro_path)
    
    # Standardize dates
    df_nifty['date'] = pd.to_datetime(df_nifty['date']).dt.normalize()
    df_macro['date'] = pd.to_datetime(df_macro['date']).dt.normalize()
    
    # Sort chronologically
    df_nifty.sort_values('date', inplace=True)
    df_macro.sort_values('date', inplace=True)
    
    print("2. Engineering Target Variable (20-day Forward Return)...")
    # We want to predict if the Nifty will be Higher (1) or Lower (0) 20 trading days from exactly now.
    # We do NOT use future data as features, only as the target `y`.
    df_nifty['Future_Close_20d'] = df_nifty['close'].shift(-20)
    df_nifty['Forward_Return_20d_%'] = ((df_nifty['Future_Close_20d'] - df_nifty['close']) / df_nifty['close']) * 100
    
    # Target: 1 if return > 0 (Bullish), 0 if return <= 0 (Bearish)
    df_nifty['Target_Direction'] = (df_nifty['Forward_Return_20d_%'] > 0).astype(int)
    
    # Drop the last 20 rows because we inherently don't know their future outcome yet
    df_nifty.dropna(subset=['Future_Close_20d'], inplace=True)
    
    print("3. Merging Nifty Targets with Macro Features...")
    df = pd.merge(df_nifty[['date', 'open', 'high', 'low', 'close', 'volume', 'Target_Direction', 'Forward_Return_20d_%']], 
                  df_macro, on='date', how='inner')
                  
    print("NaN counts per column before cleaning:")
    # Strip any accidental duplicate columns coming from multiple merges
    df = df.loc[:, ~df.columns.str.contains('_x|_y')]
    print(df.isna().sum())
    
    # Aggressively forward-fill macro features inside the joined dataframe to patch any isolated holes
    macro_cols = [c for c in df.columns if c not in ['date', 'open', 'high', 'low', 'close', 'volume', 'Target_Direction', 'Forward_Return_20d_%']]
    df[macro_cols] = df[macro_cols].ffill()
    
    # Backward fill to populate the earliest years (e.g. 2000-2007) so we don't throw away 20 years of data just because one metric started late
    df[macro_cols] = df[macro_cols].bfill()
    
    # Now drop any completely corrupted rows
    df.dropna(inplace=True)
    
    print(f"Final aligned dataset contains {len(df)} trading days.")
    
    print("4. Preparing Train/Test Split (Chronological)...")
    # Feature selection (dropping Date, Target, and any future-looking columns)
    features = [col for col in df.columns if col not in ['date', 'Target_Direction', 'Forward_Return_20d_%', 'Future_Close_20d']]
    
    X = df[features]
    y = df['Target_Direction']
    
    # NEVER use standard random train_test_split for time series! Always split sequentially.
    # We'll use the first 80% of time for training, last 20% for testing.
    split_idx = int(len(df) * 0.8)
    
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    print(f"Training exactly on {len(X_train)} days up to {df['date'].iloc[split_idx-1].date()}")
    print(f"Testing completely strictly on unseen {len(X_test)} days from {df['date'].iloc[split_idx].date()} onwards.")
    
    print("\n5. Training XGBoost Classifier...")
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    
    print("\n6. Evaluating the Model on strictly UNSEEN test data...")
    predictions = model.predict(X_test)
    
    acc = accuracy_score(y_test, predictions)
    print(f"\n==== Model Accuracy: {acc * 100:.2f}% ====")
    print("\nClassification Report:")
    print(classification_report(y_test, predictions))
    
    print("Confusion Matrix (predicted_bear, predicted_bull vs actual_bear, actual_bull):")
    print(confusion_matrix(y_test, predictions))
    
    print("\n7. Extracting Macro Feature Importance...")
    importance = pd.DataFrame({
        'Feature': features,
        'Importance': model.feature_importances_
    }).sort_values(by='Importance', ascending=False)
    
    print("\nTop 10 Macro Drivers dictating Nifty moves:")
    print(importance.head(10).to_string(index=False))

if __name__ == "__main__":
    build_and_train_model()
